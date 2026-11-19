#!/usr/bin/env python3
"""Parse native LoL2 TRR message rows and re-create their offset directory."""
import struct
from pathlib import Path

from cli_errors import run_cli
import lol2_cli
from lol2_source_format import parse_mix
from lol2_text_tables import parse_trr, u32


def read_trr(blob):
    _, ids, offsets = parse_trr(blob, "TRR")
    return [(key, blob[start + 4:end + 3])
            for key, start, end in zip(ids, offsets, offsets[1:])]


def write_trr(rows):
    rows = tuple(rows)
    if not rows or any(b"\0" in value for _, value in rows):
        raise ValueError("TRR needs one or more rows with NUL-free message fields")
    cursor = 8 * len(rows) + 4
    offsets, contents = [cursor], bytearray()
    for _, value in rows:
        contents.extend(value + b"\0")
        offsets.append(cursor + len(contents))
    header = (len(rows), *(key for key, _ in rows), *offsets)
    return struct.pack(f"<{len(header)}I", *header) + contents


def trr_sources(data):
    for name in sorted(data.parent.iterdir()):
        if name.suffix.upper() == ".TRR":
            yield name.name, 0, name.read_bytes()
    for folder in (data, data.parent):
        for name in lol2_cli.mix_files(folder):
            if name.upper() == "CDCACHE.MIX":
                continue
            source = (folder / name).read_bytes()
            for row in parse_mix(source):
                start, size = row["offset"], row["size"]
                if size < 16:
                    continue
                count = u32(source, start)
                if not 0 < count <= (size - 8) // 8:
                    continue
                if u32(source, start + 4 + 4 * count) != 8 * count + 4:
                    continue
                blob = source[start:start + size]
                try:
                    parse_trr(blob, name)
                except ValueError:
                    continue
                yield name, start, blob


def check(data, listing=False):
    found = []
    for name, offset, blob in trr_sources(data):
        rows = read_trr(blob)
        if write_trr(rows) != blob:
            raise ValueError(f"{name}+{offset:#x}: rebuilt TRR differs")
        found.append((name, len(rows)))
        if listing:
            print(f"{name}+{offset:#x} size={len(blob)} rows={len(rows)}")
    if len(found) != 8:
        raise ValueError(f"expected eight retail TRR tables, found {found}")
    print(f"CHECK text write: {len(found)} byte-identical TRR tables, "
          f"{sum(count for _, count in found)} messages")


def main():
    parser = lol2_cli.tool_args(__doc__, writes=False)
    parser.add_argument("--list", action="store_true", help="list source offsets and counts")
    args = parser.parse_args()
    if not (args.check or args.list):
        parser.error("give --check or --list to compare the original TRRs in memory")
    check(Path(args.data), args.list)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
