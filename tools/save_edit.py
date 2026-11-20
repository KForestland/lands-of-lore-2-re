#!/usr/bin/env python3
"""Change one documented field in a new copy of an original LoL2 save; the save itself is only read."""
from dataclasses import replace
from pathlib import Path
import struct

from cli_errors import ReaderArgumentParser, run_cli
from lol2_save_writer import parse_slot, write_slot
from modkit_core import output_path

FIELDS = ("name", "heading", "position-from")
# Fields a DOS 1.30 edited-save run has shown the game loading (docs/lol2-save-format.md).
CONFIRMED = {"position-from"}


def name_bytes(value, width):
    try:
        raw = value.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("the name must use plain ASCII letters, digits and punctuation") from None
    if not raw or len(raw) >= width or not all(32 <= byte <= 126 for byte in raw):
        raise ValueError(f"the name must have 1 to {width - 1} printable ASCII characters")
    return raw + b"\0"


def integer(value, low, high):
    try:
        number = int(value, 16) if value.lower().startswith("0x") else int(value, 10)
    except ValueError:
        raise ValueError(f"the value must be a whole number from {low} to {high}, not {value!r}") from None
    if not low <= number <= high:
        raise ValueError(f"the value must be a whole number from {low} to {high}, not {number}")
    return number


def read_slot(raw, what="the save"):
    try:
        slot = parse_slot(raw)
    except (ValueError, struct.error, IndexError, KeyError):
        raise ValueError(f"{what} could not be read; it may be damaged or not an original "
                         "LoL2 1.30 save") from None
    if write_slot(slot) != raw:
        raise ValueError(f"{what} cannot be rewritten byte for byte, so it is not edited")
    return slot


def shown(field, slot):
    if field == "name":
        return repr(slot.name_area.split(b"\0")[0].decode("latin-1"))
    x, y, heading, region = slot.state[-4:]
    if field == "heading":
        return f"{heading & 0xFFFF:#06x}"
    return f"(x {x / 65536:g}, y {y / 65536:g}, heading {heading & 0xFFFF:#06x}, region {region})"


def edit(raw, field, value):
    """The edited copy and a line 'field old -> new'."""
    slot = read_slot(raw)
    if field == "name":
        name = name_bytes(value, 44)
        edited = replace(slot, name_area=name + slot.name_area[len(name):])
    elif field in ("heading", "position-from"):
        state = list(slot.state)
        if field == "heading":
            heading = integer(value, 0, 65535)
            state[-2] = (state[-2] & 0xFFFF0000) | heading
        else:
            path = Path(value)
            if not path.is_file():
                raise ValueError(f"donor save not found: {value}")
            donor = read_slot(path.read_bytes(), "the donor save")
            if donor.versions[:25] != slot.versions[:25] or donor.state[-5] != slot.state[-5]:
                raise ValueError("the donor save must come from the same level and game version")
            if donor.state[-1] == 0xFFFF:
                raise ValueError("the donor save has no player region")
            state[-4:] = donor.state[-4:]
        edited = replace(slot, state=tuple(state))
    else:
        raise ValueError(f"unknown field {field}; give one of {', '.join(FIELDS)}")
    changed = write_slot(edited)
    if len(changed) != len(raw) or parse_slot(changed) != edited:
        raise ValueError("the edited copy did not read back as requested; nothing was written")
    return changed, f"{field} {shown(field, slot)} -> {shown(field, edited)}"


def status(field):
    if field in CONFIRMED:
        return "CONFIRMED: the DOS 1.30 game loaded copies with the position group edited this way"
    return "UNCONFIRMED: no edited copy of this field has been loaded by the game yet; keep a backup of your saves"


def main():
    try:
        return run()
    except OSError as error:
        reason = (error.strerror or "the system refused").lower()
        raise ValueError(f"cannot use {error.filename or 'a file'}: {reason}") from None


def run():
    parser = ReaderArgumentParser(
        description=__doc__,
        epilog="Example: save_edit.py set '/path/to/SAVEGAME/$MUSEUM_.000' heading 0x4000 --out 'my edited save.000' (save names begin with $; on Linux and macOS use single quotes).")
    commands = parser.add_subparsers(dest="command", metavar="set")
    commands.required = True
    setter = commands.add_parser("set", help="write a copy of the save with one field changed",
                                 description="Write a copy of the save with one field changed.")
    setter.add_argument("save", type=Path, help="an original save file; only read")
    setter.add_argument("field", choices=FIELDS)
    setter.add_argument("value", help="the new value: a name, a heading 0-65535, "
                                      "or for position-from another save of the same level")
    setter.add_argument("--out", required=True, type=Path, help="the new save file to write, outside the game and save folders")
    args = parser.parse_args()
    if not args.save.is_file():
        raise ValueError(f"save not found: {args.save}")
    path = output_path(args.out, args.save.resolve().parent, args.save)
    if not path.parent.is_dir():
        raise ValueError(f"the folder {path.parent} does not exist; create it first or choose another place")
    changed, change = edit(args.save.read_bytes(), args.field, args.value)
    with path.open("xb") as target:
        target.write(changed)
    print(f"set: {change}; copy written to {path}; the original save was only read")
    print(status(args.field))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
