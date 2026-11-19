#!/usr/bin/env python3
"""Read LoL2 level texture containers (.TE_ entries in level MIX files).

A level MIX such as DAT/L1_DC.MIX holds one texture entry named
SPHERE<n>\\<LEVEL>\\<LEVEL>.TE_ (Westwood TD/RA filename hash). The entry is
LZO1X-blocked: u32 total size, then (u32 compressed size, LZO1X block) pairs
of up to 1 MiB decoded each, then a 4-byte zero trailer.

The decoded blob starts with u32 section count, u32 palette offset (seen in
L20_BB; see docs), then the section offset table at +8.
  section 2: 56-byte material descriptors ('<6H11I')
  section 3: material payload records referenced by the descriptors
  section 4: 256-byte shade (remap) rows

Ten flag values share one raw layout: 8-bit indices after an 8-byte header,
stored column by column. The check covers those, the 22-byte movie-name
records, row spans, run-length columns, and vector-coded rows and their
companion codebooks.

Requirements: Python 3.9+ standard library and the system liblzo2 shared
library (Debian/Ubuntu: liblzo2-2). It is loaded through ctypes; no python-lzo
package is needed. Reads only the user's own game files.

Usage:
  lol2_texture_container.py info     --mix DAT/L1_DC.MIX
  lol2_texture_container.py material --mix DAT/L1_DC.MIX --index 1
  lol2_texture_container.py export   --mix DAT/L1_DC.MIX --index 1 --out DIR
  lol2_texture_container.py blob     --mix DAT/L1_DC.MIX --out l1_dc.bin
  lol2_texture_container.py --check --data DAT
"""
from cli_errors import ReaderArgumentParser, run_cli
import argparse
import collections
import ctypes
import ctypes.util
import hashlib
import json
import os
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lol2_mix_parser import read_mix_with_hashes  # noqa: E402
from lol2_westwood_hash import ww_hash_v1  # noqa: E402
from lol2_decompress_westwood import decompress_westwood  # noqa: E402
import lol2_cli  # noqa: E402

MAX_DECOMPRESSED = 64 * 1024 * 1024
LZO_BLOCK = 1024 * 1024
DESCRIPTOR_SIZE = 56
DESCRIPTOR_FORMAT = "<6H11I"
SHADE_ROW_BYTES = 256
INITIAL_SHADE_ROW = 64
# Same 8-byte header and width*height index bytes. 0x8000 and 0x2000 do not
# change that layout. Measured on every mip of all 15 level containers.
RAW_LAYOUT_FLAGS = frozenset({
    0x008B, 0x00A9, 0x00C3, 0x00E1,
    0x20C3, 0x20E1,
    0x808B, 0x80A9, 0x80C3, 0x80E1,
})
NAME_FLAGS = frozenset({0x0143, 0x0161, 0x0342})
# Fourth header word is the payload length (record size minus 8).
PAYLOAD_FLAGS = frozenset({
    0x008F, 0x00C7, 0x028E, 0x02AC, 0x02C6,
    0x20C7, 0x808F, 0x80C7, 0x828E, 0x82C6,
})
FIELD8_IS_ONE = frozenset({
    0x008B, 0x008F, 0x00A9, 0x028E, 0x02AC, 0x808B, 0x808F, 0x80A9, 0x828E,
})
EXPECTED_COUNTS = {
    0x0000: 15, 0x008B: 74, 0x008F: 225, 0x00A9: 863, 0x00C3: 359, 0x00C7: 790,
    0x00E1: 570, 0x0143: 23, 0x0161: 1, 0x028E: 794, 0x02AC: 2, 0x02C6: 4785,
    0x0342: 857, 0x1246: 27889, 0x20C3: 36, 0x20C7: 25, 0x20E1: 19, 0x808B: 14,
    0x808F: 23, 0x80A9: 47, 0x80C3: 19, 0x80C7: 74, 0x80E1: 38, 0x828E: 70,
    0x82C6: 749,
}
# Rectangular samples of these flags match column-major storage.
COLUMN_FLAGS = frozenset({0x008B, 0x00A9, 0x00C3, 0x00E1, 0x20C3, 0x808B, 0x80A9, 0x80C3})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# MIX entry lookup and LZO1X block decode
# ---------------------------------------------------------------------------
def texture_entry_name(level, sphere):
    level = level.upper()
    return f"SPHERE{sphere}\\{level}\\{level}.TE_"


