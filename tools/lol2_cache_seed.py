#!/usr/bin/env python3
"""Compare the shipped LoL2 cache seed lengths with the 15 original texture banks."""
import argparse
import os
import struct
from pathlib import Path

from draracle.lol2_cache_named_wall_fixture import parse_records
from lol2_texture_container import find_texture_entry


def compare(data):
    seed = (data.parent / "CDCACHE.LS_").read_bytes()
    backup = (data.parent / "CACHEBAK.MIX").read_bytes()
    count, size = struct.unpack_from("<HI", backup)
    body = 6 + 12 * count
    if (len(backup), count, size, body) != (131, 5, 65, 66):
        raise ValueError("shipped backup MIX dimensions")
    spans = sorted(struct.unpack_from("<II", backup, 10 + 12 * i) for i in range(count))
    if spans != [(13 * i, 13) for i in range(count)]:
        raise ValueError("shipped backup MIX spans")

    rows = []
    for record in parse_records(seed):
        name = record["canonical_name"]
        level = name.rsplit("\\", 1)[-1].removesuffix(".tex").upper()
        image, entry, bank_name = find_texture_entry(data / f"{level}.MIX")
        if name != bank_name.lower().removesuffix(".te_") + ".tex":
            raise ValueError(f"{level} seed and bank name differ")
        length, = struct.unpack_from("<I", image, entry["offset"])
        rows.append((level, record["record_offset"], record["length"], length, record["pointer"]))
        if record["state"] != 0xFFFFFFFF:
            raise ValueError(f"{level} active record in shipped seed")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    data = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, default=data, required=data is None)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        rows = compare(args.data.resolve())
        matches = [level for level, _, seed, current, _ in rows if seed == current]
        offsets = [(level, pointer) for level, _, _, _, pointer in rows if pointer != 0xFFFFFFFF]
        if len(rows) != 15 or matches != ["L1_DC", "L9_DR", "L14_HT"] or offsets != [("L1_DC", 5066)]:
            raise ValueError("shipped seed comparison changed")
        print("CHECK cache seed: 15 original banks, 3 decoded lengths match, 12 differ; "
              "only L1_DC has a finite old position (5066); backup holds five 13-byte members")
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"CHECK cache seed: {error}\n")


if __name__ == "__main__":
    main()
