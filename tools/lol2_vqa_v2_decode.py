#!/usr/bin/env python3
"""Decoder for Lands of Lore II VQA version 2 movies.

Rules checked against the original movies (see docs/lol2-vqa-v2.md):

- Block size is 4x4 or 4x2. A vector is block_w * block_h bytes.
- VPTZ is LCW; VPT0 is raw. Either one decodes to two planes of `blocks` bytes,
  low then high. High byte 0xFF is a solid block of colour `low`. Any other
  index is high * 256 + low into the codebook.
- CPL0 is 768 bytes of 6-bit palette, expanded (v << 2) | (v >> 4).
- A full codebook is CBFZ (LCW) or CBF0 (raw), and it is used on the same frame.
- When VQHD byte 13 is N > 0, the next codebook is N parts (CBPZ compressed, or
  CBP0 raw). The parts are joined after the frame that carries the Nth part and
  used from the next frame on.
- When byte 13 is 0, CINF/CIND schedules the swap. Each CIND entry is a
  little-endian u16 frame and a u32 size. A non-zero size on frame F is the
  byte length of the CBPZ parts staged on earlier frames; those bytes are one
  LCW stream and become the codebook on frame F, before that frame is drawn.
  The size on frame 0 is the compressed length of that frame's CBFZ.
- Top-level VQFL chunks are seek snapshots. Linear playback skips them.
- VPRZ (LCW) and VPTR (raw) are a different pointer stream. The codebook still
  has to be whole vectors; their u16 commands are validated (validate_pointer_stream)
  but not expanded to pixels.

Malformed data and unknown chunks raise VQAError.

Requires Python 3.10+ and NumPy. Pillow is needed only for --out.

    python3 tools/lol2_vqa_v2_decode.py ./lol2_game/DAT/CHUT.MIX
    python3 tools/lol2_vqa_v2_decode.py ./lol2_game/DAT/CHUT.MIX --entry 3 --out frames/
"""
import argparse
import os
import sys
from pathlib import Path
from struct import unpack_from

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lol2_cli  # noqa: E402


class VQAError(ValueError):
    """Malformed or unsupported VQA input."""

VQHD_SIZE = 42
KNOWN_TAGS = {b'CBFZ', b'CBPZ', b'CPL0', b'VPTZ', b'CBF0', b'CBP0', b'VPT0', b'VPRZ', b'VPTR'}
POINTER_TAGS = {b'VPTZ', b'VPT0', b'VPRZ', b'VPTR'}
BLOCK_SIZES = {(4, 4), (4, 2)}


def chunks(data: bytes, start: int = 0, end: int | None = None, where: str = 'file') -> list:
    """IFF chunks (4-byte tag, big-endian u32 size, payload, pad to even) between start and end."""
    end = len(data) if end is None else end
    out = []
    i = start
    while i < end:
        if end - i < 8:
            raise VQAError(f'{where}: truncated chunk header at {i}')
        tag = bytes(data[i:i + 4])
        size = int.from_bytes(data[i + 4:i + 8], 'big')
        if not all(0x20 <= c < 0x7f for c in tag):
            raise VQAError(f'{where}: invalid chunk tag {tag!r} at {i}')
        body = i + 8
        if size > end - body:
            raise VQAError(f'{where}: chunk {tag.decode()} size {size} exceeds data at {i}')
        out.append((tag, bytes(data[body:body + size])))
        i = body + size + (size & 1)
    if i > end:
        raise VQAError(f'{where}: chunk padding overruns data')
    return out


def _lcw(src: bytes, where: str) -> bytes:
    try:
        return lcw(src)
    except VQAError as error:
        raise VQAError(f'{where}: {error}') from error


