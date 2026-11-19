#!/usr/bin/env python3
"""Inspect smaller original LoL2 formats and look up documented native rules.

Examples: lol2_inspect.py --data DAT item 68
          lol2_inspect.py --data DAT wom TCEL
          lol2_inspect.py --data DAT native --table spell-effects --row 20

All commands print to standard output. They read the supplied installation.
"""
from cli_errors import ReaderArgumentParser, run_cli
import argparse
import os
from pathlib import Path
from struct import error as StructError, unpack_from

from lol2_cache_seed import compare
from lol2_disassemble_scripts import EXPECTED_LEVELS, select_archive
from lol2_export_scripts import STREAMS, frame, section
from lol2_hmi_midi import credits_paths, decode_track, stems_from, track_table
from lol2_item_labels import STRIDE, item_layout
from lol2_loose import describe_ne, describe_wave
from lol2_media_check import (BANNER, mix_dir, panel_names, read_at, room_module_layout,
                              scene_names, wsa_frames)
from lol2_parse_le import find_le_header, flags_str
from lol2_source_format import level_geometry, parse_mix, u32
from lol2_speech_names import cue_footer
from lol2_text_tables import parse_trr
from lol2_westwood_hash import ww_hash_v1


OBJECT_2_VA = 0x59024
NATIVE_TABLES = {
    "script-low": (0xEC89C, 24, 4, True),
    "predicate-left": (0x9DA50, 8, 4, True),
    "predicate-right": (0x9DA70, 8, 4, True),
    "predicate-operator": (0x9DA90, 8, 4, True),
    "item-handlers": (0x1CD884, 108, 4, True),
    "spell-schools": (0x1CCB44, 16, 2, False),
    "spell-effects": (0x1CC980, 113, 4, False),
    "damage-switch": (0x99704, 9, 4, True),
    "global-save": (0x11F64C, 12, 4, True),
    "level-save": (0x11F800, 69, 4, True),
}
RULES = {
    "motion": (("lol2-script-motion.md", "Opcode 18", "Opcode 196"),),
    "timers": (("lol2-script-events.md", "Object timers"),
               ("lol2-timer-clock.md", "Registered 60 Hz source", "Saved frame witness and live producer", "Save restore and menu pause")),
    "events": (("lol2-script-events.md", "Event records", "Predicates and shared bytes"),
               ("lol2-event-producers.md", "Object kind 1", "Confirmed event sources", "Placed-item event lists")),
    "spells": (("lol2-spells.md", "Cast tables and resource costs", "Acquisition", "Hit requests and experience"),
               ("lol2-spell-dispatch.md", "Player effect switch", "Payloads of the 35 player slots")),
    "combat": (("lol2-combat-ai.md", "Hit context and reduction", "Scripted hits and thresholds", "Creature state and attack output"),),
    "creatures": (("lol2-creature-transitions.md", "Live state and initialization", "Behavior dispatch", "Explicit changes and animation completion"),
                  ("lol2-creature-observation.md", "Observation records", "Mode 2 branch conditions", "Other mode branches"),
                  ("lol2-object-state-word.md", "Observed Byte Ownership", "Disassembly-Proven Bit Layout (Update 2)", "Remaining Unresolved Semantics")),
    "items": (("lol2-item-effects.md", "Script grants"),
              ("lol2-item-handlers.md", "Charges and use modes", "Handler destinations", "Remaining modes and effects")),
    "executable": (("lol2-executable-tables.md", "Selected executable tables", "Worked relocation"),),
}
TRR_SOURCES = {
    "automap": ("LOCALLNG.MIX", 0), "options": ("LOCALLNG.MIX", 1),
    "help": ("LOCALLNG.MIX", 3), "credits": ("LOCALLNG.MIX", 5),
    "movie-credits": ("MOVIES.MIX", 28), "loose-options": ("OPTTEXT.TRR", None),
    "loose-credits": ("CREDITS.TRR", None), "errors": ("ERRTEXT.TRR", None),
}


def read_key(path, key):
    _, _, entries = mix_dir(path)
    matches = [row for row in entries if row["key"] == key]
    if len(matches) != 1:
        raise ValueError(f"{path.name}: expected one member with key 0x{key:X}")
    member = matches[0]
    return member, read_at(path, member["offset"], member["size"])


def pick(rows, index, subject):
    if not 0 <= index < len(rows):
        raise ValueError(f"{subject} {index} is outside 0–{len(rows)-1}")
    return rows[index]


