#!/usr/bin/env python3
"""Read LoL2 level scripts to tabulate each exit and its guard.

Each row is one level-transition command (bytes 02 01 00 00 1c). The slots
column is the kind-19 predicate on the one event that names that command's
group. Shared slots are plot bytes at [0x26E58]. Local slots are level bytes
at [0x26E54]. object+0x25 is the byte at [0xB7D80]+0x25.

  lol2_progression.py --data DAT              # print the page
  lol2_progression.py --data DAT --out FILE   # write the page
  lol2_progression.py --check --data DAT      # docs/PROGRESSION.md equals the page
"""
from cli_errors import run_cli, game_path
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lol2_export_scripts as X  # noqa: E402
from lol2_level_report import level_files  # noqa: E402
import lol2_cli  # noqa: E402

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "PROGRESSION.md")
OPS = ("==", "!=", "<=", ">=", ">", "<", "and", "or")


def decode(predicates, index, seen):
    if index in seen:
        return f"predicate {index} again"
    if index >= len(predicates):
        raise ValueError(f"predicate {index} is outside the table")
    row = predicates[index]
    if len(row) != 5 or row[0] > 7:
        raise ValueError(f"predicate {index} is not a 5-byte operator 0-7")

    def operand(kind, arg):
        if kind == 0:
            return str(arg)
        if kind == 2:
            return f"shared {arg}"
        if kind == 3:
            return f"local {arg}"
        if kind == 4:
            return decode(predicates, arg, seen | {index})
        if kind == 5:
            return "object+0x25"
        raise ValueError(f"predicate {index} operand type {kind}")

    left = operand(row[1], row[2])
    right = operand(row[3], row[4])
    return f"({left} {OPS[row[0]]} {right})"


def linked_events(scripts):
    """One event per file offset for each stream/group the scripts name."""
    found = {}

    def add(event, label):
        if "group" not in event:
            return
        key = (event["stream"], event["group"])
        found.setdefault(key, {})[event["file_offset"]] = (event, label)

    for obj in scripts["objects"]:
        if obj["table"] == "region":
            continue
        for event in obj["events"]:
            add(event, obj["ref"])
    for entry in scripts["region_lists"]:
        for event in entry["records"]:
            if "region" in event:
                add(event, f"region {event['region']}")
    return found


def event_text(event, label):
    """Name the record by the fields its matcher reads (record kinds on the events page)."""
    raw = bytes.fromhex(event["raw_hex"])
    kind = event["kind"]
    if "event" in event:
        return f"{label} kind {kind} event {event['event']}"
    if kind == 2:
        return f"{label} kind 2 timer flags 0x{raw[4]:02x}"
    if kind == 5:
        return f"{label} kind 5 event {raw[4]} value {raw[5]}"
    if kind == 8:
        return f"{label} kind 8 match {int.from_bytes(raw[4:6], 'little')}"
    return f"{label} kind {kind} value {raw[4]}"


# Opcodes that store into the level array [0x26E54] and the plot array [0x26E58].
LOCAL_WRITES = {198: "set", 201: "random", 207: "add"}
SHARED_WRITES = {199: "set", 200: "random", 206: "add"}


def collect(data_dir):
    """Rows of the exit table, and every stored write to a local or shared slot."""
    names = {int(stem.split("_")[0][1:]): stem for stem in level_files(data_dir)}
    rows, writes = [], {}
    for stem in level_files(data_dir):
        scripts = X.export(game_path(Path(data_dir), f"{stem}.MIX"))
        predicates = [bytes.fromhex(entry) for entry in scripts["predicate_table"]["entries"]]
        by_group = linked_events(scripts)
        level = scripts["level"]
        for group in scripts["groups"]:
            for command in group["commands"]:
                body = bytes.fromhex(command["raw_hex"])
                if body[0] in LOCAL_WRITES:
                    key = (f"local {body[4]}", stem)
                    writes.setdefault(key, set()).add((LOCAL_WRITES[body[0]], body[5]))
                elif body[0] in SHARED_WRITES:
                    writes.setdefault((f"shared {body[4]}", None), set()).add((SHARED_WRITES[body[0]], body[5]))
        for command in scripts["transitions"]:
            key = (command["stream"], command["group"])
            events = list(by_group.get(key, {}).values())
            if len(events) != 1:
                raise ValueError(f"{stem} group {key} is linked to {len(events)} events")
            event, label = events[0]
            predicate = event.get("predicate")
            slots = "none" if predicate is None else decode(predicates, predicate["index"], set())
            destination = command["destination_level"]
            rows.append((
                names.get(level, f"L{level}"),
                names.get(destination, f"L{destination}"),
                command["destination_entry"],
                command["stream"],
                command["group"],
                event_text(event, label),
                slots,
                label,
                event.get("event"),
            ))
    rows.sort(key=lambda row: (number(row[0]), number(row[1]), row[2], row[3], row[4]))
    return rows, writes