def lcw(src: bytes) -> bytes:
    """Strict Westwood LCW (Format80). The stream must end with 0x80."""
    d = bytearray()
    i = 0
    n = len(src)

    def need(k):
        if i + k > n:
            raise VQAError(f'LCW: truncated command at {i}')

    while True:
        need(1)
        op = src[i]
        i += 1
        if op == 0x80:
            return bytes(d)
        if op < 0x80:
            need(1)
            count = ((op & 0x70) >> 4) + 3
            off = ((op & 0x0F) << 8) | src[i]
            i += 1
            s = len(d) - off
            if off == 0 or s < 0:
                raise VQAError(f'LCW: relative reference {off} outside output at {i}')
        elif op < 0xC0:
            count = op & 0x3F
            need(count)
            d += src[i:i + count]
            i += count
            continue
        elif op == 0xFE:
            need(3)
            count = src[i] | src[i + 1] << 8
            d += bytes([src[i + 2]]) * count
            i += 3
            continue
        else:
            if op == 0xFF:
                need(4)
                count = src[i] | src[i + 1] << 8
                s = src[i + 2] | src[i + 3] << 8
                i += 4
            else:
                need(2)
                count = (op & 0x3F) + 3
                s = src[i] | src[i + 1] << 8
                i += 2
            if s >= len(d):
                raise VQAError(f'LCW: absolute reference {s} outside output ({len(d)}) at {i}')
        for k in range(count):
            d.append(d[s + k])


def header(blob: bytes) -> tuple:
    """(top-level chunks, VQHD fields) for a WVQA FORM."""
    if len(blob) < 12 or blob[:4] != b'FORM':
        raise VQAError('not an IFF FORM')
    size = int.from_bytes(blob[4:8], 'big')
    if size < 4 or size + 8 > len(blob):
        raise VQAError(f'FORM size {size} exceeds file ({len(blob)})')
    if blob[8:12] != b'WVQA':
        raise VQAError('FORM type is not WVQA')
    top = chunks(blob, 12, 8 + size, 'FORM')
    hd = [pl for t, pl in top if t == b'VQHD']
    if len(hd) != 1:
        raise VQAError(f'expected one VQHD, found {len(hd)}')
    hd = hd[0]
    if len(hd) != VQHD_SIZE:
        raise VQAError(f'VQHD is {len(hd)} bytes, expected {VQHD_SIZE}')
    f = dict(
        version=int.from_bytes(hd[0:2], 'little'),
        flags=int.from_bytes(hd[2:4], 'little'),
        frames=int.from_bytes(hd[4:6], 'little'),
        width=int.from_bytes(hd[6:8], 'little'),
        height=int.from_bytes(hd[8:10], 'little'),
        block_w=hd[10], block_h=hd[11], fps=hd[12], parts=hd[13],
        colors=int.from_bytes(hd[14:16], 'little'))
    count = sum(t == b'VQFR' for t, _ in top)
    if count != f['frames']:
        raise VQAError(f"VQFR frame count {count} does not match VQHD frame count {f['frames']}")
    return top, f


def _supported(f: dict) -> None:
    if f['version'] != 2:
        raise VQAError(f"unsupported VQA version {f['version']}")
    if (f['block_w'], f['block_h']) not in BLOCK_SIZES:
        raise VQAError(f"unsupported block size {f['block_w']}x{f['block_h']}")
    bw, bh = f['block_w'], f['block_h']
    if f['width'] <= 0 or f['height'] <= 0 or f['width'] % bw or f['height'] % bh:
        raise VQAError(f"invalid frame size {f['width']}x{f['height']} for {bw}x{bh} blocks")
    if f['colors'] != 256:
        raise VQAError(f"color count {f['colors']}")


def cinf_schedule(top) -> dict:
    """Map frame number -> compressed codebook size from the first CINF/CIND chunk."""
    swaps = None
    for t, pl in top:
        if t != b'CINF':
            continue
        if swaps is not None:
            raise VQAError('more than one CINF chunk')
        swaps = {}
        found = False
        for st, sp in chunks(pl, where='CINF'):
            if st != b'CIND':
                continue
            if found:
                raise VQAError('more than one CIND chunk')
            found = True
            if len(sp) % 6:
                raise VQAError(f'CIND is {len(sp)} bytes, not a multiple of 6')
            for i in range(0, len(sp), 6):
                frame = int.from_bytes(sp[i:i + 2], 'little')
                size = int.from_bytes(sp[i + 2:i + 6], 'little')
                if frame in swaps:
                    raise VQAError(f'CIND lists frame {frame} twice')
                swaps[frame] = size
        if not found:
            raise VQAError('CINF has no CIND chunk')
    return swaps or {}