def cache_lines(data):
    for level, address, old, new, pointer in compare(data):
        position = "absent" if pointer == 0xFFFFFFFF else f"0x{pointer:X}"
        yield (f"{level} CDCACHE.LS_+0x{address:X}  seed length {old}  current bank {new}"
               f"  old position {position}")
    for row in parse_mix((data.parent / "CACHEBAK.MIX").read_bytes()):
        yield (f"CACHEBAK.MIX+0x{row['offset']:X}  entry {row['index']}  "
               f"key 0x{row['key']:08X}  {row['size']} bytes")


def room_lines(data, stem):
    # The code member's native name key is documented in lol2-room-archives.md.
    path = data / (stem.upper() + ".MIX")
    member, payload = read_key(path, ww_hash_v1(f"WOMS\\{stem.upper()}_.WOM"))
    body_size, entry, fixups = room_module_layout(payload)
    base = member["offset"]
    body = base + len(BANNER) + 16
    yield f"{path.name}+0x{base:X}  WOM entry {member['index']}  version 0x0101  {len(payload)} bytes"
    yield f"  Code body +0x{body:X}  {body_size} bytes  dispatch +0x{body+entry:X} (body+0x{entry:X})"
    yield f"  Relocations +0x{body+body_size:X}  {len(fixups)} u32 sites"


def animation_lines(data, image, requested, frame_index):
    name = next((name for name in panel_names(image) if name.casefold() == requested.casefold()), None)
    if name is None:
        raise ValueError("choose a native panel name: " + ", ".join(panel_names(image)))
    member, payload = read_key(data.parent / "LOCAL.MIX", ww_hash_v1(name))
    count, width, height, spans = wsa_frames(payload)
    start = member["offset"]
    yield f"{name} LOCAL.MIX+0x{start:X}  {width}x{height}  {count} frames, {len(spans)} stored deltas"
    indexed = list(enumerate(spans))
    if frame_index is not None:
        indexed = [pick(indexed, frame_index, "delta")]
    for i, (offset, packed, decoded) in indexed:
        yield f"  Delta {i:03}  LOCAL.MIX+0x{start+offset:X}  packed {packed}  decoded {decoded} bytes"


def music_lines(data, image, stem):
    names = {name.upper() for name in stems_from(image) if name and name != "badfile"}
    stem = stem.upper()
    _, credits_hmi = credits_paths(image)
    if stem != "CREDITS" and stem not in names:
        raise ValueError("choose an executable music stem or CREDITS")
    name = credits_hmi if stem == "CREDITS" else f"MUSIC\\{stem}.HMI"
    member, song = read_key(data.parent / "LOCAL.MIX", ww_hash_v1(name))
    if not song.startswith(b"HMI-MIDISONG"):
        raise ValueError("the named member is not an HMI song")
    offsets = track_table(song)
    base = member["offset"]
    yield f"{stem} LOCAL.MIX+0x{base:X}  {len(offsets)} HMI tracks"
    for i, (start, end) in enumerate(zip(offsets, offsets[1:] + [len(song)])):
        messages, tail = decode_track(song, start, end)
        yield (f"  Track {i:02}  LOCAL.MIX+0x{base+start:X}  {end-start} bytes  "
               f"{len(messages)} decoded events  {tail} trailing bytes")


def cue_lines(data, index):
    bank, table, footer, cues = cue_footer(data)
    indexes = range(len(cues)) if index is None else [index]
    for i in indexes:
        row = pick(cues, i, "cue")
        address = table + row * 60
        name = bank[address+16:address+48].split(b"\0", 1)[0].decode("ascii", "replace")
        yield f"Cue {i:03} LOCALLNG.MIX+0x{footer+2*i:X}  bank row {row:04} +0x{address:X}  {name}"


def scene_lines(data, names, index, only_level):
    name = pick(names, index, "scene")
    yield f"Scene {index:02} {name}  LOLG.DAT+0x{0x1CF58C+4*index:X}"
    stems = EXPECTED_LEVELS if only_level is None else (only_level,)
    for stem in stems:
        archive = select_archive(data, stem)
        meta, raw = level_geometry(archive.read_bytes())
        for stream, offset, size, _ in STREAMS:
            base, _, blob = section(raw, offset, size, 1)
            commands, error = frame(blob)
            if error:
                raise ValueError(f"{archive.name}: unframed commands")
            matches = [meta["offset"] + base + at for at, command in commands if command[0] == 21 and command[4] == index]
            if matches:
                yield f"  {archive.name} stream {stream}: {len(matches)} opcode-21 references; first +0x{matches[0]:X}"


def trr_lines(blob, label, base=0, identifier=None):
    count, ids, offsets = parse_trr(blob, label)
    yield f"{label}+0x{base:X}  {count} records, payload starts at +0x{base+offsets[0]+4:X}"
    if identifier is not None and identifier not in ids:
        raise ValueError(f"record ID {identifier} is absent")
    for i, name in enumerate(ids):
        if identifier is not None and name != identifier:
            continue
        start, end = offsets[i]+4, offsets[i+1]+4
        yield f"  ID {name:03}  +0x{base+start:X}  {end-start} bytes"
        if identifier is not None:
            yield f"  {blob[start:end-1].decode('cp437')!r}"