def number(stem):
    return int(stem.split("_")[0][1:])


def slot_counts(rows):
    shared, local = Counter(), Counter()
    for row in rows:
        for kind, index in re.findall(r"\b(shared|local) (\d+)", row[6]):
            (shared if kind == "shared" else local)[int(index)] += 1
    return shared, local


def brief(counter):
    if not counter:
        return "none"
    return ", ".join(f"{slot} ({count})" for slot, count in sorted(counter.items()))


def selectors(rows):
    """Rows of one owner and destination level that test one slot for 0 and for 1."""
    families = {}
    for position, row in enumerate(rows):
        families.setdefault((row[0], row[7], row[1]), []).append(position)
    marked, slots = set(), {}
    for (source, _, _), members in families.items():
        tests = [re.fullmatch(r"\((shared \d+|local \d+) == ([01])\)", rows[m][6]) for m in members]
        if len(members) < 2 or not all(tests):
            continue
        if len({test.group(1) for test in tests}) == 1 and {test.group(2) for test in tests} == {"0", "1"}:
            marked.update(members)
            slot = tests[0].group(1)
            slots[(slot, source if slot.startswith("local") else None)] = source
    return marked, slots


def write_text(slot, stem, writes):
    stored = sorted(writes.get((slot, stem), set()))
    where = f"{stem} scripts" if stem else "15 archives"
    if not stored:
        return f"no stored command in the {where} writes {slot}"
    return f"the stored writes to {slot} in the {where} are " + ", ".join(f"{how} {value}" for how, value in stored)


def level_cell(stem, pending):
    if stem in pending:
        pending.remove(stem)
        return f'<a name="level-{stem.lower()}"></a>[{stem}](levels/{stem}.md)'
    return stem


def check_level_sheets(rows):
    directory = Path(PAGE).parent / "levels"
    mentioned = {stem for row in rows for stem in row[:2]}
    sheets = {path.stem for path in directory.glob("*.md")} - {"README"}
    if sheets != mentioned:
        raise ValueError(f"without a sheet: {sorted(mentioned - sheets)}; "
                         f"without a progression row: {sorted(sheets - mentioned)}")
    for stem in sorted(sheets):
        text = (directory / f"{stem}.md").read_text(encoding="utf-8")
        for link in (f"](../PROGRESSION.md#level-{stem.lower()})", "](../NUMBERS.md)"):
            if link not in text:
                raise ValueError(f"missing {link[2:-1]} link in {stem}.md")
    return len(sheets)


