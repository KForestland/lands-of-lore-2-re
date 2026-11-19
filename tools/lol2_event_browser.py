#!/usr/bin/env python3
"""Browse original LoL2 event groups in one level. Prints summaries to stdout.

  lol2_event_browser.py --data DAT L1_DC
  lol2_event_browser.py --data DAT L1_DC --stream 1 --group 0x228e
  lol2_event_browser.py --data DAT --check

Use --start and --limit to page through a level. Offsets identify the original
records. Command meanings come from the documented native opcode paths.
"""
from cli_errors import ReaderArgumentParser, run_cli
from collections import Counter, defaultdict
import argparse
import os
from pathlib import Path
from struct import error as StructError

from lol2_disassemble_scripts import EXPECTED_LEVELS, select_archive
from lol2_export_scripts import export, require
from lol2_level_notes import EVENTS, effect, event_fields, room_names, trigger_description
from lol2_level_report import item_identities, scene_names


def event_index(level):
    """Index unique trigger records while retaining shared placement or descriptor owners."""
    index = defaultdict(dict)
    sources = [(obj["events"], [obj["ref"].replace("_", " ").replace(":", " ")])
               for obj in level["objects"] if obj["table"] != "region"]
    sources.extend((row["records"], [f"descriptor {i}" for i in row["descriptors"]])
                   for row in level["region_lists"])
    for records, owners in sources:
        for event in records:
            if "group" not in event:
                continue
            records_by_address = index[event["stream"], event["group"]]
            _, hosts = records_by_address.setdefault(event["file_offset"], (event, set()))
            hosts.update(owners)
    return index


def summary(group, triggers, items, scenes, rooms, verbose=False):
    stream, index = group["stream"], group["group"]
    commands = group["commands"]
    chain = " ".join(f"{row['opcode']:02X}" for row in commands) or "empty"
    noun = "record" if len(triggers) == 1 else "records"
    yield f"s{stream}:0x{index:04X} MIX+0x{group['file_offset']:X}  {len(triggers)} trigger {noun}  opcodes {chain}"
    if not triggers:
        yield "  No serialized trigger found."
    for at, (event, hosts) in sorted(triggers.items()):
        kind = event["kind"]
        _, matcher = EVENTS[kind]
        ordered = sorted(hosts)
        owner = ", ".join(ordered if verbose else ordered[:4])
        if not verbose and len(ordered) > 4:
            owner += f" (+{len(ordered)-4} owners)"
        operands = event_fields(kind, bytes.fromhex(event["raw_hex"]), items)
        description = trigger_description({"kind": kind, "operands": operands}, owner)
        predicate = event.get("predicate")
        if predicate:
            entry = predicate["entry_file_offset"]
            guard = f"MIX+0x{entry:X}" if entry is not None else "outside predicate table"
            description += f" if predicate {predicate['index']} passes ({guard})"
        yield f"  Trigger MIX+0x{at:X} kind {kind} [VA 0x{matcher:X}] {description}"
    meanings = Counter()
    for row in commands:
        meaning, address, confirmed, _ = effect(row, items, scenes, rooms)
        offset = row["file_offset"] if verbose else None
        meanings[(row["opcode"], meaning, address, confirmed, offset)] += 1
    for (opcode, meaning, address, confirmed, offset), count in meanings.items():
        witness = f"VA 0x{address:X}" if address is not None else "handler open"
        status = "CONFIRMED" if confirmed else "continuation UNCONFIRMED"
        multiple = f" x{count}" if count > 1 else ""
        where = f"MIX+0x{offset:X}  " if offset is not None else ""
        yield f"  {where}0x{opcode:02X}{multiple}  {meaning} [{witness}, {status}]"


def context(data):
    # The documented source tables resolve item identities, scenes and rooms.
    image = (data.resolve().parent / "LOLG.DAT").read_bytes()
    scenes = scene_names(data)
    require(bool(scenes), "native scene table unavailable")
    return item_identities(data), scenes, room_names(image)


def level_source(data, name):
    level = export(select_archive(data, name), include_items=True)
    require(not level["unsupported"], f"{name}: unsupported command framing")
    return level


def check(data, lookup):
    groups = commands = references = item_only = 0
    for name in EXPECTED_LEVELS:
        level = level_source(data, name)
        index = event_index(level)
        for group in level["groups"]:
            found = index[group["stream"], group["group"]]
            require(found, f"{name}: group {group['group']:#x} has no serialized trigger")
            groups += 1
            commands += len(group["commands"])
            references += len(found)
            item_only += all(owner.startswith("placed item ") for _, owners in found.values() for owner in owners)
            lines = list(summary(group, found, *lookup))
            if name == "L1_DC" and (group["stream"], group["group"]) == (1, 0x228E):
                require("opcodes 09 03 10" in lines[0] and any("MIX+0x6EAB81" in s and "predicate 4" in s for s in lines),
                        "level-1 empty-hand tutorial witness changed")
    require((groups, commands, references, item_only) == (13197, 42594, 13932, 57), "browser corpus counts changed")
    return (f"CHECK event browser: {len(EXPECTED_LEVELS)} levels, {groups} groups, {commands} commands, "
            f"{references} group-to-trigger links, {item_only} groups linked only through placed items")


def main():
    parser = ReaderArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    dat = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", default=dat, type=Path, required=dat is None, help="original DAT directory")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("level", nargs="?", help="level name or number")
    parser.add_argument("--stream", type=int, choices=(0, 1))
    parser.add_argument("--group", type=lambda text: int(text, 0), help="stream-relative group offset, e.g. 0x228e")
    parser.add_argument("--start", type=int, default=0, help="zero-based start within the selected groups")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.check == bool(args.level):
        parser.error("choose one level or --check")
    if args.start < 0 or args.limit < 1:
        parser.error("start must be nonnegative and limit positive")
    try:
        data = args.data
        lookup = context(data)
        if args.check:
            print(check(data, lookup))
            return
        level = level_source(data, args.level)
        index = event_index(level)
        matching = [group for group in level["groups"]
                    if (args.stream is None or group["stream"] == args.stream)
                    and (args.group is None or group["group"] == args.group)]
        selected = matching[args.start:args.start + args.limit]
        if not selected:
            raise ValueError("no event groups in this selection")
        print(f"{level['area']}: groups {args.start+1}–{args.start+len(selected)} of {len(matching)}"
              "  (opcodes in hex)")
        for group in selected:
            for line in summary(group, index[group["stream"], group["group"]], *lookup, verbose=args.group is not None):
                print(line)
    except (OSError, ValueError, StructError) as error:
        parser.exit(1, f"event browser: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
