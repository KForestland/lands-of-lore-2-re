#!/usr/bin/env python3
"""Edit LoL2 TRRs and original item and creature definition fields."""
from pathlib import Path
import struct
import sys

from cli_errors import run_cli
from lol2_entity_field_analyzer import LEVEL_FILES
from lol2_item_labels import ITEMS_KEY, STRIDE
from lol2_mix_writer import write_mix
from lol2_source_format import parse_mix, u32
from lol2_text_writer import read_trr, write_trr
from lol2_westwood_hash import ww_hash_v1
import modkit_core as core

GAME = "lol2"
FOLDER = "the LoL2 game folder holding LOLG.DAT and DAT, or its DAT folder"
DATA_ENV = "LOL2_DAT"
ODF_KEYS = {Path(name).stem: {ww_hash_v1(f"SPHERE{s}\\{Path(name).stem}\\{Path(name).stem}.ODF")
                             for s in range(1, 4)} for name in LEVEL_FILES}
ITEM = (("hit_mask", 0x3B, "H"), ("hit_flags", 0x3D, "H"), ("strike_ticks", 0x44, "B"))
CREATURE = (("health_cap", 0x63, "H"), ("attack_input", 0x81, "B"))


def sources(root):
    return core.game_files(root, {".MIX", ".TRR"})


def is_loose(name):
    return name.upper().endswith(".TRR")


def members(raw):
    return [(row["key"], row["offset"], raw[row["offset"]:row["offset"] + row["size"]])
            for row in parse_mix(raw)]


def repack(rows, previous, size):
    base = 6 + 12 * len(rows)
    offsets = [0] * len(rows)
    shift = 0
    # Retain vacant spans and the physical order, including empty entries.
    for index in sorted(range(len(rows)), key=lambda i: (previous[i][1], bool(previous[i][2]))):
        offsets[index] = previous[index][1] - base + shift
        shift += len(rows[index][2]) - len(previous[index][2])
    return write_mix([(key, offsets[i], blob) for i, (key, _, blob) in enumerate(rows)], size - base + shift)


def layout(name, key, blob):
    archive = Path(name).name.upper()
    if archive == "GLOBAL.MIX" and key == ITEMS_KEY:
        return "items", (u32(blob, 4), u32(blob, 0x34), STRIDE, ITEM)
    if key in ODF_KEYS.get(Path(archive).stem, ()) and u32(blob, 0) == 18:
        return "creatures", (u32(blob, 0x10), u32(blob, 0x48), 147, CREATURE)
    return None


def view(name, key, blob):
    table = layout(name, key, blob)
    if table:
        kind, fields = table
        return kind, core.number_view(blob, *fields)
    if len(blob) >= 16 and 0 < u32(blob, 0) <= (len(blob) - 8) // 8:
        try:
            rows = read_trr(blob)
            if write_trr(rows) == blob:
                return "text", core.text_view(rows)
        except (ValueError, struct.error):
            if is_loose(name):
                raise
    return None


def encode(name, key, blob, kind, value):
    if kind == "text":
        return write_trr(core.text_rows(read_trr(blob), value))
    _, fields = layout(name, key, blob)
    return core.number_write(blob, *fields, value)


if __name__ == "__main__":
    raise SystemExit(run_cli(core.main, sys.modules[__name__]))
