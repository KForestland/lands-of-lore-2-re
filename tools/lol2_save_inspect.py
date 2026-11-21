#!/usr/bin/env python3
"""Inspect a player save written by the original DOS 1.30 game. Prints to stdout."""
from cli_errors import ReaderArgumentParser, run_cli, game_path
from ctypes import byref, c_size_t, create_string_buffer
from functools import lru_cache
import os
from pathlib import Path
import re
from struct import calcsize, error as StructError, unpack_from

from lol2_save_header import HEADER_SIZE, parse_header
from lol2_save_native import check as check_native
from lol2_source_format import u32
from lol2_texture_container import _lzo_decompress_fn

# Native selector tables in docs/lol2-save-sections.md. Flag 4 is LZO1X,
# flag 2 is a delta against the writer's baseline, before pointer handling.
GLOBAL_FLAGS = (7, 7, 7, 7, 7, 1, 1, 1, 1, 1, 3)
LEVEL_FLAGS = (12, 9, 12) + (7,) * 13 + (5, 5) + (7,) * 10 + (1, 1, 7, 7, 7, 1, 1, 5, 5) + (1,) * 23 + (5, 3, 1, 3, 1, 1, 7, 3)
LEVEL_HEADER = 0x2F8
GLOBAL_NAMES = (
    "player object", "shared script bytes", "player items", "player item occupancy",
    "combat interface", "movie context", "control context", "indexed bitmap",
    "menu context", "definition flags", "clock and frame state",
)
LEVEL_NAMES = {
    7: "region event records", 8: "region commands", 9: "object event records", 10: "object commands",
    11: "vertices", 12: "regions", 13: "secondary regions", 14: "wall rows",
    16: "list nodes", 17: "list node occupancy", 18: "props", 19: "controls", 21: "actors",
    22: "movables", 24: "local script bytes", 25: "placed items", 26: "surface presets",
    27: "texture animations", 28: "first world list head", 29: "second world list head",
    31: "non-player items", 32: "non-player item occupancy", 33: "last creature hit by player",
    34: "row pointer", 35: "actor groups", 36: "effect pool", 60: "audio context",
    61: "timer list header", 62: "timer pointers", 63: "parallel object list header",
    64: "object pointers", 65: "frame context", 66: "automap marker inputs", 67: "elapsed time",
}

# Decoded section-relative fields from the save, clock and geometry references.
# Scalar meanings describe a reconstructed value. Without a baseline, XOR
# payloads are printed as their byte patterns under the same field labels.
ITEM_FIELDS = (12, {0: ("I", "definition pointer"), 4: ("B", "instance input"),
                    5: ("B", "instance byte +5"), 8: ("I", "second adjusted pointer")})