def find_texture_entry(mix_path, level=None):
    """Return (mix bytes, entry dict, entry name) for the level's .TE_ entry."""
    mix_path = Path(mix_path)
    level = (level or mix_path.stem).upper()
    data, entries, base = read_mix_with_hashes(str(mix_path))
    by_key = {key: (i, off, size) for i, (key, off, size) in enumerate(entries)}
    for sphere in range(0, 10):
        name = texture_entry_name(level, sphere)
        key = ww_hash_v1(name)
        if key in by_key:
            index, off, size = by_key[key]
            require(base + off + size <= len(data), "texture entry exceeds MIX data")
            return data, dict(index=index, key=key, offset=base + off, size=size), name
    raise ValueError(f"no SPHERE<n>\\{level}\\{level}.TE_ entry in {mix_path.name}")


def _lzo_decompress_fn():
    library = ctypes.util.find_library("lzo2")
    require(bool(library), "liblzo2 shared library is required (e.g. apt install liblzo2-2)")
    fn = ctypes.CDLL(library).lzo1x_decompress_safe
    fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                   ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
    fn.restype = ctypes.c_int
    return fn


def decode_lzo_container(raw):
    """Bounded liblzo2 decode of one .TE_ entry. Returns (blob, block list)."""
    fn = _lzo_decompress_fn()
    require(len(raw) >= 4, "entry truncated before size header")
    total = struct.unpack_from("<I", raw)[0]
    require(0 < total <= MAX_DECOMPRESSED, "decompressed size out of bounds")
    output = bytearray()
    cursor = 4
    blocks = []
    while len(output) < total:
        require(cursor + 4 <= len(raw), "truncated block header")
        size = struct.unpack_from("<I", raw, cursor)[0]
        cursor += 4
        require(0 < size <= len(raw) - cursor, "block size out of bounds")
        src = ctypes.create_string_buffer(raw[cursor:cursor + size])
        dst = ctypes.create_string_buffer(LZO_BLOCK)
        n = ctypes.c_size_t(len(dst))
        code = fn(src, size, dst, ctypes.byref(n), None)
        expected = min(LZO_BLOCK, total - len(output))
        require(code == 0 and n.value == expected,
                f"lzo1x_decompress_safe failed (code={code})")
        blocks.append(dict(offset=cursor, compressed=size, decoded=n.value))
        output.extend(dst.raw[:n.value])
        cursor += size
    require(raw[cursor:] == bytes(4), "unexpected trailer after blocks")
    return bytes(output), blocks


def load_blob(mix_path, level=None):
    data, entry, name = find_texture_entry(mix_path, level)
    blob, blocks = decode_lzo_container(data[entry["offset"]:entry["offset"] + entry["size"]])
    return blob, dict(entry_name=name, entry=entry, blocks=len(blocks),
                      size=len(blob), sha256=sha256(blob))


# ---------------------------------------------------------------------------
# Blob grammar
# ---------------------------------------------------------------------------
def sections(blob):
    require(len(blob) >= 8, "missing blob header")
    count = struct.unpack_from("<I", blob)[0]
    require(4 <= count <= 256 and 8 + 4 * count <= len(blob), "bad section count")
    offsets = struct.unpack_from("<" + "I" * count, blob, 8)
    require(all(v == 0 or 8 + 4 * count <= v <= len(blob) for v in offsets),
            "section outside blob")
    return offsets


def descriptor_count(blob):
    offsets = sections(blob)
    table, payload = offsets[2], offsets[3]
    require(table > 0 and payload > table and (payload - table) % DESCRIPTOR_SIZE == 0,
            "unsupported descriptor table extent")
    return (payload - table) // DESCRIPTOR_SIZE


def descriptor(blob, index):
    """Return the raw 56-byte descriptor fields (any flag value)."""
    offsets = sections(blob)
    count = descriptor_count(blob)
    require(0 <= index < count, "descriptor index outside table")
    position = offsets[2] + index * DESCRIPTOR_SIZE
    v = struct.unpack_from(DESCRIPTOR_FORMAT, blob, position)
    return dict(index=index, descriptor_start=position, identifier=v[0], width=v[1],
                height=v[2], flags=v[3], field8=v[4], field10=v[5],
                name_hash_candidate=v[6], mip_offsets=list(v[7:12]),
                mip_sizes=list(v[12:17]))


