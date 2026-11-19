#!/usr/bin/env python3
"""Read the two DAT files that are not MIX archives through their last byte.

  lol2_loose.py --data DAT --check

AUTOPLAY.WAV counts when its RIFF chunks tile the file. SETUP.EXE counts
when the MZ image ends at an NE header and that header's tables, segments,
relocation lists, zero padding and resources tile the file.
"""
from cli_errors import run_cli
from pathlib import Path
from struct import unpack_from

import lol2_cli

WAVE_SIZE = 147970
SETUP_SIZE = 92160
PROGRAM_SIZE = 1977007
ERRTEXT_SIZE = 2444
SEGMENT_RELOCS = (127, 42, 160, 112, 62)
INFO_CHUNKS = ((b"ICOP", 40), (b"ICRD", 11), (b"IENG", 16), (b"ISFT", 16))


def _names_with_ordinals(data, start, end):
    pos = start
    names = []
    while pos < end:
        length = data[pos]
        if length == 0:
            pos += 1
            break
        if pos + 1 + length + 2 > end:
            raise ValueError("name runs past its table")
        names.append(data[pos + 1:pos + 1 + length])
        pos += 1 + length + 2
    if pos != end:
        raise ValueError("name table does not end on its bound")
    return names


def _names_plain(data, start, end):
    pos = start
    names = []
    while pos < end:
        length = data[pos]
        if pos + 1 + length > end:
            raise ValueError("imported name runs past its table")
        names.append(data[pos + 1:pos + 1 + length])
        pos += 1 + length
    if pos != end:
        raise ValueError("imported names do not fill their table")
    return names


def _list_chunks(data, start, end):
    if start + 4 > end:
        raise ValueError("LIST has no form")
    pos = start + 4
    found = []
    while pos + 8 <= end:
        ident = data[pos:pos + 4]
        size = unpack_from("<I", data, pos + 4)[0]
        nxt = pos + 8 + size + (size & 1)
        if nxt > end:
            raise ValueError("LIST chunk runs past the list")
        found.append((ident, size))
        pos = nxt
    if pos != end:
        raise ValueError("LIST chunks leave a gap")
    return found


