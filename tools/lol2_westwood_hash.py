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

import sys
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


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <filename> [filename ...]")
        print("Prints all Westwood hash variants for each filename.")
        sys.exit(1)

    for name in sys.argv[1:]:
        print(f"  {name}:")
        for func_name, func in ALL_HASH_FUNCS:
            h = func(name)
            print(f"    {func_name:16s} = 0x{h:08X}  ({h})")


if __name__ == "__main__":
    main()