LIST_FIELDS = (12, {0: ("I", "list pointer"), 4: ("I", "capacity"), 8: ("I", "active count")})
GLOBAL_FIELDS = {
    0: (0x22E, {0x145: ("I", "mana"), 0x162: ("B", "spell skill input"),
                0x185: ("i", "countdown (first nonzero writer UNCONFIRMED)"),
                0x19A: ("B", "first spell discount flags"), 0x19B: ("B", "second spell discount flags"),
                0x1AB: ("B", "player form")}),
    1: (1, {0: ("B", "shared byte")}), 2: ITEM_FIELDS,
    3: (1, {0: ("B", "item occupancy mask")}),
    5: (0x2D, {0x2C: ("B", "movie resume byte (object +0x3C)")}),
    6: (12, {4: ("I", "12-byte material row index"), 8: ("I", "remapped object pointer")}),
    7: (4, {0: ("I", "bitmap word")}), 9: (1, {0: ("B", "definition flag byte")}),
    10: (0x30, {4: ("I", "level clock"), 0x14: ("I", "accumulated sample"), 0x21: ("B", "frame index")}),
}
LEVEL_FIELDS = {
    11: (8, {0: ("i", "X (16.16)"), 4: ("i", "Y (16.16)")}),
    12: (44, {0: ("I", "adjusted pointer"), **{4 + 2*i: ("H", f"neighbour {i}") for i in range(4)},
              **{12 + 2*i: ("H", f"vertex {i}") for i in range(4)}, 0x14: ("h", "floor height"),
              0x16: ("h", "ceiling height"), 0x1A: ("H", "wall run selector"), 0x1C: ("H", "region flags")}),
    14: (8, {0: ("h", "material selector"), 5: ("B", "wall flags byte +5"), 6: ("B", "wall flags byte +6")}),
    19: (0x40, {0x26: ("H", "durability"), 0x36: ("H", "event-data offset")}),
    21: (0xBC, {0x88: ("H", "health"), 0xA8: ("B", "state byte"), 0xA9: ("B", "state mirror")}),
    22: (0x58, {0x48: ("I", "position field"), 0x55: ("B", "state"), 0x36: ("H", "event-data offset")}),
    24: (1, {0: ("B", "local script byte")}),
    25: (0x3C, {0xC: ("I", "adjusted region link"), 0x10: ("I", "next world-list link"),
                 0x16: ("B", "placement flags"), 0x18: ("H", "event-data offset"),
                 0x2C: ("I", "item definition pointer"), 0x30: ("B", "item instance input")}),
    26: (24, {4: ("h", "material selector"), 6: ("H", "surface word +6"), 8: ("H", "surface word +8"),
              0xA: ("H", "surface word +0x0A"), 0xC: ("h", "countdown"), 0xE: ("B", "period"),
              0xF: ("B", "mode"), 0x10: ("B", "update and direction flags"),
              0x11: ("b", "step for +8"), 0x12: ("b", "step for +0x0A"), 0x13: ("b", "step for +6 (times 32)"),
              0x14: ("B", "draw flags input"), 0x15: ("B", "region +0x27 input"),
              0x16: ("B", "surface class"), 0x17: ("B", "advance count for surface word changes")}),
    27: (8, {0: ("H", "base material index"), 2: ("h", "countdown"), 4: ("B", "period"), 5: ("B", "mode"),
             6: ("B", "update and direction flags"), 7: ("B", "current frame")}),
    28: (4, {0: ("I", "first list head pointer")}), 29: (4, {0: ("I", "second list head pointer")}),
    31: ITEM_FIELDS, 32: (1, {0: ("B", "item occupancy mask")}),
    33: (4, {0: ("I", "creature pointer")}), 34: (4, {0: ("I", "row pointer")}),
    35: (8, {0: ("I", "group head pointer"), 4: ("B", "member count"), 7: ("B", "group index")}),
    **{section: (4, {0: ("I", label)}) for section, label in enumerate((
        "effect-8 step limit", "effect-8 step counter", "effect-8 object +0x56 copy", "effect-8 target pointer",
        "step limit", "step counter", "object +0x56 copy", "target pointer", "effect-2 admission input",
        "effect link", "effect flag", "effect-2 admission input", "effect count",
    ), 37)},
    50: (12, {0: ("i", "position dword 0"), 4: ("i", "position dword 1"), 8: ("i", "height input")}),
    55: (12, {4*i: ("i", f"target coordinate {i}") for i in range(3)}),
    **{section: (4, {0: ("I", label)}) for section, label in enumerate((
        "enable flag", "effect-18 counter", "effect-18 phase", "effect-18 repeat count",
    ), 51)},
    **{section: (4, {0: ("I", label)}) for section, label in enumerate((
        "mode-5 follow-up gate", "effect counter", "effect counter compared with 10", "effect pool lookup gate",
    ), 56)},
    61: LIST_FIELDS, 62: (4, {0: ("I", "timer record pointer")}),
    63: LIST_FIELDS, 64: (4, {0: ("I", "object pointer")}),
    65: (0x140, {0x18: ("I", "rebased frame context pointer")}),
    66: (12, {0: ("H", "marker word 0"), 2: ("H", "marker word 1"), 6: ("H", "region index"),
              8: ("B", "marker input"), 9: ("B", "activated")}),
    67: (0x51, {0x14: ("i", "elapsed (16.16)"), 0x18: ("h", "elapsed (8.8)"), 0x1A: ("i", "elapsed whole ticks")}),
}
SLOT_FIELDS = {
    0x2C: ("I", "file size"), 0x30: ("I", "version"), 0x34: ("I", "layout version"),
    0x38: ("I", "global data version stamp"), 0x3C: ("I", "spell data version stamp"),
    0x40: ("I", "sound data version stamp"), 0x94: ("4s", "unknown"),
    0x98: ("4s", "unknown preview descriptor word"), 0x9C: ("I", "preview width"),
    0xA0: ("I", "preview height"), 0xA4: ("I", "preview data offset"),
    0x178: ("I", "address-map status"), 0x17C: ("i", "active level"),
    0x180: ("i", "player X (16.16)"), 0x184: ("i", "player Y (16.16)"),
    0x188: ("I", "player heading dword (low word)"), 0x18C: ("H", "player region (0xFFFF absent)"),
}


