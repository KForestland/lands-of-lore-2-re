# Cookbook

Each recipe uses the tools on your own copy of the original game. Run them from the clone after:

```bash
export LOL2_DAT=/path/to/your/LOL2/DAT
```

Pictures, MIDI and written sheets go outside the clone. The examples use `../lol2-out`. A save slot is a game-written player save: a file the game wrote when you saved.

## Write a full report

```bash
python3 tools/full_report.py --data "$LOL2_DAT" --out ../lol2-out/report
```

The tool writes `inventory.tsv` with the files in `DAT`, their sizes, the reader used and its result. For an archive, `complete` describes its directory and payload spans. The two copies of the credits table have separate rows. Open `levels/README.md` for the level sheets. `text-counts.tsv` gives one count per table from the localized and movie archive tables and the shipped loose TRRs.

Choose an output folder outside the game and clone. Use a fresh folder for each report.

## Draw a level schematic

```bash
python3 tools/lol2_level_schematic.py --data "$LOL2_DAT" --level 5 --out ../lol2-out/l5.png
```

The tool prints one line. Before the path it reads:

```text
L5_HC: 64 placements, 11 crowded labels omitted; wrote
```

and then the PNG path, resolved. The picture is an overhead line drawing: walls, portals, placed items marked I and creatures marked A, with a legend. Eleven crowded labels are left off the picture.

## See what an event does

```bash
python3 tools/lol2_event_browser.py --data "$LOL2_DAT" L1_DC --stream 1 --group 0x228e
```

```text
L1_DC: groups 1–1 of 1  (opcodes in hex)
s1:0x228E MIX+0x6E7FF5  1 trigger record  opcodes 09 03 10
  Trigger MIX+0x6EAB81 kind 4 [VA 0xADD36] prop 1050 interaction finds the player has no item selected if predicate 4 passes (MIX+0x7061D1)
```

The next lines are one opcode each: stop a sound, grant item definition 68, set an object state byte.

## Read your position from a save

```bash
python3 tools/lol2_save_inspect.py /path/to/your/slot
```

The first line on one autosave slot was:

```text
Slot+0x0000  display name = '**AUTOSAVE**'
```

The position fields, later in the same listing, were:

```text
Slot+0x0180  player X (16.16) = -231300570 (0xF236A226)
Slot+0x0184  player Y (16.16) = 308025890 (0x125C1A22)
Slot+0x0188  player heading dword (low word) = 64790 (0x0000FD16)
Slot+0x018C  player region (0xFFFF absent) = 807 (0x0327)
```

## Look up an item definition

```bash
python3 tools/lol2_inspect.py --data "$LOL2_DAT" item 68
```

```text
Item 68 GLOBAL.MIX+0x5B9115  identity 0xE0649CBA
  row+0x2E selector count 0 = 1 (0x1)
  row+0x2F selector count 1 = 0 (0x0)
```

The listing continues with the row's other named fields, then the raw bytes.

## List an archive

```bash
python3 tools/lol2_mix_parser.py --data "$LOL2_DAT" L1_DC.MIX
```

The first line is `MIX file:` and the path you named. The next lines are:

```text
Entries: 3
  [  0] key=0xB1162802  offset=  7389520  size=    35028
  [  1] key=0xB1202500  offset=  7091978  size=   297542
  [  2] key=0xB12F2907  offset=       42  size=  7091936
```

## Convert the music to MIDI

```bash
python3 tools/lol2_hmi_midi.py --data "$LOL2_DAT" --check
```

```text
CHECK hmi: 33 songs, 438 tracks, all end on FF 2F 00; 80067 note-ons with a duration; 32 table stems and CREDITS; standard MIDI in memory, division 120
```

To write the files, pass `--out` a directory that does not exist yet, outside the clone. A successful write prints nothing and leaves one `.mid` per song (33 files on this copy). If that directory already exists, the tool prints `CHECK hmi: FAIL` and a file-exists error.

## List a level's creatures

```bash
python3 tools/lol2_level_report.py --data "$LOL2_DAT" --level 1 --out ../lol2-out/sheets
```

```text
wrote 1 sheets to ../lol2-out/sheets
```

The sheet's geometry table counts `actors` as 57. Its entity section is:

```text
## Entity records

11 records of 147 bytes, by name tag: `B_HUMAN` ×3, `GGUARD` ×2, `WORM` ×2, `GGCAPT` ×1, `Kenneth` ×1, `ROACH` ×1, `Roach` ×1.
```

## Change text or numbers with the mod kit