def _book(raw: bytes, vec: int, where: str):
    if not raw or len(raw) % vec:
        raise VQAError(f'{where}: codebook is {len(raw)} bytes (not whole {vec}-byte vectors)')
    return np.frombuffer(raw, np.uint8).copy()


def validate_pointer_stream(raw: bytes, columns: int, rows: int, vectors: int, where: str):
    """Check the indexed VPR command words at LOLG.DAT 0x17D412–0x17D847."""
    at = 0
    block = 0
    while block < columns * rows:
        if at + 2 > len(raw):
            raise VQAError(f'{where}: truncated pointer command at {at}')
        word, = unpack_from('<H', raw, at)
        at += 2
        opcode = word >> 12
        count = 1
        vector = None
        if opcode < 8:
            vector = word
        elif opcode == 0xA:
            count = word & 0xFFF
            if at + 2 > len(raw):
                raise VQAError(f'{where}: truncated repeated block at {at}')
            nested, = unpack_from('<H', raw, at)
            at += 2
            if nested < 0x8000:
                vector = nested
            elif nested >= 0xC000:
                vector = nested & 0xFFF
        elif opcode == 0xB:
            count = (word >> 8) & 0xF
        elif opcode == 0xC:
            count = word & 0xFFF
            if count & 1 or at + count > len(raw):
                raise VQAError(f'{where}: invalid literal colour span at {at}')
            at += count
        elif opcode == 0xE:
            vector = word & 0xFFF
        elif opcode != 0xF:
            raise VQAError(f'{where}: unknown pointer command {word:#06x}')
        if not count or block % columns + count > columns:
            raise VQAError(f'{where}: pointer run {word:#06x} crosses a row at block {block}')
        if vector is not None and vector >= vectors:
            raise VQAError(f'{where}: vector {vector} outside codebook of {vectors}')
        block += count
    if at != len(raw):
        raise VQAError(f'{where}: {len(raw) - at} unread pointer bytes')