def directory(data):
    header = parse_header(data, len(data))
    if header["stored_level_lengths"] != tuple(size for _, size in header["levels"]):
        raise ValueError("stored level lengths disagree with the slot directory")
    return header


def level_sections(block):
    if len(block) < LEVEL_HEADER or u32(block, 0) != len(block):
        raise ValueError("invalid level block size")
    offsets = (*unpack_from("<68I", block, 0xD8), len(block))
    lengths = unpack_from("<68I", block, 0x1E8)
    if offsets[0] != LEVEL_HEADER or any(a > b for a, b in zip(offsets, offsets[1:])):
        raise ValueError("invalid level section directory")
    for start, end, length, flags in zip(offsets, offsets[1:], lengths, LEVEL_FLAGS):
        if bool(end - start) != bool(length) or (not flags & 4 and end - start != length):
            raise ValueError(f"level section at +0x{start:X} disagrees with its length")
    return list(zip(offsets, (b - a for a, b in zip(offsets, offsets[1:])), lengths))


lzo = lru_cache(maxsize=1)(_lzo_decompress_fn)


def decode_chunks(data, expected=None):
    raw = bytearray()
    cursor = 0
    while cursor < len(data):
        if len(data) - cursor < 8:
            raise ValueError(f"truncated LZO header at +0x{cursor:X}")
        size, packed = unpack_from("<2I", data, cursor)
        start = cursor + 8
        if not 0 < size <= 0x2000 or not 0 < packed <= 0x2090 or start + packed > len(data):
            raise ValueError(f"invalid LZO chunk length at +0x{cursor:X}")
        if expected is not None and len(raw) + size > expected:
            raise ValueError("LZO output exceeds the declared length")
        buffer = create_string_buffer(size)
        written = c_size_t(size)
        if lzo()(data[start:start + packed], packed, buffer, byref(written), None) != 0 or written.value != size:
            raise ValueError(f"invalid LZO data at +0x{start:X}")
        raw.extend(buffer.raw)
        cursor = start + packed
    if expected is not None and len(raw) != expected:
        raise ValueError("LZO output differs from the declared length")
    return raw


def dump_fields(data, fields, prefix, offset=0, delta=False):
    cursor = 0
    while cursor < len(data):
        at = offset + cursor
        if cursor in fields:
            fmt, label = fields[cursor]
            size = calcsize("<" + fmt)
            span = data[cursor:cursor + size]
            if delta or fmt.endswith("s"):
                value = span.hex(" ")
            else:
                value = unpack_from("<" + fmt, span)[0]
                value = f"{value} (0x{int.from_bytes(span, 'little'):0{2*size}X})"
        else:
            label = "unknown"
            size = next((n for n in range(1, 16) if cursor + n in fields), 16)
            value = data[cursor:cursor + size].hex(" ")
        yield f"{prefix}+0x{at:04X}  {label} = {value}"
        cursor += size