def text_lines(data, table, identifier):
    filename, index = TRR_SOURCES[table]
    if index is None:
        return trr_lines((data.parent / filename).read_bytes(), filename, identifier=identifier)
    path = (data if table == "movie-credits" else data.parent) / filename
    _, _, entries = mix_dir(path)
    row = pick(entries, index, "MIX entry")
    return trr_lines(read_at(path, row["offset"], row["size"]), filename, row["offset"], identifier)


# Item row fields printed by --item: (offset, width, name). docs/lol2-item-format.md
ITEM_FIELDS = ((0x2E, 1, "selector count 0"), (0x2F, 1, "selector count 1"), (0x37, 2, "strike sound"),
               (0x39, 2, "cursor sprite"), (0x3B, 2, "hit mask"), (0x3D, 2, "hit flags"),
               (0x3F, 1, "class byte"), (0x42, 1, "handler index"), (0x43, 1, "class flags"),
               (0x44, 1, "post-strike countdown addend"), (0x45, 1, "kind-4 operand"))


def item_lines(data, image, index):
    base, rows = item_layout(data)
    row = pick(rows, index, "definition")
    address = base + STRIDE*index
    yield f"Item {index} GLOBAL.MIX+0x{address:X}  identity 0x{u32(row,0x18):08X}"
    for at, width, name in ITEM_FIELDS:
        value = int.from_bytes(row[at:at+width], "little")
        yield f"  row+0x{at:02X} {name} = {value} (0x{value:X})"
    handler = row[0x42]
    yield from native_rows(image, "item-handlers", handler)
    for i in range(4):
        at = 0x47 + 5*i
        yield f"  row+0x{at:02X} descriptor {i} = {unpack_from('<BHH', row, at)}"
    yield f"  Raw row (91 bytes): {row.hex(' ')}"


def executable_layout(image):
    le = find_le_header(image)
    if le != 0x3BCB4 or image[0x39024:0x39026] != b"MZ":
        raise ValueError("embedded retail LE header is absent")
    page = u32(image, le + 0x28)
    start = 0x39024 + u32(image, le + 0x80)
    table, count = unpack_from("<2I", image, le + 0x40)
    yield f"LOLG.DAT+0x{le:X}  LE  {count} objects, page size 0x{page:X}, first data page +0x{start:X}"
    for i in range(count):
        at = le + table + i*24
        size, link, flags, first, pages, _ = unpack_from("<6I", image, at)
        yield f"  Object {i+1} +0x{at:X}  link 0x{link:X}  size 0x{size:X}  first page {first}  pages {pages}  {flags_str(flags)}"


def native_rows(image, table, row=None):
    start, count, stride, relocated = NATIVE_TABLES[table]
    if row is not None:
        pick(range(count), row, "row")
    rows = range(count) if row is None else [row]
    for i in rows:
        at = start + stride*i
        raw = image[at:at+stride]
        if len(raw) != stride:
            raise ValueError(f"table {table} extends outside LOLG.DAT")
        target = f"  analysis VA 0x{u32(raw,0) + OBJECT_2_VA:X}" if relocated else ""
        yield f"{table}[{i}] LOLG.DAT+0x{at:X}  {raw.hex(' ')}{target}"


def reference_section(text, title):
    selected = []
    active = False
    for line in text.splitlines():
        if line.startswith("## "):
            if active:
                break
            active = line[3:] == title
        if active:
            selected.append(line)
    if not selected:
        raise ValueError(f"missing documented section {title}")
    return "\n".join(selected).rstrip()


def rule_lines(topic):
    docs = Path(__file__).resolve().parents[1] / "docs"
    for filename, *headings in RULES[topic]:
        text = (docs / filename).read_text(encoding="utf-8")
        for heading in headings:
            yield f"docs/{filename}\n{reference_section(text, heading)}\n"


def loose_lines(data):
    wave = describe_wave(data / "AUTOPLAY.WAV")
    channels, rate, bits = wave["fmt"]
    yield f"AUTOPLAY.WAV  {wave['size']} bytes  PCM {channels} channel(s), {rate} Hz, {bits} bits"
    for at, chunk, size in wave["chunks"]:
        yield f"  +0x{at:X}  {chunk.decode('ascii', 'replace')}  {size} payload bytes"
    ne = describe_ne(data / "SETUP.EXE")
    yield f"SETUP.EXE  {ne['size']} bytes  NE header +0x{ne['ne']:X}"
    for i, (start, end, relocs) in enumerate(ne["segments"], 1):
        yield f"  Segment {i}  +0x{start:X} to +0x{end:X}  {relocs} relocations"
    for i, (start, end) in enumerate(ne["resources"], 1):
        yield f"  Resource {i}  +0x{start:X} to +0x{end:X}"