def page(rows, names, writes):
    present = {number(stem) for stem in names.values()}
    sources = {number(row[0]) for row in rows}
    targets = {number(row[1]) for row in rows}
    silent = [names[level] for level in sorted(present - sources)]
    unentered = [names[level] for level in sorted(present - targets)]
    guarded = sum(row[6] != "none" for row in rows)
    objects = [row for row in rows if row[8] is None]
    event4 = [row for row in rows if row[8] == 4]
    marked, selector_slots = selectors(rows)
    shared, local = slot_counts(rows)
    lines = [
        "# Progression",
        "",
        "Made by `tools/lol2_progression.py` from the level-transition commands in the 15 level archives. "
        "One row is one command whose first five bytes are `02 01 00 00 1c`. Byte 5 stores the destination "
        "level in the low 5 bits and the destination entry in the high 3 bits. The event column is the one "
        "object or region record whose list names that command's group ([level sheets](levels/README.md)), "
        "with the fields its matcher reads ([record kinds](lol2-script-events.md#event-records)). "
        "The slots column is the kind-19 predicate on that record, from the 5-byte predicate table "
        "([predicates](lol2-script-events.md), [exit census](lol2-shared-predicates.md#exit-predicate-census)). "
        "`shared N` is byte N of the plot array at `[0x26E58]`. `local N` is byte N of the level array at "
        "`[0x26E54]`. `object+0x25` is the byte at `[0xB7D80]+0x25`. A type-4 operand is another row of the "
        "same table. `none` means that record has no predicate trailer. Slot numbers are table indexes, not names.",
        "",
        f"{len(rows)} exit commands, {guarded} with a predicate. "
        f"Shared slots named on those rows: {brief(shared)}. "
        f"Local slots named on those rows: {brief(local)}. "
        "Levels with no exit command: " + (", ".join(silent) if silent else "none") + ". "
        "Levels no exit command leads to: " + (", ".join(unentered) if unentered else "none") + ".",
        "",
        "Locked doors are not on this page. It lists level-transition commands only.",
        "",
        "**CONFIRMED.** Every matcher an exit row uses runs all matching records in list order, not only the first: "
        "the region walker `0xF2D2C` and the kind 5, 6 and 8 matchers `0xAD8E0`, `0xADDE0` and `0xAE510` "
        "advance to the next record after each run (back edges `0xF2FAD`, `0xAD9EF`, `0xADF26`, `0xAE5FA`). "
        "Each guard is checked after earlier matching groups in the same walk have run, and when two exits fire "
        "the later one wins, because the exit arm only stores the pending level (`0xD87AE`, `mov [0x223C8],eax`).",
        "",
        "## What a row does not show",
        "",
        f"{len(objects)} exits run from an object's event list. A row with `none` for slots still needs "
        "its event or timer to fire. The following upstream commands are from the original DOS 1.30 files. "
        "Archive offsets are file offsets and executable addresses are in the analysis convention. "
        "[Record kinds](lol2-script-events.md#event-records) · [Executable addresses](lol2-executable-tables.md)",
        "",
        "| Exit owner | What sends or arms the exit |",
        "|---|---|",
        "| L1_DC prop 447 | **CONFIRMED.** With local 2 = 0, entering any of regions 1190 or 1217–1224 requests "
        "cue 973 on prop 447. The first request is `L1_DC.MIX+0x6FD5B1`. Opcode 20 passes the object and cue "
        "through `0xB5C0D`. A voice slot keeps both, and the cleanup path at `0xE3824–0xE3841` can forward "
        "them to the kind-8 matcher. Its record at `+0x6EA117` runs group 4030. "
        "[Cue path](lol2-sound-cues.md) |",
        "| L3_DH control 82 | **CONFIRMED.** Region 1419 event 4 sets state 1 at `L3_DH.MIX+0x59C864`. "
        "On kind-6 value 1, the earlier record at `+0x5947E0` tests for 1 and sets 3 at `+0x5922F4`. "
        "The later record at `+0x5947F6` sees 3 and requests L4_HJ. The resource callback at `0x9EC60` "
        "sends this event value to its owner. **UNCONFIRMED.** Which resource instance supplies control 82 "
        "to that callback. Read the callback context +0x14 and resource +0x30 when entering region 1419. "
        "[Callback](lol2-event-producers.md#confirmed-event-sources) |",
        "| L8_SJ prop 1198 | **CONFIRMED.** Entry into regions 1514, 1515, 1519, 1523, 1527 or 1530 "
        "sends kind-6 value 20 through opcode 9 property 21 (`L8_SJ.MIX+0xCEC80D` through `+0xCEC8FD`, "
        "stride `0x30`). The record at `+0xCD7C4A` tests local 13 = 1. "
        "[Property 21](lol2-event-producers.md#confirmed-event-sources) |",
        "| L9_DR prop 104 | **CONFIRMED.** Control 82 kind-5 event 4 with state 2 starts timer 0 at "
        "`L9_DR.MIX+0x1628758`. Group 2140 starts timer 1 at `+0x16258D8`. Timer 1 runs group 2168 and "
        "requests L8_SJ. **UNCONFIRMED.** The sender of control 82's event 4. "
        "[Timer actions](lol2-script-events.md#object-timers) |",
        "| L14_HT prop 170 | **CONFIRMED.** Controls 78 and 79 have empty-hand records guarded by state 1. "
        "Both send kind-6 value 20 to prop 170 at `L14_HT.MIX+0xB2FD28` and `+0xB2FD3A`. "
        "The record at `+0xB322F0` tests local 22 = 1. [Held-item test](lol2-script-events.md#event-records) |",
        "| L17_HC movable 50 | **CONFIRMED.** Hit records on props 307–310 each send kind-6 value 20 "
        "to movable 50 (`L17_HC.MIX+0x490384`, `+0x4903A8`, `+0x4903CC`, `+0x4903F0`). "
        "With local 0 = 10, group 3878 sets its state to 1 at `+0x49053A`. The later kind-5 event 4 exit "
        "requires state 1. **UNCONFIRMED.** The sender of that event 4. |",
        "",
        "**UNCONFIRMED.** The kind-5 event 4 sends that trigger the L12_CM and L16_CA control 74 exits "
        "and advance the L9_DR and L17_HC chains are still open. At the kind-5 entry `0xAD8E0`, filter "
        "on event 4 and compare the incoming list pointer with the listed owner. The call return address "
        "will identify where that known owner gets its event.",
        "",
    ]
    if event4:
        lines += [
            f"**CONFIRMED.** {len(event4)} region {'exit uses' if len(event4) == 1 else 'exits use'} region event 4 ("
            + ", ".join(f"{row[0]} {row[7]}" for row in event4)
            + "). The player region update tests region +0x28 bit 1 (mask 2), sets it on first contact and "
            "passes event 4 at `0xD394A` before event 2 at `0xD39BB`. The alternate-region path sends event 4 "
            "at `0xD38D1` and sets the same bit. The L4_HJ exit record uses argument byte 0, so "
            "the matcher accepts either value of the incoming height comparison. No predicate follows it "
            "([region event arms](lol2-script-events.md#region-event-arms)).",
            "",
        ]
    if marked:
        notes = []
        for (slot, stem), source in sorted(selector_slots.items()):
            notes.append(f"{source} {slot}: {write_text(slot, stem, writes)}")
        lines += [
            f"`selector` marks {len(marked)} rows: rows of one record owner and one destination level that test "
            "one slot for 0 and for 1. While the slot holds 0 or 1, one of them runs whenever that record fires, "
            "so the slot picks the group or the arrival and does not close the way to that level. "
            + ". ".join(notes) + ".",
            "",
        ]
    lines += [
        "## Level to level",
        "",
        "One row per pair of levels, from the table below. Only command bytes and their linked records are "
        "counted; whether the player can reach each record is not part of this table. The "
        "[level graph](lol2-level-graph.md#exit-graph-decoded) has the same commands by arrival entry.",
        "",
        "| From | To | Commands | With predicate | Selector | Object record |",
        "|---|---|---:|---:|---:|---:|",
    ]
    pairs = {}
    for position, row in enumerate(rows):
        pairs.setdefault((row[0], row[1]), []).append((position, row))
    for (source, target), members in pairs.items():
        lines.append(f"| {source} | {target} | {len(members)} | "
                     f"{sum(row[6] != 'none' for _, row in members)} | "
                     f"{sum(position in marked for position, _ in members)} | "
                     f"{sum(row[8] is None for _, row in members)} |")
    lines += [
        "",
        "## Exit commands",
        "",
        "| From | To | Entry | Stream | Group | Event | Slots |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    # Put the jump target on the first outgoing row, or an incoming row
    # for a level with no exit of its own.
    outgoing = {row[0] for row in rows}
    pending = set(names.values())
    for position, row in enumerate(rows):
        cells = list(row[:7])
        cells[0] = level_cell(cells[0], pending)
        if row[1] not in outgoing:
            cells[1] = level_cell(cells[1], pending)
        if position in marked:
            cells[6] = f"{cells[6]} selector"
        lines.append("| " + " | ".join(str(part) for part in cells) + " |")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = lol2_cli.tool_args(__doc__, out_help="write the progression page to this file")
    args = parser.parse_args()
    try:
        names = {int(stem.split("_")[0][1:]): stem for stem in level_files(args.data)}
        rows, writes = collect(args.data)
        text = page(rows, names, writes)
    except (OSError, ValueError) as error:
        parser.exit(1, f"CHECK progression: {error}")
    guarded = sum(row[6] != "none" for row in rows)
    if args.check:
        stored = open(PAGE, encoding="utf-8").read() if os.path.isfile(PAGE) else ""
        if stored != text:
            parser.exit(1, "CHECK progression: docs/PROGRESSION.md differs from the exit table")
        try:
            covered = check_level_sheets(rows)
        except (OSError, ValueError) as error:
            parser.exit(1, f"CHECK progression: {error}")
        print(f"CHECK progression: {len(rows)} exits, {guarded} predicates; docs/PROGRESSION.md matches; {covered} linked level sheets")
        return 0
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {len(rows)} exits, {guarded} predicates to {args.out}")
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
