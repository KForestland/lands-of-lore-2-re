#!/usr/bin/env python3
"""Rebuild native command and event fields in the original LoL2 level MIXes."""
from collections import Counter
import struct

from cli_errors import run_cli
import lol2_cli
from lol2_disassemble_scripts import EXPECTED_LEVELS, select_archive
from lol2_export_scripts import (
    OBJECT_EVENTS, PLACED_ITEMS, PREDICATE_TABLE, REGION_DESCRIPTORS, REGION_EVENTS,
    STREAMS, TABLES, frame, group, require, section, walk,
)
from lol2_mix_writer import write_mix
from lol2_source_format import SIZES, level_geometry, parse_mix

# Formats begin at command +4 and event +2. Remainders retain unmapped bytes.
COMMAND_FIELDS = {
    2: ("BB", "action argument"), 5: ("BB", "action argument"),
    6: ("BB", "action argument"), 7: ("bB", "action argument"),
    9: ("BB", "property value"), 11: ("H", "request"),
    12: ("B", "room"), 14: ("BBB", "action argument timer"),
    15: ("BBH", "action source_kind source_target"), 16: ("B", "value"),
    17: ("b", "delta"), 18: ("6sH", "prefix flags"),
    19: ("HHBB", "mask flags magnitude mode"), 20: ("H", "sound"),
    21: ("BB", "index value"), 24: ("H", "event"),
    196: ("h4sh", "height middle remainder"), 197: ("B", "action"),
    198: ("BB", "index value"), 199: ("BB", "index value"),
    200: ("BB", "index max"), 201: ("BB", "index max"),
    204: ("hH", "selector value"), 206: ("Bb", "index delta"),
    207: ("Bb", "index delta"), 208: ("BBB", "action value duration"),
    209: ("hhh", "dx dy dz"), 210: ("Bb", "setting argument"),
    240: ("B", "child_count"),
}
EVENT_FIELDS = {
    1: ("HhHBbbBbB", "flags progress fade inner lower upper period z_offset live"),
    2: ("HBBBBH", "group flags status min max countdown"),
    3: ("HB", "group event"),
    4: ("HBBI", "group mode inversion argument"),
    5: ("HBB", "group event value"), 6: ("HB", "group value"),
    7: ("HBB", "group mode threshold"), 8: ("HH", "group match"),
    9: ("HHHBB", "group mask_a mask_b threshold flags"),
    10: ("HBBH", "group event stored_byte selector"),
    11: ("HHB", "group region event"), 12: ("HHBB", "group region event value"),
    15: ("HHBBH", "group region mode operand_kind operand"),
    19: ("H", "predicate"),
}


def read_fields(raw, start, formats, kind):
    fmt, names = formats.get(kind, ("", ""))
    layout = struct.Struct("<" + fmt)
    values = dict(zip(names.split(), layout.unpack_from(raw, start)))
    values["tail"] = raw[start + layout.size:]
    return values


def write_fields(row, formats, kind):
    fmt, names = formats.get(kind, ("", ""))
    return struct.pack("<" + fmt, *(row[name] for name in names.split())) + row["tail"]


def read_command(raw):
    opcode, selector, target = struct.unpack_from("<BBH", raw)
    return dict(opcode=opcode, selector=selector, target=target,
                fields=read_fields(raw, 4, COMMAND_FIELDS, opcode))


def write_command(row):
    opcode = row["opcode"]
    raw = struct.pack("<BBH", opcode, row["selector"], row["target"])
    raw += write_fields(row["fields"], COMMAND_FIELDS, opcode)
    require(len(raw) == SIZES[opcode], f"invalid command size for opcode {opcode}")
    return raw


def read_event(raw):
    return dict(kind=raw[1], fields=read_fields(raw, 2, EVENT_FIELDS, raw[1]))


def write_event(row):
    kind = row["kind"]
    body = write_fields(row["fields"], EVENT_FIELDS, kind)
    return struct.pack("<BB", len(body) + 2, kind) + body