def address_map(base_at, length_at):
    return {**{base_at + 4*i: ("I", f"range {i} base") for i in range(26)},
            **{length_at + 4*i: ("I", f"range {i} length") for i in range(26)}}


def header_fields(data):
    name = data[:0x2C].split(b"\0", 1)[0]
    yield f"Slot+0x0000  display name = {name.decode('cp437')!r}"
    fields = {**SLOT_FIELDS, **address_map(0xA8, 0x110)}
    for first, count, label in ((0x44, 20, "version stamp"), (0x1BA, 20, "block offset"),
                                (0x20A, 20, "stored length")):
        fields.update({first + 4*i: ("I", f"level {i+1} {label}") for i in range(count)})
    fields.update({0x18E + 4*i: ("I", f"global {i} offset") for i in range(11)})
    # Keep the NUL delimiter with the display name and show the remaining bytes.
    start = min(len(name) + 1, 0x2C)
    yield from dump_fields(data[start:HEADER_SIZE], {k-start: v for k, v in fields.items()}, "Slot", start)


def level_at(data, span):
    offset, length = span
    if not length:
        raise ValueError("the requested level has no block in this slot")
    block = data[offset:offset + length]
    return offset, block, level_sections(block)


def inspect(data, level=None, section=None, global_section=None, row=None, baseline=None):
    header = directory(data)
    if section is None and global_section is None:
        yield from header_fields(data)
        start, size = header["preview"]
        yield f"Preview  slot+0x{start:X}  stored {size} bytes"
        for i, (start, size) in enumerate(header["sections"]):
            yield f"Global {i:02}: {GLOBAL_NAMES[i]}  slot+0x{start:X}  stored {size} bytes  flags 0x{GLOBAL_FLAGS[i]:X}"
        for number, span in enumerate(header["levels"], 1):
            if level is not None and level != number:
                continue
            if not span[1]:
                yield f"Level {number:02}: empty  slot+0x{span[0]:X}"
                continue
            offset, block, sections = level_at(data, span)
            yield f"Level {number:02}: slot+0x{offset:X}  {len(block)} bytes"
            fields = {0: ("I", "block length"), **address_map(4, 0x6C)}
            # Short blocks carry the observed, still unexplained status residue.
            fields[0xD4] = (("I", "address-map status") if u32(block, 0xD4) in (0, 1)
                            else ("4s", "unknown short-block status"))
            yield from dump_fields(block[:0xD8], fields, f"Level {number:02} block")
            for i, (start, stored, length) in enumerate(sections):
                yield (f"  L{i:02}: {LEVEL_NAMES.get(i, 'unlabelled')}  block+0x{start:X}  slot+0x{offset+start:X}"
                       f"  stored {stored} bytes  decoded {length} bytes  flags 0x{LEVEL_FLAGS[i]:X}")
        return

    if global_section is not None:
        i = global_section
        start, size = header["sections"][i]
        flags, name = GLOBAL_FLAGS[i], GLOBAL_NAMES[i]
        stride, fields = GLOBAL_FIELDS.get(i, (0, {}))
        label = f"G{i:02}"
        payload = data[start:start + size]
        decoded = decode_chunks(payload) if flags & 4 else payload
    else:
        level = level if level is not None else unpack_from("<i", data, 0x17C)[0]
        if not 1 <= level <= 20:
            raise ValueError("active level is outside the directory")
        i = section
        offset, block, spans = level_at(data, header["levels"][level-1])
        relative, size, length = spans[i]
        start = offset + relative
        flags, name = LEVEL_FLAGS[i], LEVEL_NAMES.get(i, "unlabelled")
        stride, fields = LEVEL_FIELDS.get(i, (0, {}))
        label = f"L{level:02} section {i:02}"
        payload = block[relative:relative + size]
        decoded = decode_chunks(payload, length) if flags & 4 else payload
        if baseline is not None:
            based = [(j, span[2]) for j, span in enumerate(spans) if LEVEL_FLAGS[j] & 2]
            expected = sum(length for _, length in based)
            if not flags & 2 or len(baseline) != expected or not size:
                raise ValueError("baseline does not match the level's XOR section lengths")
            begin = sum(length for j, length in based if j < i)
            decoded = bytes(a ^ b for a, b in zip(decoded, baseline[begin:begin + len(decoded)]))
    delta = bool(flags & 2) and baseline is None
    representation = "XOR bytes" if delta else "baseline XOR applied" if baseline is not None else "stored values"
    yield f"{label}: {name}  slot+0x{start:X}  {len(decoded)} decoded bytes  {representation}"
    if row is not None and (not stride or (row + 1) * stride > len(decoded)):
        raise ValueError("row is outside the documented payload layout")
    if not stride:
        yield from dump_fields(decoded, {}, label)
        return
    first, stop = (0, len(decoded)) if row is None else (row * stride, (row + 1) * stride)
    for at in range(first, stop, stride):
        chunk = decoded[at:at + stride]
        if len(chunk) < stride:
            yield from dump_fields(chunk, {}, label, at)
            break
        yield f"  Row {at // stride}"
        yield from dump_fields(chunk, fields, label, at, delta)