def material_record(blob, index, allow_partial_mips=False):
    """Validate one raw-layout descriptor and its mip chain (5 levels by default)."""
    offsets = sections(blob)
    d = descriptor(blob, index)
    require(d["flags"] in RAW_LAYOUT_FLAGS,
            f"flag 0x{d['flags']:X} is not a raw 8-bit layout")
    require(d["width"] > 0 and d["height"] > 0, "zero material dimension")
    payload = offsets[3]
    payload_end = min((v for v in offsets if v > payload), default=len(blob))
    sizes = d["mip_sizes"]
    levels = 5
    if allow_partial_mips:
        levels = sum(s != 0 for s in sizes)
        require(1 <= levels <= 5, "empty mip chain")
        require(all(sizes[k] > 0 for k in range(levels)) and
                all(sizes[k] == d["mip_offsets"][k] == 0 for k in range(levels, 5)),
                "mip chain has holes")
        require((d["field10"] & 255) == levels, "mip count field mismatch")
    mips = []
    for level in range(levels):
        start = payload + d["mip_offsets"][level]
        size = sizes[level]
        require(size >= 8 and payload <= start and start + size <= payload_end,
                "mip outside payload section")
        flags, w, h, length16 = struct.unpack_from("<4H", blob, start)
        require(flags == d["flags"], "descriptor/mip flags mismatch")
        require((w, h) == (max(1, d["width"] >> level), max(1, d["height"] >> level)),
                "descriptor/mip dimensions mismatch")
        require(size == 8 + w * h and length16 == (w * h) & 0xFFFF,
                "mip byte extent mismatch")
        mips.append(dict(level=level, start=start, data_start=start + 8, width=w,
                         height=h, record_size=size,
                         pixels_sha256=sha256(blob[start + 8:start + size])))
    d["mips"] = mips
    return d


def shade_row(blob, row=INITIAL_SHADE_ROW):
    """256-byte shade row: section 4 + row * 256, bounded by section 5."""
    offsets = sections(blob)
    require(len(offsets) > 4 and offsets[4] > 0, "shade section missing")
    start = offsets[4] + row * SHADE_ROW_BYTES
    end = start + SHADE_ROW_BYTES
    shade_end = offsets[5] if len(offsets) > 5 and offsets[5] else len(blob)
    require(0 <= row and end <= shade_end, "shade row outside shade section")
    return blob[start:end]


def palette_dac(blob):
    """768-byte 6-bit palette at the header dword +4 (witnessed for L20_BB)."""
    offset = struct.unpack_from("<I", blob, 4)[0]
    require(0 < offset and offset + 768 <= len(blob), "palette offset out of bounds")
    dac = blob[offset:offset + 768]
    require(max(dac) <= 63, "palette exceeds 6-bit DAC range")
    return dac


def column_major_to_rows(data, width, height):
    require(len(data) == width * height, "pixel extent mismatch")
    return bytes(data[x * height + y] for y in range(height) for x in range(width))


def png_rgb(width, height, pixels):
    def chunk(kind, content):
        return (struct.pack(">I", len(content)) + kind + content +
                struct.pack(">I", zlib.crc32(kind + content)))
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_info(args):
    blob, info = load_blob(args.mix, args.level)
    offsets = sections(blob)
    count = descriptor_count(blob)
    flags = collections.Counter(descriptor(blob, i)["flags"] for i in range(count))
    info.update(sections=[f"0x{v:X}" for v in offsets], descriptors=count,
                flags={f"0x{k:X}": v for k, v in sorted(flags.items())})
    print(json.dumps(info, indent=2))


def cmd_material(args):
    blob, _ = load_blob(args.mix, args.level)
    d = descriptor(blob, args.index)
    if d["flags"] in RAW_LAYOUT_FLAGS:
        d = material_record(blob, args.index, args.partial_mips)
    elif d["flags"] in NAME_FLAGS:
        d["note"] = "22-byte movie-name record; not pixels"
    else:
        d["note"] = "header only; payload is not raw pixels"
    print(json.dumps(d, indent=2))


