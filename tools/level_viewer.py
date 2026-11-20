#!/usr/bin/env python3
"""Write interactive LoL2 map pages from your original MIX archives."""
from collections import defaultdict
import struct

from cli_errors import run_cli
from level_html import Plan, main
from level_move_ui import sections
from level_edit_data import placement_name
from lol2_export_scripts import PLACED_ITEMS, TABLES, section
from lol2_level_report import level_files
from lol2_level_schematic import edge_type, parse_geometry
from lol2_progression import collect, number, selectors
from lol2_source_format import level_geometry, u32

MARKS = {
    "actor": ("Actors", "#ffadbb", "A"),
    "prop": ("Props", "#a8bafa", "P"),
    "control": ("Controls", "#ffcb78", "C"),
    "movable": ("Movables", "#d6a9e7", "M"),
    "placed_item": ("Items", "#79e3c8", "I"),
}


def levels(data, selection):
    stems = level_files(data)
    if selection == "ALL":
        return stems
    matches = [stem for stem in stems if selection == stem or
               (selection.isdecimal() and number(stem) == int(selection))]
    if not matches:
        raise ValueError(f"Level {selection} was not found. Choose {', '.join(stems)} or all.")
    return matches


def progression(data, _selected):
    result = defaultdict(list)
    rows = collect(data)[0]
    marked, _ = selectors(rows)
    for i, row in enumerate(rows):
        result[row[0]].append((*row, i in marked))
    return result


def view(data, stem, gates):
    archive = data / f"{stem}.MIX"
    entry, raw = level_geometry(archive.read_bytes())
    base = entry["offset"]
    vertices, regions, _ = parse_geometry(raw)
    exit_regions = {int(row[7].split()[1]) for row in gates if row[7].startswith("region ")}
    plan = Plan(f"{stem} level plan", vertices,
                f"The map comes from {archive.name}. Source offsets show where records start in the archive. "
                "Exit conditions come from the stored scripts.")
    plan.legend.update({"Region": "#587888", "Wall edge": "#9ab0bb",
                        "Exit region or collapsed portal side": "var(--exit)"})
    start = base + u32(raw, 0x0C)
    for i, row in enumerate(regions):
        coords = [vertices[j] for j in row[6:10]]
        floor, ceiling = struct.unpack_from("<hh", raw, start - base + i * 44 + 0x14)
        neighbours = [str(value) if value != 0xFFFF else "wall" for value in row[2:6]]
        plan.polygon(coords, f"region-{i}", f"Region {i}", "Regions",
                     {"Floor / ceiling": f"{floor} / {ceiling}", "Neighbors": ", ".join(neighbours),
                      "Source": f"{archive.name} +{start + i * 44:#x}"},
                     style="region exit-region" if i in exit_regions else "region")
    for row in regions:
        coords = [vertices[j] for j in row[6:10]]
        for side, other in enumerate(row[2:6]):
            style = edge_type(row, regions[other] if other != 0xFFFF else None)
            if style != "portal":
                plan.line((coords[side], coords[(side + 1) % 4]), style)
    for key, start_at, count_at, stride in (*TABLES, PLACED_ITEMS):
        offset, count, stored = section(raw, start_at, count_at, stride)
        kind, color, prefix = MARKS[key]
        for i in range(count):
            at = i * stride
            x, y = struct.unpack_from("<hh", stored, at)
            region, = struct.unpack_from("<H", stored, at + 0x0A)
            name = placement_name(data, raw, key, i, offset + at)
            plan.dot((x << 16, y << 16), f"{key}-{i}", name or f"{kind[:-1]} {i}", kind,
                     {"Row": i, "Stored X / Y": f"{x} / {y}",
                      "Stored region word": region if region != 0xFFFF else "none",
                      "Source": f"{archive.name} +{base + offset + at:#x}"}, color, f"{prefix}{i}")
    shapes = {row["id"] for row in plan.records}
    for i, row in enumerate(gates, 1):
        _, dest, dest_entry, stream, group, event, guard, label, _, selector = row
        if selector:
            guard += " selector"
        target = label.replace(" ", "-").replace(":", "-")
        plan.note(f"exit-{i}", f"Exit {i} to {dest}", "Exits",
                  {"Destination entry": dest_entry, "Event": event,
                   "Gate": guard if guard != "none" else "No predicate on this event record.",
                   "Script": f"Stream {stream}, group {group} ({group:#x})"},
                  target=target if target in shapes else None)
    plan.edit_controls, plan.edit_script = sections(plan, stem, raw)
    return plan


if __name__ == "__main__":
    raise SystemExit(run_cli(main, __doc__, "DAT", "L1_DC.MIX", "L1_DC", levels, view, progression))
