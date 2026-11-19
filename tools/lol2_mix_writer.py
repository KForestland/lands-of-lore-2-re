#!/usr/bin/env python3
"""Read the MIX archives in DAT and in the game folder beside it, rebuild each in memory and compare.

CDCACHE.MIX is skipped: the game writes it when it runs, so it is not shipped data.
Nothing is written to disk.
"""
from pathlib import Path
import struct

from cli_errors import run_cli
import lol2_cli
from lol2_mix_parser import read_mix_with_hashes
from lol2_source_format import parse_mix


def write_mix(entries, data_size):
    """Write ordered (key, offset, payload) rows and zero-fill vacant spans."""
    entries = tuple(entries)
    directory = bytearray(struct.pack("<HI", len(entries), data_size))
    for key, offset, payload in entries:
        if not 0 <= offset <= offset + len(payload) <= data_size:
            raise ValueError("MIX row outside its data span")
        directory.extend(struct.pack("<III", key, offset, len(payload)))
    data = bytearray(data_size)
    end = 0
    for _, offset, payload in sorted(entries, key=lambda row: row[1]):
        if not payload:
            continue
        if offset < end:
            raise ValueError("overlapping MIX entries")
        end = offset + len(payload)
        data[offset:end] = payload
    return bytes(directory + data)


def check(data_dir):
    folder = Path(data_dir)
    entries = padding = 0
    counts = []
    for root in (folder, folder.parent):
        names = [name for name in lol2_cli.mix_files(root)
                 if root == folder or name.upper() != "CDCACHE.MIX"]
        counts.append(len(names))
        for name in names:
            source, rows, base = read_mix_with_hashes(root / name)
            length = len(source) - base
            data = memoryview(source)[base:]
            rebuilt = write_mix([(key, off, data[off:off + size]) for key, off, size in rows], length)
            if rebuilt != source:
                raise ValueError(f"{name}: the generated MIX bytes differ from the original")
            if [(row["key"], row["offset"] - base, row["size"]) for row in parse_mix(rebuilt)] != rows:
                raise ValueError(f"{name}: the original reader sees different directory rows")
            entries += len(rows)
            padding += length - sum(size for _, _, size in rows)
    if not counts[0]:
        raise ValueError("no MIX archives inside DAT")
    print(f"CHECK mix write: {counts[0]} DAT archives and {counts[1]} loose archives; "
          f"{entries} ordered entries and {padding} zero-padding bytes; byte-identical")


def main():
    parser = lol2_cli.tool_args(__doc__, writes=False)
    args = parser.parse_args()
    if not args.check:
        parser.error("give --check to rebuild the original archives in memory")
    check(args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
