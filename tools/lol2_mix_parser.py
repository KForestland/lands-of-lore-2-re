#!/usr/bin/env python3
"""Read an original LoL2 MIX archive's directory and entries.

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
from cli_errors import run_cli
import os
import struct

LOL2_DAT = os.environ.get("LOL2_DAT")   # no built-in default; see lol2_cli.py


def read_mix(path):
    """Parse a Westwood MIX file, return list of entry byte strings."""
    data, entries, data_base = read_mix_with_hashes(path)
    return [data[data_base + o : data_base + o + s] for h, o, s in entries]


def read_mix_with_hashes(path):
    """Parse a MIX file, return (raw_data, [(hash, offset, size)], data_base_offset)."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 6:
        raise ValueError(f"{path}: truncated MIX header")
    count, total = struct.unpack_from("<HI", data)
    data_base = 6 + count * 12
    if data_base + total != len(data):
        raise ValueError(f"{path}: MIX header and payload sizes do not match the file")
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, o, s = struct.unpack_from("<III", data, off)
        if o + s > total:
            raise ValueError(f"{path}: MIX entry {i} lies outside the payload")
        entries.append((h, o, s))
    return data, entries, data_base


def read_mix_entry(path, entry_idx):
    """Read a single entry from a MIX file by index."""
    entries = read_mix(path)
    if entry_idx < 0 or entry_idx >= len(entries):
        raise IndexError(f"Entry {entry_idx} out of range (file has {len(entries)} entries)")
    return entries[entry_idx]


USAGE = """
  lol2_mix_parser.py L1_DC.MIX                  # list entries (key, offset, size)
  lol2_mix_parser.py L1_DC.MIX 1 --out e1.bin   # extract entry 1 (write outside the repository)
  lol2_mix_parser.py --check                    # parse every MIX in the DAT folder
"""


def main():
    import lol2_cli
    import lol2_source_format as strict
    ap = lol2_cli.tool_args((__doc__ or "") + USAGE)
    ap.add_argument("mix", nargs="?")
    ap.add_argument("index", nargs="?", type=int)
    a = ap.parse_args()
    if a.check:
        n = rows = signed = unsigned = 0
        bad = []
        for f in lol2_cli.mix_files(a.data):
            path = os.path.join(a.data, f)
            data, entries, base = read_mix_with_hashes(path)
            n += 1
            try:
                other = strict.parse_mix(data)
            except ValueError as ex:
                bad.append(f"{f}: {ex}")
                continue
            rows += len(entries)
            same = [(h, base + o, s) for h, o, s in entries] == [(r["key"], r["offset"], r["size"]) for r in other]
            inside = all(base + o + s <= len(data) for h, o, s in entries)
            keys = [h - (1 << 32) if h >= 1 << 31 else h for h, o, s in entries]
            signed += keys == sorted(keys)
            unsigned += [h for h, o, s in entries] == sorted(h for h, o, s in entries)
            if not (same and inside):
                bad.append(f)
        good = n - len(bad)
        print(f"CHECK mix: {n} MIX files, {rows} entries; this reader and lol2_source_format.parse_mix agree "
              f"and every entry lies inside its file: {good}/{n}; index sorted by signed key: {signed}/{good} (by unsigned key: {unsigned}); "
              f"bad={bad or 'none'}")
        return 0 if not bad else 1
    if not a.mix:
        ap.print_help(); return 2
    path = a.mix if os.path.isabs(a.mix) else os.path.join(a.data, a.mix)
    data, entries, base = read_mix_with_hashes(path)
    if a.index is not None:
        if not 0 <= a.index < len(entries):
            ap.error(f"{os.path.basename(path)} has entries 0 to {len(entries) - 1}")
        h, o, s = entries[a.index]
        blob = data[base + o:base + o + s]
        if a.out:
            open(a.out, "wb").write(blob); print(f"wrote {len(blob)} bytes to {a.out}")
        else:
            print(f"entry {a.index}: key 0x{h:08X}, offset {base + o}, size {s} (use --out to write it)")
        return 0
    print(f"MIX file: {path}\nEntries: {len(entries)}")
    for i, (h, o, s) in enumerate(entries):
        print(f"  [{i:3d}] key=0x{h:08X}  offset={base + o:9d}  size={s:9d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