def event_lists(raw, is_region):
    if is_region:
        tables = (("region", *REGION_DESCRIPTORS),)
        field = 10
    else:
        tables = (*TABLES, PLACED_ITEMS)
        field = 12
    offsets = set()
    for _, start_field, count_field, stride in tables:
        _, count, table = section(raw, start_field, count_field, stride)
        offsets.update(struct.unpack_from("<H", table, i * stride + field)[0] for i in range(count))
    return sorted(offsets)


def read_pool(pool, starts):
    records, terminators = {}, {}
    for start in starts:
        rows, end = walk(pool, start)
        for offset, raw in rows:
            records[offset] = read_event(raw)
        terminators[end] = struct.unpack_from("<BB", pool, end)
    cursor, gaps = 0, []
    sizes = {offset: len(write_event(row)) for offset, row in records.items()}
    sizes.update((offset, 2) for offset in terminators)
    for offset in sorted(sizes):
        require(offset >= cursor, f"overlapping pool records at +{offset:#x}")
        if offset > cursor:
            gaps.append((cursor, pool[cursor:offset]))
        cursor = offset + sizes[offset]
    if cursor < len(pool):
        gaps.append((cursor, pool[cursor:]))
    return records, terminators, gaps


def write_pool(size, records, terminators, gaps):
    rows = [(offset, write_event(row)) for offset, row in records.items()]
    rows.extend((offset, struct.pack("<BB", *pair)) for offset, pair in terminators.items())
    rows.extend(gaps)
    out = bytearray()
    for offset, body in sorted(rows):
        require(offset == len(out), f"pool rows must keep stored offsets at +{offset:#x}")
        out.extend(body)
    require(len(out) == size, "pool length changed")
    return bytes(out)


def rebuild_map(raw):
    rebuilt = bytearray(raw)
    counts = Counter()
    for _, offset_field, size_field, _ in STREAMS:
        offset, size, original = section(raw, offset_field, size_field, 1)
        commands, stop = frame(original)
        require(stop is None, f"unsupported command {stop}")
        groups = group(commands)
        parsed = [read_command(body) for _, body in commands]
        rebuilt[offset:offset + size] = b"".join(map(write_command, parsed))
        counts["groups"] += sum(head is not None for _, head, _ in groups)
        counts["commands"] += len(parsed) - sum(head is not None for _, head, _ in groups)
    for region, fields in ((False, OBJECT_EVENTS), (True, REGION_EVENTS)):
        offset, size, pool = section(raw, *fields, 1)
        records, terminators, gaps = read_pool(pool, event_lists(raw, region))
        rebuilt[offset:offset + size] = write_pool(size, records, terminators, gaps)
        counts["region_events" if region else "object_events"] += len(records)
        counts["terminators"] += len(terminators)
        counts["unreferenced"] += sum(len(body) for _, body in gaps)
    offset, count, predicates = section(raw, *PREDICATE_TABLE)
    rows = struct.iter_unpack("<BBBBB", predicates)
    rebuilt[offset:offset + count * 5] = b"".join(struct.pack("<BBBBB", *row) for row in rows)
    counts["predicates"] += count
    return bytes(rebuilt), counts


def rebuild_archive(archive):
    entry, raw = level_geometry(archive)
    rebuilt, counts = rebuild_map(raw)
    entries = parse_mix(archive)
    base = 6 + 12 * len(entries)
    rows = ((row["key"], row["offset"] - base,
             rebuilt if row == entry else memoryview(archive)[row["offset"]:row["offset"] + row["size"]])
            for row in entries)
    return write_mix(rows, len(archive) - base), counts


def check(data):
    counts = Counter()
    for stem in EXPECTED_LEVELS:
        path = select_archive(data, stem)
        source = path.read_bytes()
        rebuilt, level_counts = rebuild_archive(source)
        require(rebuilt == source, f"{path.name}: original and rebuilt MIX differ")
        counts.update(level_counts)
    require(counts["commands"] == 42594 and counts["groups"] == 9678, "retail command census changed")
    print("CHECK level write: 15 byte-identical MIXes, " +
          ", ".join(f"{value} {name}" for name, value in counts.items()))


def main():
    from pathlib import Path
    parser = lol2_cli.tool_args(__doc__, writes=False)
    args = parser.parse_args()
    if not args.check:
        parser.error("give --check to compare the original archives in memory")
    check(Path(args.data))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
