#!/usr/bin/env python3
"""Read the 15 LoL2 level archives and list plot branches outside the exits.

Each row is one event record whose kind-19 predicate names a shared plot byte
(an operand of type 2, directly or through a type-4 sub-predicate) and whose
group holds no level-transition command. Shared slots are bytes of the plot
array at [0x26E58]. The record column gives each owner of the record and the
fields its matcher reads. The commands column names every command in that group.

  lol2_plot_branches.py --data DAT
  lol2_plot_branches.py --check --data DAT
"""
from cli_errors import run_cli
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lol2_cli  # noqa: E402
import lol2_export_scripts as X  # noqa: E402
from lol2_disassemble_scripts import NAMES, operands  # noqa: E402
from lol2_level_report import exit_predicates, level_files  # noqa: E402
from lol2_progression import decode, event_text  # noqa: E402

PAGE = Path(__file__).resolve().parents[1] / "docs" / "lol2-shared-predicates.md"
BEGIN = "<!-- plot-branches:begin -->"
END = "<!-- plot-branches:end -->"
EXIT_PREFIX = bytes.fromhex("020100001c")
PINS = {
    ("L1_DC", 0x6FDB2F, 0, 432, 51, (45,)),
    ("L8_SJ", 0xCD7FDA, 1, 13416, 108, (12, 13, 46)),
    ("L12_CM", 0x95FC40, 1, 5510, 7, (12,)),
    ("L20_BB", 0xECE1E3, 1, 6886, 1, (0,)),
}


def command_text(command):
    """Name one command from the opcode table. Known stores use the existing operand text."""
    name = NAMES[command["opcode"]]
    tail = operands(command)
    text = f"{command['opcode']:02X} {name}"
    if tail:
        text += " " + tail
    text += " bytes=" + command["raw_hex"]
    if "|" in text or "\n" in text:
        raise ValueError(f"command text is not a table cell: {text!r}")
    return text


def owners(scripts):
    """Every object or region that lists each linked record, by file offset."""
    found = defaultdict(list)
    for obj in scripts["objects"]:
        if obj["table"] == "region":
            continue
        for event in obj["events"]:
            if "group" in event:
                found[event["file_offset"]].append((event, obj["ref"]))
    for entry in scripts["region_lists"]:
        for event in entry["records"]:
            if "group" in event:
                found[event["file_offset"]].append((event, f"region {event['region']}"))
    return found


def record_text(listed):
    event = listed[0][0]
    labels = sorted({label for _, label in listed})
    return event_text(event, ", ".join(labels)), event.get("region") is None


def selectors(rows):
    """Rows of one record owner that test one shared slot for 0 and for 1, and nothing else."""
    families = defaultdict(list)
    for position, row in enumerate(rows):
        families[(row["stem"], row["owner"])].append(position)
    marked = set()
    for members in families.values():
        by_slot = defaultdict(set)
        for member in members:
            test = re.fullmatch(r"\(shared (\d+) == ([01])\)", rows[member]["predicate"])
            if test:
                by_slot[test.group(1)].add((test.group(2), member))
        for tests in by_slot.values():
            if {value for value, _ in tests} == {"0", "1"}:
                marked.update(member for _, member in tests)
    return marked


def collect(data_dir):
    rows = []
    stems = level_files(data_dir)
    for stem in stems:
        scripts = X.export(Path(data_dir) / f"{stem}.MIX")
        predicates = [bytes.fromhex(entry) for entry in scripts["predicate_table"]["entries"]]
        listed = owners(scripts)
        groups = {}
        for group in scripts["groups"]:
            key = (group["stream"], group["group"])
            if key in groups:
                raise ValueError(f"{stem} has two groups at {key}")
            groups[key] = group
        for key, offset, index, slots in exit_predicates(scripts)[3]:
            group = groups[key]
            for command in group["commands"]:
                if bytes.fromhex(command["raw_hex"])[:5] == EXIT_PREFIX:
                    raise ValueError(f"{stem} group {key} still holds a level transition")
            predicate = decode(predicates, index, set())
            if "|" in predicate or "\n" in predicate:
                raise ValueError(f"{stem} predicate {index} is not a table cell")
            record, on_object = record_text(listed[offset])
            commands = "; ".join(command_text(command) for command in group["commands"]) or "none"
            rows.append({
                "stem": stem,
                "offset": offset,
                "stream": key[0],
                "group": key[1],
                "index": index,
                "slots": slots,
                "predicate": predicate,
                "record": record,
                "owner": record.split(" kind ")[0],
                "object": on_object,
                "commands": commands,
            })
    rows.sort(key=lambda row: (int(row["stem"].split("_")[0][1:]), row["offset"], row["stream"], row["group"]))
    return stems, rows


