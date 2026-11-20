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

Open `my mod work/edits/0007_OPTTEXT.TRR_text.json` in a text editor and change `Save Game` to `Save Your Game` inside `"value"`. Then build and verify:

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