def cmd_export(args):
    blob, info = load_blob(args.mix, args.level)
    d = material_record(blob, args.index, args.partial_mips)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rgb = bytes((v * 255 + 31) // 63 for v in palette_dac(blob))
    shade = shade_row(blob, args.shade_row) if args.shade_row is not None else None
    for mip in d["mips"]:
        w, h = mip["width"], mip["height"]
        raw = blob[mip["data_start"]:mip["data_start"] + w * h]
        indices = column_major_to_rows(raw, w, h)
        if shade is not None:
            indices = bytes(shade[i] for i in indices)
        pixels = b"".join(rgb[i * 3:i * 3 + 3] for i in indices)
        (out / f"material_{args.index}_mip{mip['level']}.png").write_bytes(png_rgb(w, h, pixels))
    print(f"wrote {len(d['mips'])} mip PNGs for descriptor {args.index} to {out}")


def cmd_blob(args):
    blob, info = load_blob(args.mix, args.level)
    Path(args.out).write_bytes(blob)
    print(json.dumps(info, indent=2))


def _mix_keys(data_dir):
    keys = set()
    for name in sorted(os.listdir(data_dir)):
        if not name.upper().endswith(".MIX"):
            continue
        with open(os.path.join(data_dir, name), "rb") as handle:
            head = handle.read(6)
            if len(head) < 6:
                continue
            count = struct.unpack_from("<H", head)[0]
            table = handle.read(count * 12)
        for index in range(min(count, len(table) // 12)):
            keys.add(struct.unpack_from("<I", table, index * 12)[0])
    return keys


def _column_scores(pixels, width, height):
    step = max(1, (width * height) // 2500)
    adj = sw = sh = na = nw = nh = 0
    for pos in range(0, width * height - 1, step):
        adj += abs(pixels[pos] - pixels[pos + 1])
        na += 1
    for pos in range(0, width * height - width, step):
        sw += abs(pixels[pos] - pixels[pos + width])
        nw += 1
    for pos in range(0, width * height - height, step):
        sh += abs(pixels[pos] - pixels[pos + height])
        nh += 1
    if not (na and nw and nh):
        return None
    return adj / na, sw / nw, sh / nh


def validate_row_payload(blob, start, size):
    """Frame one row header and its literal bytes per declared image row."""
    flags, width, height, length = struct.unpack_from("<4H", blob, start)
    end = start + size
    require(length == size - 8 and end <= len(blob), "invalid row payload size")
    at = start + 8
    for _ in range(height):
        require(at + 4 <= end, "truncated row header")
        first, count = struct.unpack_from("<HH", blob, at)
        if flags == 0x02AC:
            require((first, count) == (0, width), "0x02AC row is not a full-width literal")
        at += 4 + count
        require((first & 0x3FFF) + count <= width and at <= end, "row span exceeds dimensions")
    require(at == end, "trailing bytes in row payload")



COLUMN_RLE_FLAGS = frozenset({0x008F, 0x00C7, 0x20C7, 0x808F, 0x80C7})


def validate_column_payload(blob, start, size):
    """Read the offset table and column runs used by 0x12621C."""
    width, height = struct.unpack_from("<HH", blob, start + 2)
    base = start + 8
    end = start + size
    cursor = base + 2 * width
    require(cursor <= end <= len(blob), "column directory outside record")
    for column in range(width):
        offset = struct.unpack_from("<H", blob, base + 2 * column)[0]
        if not offset:
            continue
        require(base + offset == cursor, "column run offset")
        remaining = height
        while remaining:
            require(cursor + 2 <= end, "truncated column run")
            count, value = blob[cursor], blob[cursor + 1]
            require(0 < count <= remaining, "column run count")
            cursor += 2 if value <= 2 else 1 + count
            remaining -= count
    require(cursor == end, "column payload end")


def vector_book(blob, offsets, key):
    """Decode the matching section-8 companion, using section 9's 12-byte rows."""
    table_end = offsets[2]
    at = offsets[9] + 12 * key
    require(offsets[8] < offsets[9] <= at and at + 12 <= table_end, "vector companion row")
    start, capacity, length = struct.unpack_from("<III", blob, at)
    require(0 < length <= capacity and capacity in (32000, 64000), "vector companion size")
    require(offsets[8] <= start and start + length <= offsets[9], "vector companion bounds")
    decoded, errors, used = decompress_westwood(blob[start:start + length], capacity)
    require(errors == 0 and 0 < len(decoded) <= capacity and len(decoded) % 16 == 0,
            "malformed vector companion")
    return capacity // 16, len(decoded) // 16, length - used


def validate_vector_payload(blob, start, size, books, offsets, metrics):
    """Frame the 0x12607C tile-row directory and each run."""
    width, height = struct.unpack_from("<HH", blob, start + 2)
    first, last = blob[start + 0x16:start + 0x18]
    base = start + 0x18
    end = start + size
    require(width % 4 == 0 and height % 4 == 0 and 0 < width // 4 <= 255,
            "invalid vector dimensions")
    require(first <= last < height // 4 and base + 2 * (last - first + 1) <= end,
            "vector row range")
    key = struct.unpack_from("<I", blob, start + 8)[0]
    if key not in books:
        books[key] = vector_book(blob, offsets, key)
    capacity, decoded, _ = books[key]
    cursor = base + 2 * (last - first + 1)
    for row in range(last - first + 1):
        offset = struct.unpack_from("<H", blob, base + 2 * row)[0]
        metrics["slots"] += 1
        if not offset:
            metrics["empty"] += 1
            continue
        require(base + offset == cursor, "vector row offset")
        remaining = width // 4
        missing = 0
        while remaining:
            require(cursor + 2 <= end, "truncated vector run")
            marker, count = blob[cursor], blob[cursor + 1]
            cursor += 2
            require(0 < count <= remaining, "vector run count")
            if marker:
                require(cursor + 2 * count <= end, "vector indices outside record")
                indices = struct.unpack_from(f"<{count}H", blob, cursor)
                require(max(indices) < capacity, "vector index exceeds book allocation")
                metrics["lookups"] += count
                if max(indices) >= decoded:
                    missing += sum(index >= decoded for index in indices)
                cursor += 2 * count
            remaining -= count
        if missing:
            metrics["short_rows"] += 1
            metrics["short_indices"] += missing
    require(end - cursor == 2 * (height // 4) - 2, "vector record tail length")


def check(data_dir):
    """Walk every level .TE_ and pin the flag layouts measured on 2026-11-18 (row framing added 2026-11-19)."""
    bad = []
    counts = collections.Counter()
    levels = 0
    name_hit = name_total = 0
    height_mismatch = 0
    row_payloads = ambiguous_rows = column_payloads = raw_fallbacks = 0
    book_count = short_books = book_tails = 0
    vectors = collections.Counter()
    scores = {flag: [0.0, 0.0, 0.0, 0] for flag in COLUMN_FLAGS}
    keys = _mix_keys(data_dir)
    for name in sorted(os.listdir(data_dir)):
        if not name.upper().endswith(".MIX"):
            continue
        path = os.path.join(data_dir, name)
        try:
            _data, entry, _entry_name = find_texture_entry(path)
        except ValueError:
            continue
        levels += 1
        raw = Path(path).read_bytes()[entry["offset"]:entry["offset"] + entry["size"]]
        blob, _blocks = decode_lzo_container(raw)
        total = descriptor_count(blob)
        offsets = sections(blob)
        payload = offsets[3]
        books = {}
        for index in range(total):
            d = descriptor(blob, index)
            flag = d["flags"]
            counts[flag] += 1
            present = [level for level in range(5) if d["mip_sizes"][level]]
            if flag in FIELD8_IS_ONE and d["field8"] != 1:
                bad.append(f"{name}#{index} flag 0x{flag:X} field8 {d['field8']}")
            if flag == 0:
                if d["width"] or d["height"] or present:
                    bad.append(f"{name}#{index} empty flag has dimensions or mips")
                continue
            if not present:
                bad.append(f"{name}#{index} flag 0x{flag:X} has no mips")
                continue
            if flag in RAW_LAYOUT_FLAGS:
                try:
                    material_record(blob, index, allow_partial_mips=True)
                except ValueError as error:
                    bad.append(f"{name}#{index}: {error}")
                    continue
                if (d["width"] != d["height"] and d["width"] >= 8 and d["height"] >= 8
                        and flag in scores):
                    start = payload + d["mip_offsets"][0] + 8
                    pixels = blob[start:start + d["width"] * d["height"]]
                    got = _column_scores(pixels, d["width"], d["height"])
                    if got:
                        for part in range(3):
                            scores[flag][part] += got[part]
                        scores[flag][3] += 1
                continue
            start = payload + d["mip_offsets"][0]
            size = d["mip_sizes"][0]
            if size < 8 or start + size > len(blob):
                bad.append(f"{name}#{index} mip0 out of range")
                continue
            header_flags, header_w, header_h, fourth = struct.unpack_from("<4H", blob, start)
            if header_flags != flag or header_w != d["width"]:
                bad.append(f"{name}#{index} header 0x{header_flags:X} {header_w}x{header_h}")
                continue
            if flag in NAME_FLAGS:
                body = blob[start + 8:start + size]
                text, _, rest = body.partition(b"\0")
                if (size != 22 or fourth != 22 or header_h != d["height"]
                        or d["field8"] != 0xFF or (d["field10"] >> 8) != 4
                        or rest.strip(b"\0") or not text.endswith(b".vqa")
                        or any(c < 32 or c > 126 for c in text)):
                    bad.append(f"{name}#{index} bad movie name {body[:14]!r}")
                else:
                    name_total += 1
                    if ww_hash_v1(text.decode("ascii")) in keys:
                        name_hit += 1
                continue
            if flag == 0x1246:
                if (header_h != d["height"] or size != 22 + fourth or present != [0]
                        or (d["field10"] & 0xFF) != 1 or (d["field10"] >> 8) != 3):
                    bad.append(f"{name}#{index} bad 0x1246 size {size} fourth {fourth}")
                else:
                    try:
                        validate_vector_payload(blob, start, size, books, offsets, vectors)
                    except (ValueError, struct.error) as error:
                        bad.append(f"{name}#{index}: {error}")
                continue
            if flag in PAYLOAD_FLAGS:
                if size != 8 + fourth or (d["field10"] >> 8) != 3:
                    bad.append(f"{name}#{index} payload header size {size} fourth {fourth}")
                    continue
                if header_h != d["height"]:
                    height_mismatch += 1
                    if not (d["width"] == 640 and d["height"] == 434 and header_h == 192):
                        bad.append(f"{name}#{index} unexpected height {header_h} vs {d['height']}")
                if flag in (0x028E, 0x02AC, 0x02C6, 0x828E, 0x82C6):
                    for mip in present:
                        mip_start = payload + d["mip_offsets"][mip]
                        mip_size = d["mip_sizes"][mip]
                        try:
                            validate_row_payload(blob, mip_start, mip_size)
                        except (ValueError, struct.error) as error:
                            bad.append(f"{name}#{index} mip {mip}: {error}")
                        else:
                            row_payloads += flag != 0x02AC
                            ambiguous_rows += flag == 0x02AC
                if flag in COLUMN_RLE_FLAGS:
                    for mip in present:
                        mip_start = payload + d["mip_offsets"][mip]
                        mip_size = d["mip_sizes"][mip]
                        try:
                            mip_flag, width, height, length = struct.unpack_from("<4H", blob, mip_start)
                            if mip_flag == flag:
                                validate_column_payload(blob, mip_start, mip_size)
                                column_payloads += 1
                            else:
                                require(mip_flag == flag & ~4 and mip_flag in RAW_LAYOUT_FLAGS,
                                        "unexpected column mip flag")
                                require(mip_start + mip_size <= len(blob) and mip_size == 8 + width * height
                                        and length == (width * height) & 0xFFFF, "invalid raw fallback size")
                                raw_fallbacks += 1
                        except (ValueError, struct.error) as error:
                            bad.append(f"{name}#{index} mip {mip}: {error}")
                continue
            bad.append(f"{name}#{index} unclassified flag 0x{flag:X}")
        book_count += len(books)
        short_books += sum(decoded < capacity for capacity, decoded, _ in books.values())
        book_tails += sum(tail > 1 for _, _, tail in books.values())
    if levels != 15:
        bad.append(f"levels {levels}")
    if dict(counts) != EXPECTED_COUNTS:
        bad.append("flag counts " + ", ".join(
            f"0x{flag:X}:{counts[flag]}" for flag in sorted(set(counts) | set(EXPECTED_COUNTS))
            if counts[flag] != EXPECTED_COUNTS.get(flag)))
    if height_mismatch != 1:
        bad.append(f"header-height mismatches {height_mismatch}")
    if (book_count, short_books, book_tails) != (400, 253, 6):
        bad.append(f"vector books {(book_count, short_books, book_tails)}")
    if vectors != dict(slots=1135521, empty=1762, lookups=21231709, short_rows=180, short_indices=190):
        bad.append(f"vector census {dict(vectors)}")
    if (column_payloads, raw_fallbacks) != (4366, 1185):
        bad.append(f"column and raw payload counts {(column_payloads, raw_fallbacks)}")
    if (row_payloads, ambiguous_rows) != (30593, 4):
        bad.append(f"row payload counts {(row_payloads, ambiguous_rows)}")
    if name_total != 881 or name_hit != 0:
        bad.append(f"movie names {name_total} bare keys {name_hit}")
    for flag, (adj, stride_w, stride_h, count) in scores.items():
        if count < (2 if flag == 0x808B else 10):
            bad.append(f"0x{flag:X} rectangular samples {count}")
            continue
        adj, stride_w, stride_h = adj / count, stride_w / count, stride_h / count
        if not (stride_w > stride_h and abs(adj - stride_h) < abs(adj - stride_w)):
            bad.append(f"0x{flag:X} orientation adj {adj:.2f} stride_w {stride_w:.2f} "
                       f"stride_h {stride_h:.2f} n {count}")
    raw_n = sum(counts[flag] for flag in RAW_LAYOUT_FLAGS)
    payload_n = sum(counts[flag] for flag in PAYLOAD_FLAGS)
    line = (f"CHECK textures: {levels} levels, {sum(counts.values())} descriptors; "
            f"raw 8-bit {raw_n}; movie-name records {name_total} "
            f"({name_hit} bare names are DAT keys); payload-length header {payload_n} "
            f"({height_mismatch} header-height mismatch); flag 0x1246 records {counts[0x1246]}; "
            f"{row_payloads} row spans and {ambiguous_rows} ambiguous spans, {column_payloads} compressed columns, "
            f"{raw_fallbacks} raw fallback mips; {book_count} vector books, "
            f"{vectors['slots']} row slots, {vectors['short_indices']} indexes beyond decoded book data; empty {counts[0]}; rectangular raw samples store columns; "
            f"bad={'none' if not bad else '; '.join(bad[:6])}")
    print(line)
    return 1 if bad else 0


def main(argv=None):
    parser = ReaderArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default=os.environ.get("LOL2_DAT"),
                        help="the game's DAT folder (default: $LOL2_DAT)")
    parser.add_argument("--check", action="store_true", help="check the texture banks in all original levels")
    sub = parser.add_subparsers(dest="command")
    legacy = sub.add_parser("check", help="alias for --check")
    legacy.add_argument("--data", default=argparse.SUPPRESS, help="the game's DAT folder")
    for name, fn in (("info", cmd_info), ("material", cmd_material),
                     ("export", cmd_export), ("blob", cmd_blob)):
        p = sub.add_parser(name, description="Read a .TE_ texture bank from an original LoL2 level MIX.")
        p.add_argument("--data", default=argparse.SUPPRESS, help="the game's DAT folder")
        p.add_argument("--mix", required=True, help="level MIX path or a bare name, e.g. L1_DC.MIX")
        p.add_argument("--level", help="level name if it differs from the MIX file stem")
        p.set_defaults(func=fn)
        if name in ("material", "export"):
            p.add_argument("--index", type=int, required=True, help="descriptor index")
            p.add_argument("--partial-mips", action="store_true",
                           help="accept fewer than five mip levels (count from field10)")
        if name == "export":
            p.add_argument("--out", required=True, help="output directory")
            p.add_argument("--shade-row", type=int, default=None,
                           help="apply this 256-byte shade row before the palette")
        if name == "blob":
            p.add_argument("--out", required=True, help="output file for the decoded blob")
    args = parser.parse_args()
    if args.check or args.command == "check":
        if args.command not in (None, "check") or not args.data:
            parser.error("--check needs the DAT folder and no other command")
        return check(args.data)
    if args.command is None:
        parser.error("give --check or an inspection command")
    args.mix = lol2_cli.resolve_input(args.mix, args.data)
    if getattr(args, "out", None):
        lol2_cli.refuse_repo_output(args.out)
    try:
        args.func(args)
    except (ValueError, OSError, struct.error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
