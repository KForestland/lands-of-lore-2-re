#!/usr/bin/env python3
"""Read game-written LoL2 saves in SAVEGAME next to --data and rebuild them in memory from fields and stored chunks."""
from dataclasses import dataclass
import os
from pathlib import Path
import re
import struct

from cli_errors import ReaderArgumentParser, run_cli
from lol2_save_header import HEADER_SIZE
from lol2_save_inspect import GLOBAL_FLAGS, LEVEL_FLAGS, LEVEL_HEADER, directory, level_sections, verify_slot

# Slot +0x30..+0x9B has the versions, stamps and two descriptor words.
SLOT_VERSIONS = struct.Struct("<27I")
# Slot +0xA8..+0x18D has the address map, status and player location.
SLOT_STATE = struct.Struct("<53IiiiIH")
LEVEL_MAP = struct.Struct("<53I")


@dataclass(frozen=True)
class Packed:
    chunks: tuple

    @property
    def expanded_size(self):
        return sum(size for size, _ in self.chunks)

    def write(self):
        return b"".join(struct.pack("<2I", size, len(data)) + data for size, data in self.chunks)


@dataclass(frozen=True)
class Level:
    address_map: tuple
    sections: tuple


@dataclass(frozen=True)
class Slot:
    name_area: bytes
    versions: tuple
    dimensions: tuple
    state: tuple
    gap: bytes
    preview: Packed
    sections: tuple
    levels: tuple


def parse_packed(blob):
    cursor = 0
    chunks = []
    while cursor < len(blob):
        if cursor + 8 > len(blob):
            raise ValueError("partial LZO chunk header in save")
        size, packed = struct.unpack_from("<2I", blob, cursor)
        start, end = cursor + 8, cursor + 8 + packed
        if not (0 < size <= 0x2000 and 0 < packed <= 0x2090 and end <= len(blob)):
            raise ValueError(f"LZO chunk extent at section +{cursor:#x}")
        chunks.append((size, blob[start:end]))
        cursor = end
    return Packed(tuple(chunks))


def read_part(blob, start, size, flags):
    part = blob[start:start + size]
    return parse_packed(part) if flags & 4 else part


def serialize_part(part):
    return (part.write(), part.expanded_size) if isinstance(part, Packed) else (part, len(part))


def parse_level(blob):
    spans = level_sections(blob)
    sections = []
    for (offset, size, expanded), flags in zip(spans, LEVEL_FLAGS):
        part = read_part(blob, offset, size, flags)
        length = part.expanded_size if isinstance(part, Packed) else len(part)
        if length != expanded:
            raise ValueError(f"section at level +{offset:#x} has a mismatched expanded length")
        sections.append(part)
    return Level(LEVEL_MAP.unpack_from(blob, 4), tuple(sections))


def parse_slot(blob):
    header = directory(blob)
    at, length = header["preview"]
    preview = parse_packed(blob[at:at + length])
    if preview.expanded_size != header["width"] * header["height"]:
        raise ValueError("preview chunks disagree with the dimensions")
    sections = tuple(read_part(blob, start, size, flags)
                     for (start, size), flags in zip(header["sections"], GLOBAL_FLAGS))
    levels = tuple(parse_level(blob[start:start + size]) if size else None
                   for start, size in header["levels"])
    return Slot(blob[:0x2C], SLOT_VERSIONS.unpack_from(blob, 0x30), (header["width"], header["height"]),
                SLOT_STATE.unpack_from(blob, 0xA8), blob[HEADER_SIZE:at], preview, sections, levels)


def write_level(level):
    at = LEVEL_HEADER
    starts = []
    expanded = []
    body = []
    for part in level.sections:
        encoded, length = serialize_part(part)
        starts.append(at)
        expanded.append(length)
        body.append(encoded)
        at += len(encoded)
    return (struct.pack("<I", at) + LEVEL_MAP.pack(*level.address_map)
            + struct.pack("<68I", *starts) + struct.pack("<68I", *expanded) + b"".join(body))


def write_slot(slot):
    preview_start = HEADER_SIZE + len(slot.gap)
    preview = slot.preview.write()
    at = preview_start + len(preview)
    offsets = []
    body = []
    for part in slot.sections:
        encoded, _ = serialize_part(part)
        offsets.append(at)
        body.append(encoded)
        at += len(encoded)
    block_sizes = []
    for level in slot.levels:
        encoded = b"" if level is None else write_level(level)
        offsets.append(at)
        block_sizes.append(len(encoded))
        body.append(encoded)
        at += len(encoded)
    return (slot.name_area + struct.pack("<I", at) + SLOT_VERSIONS.pack(*slot.versions)
            + struct.pack("<3I", *slot.dimensions, preview_start) + SLOT_STATE.pack(*slot.state)
            + struct.pack("<31I", *offsets) + struct.pack("<20I", *block_sizes)
            + slot.gap + preview + b"".join(body))


def synthetic_slot():
    """Build an empty preview plus one uncompressed section in a level."""
    sections = tuple(Packed(()) if flag & 4 else b"" for flag in GLOBAL_FLAGS)
    parts = [Packed(()) if flag & 4 else b"" for flag in LEVEL_FLAGS]
    parts[1] = b"sample"
    level = Level(tuple(range(53)), tuple(parts))
    slot = Slot(b"Writer\0".ljust(44, b"\xcd"), (0x12, 0x66) + (0,) * 25, (0, 0),
                (0,) * 58, b"gap", Packed(()), sections, (None, level) + (None,) * 18)
    return slot


def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=os.environ.get("LOL2_DAT"), help="DAT folder; its sibling SAVEGAME folder is read")
    parser.add_argument("--check", action="store_true", help="rebuild each save in memory and compare; writes no file")
    parser.add_argument("slot", type=Path, nargs="?", help="one save slot instead of the SAVEGAME folder")
    args = parser.parse_args()
    if not args.check or not (args.data or args.slot):
        parser.error("give --check with a save slot or the DAT folder")
    fixture = synthetic_slot()
    if parse_slot(write_slot(fixture)) != fixture:
        raise ValueError("synthetic LoL2 slot changed while rebuilding")
    paths = [args.slot] if args.slot else sorted(path for path in (args.data.resolve().parent / "SAVEGAME").glob("$*")
                                               if path.is_file() and re.fullmatch(r"\.(?:\d{3}|XXX)", path.suffix.upper()))
    blocks = 0
    for path in paths:
        original = path.read_bytes()
        rebuilt = write_slot(parse_slot(original))
        if rebuilt != original:
            raise ValueError(f"{path.name}: rebuilt save differs")
        blocks += verify_slot(rebuilt)
    if paths:
        print(f"CHECK LoL2 save write: {len(paths)} game-written saves and {blocks} level blocks byte-identical; "
              "stored LZO chunks copied, not re-compressed")
    else:
        print("CHECK LoL2 save write: synthetic slot passes; no game-written slots in SAVEGAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