def describe_wave(path):
    data = Path(path).read_bytes()
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a RIFF WAVE")
    if unpack_from("<I", data, 4)[0] + 8 != len(data):
        raise ValueError("RIFF size does not reach the last byte")
    pos = 12
    fmt = None
    data_size = None
    info = None
    chunks = []
    while pos + 8 <= len(data):
        ident = data[pos:pos + 4]
        size = unpack_from("<I", data, pos + 4)[0]
        payload = pos + 8
        end = payload + size
        if end > len(data):
            raise ValueError(f"{ident!r} runs past the file")
        chunks.append((pos, ident, size))
        if ident == b"fmt ":
            if size < 16:
                raise ValueError("fmt is short")
            tag, channels, rate, average, align, bits = unpack_from("<HHIIHH", data, payload)
            if tag != 1 or channels == 0 or bits == 0 or bits % 8:
                raise ValueError("fmt is not PCM")
            if align != channels * (bits // 8) or average != rate * align:
                raise ValueError("fmt rates disagree")
            fmt = (channels, rate, bits)
        elif ident == b"data":
            data_size = size
        elif ident == b"LIST":
            info = _list_chunks(data, payload, end)
        pos = end + (size & 1)
    if pos != len(data) or fmt is None or data_size is None:
        raise ValueError("WAVE chunks do not tile the file")
    return {"size": len(data), "fmt": fmt, "data": data_size, "info": info, "chunks": chunks}


def describe_ne(path):
    data = Path(path).read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ValueError("not MZ")
    last, pages = unpack_from("<HH", data, 2)
    mz_end = (pages - 1) * 512 + (last or 512)
    ne_off = unpack_from("<I", data, 0x3C)[0]
    if mz_end != ne_off or ne_off + 0x40 > len(data) or data[ne_off:ne_off + 2] != b"NE":
        raise ValueError("MZ image does not end on an NE header")
    entry_off, entry_len = unpack_from("<HH", data, ne_off + 4)
    seg_count = unpack_from("<H", data, ne_off + 0x1C)[0]
    mod_count = unpack_from("<H", data, ne_off + 0x1E)[0]
    nonres_size = unpack_from("<H", data, ne_off + 0x20)[0]
    seg_off, res_off, resname_off, modref_off, imp_off = unpack_from("<HHHHH", data, ne_off + 0x22)
    nonres_off = unpack_from("<I", data, ne_off + 0x2C)[0]
    align_shift = unpack_from("<H", data, ne_off + 0x32)[0]
    if seg_off != 0x40 or align_shift > 16:
        raise ValueError("NE header does not meet its segment table")
    align = 1 << align_shift
    cursor = ne_off + seg_off + seg_count * 8
    if cursor != ne_off + res_off:
        raise ValueError("segment table does not meet the resource table")
    res_end, _res_align, resources = _resources(data, ne_off + res_off)
    if res_end != ne_off + resname_off:
        raise ValueError("resource table does not meet the resident names")
    resident = _names_with_ordinals(data, ne_off + resname_off, ne_off + modref_off)
    if ne_off + modref_off + mod_count * 2 != ne_off + imp_off:
        raise ValueError("module references do not meet the imported names")
    _names_plain(data, ne_off + imp_off, ne_off + entry_off)
    if ne_off + entry_off + entry_len != nonres_off:
        raise ValueError("entry table does not meet the nonresident names")
    nonresident = _names_with_ordinals(data, nonres_off, nonres_off + nonres_size)
    segments = []
    for index in range(seg_count):
        at = ne_off + seg_off + index * 8
        sector, length, flags, _minalloc = unpack_from("<HHHH", data, at)
        start = sector * align
        end = start + (65536 if length == 0 else length)
        if end > len(data):
            raise ValueError("segment runs past the file")
        if flags & 0x0100:
            if end + 2 > len(data):
                raise ValueError("relocation count")
            count = unpack_from("<H", data, end)[0]
            rel_end = end + 2 + count * 8
        else:
            count = 0
            rel_end = end
        if rel_end > len(data):
            raise ValueError("relocation records run past the file")
        segments.append((start, rel_end, count))
    if any(segments[i][0] >= segments[i + 1][0] for i in range(len(segments) - 1)):
        raise ValueError("segments are not in order")
    resources = sorted(resources)
    if not resources or resources[-1][1] != len(data):
        raise ValueError("resources do not end at the last byte")
    for left, right in zip(resources, resources[1:]):
        if left[1] != right[0]:
            raise ValueError("resources leave a gap")
    bounds = [nonres_off + nonres_size]
    bounds.extend(start for start, _rel_end, _count in segments)
    bounds.append(resources[0][0])
    ends = [nonres_off + nonres_size]
    ends.extend(rel_end for _start, rel_end, _count in segments)
    for end, nxt in zip(ends, bounds[1:]):
        if end > nxt or data[end:nxt] != bytes(nxt - end):
            raise ValueError("padding between objects is not zero")
    return {
        "size": len(data),
        "ne": ne_off,
        "relocs": tuple(count for _start, _rel_end, count in segments),
        "module": resident[0] if resident else b"",
        "nonresident": nonresident[0] if nonresident else b"",
        "segments": segments,
        "resources": resources,
    }


def _resources(data, start):
    shift = unpack_from("<H", data, start)[0]
    if shift > 16:
        raise ValueError("resource alignment")
    align = 1 << shift
    pos = start + 2
    spans = []
    while True:
        if pos + 2 > len(data):
            raise ValueError("resource type")
        kind = unpack_from("<H", data, pos)[0]
        if kind == 0:
            pos += 2
            break
        if pos + 8 > len(data):
            raise ValueError("resource type header")
        count = unpack_from("<H", data, pos + 2)[0]
        pos += 8
        for _index in range(count):
            if pos + 12 > len(data):
                raise ValueError("resource row")
            offset, length, _flags, _ident = unpack_from("<HHHH", data, pos)
            pos += 12
            span = offset * align
            spans.append((span, span + length * align))
    return pos, align, spans


def covered(path):
    """True when every byte of a loose WAVE or NE file belongs to its header or a counted span."""
    path = Path(path)
    try:
        if path.suffix.lower() == ".wav":
            describe_wave(path)
            return True
        if path.suffix.lower() == ".exe":
            describe_ne(path)
            return True
    except (OSError, ValueError):
        return False
    return False


def main():
    parser = lol2_cli.tool_args(__doc__)
    args = parser.parse_args()
    if args.out:
        parser.error("prints only")
    if not args.check:
        parser.error("this tool only checks; pass --check")
    data = Path(args.data)
    try:
        loose = [p for p in data.iterdir() if p.is_file() and p.suffix.lower() != ".mix"]
        found = {p.name.upper(): p for p in loose}
        if len(loose) != 2 or set(found) != {"AUTOPLAY.WAV", "SETUP.EXE"}:
            raise ValueError(f"loose names {sorted(p.name for p in loose)}")
        wave = describe_wave(found["AUTOPLAY.WAV"])
        program = describe_ne(found["SETUP.EXE"])
        if wave["size"] != WAVE_SIZE or wave["fmt"] != (1, 22050, 16) or wave["data"] != 147798:
            raise ValueError(f"wave {wave['size']} {wave['fmt']} data {wave['data']}")
        if wave["info"] != list(INFO_CHUNKS):
            raise ValueError(f"INFO chunks {wave['info']}")
        if (program["size"], program["ne"], program["relocs"], program["module"], program["nonresident"]) != (
                SETUP_SIZE, 0xA270, SEGMENT_RELOCS, b"SETUP", b"Guardians Setup Parser"):
            raise ValueError("SETUP.EXE layout differs")
        root = data.resolve().parent
        image = (root / "LOLG.DAT").read_bytes()
        if len(image) != PROGRAM_SIZE:
            raise ValueError(f"LOLG.DAT is {len(image)} bytes")
        if image.find(b"setup.exe") != 0x1C4B0E or image.count(b"setup.exe") != 1:
            raise ValueError("the lowercase setup.exe sentence moved")
        if b"AUTOPLAY" in image or b".WAV" in image or b".wav" in image:
            raise ValueError("LOLG.DAT names AUTOPLAY or a WAV file")
        err = (root / "ERRTEXT.TRR").read_bytes()
        if len(err) != ERRTEXT_SIZE or err.find(b"SETUP.EXE") != 0x747 or err.count(b"SETUP.EXE") != 1:
            raise ValueError("ERRTEXT.TRR SETUP.EXE string moved")
    except (OSError, ValueError) as exc:
        print(f"CHECK loose FAILED: {exc}")
        return 1
    print("CHECK loose: AUTOPLAY.WAV 147970 (PCM mono 22050 Hz 16-bit) and SETUP.EXE 92160 "
          "(NE, 5 segments, resources end at the last byte); AUTOPLAY is absent from LOLG.DAT")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
