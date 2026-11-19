# Cookbook

Seven short recipes. Each one uses the tools on your own copy of the original game. Run them from the clone after:

```bash
export LOL2_DAT=/path/to/your/LOL2/DAT
```

Pictures, MIDI and written sheets go outside the clone. The examples use `../lol2-out`. A save slot is a game-written player save: a file the game wrote when you saved.

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
Slot+0x0180  player position dword 0 = -231300570 (0xF236A226)
Slot+0x0184  player position dword 1 = 308025890 (0x125C1A22)
Slot+0x0188  player position dword 2 = 64790 (0x0000FD16)
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
