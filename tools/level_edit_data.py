"""LoL2 MIX placement fields used by the level editor."""
from lol2_export_scripts import PLACED_ITEMS, TABLES, section
from lol2_level_report import level_files as levels
from lol2_level_schematic import parse_geometry
from lol2_source_format import level_geometry

MARKER = "L1_DC.MIX"
ANCHOR = "Region"
AXIS = "Y"
KINDS = {"prop", "placed_item"}


def archive(data, level):
    if level not in levels(data):
        raise ValueError(f"{level} is not an original level archive.")
    return data / f"{level}.MIX"


def map_index(_level, original, _rows):
    return level_geometry(original)[0]["index"]


def fields(raw):
    vertices, regions, _ = parse_geometry(raw)
    outline = [[vertices[point] for point in row[6:10]] for row in regions]
    records = []
    for key, start, count_at, stride in (*TABLES, PLACED_ITEMS):
        if key in KINDS:
            offset, count, _ = section(raw, start, count_at, stride)
            records.extend((f"{key}-{i}", offset + i * stride) for i in range(count))
    return outline, records
