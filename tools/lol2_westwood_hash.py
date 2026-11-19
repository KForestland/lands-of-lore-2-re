#!/usr/bin/env python3
"""Westwood Studios MIX file hash functions.

Implements the hash algorithms used by Westwood's MIX archive format across
different engine generations:

TD/RA era (Tiberian Dawn, Red Alert, Lands of Lore 1 & 2):
    Rolling hash: pack 4 bytes at a time, ROL1 + add accumulator.
    Two known variants exist (xcc vs ccmix) differing in whether the
    inner loop index increments unconditionally or only when i < len.

TS/RA2 era (Tiberian Sun, Red Alert 2):
    CRC32 with Westwood-specific padding on the filename.

All functions uppercase the input before hashing, matching engine behavior.

Usage as CLI:
    python lol2_westwood_hash.py <filename>

Usage as library:
    from lol2_westwood_hash import ww_hash_v1, ww_hash_v2, ww_hash_ts, ww_hash_crc
"""

from cli_errors import ReaderArgumentParser, run_cli
import zlib


def ww_hash_v1(name: str) -> int:
    """TD/RA era hash (xcc variant).

    Inner index advances only when i < len, so excess iterations within
    the 4-byte packing loop re-read nothing (a >>= 8 drains to zero).
    """
    name = name.upper()
    i = 0
    id_val = 0
    l = len(name)
    while i < l:
        a = 0
        for j in range(4):
            a = (a >> 8) & 0xFFFFFFFF
            if i < l:
                a |= ord(name[i]) << 24
                i += 1
        id_val = ((id_val << 1) | (id_val >> 31)) & 0xFFFFFFFF
        id_val = (id_val + a) & 0xFFFFFFFF
    return id_val


def ww_hash_v2(name: str) -> int:
    """TD/RA era hash (ccmix variant).

    Inner index advances unconditionally (i++ even when i >= len), and
    uses addition instead of OR for the high-byte merge.
    """
    name = name.upper()
    i = 0
    id_val = 0
    l = len(name)
    while i < l:
        a = 0
        for j in range(4):
            a = (a >> 8) & 0xFFFFFFFF
            if i < l:
                a += ord(name[i]) << 24
                a &= 0xFFFFFFFF
            i += 1
        id_val = ((id_val << 1) | (id_val >> 31)) & 0xFFFFFFFF
        id_val = (id_val + a) & 0xFFFFFFFF
    return id_val


def ww_hash_ts(name: str) -> int:
    """TS/RA2 era hash (CRC32 with Westwood padding).

    If the filename length is not a multiple of 4, it is padded:
    one byte equal to the remainder count, then the character at the
    alignment boundary repeated to fill.
    """
    name = name.upper()
    l = len(name)
    a = l & ~3
    if l & 3:
        name += chr(l - a)
        name += name[a] * (3 - (l & 3))
    return zlib.crc32(name.encode('ascii')) & 0xFFFFFFFF


def ww_hash_crc(name: str) -> int:
    """Plain CRC32 of the uppercased filename (no padding)."""
    return zlib.crc32(name.upper().encode('ascii')) & 0xFFFFFFFF


ALL_HASH_FUNCS = [
    ("V1(xcc)", ww_hash_v1),
    ("V2(ccmix)", ww_hash_v2),
    ("TS(crc32pad)", ww_hash_ts),
    ("CRC32", ww_hash_crc),
]


USAGE = """
  lol2_westwood_hash.py NAME [NAME ...]     # print the hashes of file names
  lol2_westwood_hash.py --check --data DAT  # the documented entry names are found as keys:
      SPHERE<n>\\<LEVEL>\\<LEVEL>.TE_ in every level MIX and WOMS\\<ROOM>_.WOM in room MIX files
"""


def main():
    import argparse, os
    ap = ReaderArgumentParser(description=(__doc__ or "") + USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--data", default=os.environ.get("LOL2_DAT"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        if not a.data:
            ap.error("--check needs --data or $LOL2_DAT")
        import lol2_source_format as S
        tex = rooms = levels = 0
        for f in sorted(x for x in os.listdir(a.data) if x.upper().endswith(".MIX")):
            stem = f[:-4]
            keys = {r["key"] for r in S.parse_mix(open(os.path.join(a.data, f), "rb").read())}
            if stem.upper().startswith("L") and "_" in stem and not stem.upper().endswith("I"):
                levels += 1
                tex += any(ww_hash_v1(f"SPHERE{n}\\{stem}\\{stem}.TE_") in keys for n in range(1, 8))
            rooms += ww_hash_v1(f"WOMS\\{stem}_.WOM") in keys
        ok = tex == levels and levels > 0
        print(f"CHECK hash: ww_hash_v1 of the documented texture entry name is a key in {tex}/{levels} level MIX "
              f"files; the WOMS room-module name in {rooms} room MIX files")
        return 0 if ok else 1
    if not a.names:
        ap.print_help(); return 2
    for name in a.names:
        print(f"{name}: v1 0x{ww_hash_v1(name):08X} ({ww_hash_v1(name)})  v2 0x{ww_hash_v2(name):08X}  "
              f"ts 0x{ww_hash_ts(name):08X}  crc 0x{ww_hash_crc(name):08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
