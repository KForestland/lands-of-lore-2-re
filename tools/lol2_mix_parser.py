#!/usr/bin/env python3
"""Westwood MIX container parser for Lands of Lore 2.

MIX format:
  - u16 entry_count
  - 4 bytes (data section size or padding)
  - For each entry: u32 hash, u32 offset, u32 size (12 bytes each)
  - Then: raw entry data

Usage:
  from lol2_mix_parser import read_mix, read_mix_with_hashes, LOL2_DAT

Environment variables:
  LOL2_DAT  - path to the LoL2 DAT/ directory (default: current directory)
"""
import os
import struct

LOL2_DAT = os.environ.get("LOL2_DAT", ".")


def read_mix(path):
    """Parse a Westwood MIX file, return list of entry byte strings."""
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack_from("<H", data, 0)[0]
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, o, s = struct.unpack_from("<III", data, off)
        entries.append((h, o, s))
    data_base = 6 + count * 12
    return [data[data_base + o : data_base + o + s] for h, o, s in entries]


def read_mix_with_hashes(path):
    """Parse a MIX file, return (raw_data, [(hash, offset, size)], data_base_offset)."""
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack_from("<H", data, 0)[0]
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, o, s = struct.unpack_from("<III", data, off)
        entries.append((h, o, s))
    data_base = 6 + count * 12
    return data, entries, data_base


def read_mix_entry(path, entry_idx):
    """Read a single entry from a MIX file by index."""
    entries = read_mix(path)
    if entry_idx < 0 or entry_idx >= len(entries):
        raise IndexError(f"Entry {entry_idx} out of range (file has {len(entries)} entries)")
    return entries[entry_idx]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: lol2_mix_parser.py <mixfile> [entry_index]")
        print("  Lists entries or extracts a single entry to stdout")
        print(f"  LOL2_DAT={LOL2_DAT}")
        sys.exit(1)
    mix_path = sys.argv[1]
    if not os.path.isabs(mix_path):
        mix_path = os.path.join(LOL2_DAT, mix_path)
    data, entries, data_base = read_mix_with_hashes(mix_path)
    if len(sys.argv) >= 3:
        idx = int(sys.argv[2])
        entry = data[data_base + entries[idx][1] : data_base + entries[idx][1] + entries[idx][2]]
        sys.stdout.buffer.write(entry)
    else:
        print(f"MIX file: {mix_path}")
        print(f"Entries: {len(entries)}")
        for i, (h, o, s) in enumerate(entries):
            print(f"  [{i:3d}] hash=0x{h:08X}  offset={o:8d}  size={s:8d}")