def decode(blob: bytes, pixels: bool = False):
    """Yield ('vpt', rgb_or_None) or ('stream', None) for each frame.

    rgb is an (H, W, 3) uint8 array when pixels is set and the frame uses a
    pointer table. A VPRZ/VPTR frame yields 'stream' and is not expanded.
    """
    top, f = header(blob)
    _supported(f)
    bw, bh = f['block_w'], f['block_h']
    vec = bw * bh
    w, h, per = f['width'], f['height'], f['parts']
    gx, gy = w // bw, h // bh
    n = gx * gy
    vqfr = [pl for t, pl in top if t == b'VQFR']
    if not vqfr:
        raise VQAError('no VQFR frames')
    swaps = cinf_schedule(top) if per == 0 else {}
    cb = None
    pal = None
    pending = b''
    pending_z = None
    staged = 0
    for fi, pl in enumerate(vqfr):
        if per == 0 and pending and swaps.get(fi):
            if len(pending) != swaps[fi]:
                raise VQAError(
                    f'VQFR {fi}: staged codebook is {len(pending)} bytes, CIND says {swaps[fi]}')
            raw = _lcw(pending, f'VQFR {fi} scheduled codebook') if pending_z else pending
            cb = _book(raw, vec, f'VQFR {fi} scheduled codebook')
            pending = b''
            pending_z = None
            staged = 0
        sub = chunks(pl, where=f'VQFR {fi}')
        seen = set()
        for t, _ in sub:
            if t not in KNOWN_TAGS:
                raise VQAError(f'VQFR {fi}: unknown sub-chunk {t!r}')
            if t in seen:
                raise VQAError(f'VQFR {fi}: duplicate sub-chunk {t.decode()}')
            seen.add(t)
        parts = dict(sub)
        pointers = seen & POINTER_TAGS
        if len(pointers) != 1:
            raise VQAError(f'VQFR {fi}: pointer chunks {sorted(t.decode() for t in pointers)}')
        if b'CPL0' in parts:
            if len(parts[b'CPL0']) != 768:
                raise VQAError(f"VQFR {fi}: CPL0 is {len(parts[b'CPL0'])} bytes, expected 768")
            p = np.frombuffer(parts[b'CPL0'], np.uint8).astype(np.uint16) & 63
            pal = ((p << 2) | (p >> 4)).astype(np.uint8).reshape(-1, 3)
        if b'CBF0' in parts:
            cb = _book(parts[b'CBF0'], vec, f'VQFR {fi} CBF0')
        if b'CBFZ' in parts:
            comp = parts[b'CBFZ']
            if fi == 0 and per == 0 and swaps.get(0) not in (None, 0) and swaps[0] != len(comp):
                raise VQAError(
                    f'VQFR 0: CBFZ is {len(comp)} bytes, CIND says {swaps[0]}')
            cb = _book(_lcw(comp, f'VQFR {fi} CBFZ'), vec, f'VQFR {fi} CBFZ')
        if pal is None:
            raise VQAError(f'VQFR {fi}: no palette before the first rendered frame')
        if cb is None:
            raise VQAError(f'VQFR {fi}: no codebook before the first rendered frame')
        kind = 'vpt'
        rgb = None
        if b'VPRZ' in parts or b'VPTR' in parts:
            kind = 'stream'
            tag = next(iter(pointers))
            where = f'VQFR {fi} {tag.decode()}'
            raw = _lcw(parts[tag], where) if tag == b'VPRZ' else parts[tag]
            validate_pointer_stream(raw, gx, gy, len(cb) // vec, where)
        else:
            raw = _lcw(parts[b'VPTZ'], f'VQFR {fi} VPTZ') if b'VPTZ' in parts else parts[b'VPT0']
            if len(raw) != 2 * n:
                raise VQAError(f'VQFR {fi}: pointer table is {len(raw)} bytes, expected {2 * n}')
            lo = np.frombuffer(raw[:n], np.uint8).astype(np.int64)
            hi = np.frombuffer(raw[n:], np.uint8).astype(np.int64)
            solid = hi == 0xFF
            nvec = len(cb) // vec
            index = hi * 256 + lo
            if (index[~solid] >= nvec).any():
                raise VQAError(
                    f'VQFR {fi}: vector {int(index[~solid].max())} outside codebook of {nvec}')
            if pixels:
                table = cb.reshape(nvec, bh, bw)
                picked = table[np.where(solid, 0, index)]
                blocks = np.where(solid[:, None, None], lo[:, None, None].astype(np.uint8), picked)
                rgb = pal[blocks.reshape(gy, gx, bh, bw).transpose(0, 2, 1, 3).reshape(h, w)]
        yield kind, rgb
        part = parts.get(b'CBPZ', parts.get(b'CBP0'))
        if part is not None:
            z = b'CBPZ' in parts
            if pending and pending_z is not None and pending_z != z:
                raise VQAError(f'VQFR {fi}: codebook parts mix CBP0 and CBPZ')
            pending += part
            pending_z = z
            staged += 1
            if per > 0 and staged == per:
                raw = _lcw(pending, f'VQFR {fi} partial codebook') if pending_z else pending
                cb = _book(raw, vec, f'VQFR {fi} partial codebook')
                pending = b''
                pending_z = None
                staged = 0
    if per == 0 and pending:
        raise VQAError(f'{len(pending)} codebook bytes were staged and never scheduled')


def frames(blob: bytes):
    """Yield RGB frames for a pointer-table movie. Raises if any frame is a pointer stream."""
    for kind, rgb in decode(blob, pixels=True):
        if kind != 'vpt':
            raise VQAError('pointer stream (VPRZ/VPTR) is not expanded to pixels')
        yield rgb


def save_frames(blob: bytes, folder: Path) -> int:
    """Write %04d.png frames (1-based). Returns the frame count."""
    from PIL import Image
    folder.mkdir(parents=True, exist_ok=True)
    count = 0
    for i, rgb in enumerate(frames(blob)):
        Image.fromarray(rgb).save(folder / f'{i + 1:04d}.png')
        count += 1
    return count


def _mix_entries(data: bytes):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lol2_source_format import parse_mix
    return parse_mix(data)


def _layout(f: dict, stream: bool) -> str:
    if stream:
        return 'pointer-stream'
    if f['block_w'] == 4 and f['block_h'] == 2:
        return '4x2'
    if f['parts'] == 0:
        return 'parts 0'
    return 'partial codebook'


def _frame_tag_counts(payload: bytes, where: str) -> dict:
    """Count sub-chunk tags in one VQFR without copying the payloads."""
    counts = {}
    i = 0
    end = len(payload)
    while i < end:
        if end - i < 8:
            raise VQAError(f'{where}: truncated chunk header at {i}')
        tag = bytes(payload[i:i + 4])
        size = int.from_bytes(payload[i + 4:i + 8], 'big')
        if not all(0x20 <= c < 0x7f for c in tag):
            raise VQAError(f'{where}: invalid chunk tag {tag!r} at {i}')
        if size > end - (i + 8):
            raise VQAError(f'{where}: chunk {tag.decode()} size {size} exceeds data at {i}')
        counts[tag] = counts.get(tag, 0) + 1
        i += 8 + size + (size & 1)
    if i != end:
        raise VQAError(f'{where}: chunk padding overruns data')
    return counts


def _census(folder):
    """Header and chunk census. Does not run LCW."""
    total = streams = 0
    layouts = {}
    staged = single = 0
    bad = []
    for mix in sorted(Path(folder).glob('*.[Mm][Ii][Xx]')):
        data = mix.read_bytes()
        try:
            entries = _mix_entries(data)
        except Exception:
            continue
        for e in entries:
            blob = data[e['offset']:e['offset'] + e['size']]
            if len(blob) < 12 or blob[:4] != b'FORM' or blob[8:12] != b'WVQA':
                continue
            total += 1
            try:
                top, f = header(blob)
                _supported(f)
                tags = {}
                for fi, pl in enumerate(pl for t, pl in top if t == b'VQFR'):
                    for tag, n in _frame_tag_counts(pl, f'VQFR {fi}').items():
                        tags[tag] = tags.get(tag, 0) + n
            except VQAError as error:
                bad.append(f'{mix.name}#{e["index"]}: {error}')
                continue
            if tags.get(b'VPRZ') or tags.get(b'VPTR'):
                streams += 1
                continue
            key = _layout(f, False)
            layouts[key] = layouts.get(key, 0) + 1
            if f['parts'] == 0:
                if tags.get(b'CBPZ'):
                    staged += 1
                elif tags.get(b'CBFZ') == 1 and not tags.get(b'CBF0'):
                    single += 1
    return total, streams, layouts, staged, single, bad


def _sample_decode(folder, bad):
    """Decode one movie of each layout. Returns the sample text."""
    samples = {
        ('L4_HJI.MIX', 67): None,
        ('L10_DCI.MIX', 40): None,
        ('L20_BBI.MIX', 403): None,
        ('POOL.MIX', 4): None,
        ('CAN.MIX', 22): None,
    }
    for mix_name, index in samples:
        try:
            blob = _entry_blob(folder, mix_name, index)
            _, f = header(blob)
            saw = {'vpt': 0, 'stream': 0}
            for kind, _rgb in decode(blob, pixels=False):
                saw[kind] += 1
            samples[(mix_name, index)] = (f, saw)
        except VQAError as error:
            bad.append(f'{mix_name}#{index}: {error}')
    expect = {
        ('L4_HJI.MIX', 67): ('vpt', 9, 4, 4, 8),
        ('L10_DCI.MIX', 40): ('vpt', 129, 4, 2, 8),
        ('L20_BBI.MIX', 403): ('vpt', 312, 4, 4, 0),
        ('POOL.MIX', 4): ('vpt', 231, 4, 4, 8),
        ('CAN.MIX', 22): ('stream', 20, 4, 4, 0),
    }
    bits = []
    for key, want in expect.items():
        got = samples.get(key)
        kind, frames_n, bw, bh, parts = want
        if got is None:
            bad.append(f'missing sample {key[0]} entry {key[1]}')
            continue
        f, saw = got
        if saw[kind] != frames_n or f['block_w'] != bw or f['block_h'] != bh or f['parts'] != parts:
            bad.append(f'sample {key[0]}#{key[1]} is {f} {saw}, expected {want}')
        elif kind == 'vpt':
            bits.append(f'{key[0]} entry {key[1]} {frames_n}/{frames_n}')
    if samples.get(('L4_HJI.MIX', 67)) is not None and not any(b.startswith('L4_HJI.MIX#67') for b in bad):
        n = sum(1 for _ in frames(_entry_blob(folder, 'L4_HJI.MIX', 67)))
        if n != 9:
            bad.append(f'L4_HJI.MIX entry 67 expanded {n} frames')
    return bits


def _walk_all(folder):
    """Decode every movie. Relative-reference failures are returned apart from other errors."""
    bad = []
    layouts = {}
    streams = 0
    total = 0
    for mix in sorted(Path(folder).glob('*.[Mm][Ii][Xx]')):
        data = mix.read_bytes()
        try:
            entries = _mix_entries(data)
        except Exception:
            continue
        for e in entries:
            blob = data[e['offset']:e['offset'] + e['size']]
            if len(blob) < 12 or blob[:4] != b'FORM' or blob[8:12] != b'WVQA':
                continue
            total += 1
            try:
                _, f = header(blob)
                saw = {'vpt': 0, 'stream': 0}
                for kind, _rgb in decode(blob, pixels=False):
                    saw[kind] += 1
                if saw['vpt'] + saw['stream'] != f['frames']:
                    raise VQAError(f"decoded {saw['vpt'] + saw['stream']} of {f['frames']} frames")
                if saw['stream'] and saw['vpt']:
                    raise VQAError('frame mixes a pointer table with a pointer stream')
                if saw['stream']:
                    streams += 1
                else:
                    key = _layout(f, False)
                    layouts[key] = layouts.get(key, 0) + 1
            except VQAError as error:
                bad.append(f'{mix.name}#{e["index"]}: {error}')
    # Accept only a relative copy inside the LCW stream. The frame number is the
    # one the decoder reports; it is not a separate filter on the movie name.
    open_rel = [b for b in bad if 'relative reference' in b]
    bad = [b for b in bad if b not in open_rel]
    return total, streams, layouts, open_rel, bad


def check(folder, full=False) -> int:
    """Census plus one sample of each layout. --full also walks every movie."""
    if folder is None:
        print('CHECK vqa: no --data folder given')
        return 1
    total, streams, layouts, staged, single, bad = _census(folder)
    bits = _sample_decode(folder, bad)
    four = ', '.join(f'{k} {layouts.get(k, 0)}' for k in ('partial codebook', '4x2', 'parts 0'))
    ok = (not bad and total == 1948 and streams == 837 and layouts.get('partial codebook') == 976
          and layouts.get('4x2') == 5 and layouts.get('parts 0') == 130 and staged == 10 and single == 120)
    if full:
        w_total, w_streams, w_layouts, open_rel, w_bad = _walk_all(folder)
        bad.extend(w_bad)
        named = '; '.join(open_rel) if open_rel else 'none'
        print(f'CHECK vqa full: {w_total} WVQA; pointer tables {sum(w_layouts.values())} '
              f'(partial codebook {w_layouts.get("partial codebook", 0)}, 4x2 {w_layouts.get("4x2", 0)}, '
              f'parts 0 {w_layouts.get("parts 0", 0)}); pointer-stream {w_streams}; '
              f'relative-reference frames: {named}; bad={bad[:3] or "none"}')
        expected_relative_references = {
            'L20_BBI.MIX#25: VQFR 115 VPTZ: LCW: relative reference 0 outside output at 23849',
            'SPKSTON2.MIX#4: VQFR 492 VPTZ: LCW: relative reference 674 outside output at 549',
        }
        ok = (ok and not bad and w_total == 1948 and w_streams == 837
              and sum(w_layouts.values()) == 1109 and w_layouts.get('partial codebook') == 974
              and w_layouts.get('4x2') == 5 and w_layouts.get('parts 0') == 130
              and len(open_rel) == 2 and set(open_rel) == expected_relative_references)
        return 0 if ok else 1
    print(f'CHECK vqa: {total} WVQA; pointer-table headers {sum(layouts.values())} ({four}; '
          f'of parts 0, {staged} stage CBPZ and {single} have a single CBFZ); '
          f'pointer-stream {streams}; samples: {", ".join(bits)}; full frame walk is --full; '
          f'bad={bad[:3] or "none"}')
    return 0 if ok else 1


def _entry_blob(folder, mix_name, index):
    data = (Path(folder) / mix_name).read_bytes()
    for e in _mix_entries(data):
        if e['index'] == index:
            return data[e['offset']:e['offset'] + e['size']]
    raise VQAError(f'{mix_name} entry {index} missing')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Decode LoL2 VQA v2 movies (see docs/lol2-vqa-v2.md).')
    ap.add_argument('path', type=Path, nargs='?', help='a .VQA file, or a MIX archive (read only)')
    ap.add_argument('--entry', type=int, help='MIX entry index to decode')
    ap.add_argument('--key', type=lambda s: int(s, 0), help='MIX entry key (hash) to decode')
    ap.add_argument('--out', type=Path, help='write PNG frames here (needs Pillow)')
    ap.add_argument('--check', action='store_true',
                    help='census and one sample of each layout; one line')
    ap.add_argument('--full', action='store_true',
                    help='with --check, also decode every movie (slow)')
    ap.add_argument('--data', type=Path, default=os.environ.get('LOL2_DAT'), help='DAT folder (default $LOL2_DAT)')
    a = ap.parse_args(argv)
    if a.out is not None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from lol2_cli import refuse_repo_output
        refuse_repo_output(a.out)
    if a.check or a.full:
        return check(a.data, full=a.full)
    if a.path is None:
        ap.print_help(); return 2
    data = Path(lol2_cli.resolve_input(a.path, a.data)).read_bytes()
    if data[:4] == b'FORM':
        blobs = [('file', data)]
    else:
        entries = _mix_entries(data)
        if a.entry is not None or a.key is not None:
            hit = [e for e in entries if e['index'] == a.entry or e['key'] == a.key]
            if len(hit) != 1:
                ap.error('entry not found')
            e = hit[0]
            blobs = [(f"entry {e['index']} key {e['key']:#010x}", data[e['offset']:e['offset'] + e['size']])]
        else:
            blobs = [(f"entry {e['index']} key {e['key']:#010x}", data[e['offset']:e['offset'] + e['size']])
                     for e in entries if len(data) >= e['offset'] + 12 and data[e['offset'] + 8:e['offset'] + 12] == b'WVQA']
    status = 0
    for name, blob in blobs:
        try:
            _, f = header(blob)
            _supported(f)
            saw = {'vpt': 0, 'stream': 0}
            for kind, _rgb in decode(blob, pixels=False):
                saw[kind] += 1
        except VQAError as error:
            print(f'{name}: VQAError: {error}')
            status = 1
            continue
        if saw['stream']:
            kind = 'pointer stream (codebook checked, pixels not expanded)'
        else:
            kind = _layout(f, False)
        print(f"{name}: v{f['version']} {f['width']}x{f['height']} {f['frames']} frames, "
              f"{f['block_w']}x{f['block_h']} blocks, {f['fps']} fps, parts {f['parts']}: {kind}")
        if a.out is not None and len(blobs) == 1:
            if saw['stream']:
                ap.error('this movie uses a pointer stream; pixels are not written')
            print(f'wrote {save_frames(blob, a.out)} frames to {a.out}')
    if a.out is not None and len(blobs) != 1:
        ap.error('--out needs a single movie (give --entry or --key for a MIX)')
    return status


if __name__ == '__main__':
    sys.exit(main())