def counts(stems, rows):
    by_level = defaultdict(set)
    for row in rows:
        by_level[row["stem"]].add((row["stream"], row["group"]))
    present = [stem for stem in stems if stem in by_level]
    absent = [stem for stem in stems if stem not in by_level]
    slots = {slot for row in rows for slot in row["slots"]}
    return len(by_level), sum(len(groups) for groups in by_level.values()), len(slots), present, absent


def table(stems, rows):
    levels, groups, slots, _present, absent = counts(stems, rows)
    where = "none" if not absent else ", ".join(absent)
    marked = selectors(rows)
    objects = sum(row["object"] for row in rows)
    lines = [
        f"{len(rows)} events, {groups} groups, {slots} shared slots, {levels} of {len(stems)} levels (none in {where}). "
        f"{objects} rows hang on an object record and {len(rows) - objects} on a region record. "
        f"`selector` marks {len(marked)} rows: rows of one record owner that test one shared slot for 0 and for 1.",
        "",
        "| Level | Event | Record | Stream | Group | Predicate | Shared slots | Commands |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for position, row in enumerate(rows):
        slots_text = ", ".join(str(slot) for slot in row["slots"])
        predicate = f"{row['index']}: {row['predicate']}" + (" selector" if position in marked else "")
        lines.append(
            f"| {row['stem']} | +0x{row['offset']:X} | {row['record']} | {row['stream']} | {row['group']} | "
            f"{predicate} | {slots_text} | {row['commands']} |"
        )
    return "\n".join(lines)


def marked(text):
    if BEGIN not in text or END not in text:
        raise ValueError("plot-branch markers are missing")
    body = text.split(BEGIN, 1)[1].split(END, 1)[0]
    if body.startswith("\n"):
        body = body[1:]
    if body.endswith("\n"):
        body = body[:-1]
    return body


def require_pins(rows):
    found = {
        (row["stem"], row["offset"], row["stream"], row["group"], row["index"], row["slots"])
        for row in rows
    }
    missing = PINS - found
    if missing:
        raise ValueError(f"pinned plot branches missing: {sorted(missing)}")


def main():
    parser = lol2_cli.tool_args(__doc__, out_help="write the generated table to this file")
    args = parser.parse_args()
    try:
        stems, rows = collect(args.data)
        require_pins(rows)
        levels, groups, slots, _present, _absent = counts(stems, rows)
        if (len(rows), groups, slots, levels, len(stems)) != (289, 287, 28, 14, 15):
            raise ValueError(f"plot-branch census {(len(rows), groups, slots, levels, len(stems))}")
        text = table(stems, rows)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"CHECK plot_branches: {error}\n")
    if args.check:
        stored = PAGE.read_text(encoding="utf-8") if PAGE.is_file() else ""
        try:
            body = marked(stored)
        except ValueError as error:
            parser.exit(1, f"CHECK plot_branches: {error}\n")
        if body != text:
            parser.exit(1, "CHECK plot_branches: docs/lol2-shared-predicates.md differs from the table\n")
        print(f"CHECK plot_branches: {len(rows)} events, {groups} groups, {slots} shared slots; "
              f"docs/lol2-shared-predicates.md matches")
        return 0
    if args.out:
        lol2_cli.refuse_repo_output(args.out)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {len(rows)} plot branches to {args.out}")
        return 0
    sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
