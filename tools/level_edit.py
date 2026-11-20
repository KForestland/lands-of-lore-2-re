#!/usr/bin/env python3
"""Move existing item or prop placements and verify the copied level archive."""
from dataclasses import dataclass
from pathlib import Path
import os
from struct import pack_into, unpack_from
from tempfile import TemporaryDirectory

from cli_errors import ReaderArgumentParser, run_cli
from level_html import find_data, installation_root
import level_edit_data as adapter
import modkit
from modkit_core import archive_parts, digest, output_folder, read_json, replace_members


FORMAT = modkit.GAME + "-level-moves-1"


@dataclass(frozen=True)
class Placement:
    key: str
    offset: int
    anchor: int
    x: int
    y: int


def contains(points, x, y):
    # Include exact edges. Coordinates in the original vertex table use 16.16.
    x, y = x << 16, y << 16
    inside = False
    for (a, b), (c, d) in zip(points, points[1:] + points[:1]):
        if (c - a) * (y - b) == (d - b) * (x - a) and min(a, c) <= x <= max(a, c) and min(b, d) <= y <= max(b, d):
            return True
        if (b > y) != (d > y) and x < a + (y - b) * (c - a) / (d - b):
            inside = not inside
    return inside


def fields(raw):
    outline, records = adapter.fields(raw)
    sites = {}
    for key, at in records:
        x, y = unpack_from("<hh", raw, at)
        anchor, = unpack_from("<H", raw, at + 0x0A)
        if anchor < len(outline) and contains(outline[anchor], x, y):
            sites[key] = Placement(key, at, anchor, x, y)
    return outline, sites


def document(level, raw, moves):
    return {"format": FORMAT, "level": level, "source": digest(raw), "moves": moves}


def changed(raw, moves):
    if not isinstance(moves, list):
        raise ValueError("Download a move file from the level page.")
    if not moves:
        return raw, 0
    outline, sites = fields(raw)
    result = bytearray(raw)
    expected = {}
    count = 0
    for entry in moves:
        if not isinstance(entry, list) or len(entry) != 3:
            raise ValueError("Each move needs a placement ID and two coordinates.")
        key, x, y = entry
        if not isinstance(key, str) or key not in sites or key in expected:
            raise ValueError("A placement ID is repeated or does not have an editable location.")
        if any(type(v) is not int or not -32768 <= v <= 32767 for v in (x, y)):
            raise ValueError("Coordinates must be whole numbers in the signed 16-bit range.")
        old = sites[key]
        if not contains(outline[old.anchor], x, y):
            raise ValueError(f"{key} must stay inside its original {adapter.ANCHOR.lower()} {old.anchor}.")
        count += (x, y) != (old.x, old.y)
        pack_into("<hh", result, old.offset, x, y)
        expected[key] = (x, y)
    _, reread = fields(result)
    if any((reread[key].x, reread[key].y) != xy for key, xy in expected.items()):
        raise ValueError("The copied placements did not read back as requested.")
    return bytes(result), count


def rebuild(data, change):
    if (not isinstance(change, dict) or set(change) != {"format", "level", "source", "moves"}
            or change["format"] != FORMAT or not isinstance(change["level"], str)):
        raise ValueError("Give a change file exported by this game's level editor.")
    level = change["level"]
    path = adapter.archive(data, level)
    original = path.read_bytes()
    rows = archive_parts(modkit, path.name, original)
    at = adapter.map_index(level, original, rows)
    raw = rows[at][2]
    if change["source"] != digest(raw):
        raise ValueError("This move file is for different original level data. Export again from this copy.")
    edited, count = changed(raw, change["moves"])
    return path, replace_members(modkit, path.name, original, rows, {at: edited}), count


def apply(data, change, output):
    path, rebuilt, count = rebuild(data, change)
    with output_folder(output, data, installation_root(data)) as stage:
        written = stage / path.name
        written.write_bytes(rebuilt)
        if written.read_bytes() != rebuilt:
            raise ValueError("The copied archive did not read back byte for byte.")
    return path.name, count


def verify(data, change, output):
    path, rebuilt, count = rebuild(data, change)
    file = output / path.name
    if not file.is_file() or file.read_bytes() != rebuilt:
        raise ValueError(f"{file} does not match the verified copy.")
    return path.name, count


def check(data):
    levels, moved = 0, set()
    with TemporaryDirectory(prefix="lol-level-moves-") as tmp:
        folder = Path(tmp)
        for level in adapter.levels(data):
            path = adapter.archive(data, level)
            original = path.read_bytes()
            rows = archive_parts(modkit, path.name, original)
            raw = rows[adapter.map_index(level, original, rows)][2]
            empty = document(level, raw, [])
            baseline = folder / level
            apply(data, empty, baseline)
            if (baseline / path.name).read_bytes() != original:
                raise ValueError(f"{level} did not copy its unchanged archive byte for byte.")
            levels += 1
            outline, sites = fields(raw)
            for site in sites.values():
                kind = site.key.rsplit("-", 1)[0]
                if kind in moved:
                    continue
                for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    x, y = site.x + dx, site.y + dy
                    if -32768 <= x <= 32767 and -32768 <= y <= 32767 and contains(outline[site.anchor], x, y):
                        edit = document(level, raw, [[site.key, x, y]])
                        sample = folder / kind
                        apply(data, edit, sample)
                        verify(data, edit, sample)
                        moved.add(kind)
                        break
    if moved != adapter.KINDS:
        raise ValueError(f"Missing a test move for {sorted(adapter.KINDS - moved)}.")
    print(f"CHECK level moves: {levels} unchanged archives byte-identical; "
          f"{len(moved)} placement kinds applied and verified.")


def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("changes", nargs="?", type=Path, help="change file downloaded from the level page")
    default = os.environ.get(modkit.DATA_ENV)
    parser.add_argument("--data", default=default, required=default is None, help=modkit.FOLDER)
    parser.add_argument("--out", dest="copy_folder", type=Path, help="a new folder for the edited archive")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="compare an existing copy to the requested moves")
    mode.add_argument("--check", action="store_true", help="test the level corpus in temporary copies")
    args = parser.parse_args()
    data = find_data(args.data, "DAT", adapter.MARKER)
    if args.check:
        if args.changes or args.copy_folder:
            parser.error("Use --check with only --data.")
        check(data)
        return 0
    if not (args.changes and args.copy_folder):
        parser.error("Give the downloaded change file and --out, or use --check.")
    run = verify if args.verify else apply
    name, count = run(data, read_json(args.changes), args.copy_folder)
    print(f"Verified {count} moves in {name} at {args.copy_folder}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