def verify_slot(data):
    header = directory(data)
    at, size = header["preview"]
    decode_chunks(data[at:at + size], header["width"] * header["height"])
    count = 0
    for flags, (at, size) in zip(GLOBAL_FLAGS, header["sections"]):
        if flags & 4:
            decode_chunks(data[at:at + size])
    for span in header["levels"]:
        if span[1]:
            _, block, spans = level_at(data, span)
            for flags, (at, size, expected) in zip(LEVEL_FLAGS, spans):
                if flags & 4:
                    decode_chunks(block[at:at + size], expected)
            count += 1
    return count


def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("slot", type=Path, nargs="?", help="player save slot written by the game")
    parser.add_argument("--data", type=Path, default=os.environ.get("LOL2_DAT"), help="original DAT folder")
    parser.add_argument("--check", action="store_true", help="check one slot, or the native code and sibling SAVEGAME folder")
    parser.add_argument("--level", type=int, choices=range(1, 21), metavar="1–20")
    selected = parser.add_mutually_exclusive_group()
    selected.add_argument("--section", type=int, choices=range(68), metavar="0–67", help="inspect a level section (default level is active)")
    selected.add_argument("--global-section", type=int, choices=range(11), metavar="0–10")
    parser.add_argument("--row", type=int, help="limit the payload view to one zero-based row")
    parser.add_argument("--baseline", type=Path, help="apply matching game-written level .IMG to a selected XOR section")
    args = parser.parse_args()
    if not args.slot and not (args.check and args.data):
        parser.error("supply a slot, or --data DAT --check")
    if args.row is not None and (args.row < 0 or (args.section is None and args.global_section is None)):
        parser.error("--row requires a nonnegative index and a selected section")
    if args.baseline and (args.check or args.section is None):
        parser.error("--baseline requires a selected level section")
    try:
        if args.check:
            if args.slot:
                paths = [args.slot]
            else:
                root = args.data.resolve().parent
                check_native(game_path(root, "LOLG.DAT"))
                paths = sorted(path for path in game_path(root, "SAVEGAME").glob("$*")
                               if path.is_file() and re.fullmatch(r"\.(?:\d{3}|XXX)", path.suffix.upper()))
            count = sum(verify_slot(path.read_bytes()) for path in paths)
            print(f"CHECK save inspector: {len(paths)} game-written player saves and {count} level blocks"
                  if paths else "CHECK save inspector: native save witnesses checked; no save slots supplied")
        else:
            baseline = args.baseline.read_bytes() if args.baseline else None
            for line in inspect(args.slot.read_bytes(), args.level, args.section, args.global_section, args.row, baseline):
                print(line)
    except (OSError, RuntimeError, ValueError, StructError) as error:
        parser.exit(1, f"save inspector: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
