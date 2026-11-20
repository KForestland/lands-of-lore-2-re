# Lands of Lore II: file formats and game rules

*Lands of Lore: Guardians of Destiny* is a first-person role-playing game by Westwood Studios (1997). This repository documents how its original data files and rules work, and gives you Python tools that read them from your own copy of the game.

It contains documentation, tools and small tables of numbers. It contains no game files and no extracted game pictures, sounds, movies or text dumps.

## At a glance

- **What this is:** documentation of the original 1997 DOS game's data files and engine (archives, levels, scripts, items, spells, creatures, sound, movies, saves), checked against the game files and the original program.
- **What you can do today:** list and unpack every archive, decode sounds, music and movies, read every level's geometry and scripts, follow one event from a click to its result, and look up what each item and spell does in the program.
- **Start in five minutes:** the [Quick start](#quick-start) below, then [Start here, by goal](docs/START_HERE.md), [How the game works](docs/HOW_THE_GAME_WORKS.md) or the [worked example](docs/tutorial-one-event.md).
- **Recipes:** [cookbook](docs/COOKBOOK.md), seven short runs with the command and the first lines it prints.
- **Numbers at a glance:** [item combat inputs, effect costs, creature definitions and form requests](docs/NUMBERS.md), tables generated from the original files by `tools/lol2_numbers.py`.
- **What is still unknown:** the [open questions](docs/OPEN_QUESTIONS.md), counted in the [rating](#rating); most open points are the meaning of specific fields and effects. Some can only be settled by watching the original game run. Answered probes are counted in the rating; which ones and how: [NEEDS_A_RUNNING_GAME](docs/NEEDS_A_RUNNING_GAME.md#answered-probes). Some probes were also tried on [edited saves](docs/EDITED_SAVES.md), copies of a game-written save with a few bytes changed.
- **What changed lately:** [what's new](docs/WHATS_NEW.md), newest first. What the pages got wrong, how it was caught and the commit that fixed it: [corrections](docs/CORRECTIONS.md).
- **The three games:** [LoL1](https://github.com/KForestland/lands-of-lore-1-re) · [LoL2](https://github.com/KForestland/lands-of-lore-2-re) · [LoL3](https://github.com/KForestland/Lands-of-lore-3-re) ([what they share](docs/series-formats.md), [how the engine changed](docs/engine-evolution.md), [how they gate progress and scale numbers](docs/series-progress-and-numbers.md)).

![The first level, L1_DC, drawn from its region table by tools/lol2_level_map.py](docs/images/l1_dc_regions.png)

*The first level (`L1_DC`) drawn from its geometry numbers alone (`tools/lol2_level_map.py --level 1 --size 900`): each region a polygon shaded by floor height, wall sides dark, portal sides light.*

## Rating

These are counts of work done, not a percentage of how complete the project is. They are produced by `tools/rating.py` on the English DOS 1.30 copy; [how we rate](docs/HOW_WE_RATE.md) explains each line and what it does not claim.

<!-- rating:begin -->
- **Files read:** 83 of 83 files in `DAT` (1,915.6 of 1,915.6 MiB) have their whole layout read by a tool here: every byte belongs to a known header, directory, entry, chunk, segment or resource, or to zero padding between them; the DOS part of `SETUP.EXE` is counted by its length (what is inside an entry may still be only partly understood).
- **Rules traced:** the pages mark 757 statements CONFIRMED (proved from the program code or the files) and 178 UNCONFIRMED (a reading not yet proved), on 122 current pages; old notes kept as history are not counted.
- **Seen in the running game:** 4 of 9 probes that need the original game running are answered (a question can have more than one probe); 0 of them rest on edited saves only.
- **Open questions:** 20 numbered questions: 5 answered, 14 mostly answered, 1 partly answered.
<!-- rating:end -->

## Quick start

Use Python 3.10 or later and your own copy of the English GOG release, DOS version 1.30. The tools recognize the original program `LOLG.DAT` by its SHA-256 prefix `b27a35341c6e877e`. Keep `DAT/` with the rest of the game folder so the readers can also find `LOLG.DAT` and the sibling MIX and TRR files.

Install Pillow for pictures (10.1 up to 13; the image check accepts each measured rendering), Capstone 5 for disassembly checks and NumPy for VQA frame decoding. The full check uses all three and the system LZO library (`apt install liblzo2-2` on Debian or Ubuntu). The synthetic unit tests use the Python standard library.

```bash
git clone https://github.com/KForestland/lands-of-lore-2-re.git
cd lands-of-lore-2-re
python3 -m venv .venv && . .venv/bin/activate
python3 -m pip install -r requirements.txt
export LOL2_DAT="/path/to/your/LOL2/DAT"
python3 tools/check_all.py --quick              # lists the checks it skips
python3 tools/check_all.py                      # full suite of 47 checks
python3 -m unittest discover -s tests
python3 tools/lol2_mix_parser.py --data "$LOL2_DAT" L1_DC.MIX   # list the entries of level 1's archive
python3 tools/full_report.py --out "../lol2-out/report"
```

On the reference installation, the full suite took about 45 seconds and `--quick` took about 16. Quick mode skips the instance-field scan, MIX writer, AUD decoder and VQA check and prints each skip. Each run prints the time per check and the total. [Check audit](docs/CHECK_AUDIT.md)

The MIX command prints the archive path, then `Entries: 3`, then one line per entry with its name key, offset and size. The report command writes an inventory, level sheets and text counts to the named folder. On Windows, use `py -3 -m venv .venv` and `.\.venv\Scripts\python.exe` in place of `python3`. Set `$env:LOL2_DAT = 'D:\Games\LoL2\DAT'` in PowerShell, or pass `--data` with a quoted folder path to each tool.

## Tools at a glance

[How a level is put together](docs/HOW_A_LEVEL_IS_PUT_TOGETHER.md)

What you can look at with your own copy of the game. Run from the clone with `export LOL2_DAT=/path/to/your/LOL2/DAT` (and `LOL2_SLOT` set to one of your own save files for the last line); pictures and files go only where you point them (here `../lol2-out`, outside the clone; make it first with `mkdir -p ../lol2-out`). Every tool and option is in [`tools/README.md`](tools/README.md), with a table of every format and how to look at it.

| To see | Command |
|---|---|
| A level as a map | `python3 tools/lol2_level_map.py --data "$LOL2_DAT" --level 1 --out ../lol2-out/l1_map.png` |
| A level schematic with items and creatures | `python3 tools/lol2_level_schematic.py --data "$LOL2_DAT" --level 5 --out ../lol2-out/l5.png` |
| Level sheets | `python3 tools/lol2_level_report.py --data "$LOL2_DAT" --out ../lol2-out/levels` |
| A level's events and what they do | `python3 tools/lol2_event_browser.py --data "$LOL2_DAT" L1_DC --stream 1 --group 0x228e` |
| A level's full script listing | `python3 tools/lol2_disassemble_scripts.py --data "$LOL2_DAT" L1_DC` |
| An archive's entries | `python3 tools/lol2_mix_parser.py --data "$LOL2_DAT" L1_DC.MIX` |
| An item definition | `python3 tools/lol2_inspect.py --data "$LOL2_DAT" item 68` |
| An animation (WSA) | `python3 tools/lol2_inspect.py --data "$LOL2_DAT" wsa P_LUTHER.WSA --delta 0` |
| A spoken cue | `python3 tools/lol2_inspect.py --data "$LOL2_DAT" cue 161` |
| A table inside the game program | `python3 tools/lol2_inspect.py --data "$LOL2_DAT" native --table spell-effects --row 20` |
| The rules behind a topic | `python3 tools/lol2_inspect.py --data "$LOL2_DAT" rules motion` |
| Music as standard MIDI | `python3 tools/lol2_hmi_midi.py --data "$LOL2_DAT" --out ../lol2-out/midi` |
| A saved game you made | `python3 tools/lol2_save_inspect.py "$LOL2_SLOT"` |

## What you get

[Walk through one level from its map to its exit](docs/TOUR.md). Search the [JSON documentation index](docs/index.json) by page, question or tool. What each format writer proves, byte-identical or decode-identical, is on one page: [round trip](docs/ROUND_TRIP.md).

- **Format and engine pages** in [`docs/`](docs): archives, level scripts, level geometry, walls and textures, items, sound, music and movies. Short pages, one per format with worked examples: [`docs/formats/`](docs/formats/README.md). One sheet per level, generated from the level archives: [`docs/levels/`](docs/levels/README.md).
- **Tools** in [`tools/`](tools/README.md): archive reader, name hashing, decompressors, entity and level analysers, audio and video decoders, and the wall and level-geometry tools in `tools/history/draracle/`.
- **[Start here, by goal](docs/START_HERE.md)**, a **[glossary](docs/GLOSSARY.md)** and the **[open questions](docs/OPEN_QUESTIONS.md)**.

## Status

"Q8" and the like are numbered questions in [`docs/OPEN_QUESTIONS.md`](docs/OPEN_QUESTIONS.md).

Full table with evidence: [`docs/STATUS.md`](docs/STATUS.md).

| Area | State |
|------|-------|
| Archives (MIX), entry names, compression | [Format page](docs/formats/mix.md); readers check all 81 archives in `DAT/` and the 6 shipped archives in the game folder. `lol2_loose.py` reads the other two `DAT` files, `AUTOPLAY.WAV` and `SETUP.EXE`, to the last byte. The seventh MIX file in the game folder, `CDCACHE.MIX`, is a cache the game writes itself (Q20). |
| Levels, geometry, walls, textures | Documented for the traced parts; geometry entry found in all 15 levels; wall spans and UVs partly open (Q16) |
| Level scripts | Opcode dispatch and event layouts documented. Disassembler checks all 15 levels (Q4–Q7). |
| Entities, items, combat | Item definitions, what items give the player, some item effects and the combat formulas, as the original program does them (Q8, Q10). |
| Sound, music, movies | AUD sounds, the HMI songs (converted to standard MIDI, Q15) and VQA v2 headers decoded. Open: two exceptional movie frames (Q12) and the 33 `FORM` entries in `LOCAL.MIX`, which have no numbered question |
| Spells and saves | Spell costs and some spell effects from the original program; save folders and the save sections mapped so far (Q9, Q11). |
| Text | Message tables (help, options, automap, credits, errors) documented with a reader; character dialogue open (Q13). |

## Repository layout

- [`docs/`](docs): format and engine pages, status, open questions, glossary; older notes kept as history
- [`tools/`](tools/README.md): readers and analysers
- [`evidence/`](evidence): lists of program addresses and files that back up the pages
- [`data/`](data): machine-readable inventory summaries
- [`examples/`](examples/README.md): an example level schematic (`l5_hc_schematic.png`) with the command that draws it; it and the level map above (`docs/images/l1_dc_regions.png`) are checked against today's tools by `example_images.py`

## Asset policy

No game files and no dumps of extracted game media are included; short byte excerpts appear in the documentation as examples. `tools/check_all.py` includes `repo_guard.py`, which fails if a game file, media file or stray image is committed. To run the tools you need your own copy of the game.

## The other Lands of Lore games

Formats the three games share, with links to the LoL1 and LoL3 repositories: [docs/series-formats.md](docs/series-formats.md).

## Sources

Facts are checked against the original files and the original program (`LOLG.DAT`), with addresses or file offsets cited on each page. This is independent documentation.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) to help.