def check(data, image, names):
    witnesses = (
        (cache_lines(data), "CDCACHE.LS_", 20),
        (room_lines(data, "TCEL"), "WOM entry 3", 3),
        (animation_lines(data, image, "P_LUTHER.WSA", 0), "LOCAL.MIX+0x1909B17", 2),
        (music_lines(data, image, "CREDITS"), "LOCAL.MIX+0x1A4B52B  22 HMI tracks", 23),
        (cue_lines(data, 161), "bank row 0298", 1),
        (scene_lines(data, names, 13, "L12_CM"), "L12_CM.MIX", 2),
        (text_lines(data, "help", None), "41 records", 42),
        (item_lines(data, image, 68), "GLOBAL.MIX+0x5B9115", 18),
        (executable_layout(image), "LE  5 objects", 6),
        (native_rows(image, "item-handlers", 1), "VA 0x95FF0", 1),
        (loose_lines(data), "NE header +0xA270", None),
    )
    for view, fragment, length in witnesses:
        lines = list(view)
        if not any(fragment in line for line in lines) or (length is not None and len(lines) != length):
            raise ValueError(f"expected inspector witness {fragment}")
    for topic in RULES:
        if not any("|" in page for page in list(rule_lines(topic))):
            raise ValueError(f"missing tables in the {topic} reference")
    return "CHECK format inspector: cache, WOM, WSA, HMI, cues, scenes, TRR, items, LE, loose files and rule references"


def main():
    parser = ReaderArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    dat = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, required=dat is None, default=dat, help="original DAT folder")
    parser.add_argument("--check", action="store_true")
    sub = parser.add_subparsers(dest="topic")
    sub.add_parser("cache", help="seed row lengths and backup directory")
    sub.add_parser("loose", help="WAV chunks and setup executable sections")
    sub.add_parser("wom", help="room module framing").add_argument("stem", metavar="ROOM")
    wsa = sub.add_parser("wsa", help="panel animations and delta spans")
    wsa.add_argument("name")
    wsa.add_argument("--delta", type=int)
    sub.add_parser("hmi", help="music track spans and event counts").add_argument("stem")
    sub.add_parser("cue", help="speech cue lookup").add_argument("index", type=int, nargs="?")
    scene = sub.add_parser("scene", help="native movie name and script references")
    scene.add_argument("index", type=int)
    scene.add_argument("--level")
    trr = sub.add_parser("trr", help="message table record directory or selected record")
    trr.add_argument("table", choices=TRR_SOURCES)
    trr.add_argument("--id", type=int, dest="identifier")
    sub.add_parser("item", help="item definition and handler address").add_argument("index", type=int)
    native = sub.add_parser("native", help="executable objects or a selected native table")
    native.add_argument("--table", choices=NATIVE_TABLES)
    native.add_argument("--row", type=int)
    sub.add_parser("rules", help="documented rules by topic").add_argument("subject", choices=RULES)
    args = parser.parse_args()
    if args.check == bool(args.topic):
        parser.error("choose a topic or --check")
    if args.topic == "wom" and (not args.stem.isascii() or not args.stem.isalnum()):
        parser.error("ROOM must be an archive stem such as TCEL")
    if args.topic == "native" and args.row is not None and args.table is None:
        parser.error("--row requires --table")
    root = args.data.resolve()
    try:
        if args.check or args.topic in ("wsa", "hmi", "scene", "item", "native", "rules"):
            image, names = scene_names(root)
        if args.check:
            print(check(root, image, names))
            return
        views = {
            "cache": lambda: cache_lines(root), "loose": lambda: loose_lines(root),
            "wom": lambda: room_lines(root, args.stem), "cue": lambda: cue_lines(root, args.index),
            "wsa": lambda: animation_lines(root, image, args.name, args.delta),
            "hmi": lambda: music_lines(root, image, args.stem),
            "scene": lambda: scene_lines(root, names, args.index, args.level),
            "trr": lambda: text_lines(root, args.table, args.identifier),
            "item": lambda: item_lines(root, image, args.index),
            "native": lambda: native_rows(image, args.table, args.row) if args.table else executable_layout(image),
            "rules": lambda: rule_lines(args.subject),
        }
        for line in views[args.topic]():
            print(line)
    except (OSError, ValueError, StructError) as error:
        parser.exit(1, f"format inspector: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
