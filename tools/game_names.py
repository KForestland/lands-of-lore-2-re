"""Read the names stored with LoL2's maps, items, spell schools and creatures."""
from functools import lru_cache
from pathlib import Path
import re
from struct import unpack_from

from cli_errors import ReaderArgumentParser, game_path, run_cli
from level_html import find_data
from lol2_cli import DEFAULT_DATA
from lol2_entity_field_analyzer import BODY_SIZE, RECORD_SIZE, locate_entity_table
from lol2_item_labels import OBJ5, display_names
from lol2_level_report import level_files
from lol2_source_format import parse_mix
from lol2_text_writer import read_trr
from lol2_westwood_hash import ww_hash_v1


@lru_cache(maxsize=1)
def language_mix(data):
    path = game_path(data.parent, "LOCALLNG.MIX")
    return path.read_bytes() if path.is_file() else b""


def language_table(data, name):
    mix = language_mix(data)
    if not mix:
        return []
    key = ww_hash_v1(name)
    match = next((row for row in parse_mix(mix) if row["key"] == key), None)
    if match is None:
        return []
    start = match["offset"]
    return read_trr(mix[start:start + match["size"]])


def level_names(data):
    names = dict(language_table(data, "automap.trr"))
    return {stem: names[index].decode("cp437") for stem in level_files(data)
            if (index := int(stem.split("_", 1)[0][1:])) in names and names[index]}


def creature_roles(data):
    """Read role labels from the dramatic cast pages of the installed credits."""
    loose = game_path(data.parent, "CREDITS.TRR")
    try:
        rows = read_trr(loose.read_bytes()) if loose.is_file() else language_table(data, "credits.trr")
    except (OSError, ValueError):
        return {}
    roles = {}
    for index, payload in rows:
        if 17 <= index <= 35:
            for line in payload.decode("cp437").split("\r"):
                if line.startswith("^%") and ":" not in line:
                    name = line[2:].strip()
                    if name and name.isprintable():
                        roles[name.casefold().removeprefix("the ")] = name
    return roles


def creature_label(tag, roles):
    key = tag.casefold()
    if key in roles:
        return roles[key]
    # These level-suffixed resource families reuse the same cast role.
    variant = re.fullmatch(r"(bac|dawn)l[0-9]+", key)
    if variant:
        matches = [name for role, name in roles.items() if role.startswith(variant[1])]
        if len(matches) == 1:
            return matches[0]
    words = tag.split()
    if words and all(word.isalpha() for word in words):
        return " ".join(word.capitalize() if word.isupper() or word.islower() else word for word in words)
    return "—"


def spell_names(data):
    """The executable's name/index pairs, through the final school row."""
    path = game_path(data.parent, "LOLG.DAT")
    if not path.is_file():
        return {}
    image = path.read_bytes()
    if len(image) < 0x1CFC08 or image[:2] != b"MZ":
        return {}
    names = {}
    for school in range(15):
        pointer, index = unpack_from("<II", image, 0x1CFB90 + 8 * school)
        start = OBJ5 + pointer
        field, end, _ = image[start:start + 36].partition(b"\0")
        if index == school and end and field.isascii():
            label = field.decode("ascii")
            if label.isprintable():
                names[school] = label
    return names


def creature_tags(archive, stem):
    """The definition selected by an actor's type byte carries a resource tag."""
    try:
        _, start, count = locate_entity_table(archive, stem)
    except ValueError:
        return {}
    names = {}
    for i in range(count):
        at = start + i * RECORD_SIZE
        field = archive[at + BODY_SIZE:at + RECORD_SIZE].partition(b"\0")[0]
        if field.isascii():
            label = field.decode("ascii")
            if label.isprintable():
                names[i] = label
    return names


def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, required=DEFAULT_DATA is None,
                        help="your game folder or its DAT folder")
    args = parser.parse_args()
    data = find_data(args.data, "DAT", "L1_DC.MIX")
    sections = (
        ("Levels", level_names(data).items()),
        ("Items", ((f"{key:#010x}", name) for key, name in display_names(data).items())),
        ("Spell schools", spell_names(data).items()),
    )
    for title, labels in sections:
        print(f"\n{title}")
        for key, name in labels:
            print(f"{name} ({key})")
    print("\nCreature definition tags")
    for stem in level_files(data):
        archive = game_path(data, f"{stem}.MIX").read_bytes()
        for slot, name in creature_tags(archive, stem).items():
            print(f"{name} ({stem}, definition {slot})")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