The [mod kit](../tools/README.md#modkitpy) writes the game's text tables and numbers as files you can edit, and builds changed archives into a new folder. The game folder is only read.

```bash
python3 tools/modkit.py unpack "/path/to/LoL2" "my mod work"
```

Open the file in `my mod work/edits/` whose name ends in `_OPTTEXT.TRR_text.json` (the number in front may differ on your copy) in a text editor and change `Save Game` to `Save Your Game` inside `"value"`. Then build and verify:

```bash
python3 tools/modkit.py build "/path/to/LoL2" "my mod work" "my mod output"
python3 tools/modkit.py verify "/path/to/LoL2" "my mod work" "my mod output"
```

Each command ends with one summary line; build and verify print `22 archives or loose tables, 1 changed (OPTTEXT.TRR)`. Copy `OPTTEXT.TRR` from the output folder over a backup copy of your game to try it.

## Change one thing safely

This example replaces the help message with ID 0 in a copy of
`LOCALLNG.MIX`. **CONFIRMED.** The table starts at archive `+0x1B185DF`
and its first message at `+0x1B1872F`. The replacement uses the same
field length, so the other rows and MIX offsets stay at their stored
positions. See [message tables](lol2-text-tables.md).

The result is a modified copy for your own tests, not the original game.
This repository ships no game files and no changed files. The script only
reads your installation and writes only inside the new folder, so your
original stays untouched. Keep the changed copy to yourself and do not
share modified game files.

From this repository's root, set `source` to your game folder containing
`DAT`. Set `out` to a new directory outside the installation and the
repository. The script refuses an output folder inside either and needs
room for a full copy.

```bash
source="/path/to/LoL2"
out="/path/to/my-lol2-copy"
PYTHONPATH=tools python3 - "$source" "$out" <<'PY'
from pathlib import Path
import shutil
import sys

from lol2_mix_parser import read_mix_with_hashes
from lol2_mix_writer import write_mix
from lol2_text_writer import read_trr, write_trr
from lol2_westwood_hash import ww_hash_v1

source, out = (Path(arg).resolve() for arg in sys.argv[1:])
repo = Path.cwd()
if any(root == out or root in out.parents for root in (source, repo)):
    raise SystemExit("choose a new output directory outside the source and repo")
archive = Path("LOCALLNG.MIX")
original, directory, base = read_mix_with_hashes(source / archive)
members = [(key, start, original[base + start:base + start + size])
           for key, start, size in directory]
index, = (i for i, (key, _, _) in enumerate(members)
          if key == ww_hash_v1("helptext.trr"))
key, start, body = members[index]
rows = read_trr(body)
first, = (i for i, (key, _) in enumerate(rows) if key == 0)
ident, text = rows[first]
replacement = b"LOCAL TEST"
if len(replacement) > len(text):
    raise SystemExit("replacement exceeds the stored field length")
rows[first] = ident, replacement.ljust(len(text), b" ")
members[index] = key, start, write_trr(rows)
rebuilt = write_mix(members, len(original) - base)
shutil.copytree(source, out)
(out / archive).write_bytes(rebuilt)
PY
python3 tools/lol2_inspect.py --data "$out/DAT" trr help --id 0
```

Expect the reader to display ID 0 at `+0x1B1872F`, 262 bytes including
its terminating NUL, and the text `LOCAL TEST` followed by spaces.

## Share a change as a patch

The [README](../README.md#change-a-number-in-your-own-copy) walks through the whole route on your own copy: unpack, change one number, build, make a patch, apply it to a copy, read it back and undo it. The [patch format](formats/patch.md) page gives every rule and limit.

- `make` compares the game folder (`--data`) with a folder of changed files. The output folder of `modkit.py build` works as it is, and so does a copy of the game folder in which only some files changed.
- File names in the patch start at the game folder holding `LOLG.DAT` and `DAT`, whether you give that folder or its `DAT` folder, so a patch made from one applies to the other. A change made in `DAT` is named `DAT/GLOBAL.MIX`, never the copy beside `DAT`.
- `apply` writes nothing until every check has passed: the old bytes, for a program patch the whole file's SHA-256, and the undo. Applying a patch twice, or to another edition, is refused with one sentence.
- Program patches: copy the program file (`LOLG.DAT` or `LOLG.EXE`) into a new folder, at the same path it has in the game folder, change a byte with a hex editor, for example one letter of a message, and run `make` with that folder. The patch records the program's SHA-256 and applies only to that exact file. A program change may replace at most 16 bytes at a time and 256 in all, never changes the file length, and never touches copy-protection code.
- `GLOBAL.MIX` ships twice, byte for byte the same: in the game folder and in `DAT`. The mod kit unpacks both as separate edit files (`0002_GLOBAL.MIX_items.json` and `0008_GLOBAL.MIX_items.json`). Which copy the game opens has not been shown (not known), so make the same change in both; the patch then names both files.

## Change a saved game (a copy)

```bash
python3 tools/save_edit.py set '/path/to/LoL2/SAVEGAME/$MUSEUM_.000' heading 0x4000 --out "my edited save.000"
python3 tools/lol2_save_inspect.py "my edited save.000"
```

Save names begin with `$`; on Linux and macOS put them in single quotes as above (on Windows, double quotes are fine). The first command prints `set: heading OLD -> 0x4000; copy written to ...`, with your save's old value for OLD, then one line saying how far the field is proven. The save itself is only read, and the copy must go outside the game and save folders. Copy it over a slot in the `SAVEGAME` folder of a **copy** of your game to load it.

| Field | Value | Proven |
| --- | --- | --- |
| `position-from` | another save of the same level and version; copies its 14-byte position group (X, Y, heading, region) | tested: the DOS 1.30 game loaded copies with the position group edited (edited-save run) |
| `heading` | 0–65535, the low word of the heading dword at +0x188 | not yet tested: a heading-only copy has not been loaded |
| `name` | the display name, printable ASCII | not yet tested: no edited copy loaded yet |

A donor from another level or version, or with no region, is refused. Choose a donor whose place can be reached in the edited save's world. The editor rewrites the slot byte for byte before the change and checks the lengths, directories and stored packets after it.
[Slot offsets](lol2-save-format.md#slot-header-and-directory) ·
[What an edited copy must keep](lol2-save-format.md#editing-a-copy-of-an-original-slot)

Map viewer and editor notes for tool makers: [tool makers](TOOL_MAKERS.md).
