#!/usr/bin/env python3
"""Shared, standard-library-only LoL2 archive and script-command framing.

- parse_mix(): strict Westwood MIX reader (u16 count, u32 data size, 12-byte
  key/offset/size rows). Offsets returned are absolute file offsets.
- level_geometry(): finds the single level geometry entry of a level archive
  (DAT/L<n>_<xx>.MIX) by its header (dword 0 = 18, dword 4 = 5300, at least
  0x244 bytes, the size the native loader reads).
- SIZES: the command length of each of the 37 script opcodes, as returned by the
  native length routine at 0x645E0 in LOLG.DAT 1.30. It describes framing only,
  not what a command does.

No game data is bundled. Callers read the user's own files.
"""
import struct


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def parse_mix(b):
    """Return [{index, key, offset, size}] for a MIX archive held in memory."""
    if len(b) < 6:
        raise ValueError('Truncated MIX header')
    count, total = struct.unpack_from('<HI', b)
    base = 6 + 12 * count
    if base > len(b) or base + total != len(b):
        raise ValueError('MIX size mismatch')
    entries = []
    for i in range(count):
        key, off, size = struct.unpack_from('<III', b, 6 + 12 * i)
        if off + size > total:
            raise ValueError('Entry exceeds MIX data')
        entries.append(dict(index=i, key=key, offset=base + off, size=size))
    spans = sorted((e['offset'], e['offset'] + e['size']) for e in entries)
    if any(a[1] > c[0] for a, c in zip(spans, spans[1:])):
        raise ValueError('Overlapping MIX entries')
    return entries


GEOMETRY_HEADER_SIZE = 0x244


def level_geometry(archive):
    """Return (entry, raw bytes) of the one geometry entry in a level archive."""
    found = []
    for entry in parse_mix(archive):
        raw = archive[entry['offset']:entry['offset'] + entry['size']]
        if len(raw) >= GEOMETRY_HEADER_SIZE and u32(raw, 0) == 18 and u32(raw, 4) == 5300:
            found.append((entry, raw))
    if len(found) != 1:
        raise ValueError(f'expected one level geometry entry, found {len(found)}')
    return found[0]


# Opcode -> command length in bytes (native 0x645E0, 37 opcodes).
SIZES = {0: 4, 1: 6, 2: 6, 3: 12, 5: 6, 6: 6, 7: 6, 8: 8, 9: 6,
         11: 8, 12: 6, 13: 8, 14: 8, 15: 8, 16: 6, 17: 6, 18: 18,
         19: 10, 20: 10, 21: 6, 22: 18, 23: 6, 24: 10, 196: 12,
         197: 6, 198: 6, 199: 6, 200: 6, 201: 6, 204: 8, 205: 8,
         206: 6, 207: 6, 208: 8, 209: 10, 210: 6, 240: 6}


USAGE = """
  lol2_source_format.py --check --data DAT   # strict MIX read of every archive, and exactly one
                                             # geometry entry in each level archive
It is mainly a library (parse_mix, level_geometry, SIZES) for the other tools.
"""


def main():
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lol2_cli
    ap = lol2_cli.tool_args((__doc__ or "") + USAGE)
    a = ap.parse_args()
    if not a.check:
        ap.print_help()
        return 2
    mixes = lol2_cli.mix_files(a.data)
    bad, levels, geo = [], 0, 0
    for f in mixes:
        b = open(os.path.join(a.data, f), "rb").read()
        try:
            parse_mix(b)
        except ValueError as ex:
            bad.append(f"{f}:{ex}")
            continue
        stem = f[:-4].upper()
        if stem.startswith("L") and "_" in stem and not stem.endswith("I"):
            levels += 1
            try:
                level_geometry(b)
                geo += 1
            except ValueError as ex:
                bad.append(f"{f}:{ex}")
    strict_bad = sum(1 for x in bad if "geometry" not in x)
    print(f"CHECK source_format: {len(mixes) - strict_bad}/{len(mixes)} MIX files pass the strict reader (sizes, bounds, no overlap); "
          f"one geometry entry (dword 0 = 18, dword 4 = 5300) in {geo}/{levels} level archives; bad={bad or 'none'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
