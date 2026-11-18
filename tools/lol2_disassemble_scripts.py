#!/usr/bin/env python3
"""Disassemble original LoL2 scripts with MIX offsets and event references.

  python3 tools/lol2_disassemble_scripts.py --data DAT L7_DH
  python3 tools/lol2_disassemble_scripts.py --data DAT --check

The listing includes numeric operands, group links and predicate bytes. It
describes static instructions and never executes the bytecode.
"""

from collections import Counter
from pathlib import Path
import re
import sys

import lol2_cli
from lol2_export_scripts import SourceError, export, require
from lol2_source_format import SIZES


# The addresses and operand interpretations are in docs/lol2-script-opcodes.md.
NAMES = {
    0: "zero", 1: "object_command", 2: "game_command", 3: "object_command",
    5: "object_selector", 6: "object_action", 7: "object_signed_action",
    8: "object_command", 9: "object_property", 11: "request_word",
    12: "request_byte", 13: "object_command", 14: "timer_control",
    15: "request_with_value", 16: "set_state", 17: "add_state",
    18: "start_sequence", 19: "deliver_hit", 20: "audio_request",
    21: "set_indexed_value", 22: "set_sequence_data", 23: "random_value",
    24: "audio_request", 196: "region_command", 197: "region_action",
    198: "set_local_byte", 199: "set_shared_byte", 200: "random_shared_byte",
    201: "random_local_byte", 204: "region_or_entry_update",
    205: "command_205", 206: "add_shared_byte", 207: "add_local_byte",
    208: "duration_or_region", 209: "move_region_objects", 210: "game_setting",
    240: "group",
}

EXPECTED_LEVELS = (
    "L1_DC", "L3_DH", "L4_HJ", "L5_HC", "L7_DH", "L8_SJ", "L9_DR",
    "L10_DC", "L12_CM", "L13_RC", "L14_HT", "L16_CA", "L17_HC", "L19_BC", "L20_BB",
)


def select_archive(data, level):
    level = level.upper()
    choices = sorted(
        p for p in data.iterdir()
        if p.suffix.upper() == ".MIX" and re.fullmatch(r"L\d+_[A-Z]{2}", p.stem.upper())
    )
    if level.isdecimal():
        level = "L" + str(int(level))
        choices = [p for p in choices if p.stem.split("_")[0].upper() == level]
    else:
        choices = [p for p in choices if p.stem.upper() == level]
    require(len(choices) == 1, f"expected one archive for {level}, found {len(choices)}")
    return choices[0]


def operands(command):
    opcode = command["opcode"]
    raw = bytes.fromhex(command["raw_hex"])
    if opcode == 2 and raw[:5] == b"\x02\x01\x00\x00\x1c":
        return f"level={raw[5] & 31} arrival={raw[5] >> 5}"
    if opcode == 14:
        return f"action={raw[4]} value={raw[5]} timer={raw[6]}"
    if opcode in (16, 17, 198, 199, 200, 201, 206, 207):
        value = raw[4] if opcode in (16, 17) else raw[5]
        if opcode in (17, 206, 207) and value >= 128:
            value -= 256
        prefix = "" if opcode in (16, 17) else f"index={raw[4]} "
        label = "max" if opcode in (200, 201) else "value"
        return f"{prefix}{label}={value}"
    return ""


def event_line(row):
    text = f"  MIX+0x{row['file_offset']:X}  kind={row['kind']:2} bytes={row['raw_hex']}"
    if "group" in row:
        text += f" -> S{row['stream']}:{row['group']:04X}"
    if row.get("predicate"):
        predicate = row["predicate"]
        text += f" predicate={predicate['index']}"
    if "event" in row:
        text += f" region={row['region']} byte6={row['event']} byte7={row['value']}"
    return text


def listing(level):
    yield f"{level['area']}  geometry MIX+0x{level['source']['geometry_entry_offset']:X}"
    for stream in level["streams"]:
        yield (f"STREAM {stream['stream']} MIX+0x{stream['file_offset']:X} "
               f"size={stream['size']} commands={stream['command_count']}")
    for group in level["groups"]:
        yield (f"S{group['stream']}:{group['group']:04X}  MIX+0x{group['file_offset']:X} "
               f"count={group['count']}")
        if group["header_hex"] is not None:
            yield f"  MIX+0x{group['file_offset']:X}  F0 group bytes={group['header_hex']}"
        for command in group["commands"]:
            opcode = command["opcode"]
            tail = operands(command)
            yield (f"  MIX+0x{command['file_offset']:X}  {opcode:02X} {NAMES[opcode]} "
                   f"kind=0x{command['kind']:02X} word2=0x{command['target']:04X} "
                   f"bytes={command['raw_hex']}" + (f" {tail}" if tail else ""))
    for source in level["objects"]:
        if source["events"] and source["table"] != "region":
            yield source["ref"]
            yield from map(event_line, source["events"])
    for row in level["region_lists"]:
        if row["records"]:
            yield ("region descriptors " + ",".join(map(str, row["descriptors"]))
                   + f" list=0x{row['list_offset']:X}")
            yield from map(event_line, row["records"])
    base = level["predicate_table"]["file_offset"]
    for index, entry in enumerate(level["predicate_table"]["entries"]):
        yield f"predicate {index:3} MIX+0x{base + 5 * index:X} {entry}"


def verify(level):
    for row in level["unsupported"]:
        raise SourceError(f"MIX+0x{row['file_offset']:X}: {row['reason']}")
    for stream in level["streams"]:
        require(stream["framed_bytes"] == stream["size"], "incomplete command stream")
    # Consume the same listing code used in ordinary operation.
    total = sum(line.startswith("  MIX+") and " word2=" in line for line in listing(level))
    require(total == level["counts"]["commands"], "listing omitted a command")
    return Counter({int(k): v for k, v in level["counts"]["opcode_use"].items()})


def check(data):
    require(NAMES.keys() == SIZES.keys(), "opcode names and size table disagree")
    counts = Counter()
    headers = 0
    for name in EXPECTED_LEVELS:
        try:
            level = export(select_archive(data, name))
            counts.update(verify(level))
            headers += sum(group["header_hex"] is not None for group in level["groups"])
        except (OSError, ValueError) as error:
            raise SourceError(f"{name}: {error}") from error
    require(sum(counts.values()) == 42594 and len(counts) == 32 and headers == 9678,
            "opcode counts differ from the verified retail corpus")
    print(f"CHECK scripts: {len(EXPECTED_LEVELS)}/15 levels, {sum(counts.values())} commands, "
          f"{len(counts)} observed opcodes, 0 unsupported")


def main(argv=None):
    parser = lol2_cli.tool_args(__doc__)
    parser.add_argument("level", nargs="?", help="e.g. L7_DH or 7")
    args = parser.parse_args(argv)
    data = Path(args.data).resolve()
    try:
        if args.check:
            if args.level or args.out:
                parser.error("--check reads the entire corpus and prints its result")
            check(data)
            return 0
        if not args.level:
            parser.error("a level is required without --check")
        level = export(select_archive(data, args.level))
        verify(level)
        if args.out:
            output = Path(args.out).resolve()
            require(data.parent != output and data.parent not in output.parents,
                    "output must be outside the game directory")
            with output.open("w", encoding="utf-8") as stream:
                for line in listing(level):
                    print(line, file=stream)
        else:
            for line in listing(level):
                print(line)
    except BrokenPipeError:
        return 0
    except (OSError, ValueError) as error:
        print(f"CHECK scripts: FAIL {error}" if args.check else str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
