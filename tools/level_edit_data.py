"""LoL2 MIX placement fields used by the level editor."""
from cli_errors import game_path
from functools import lru_cache
from struct import unpack_from

from lol2_item_labels import OBJ5, PAIRS, TABLE, display_names, item_definitions, native_hash
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
    return game_path(data, f"{level}.MIX")


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


@lru_cache(maxsize=1)
def item_names(data):
    identities = {unpack_from("<I", row, 0x18)[0]: f"Item definition {index}"
                  for index, row in enumerate(item_definitions(data))}
    image_path = game_path(data.parent, "LOLG.DAT")
    if image_path.is_file():
        image = image_path.read_bytes()
        for i in range(PAIRS):
            pointer, = unpack_from("<I", image, OBJ5 + TABLE + 8 * i)
            label = image[OBJ5 + pointer:OBJ5 + pointer + 64].split(b"\0", 1)[0]
            key = native_hash(label)
            if key in identities and label and label.isascii():
                identities[key] = label.decode("ascii")
    identities.update(display_names(data))
    return identities


def placement_name(data, raw, kind, row, at):
    if kind == "placed_item":
        identity, = unpack_from("<I", raw, at + 0x20)
        label = item_names(data).get(identity, f"Item identity {identity:#010x}")
    elif kind == "prop":
        template, = unpack_from("<H", raw, at + 0x20)
        label = f"Prop template {template}"
    else:
        return None
    return f"{label} · row {row}"
