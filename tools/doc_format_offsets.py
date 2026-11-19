#!/usr/bin/env python3
"""Check selected format-page offsets against the readers that decode them."""
from pathlib import Path
import re
import struct

from cli_errors import ReaderArgumentParser, run_cli
from doc_links import prose_lines
from lol2_export_scripts import REGION_DESCRIPTORS, STREAMS
from lol2_hmi_midi import track_table
from lol2_inspect import ITEM_FIELDS
from lol2_save_header import HEADER_SIZE, parse_header
from lol2_source_format import parse_mix

DOCS = Path(__file__).resolve().parents[1] / "docs"
NUMBER = re.compile(r"0x[0-9a-f]+|[0-9]+", re.I)


def offsets(cell):
    return tuple(int(token, 16 if token.lower().startswith("0x") else 10)
                 for token in NUMBER.findall(cell))


def documented(page, label_column, starts_with, columns=(0,)):
    lines = prose_lines((DOCS / page).read_text(encoding="utf-8"))
    rows = [tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            for line in lines if line.lstrip().startswith("|")]
    matches = [row for row in rows
               if len(row) > label_column and row[label_column].startswith(starts_with)]
    if len(matches) != 1:
        raise ValueError(f"{page}: expected one layout row for {starts_with}")
    try:
        observed = tuple(value for index in columns for value in offsets(matches[0][index]))
    except IndexError as error:
        raise ValueError(f"{page}: incomplete layout row for {starts_with}") from error
    if not observed:
        raise ValueError(f"{page}: {starts_with}: no documented offset")
    return observed


def agree(page, field, observed, expected, source):
    if observed != tuple(expected):
        want = ", ".join(f"{value:#x}" for value in expected)
        got = ", ".join(f"{value:#x}" for value in observed)
        raise ValueError(f"{page}: {field}: documented {got}, {source} reads {want}")


def probe(page, field, offset, read):
    """Build a synthetic file around the documented offset and ask the reader
    for the field. A wrong offset on the page, or a reader that reads the
    field elsewhere, gives something other than the expected value."""
    try:
        result = read(offset)
    except (ValueError, IndexError, KeyError, struct.error) as error:
        result = f"error: {error}"
    if result is not True:
        raise ValueError(f"{page}: {field}: documented +{offset:#x}, but the reader does not read it there"
                         + (f" ({result})" if result is not False else ""))


def mix_key(offset):
    raw = bytearray(18)
    struct.pack_into("<I", raw, offset, 0xA1B2C3D4)
    struct.pack_into("<HI", raw, 0, 1, 0)
    return parse_mix(bytes(raw))[0]["key"] == 0xA1B2C3D4


def save_globals(offset):
    header = bytearray(HEADER_SIZE)
    size = HEADER_SIZE + 64
    struct.pack_into("<3I", header, 0x2C, size, 0x12, 0x66)
    struct.pack_into("<3I", header, 0x9C, 1, 1, HEADER_SIZE)
    struct.pack_into("<31I", header, 0x18E, *([size] * 31))
    struct.pack_into("<11I", header, offset, *range(HEADER_SIZE + 1, HEADER_SIZE + 12))
    sections = parse_header(bytes(header), size)["sections"]
    return [start for start, _ in sections] == list(range(HEADER_SIZE + 1, HEADER_SIZE + 12))


def hmi_table(offset):
    song = bytearray(0x110)
    struct.pack_into("<I", song, 0xE4, 1)
    struct.pack_into("<I", song, offset, 0x100)
    struct.pack_into("<I", song, 0x100, 0x104)
    return track_table(bytes(song)) == [0x104]


def check():
    page = "formats/mix.md"
    probe(page, "index rows", documented(page, 2, "index rows:")[0], mix_key)
    page = "lol2-level-script-format.md"
    agree(page, "command stream 0", documented(page, 3, "command stream 0", (0, 1)), STREAMS[0][1:3],
          "lol2_export_scripts.STREAMS")
    agree(page, "region descriptors", documented(page, 3, "region descriptors", (0, 1)), REGION_DESCRIPTORS[:2],
          "lol2_export_scripts.REGION_DESCRIPTORS")
    page = "lol2-save-format.md"
    first, last = documented(page, 2, "Absolute offsets for global sections")
    probe(page, "global section directory", first, save_globals)
    agree(page, "global section directory end", (last,), (first + 4 * 11 - 1,), "lol2_save_header (11 u32)")
    page = "lol2-music-2026-11.md"
    probe(page, "track table pointer", documented(page, 2, "file-relative offset of the track table")[0], hmi_table)
    page = "lol2-item-format.md"
    agree(page, "flags word", documented(page, 2, "flags word,"),
          [at for at, width, name in ITEM_FIELDS if name == "hit flags"], "lol2_inspect.ITEM_FIELDS")
    print("CHECK format offsets: six documented MIX, MAP, save, HMI and item fields agree with the readers")

def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("--data", help="accepted for check_all compatibility")
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    check()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
