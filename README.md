# Lands of Lore II: file formats and game rules

*Lands of Lore: Guardians of Destiny* is a first-person role-playing game by Westwood Studios (1997). This repository documents how its original data files and rules work, and gives you Python tools that read them from your own copy of the game.

It contains documentation, tools and small tables of numbers. It contains no game files and no extracted game pictures, sounds, movies or text dumps.

## At a glance

- **What this is:** documentation of the original 1997 DOS game's data files and engine (archives, levels, scripts, items, spells, creatures, sound, movies, saves), checked against the game files and the original program.
- **What you can do today:** list and unpack every archive, decode sounds, music and movies, read every level's geometry and scripts, follow one event from a click to its result, and look up what each item and spell does in the program.
- **Start in five minutes:** the [Quick start](#quick-start) below, then [Start here, by goal](docs/START_HERE.md), [How the game works](docs/HOW_THE_GAME_WORKS.md) or the [worked example](docs/tutorial-one-event.md).
- **Recipes:** [cookbook](docs/COOKBOOK.md), seven short runs with the command and the first lines it prints.
- **What is still unknown:** the [open questions](docs/OPEN_QUESTIONS.md), counted in the [rating](#rating); most open points are the meaning of specific fields and effects. Some can only be settled by watching the original game run. Answered probes are counted in the rating; which ones and how: [NEEDS_A_RUNNING_GAME](docs/NEEDS_A_RUNNING_GAME.md#answered-probes). Some probes were also tried on [edited saves](docs/EDITED_SAVES.md), copies of a game-written save with a few bytes changed.
- **What changed lately:** [what's new](docs/WHATS_NEW.md), newest first.
- **The three games:** [LoL1](https://github.com/KForestland/lands-of-lore-1-re) · [LoL2](https://github.com/KForestland/lands-of-lore-2-re) · [LoL3](https://github.com/KForestland/Lands-of-lore-3-re) ([what they share](docs/series-formats.md), [how the engine changed](docs/engine-evolution.md)).

![The first level, L1_DC, drawn from its region table by tools/lol2_level_map.py](docs/images/l1_dc_regions.png)

*The first level (`L1_DC`) drawn from its geometry numbers alone (`tools/lol2_level_map.py --level 1 --size 900`): each region a polygon shaded by floor height, wall sides dark, portal sides light.*

## Rating

These are counts of work done, not a percentage of how complete the project is. They are produced by `tools/rating.py` on the English DOS 1.30 copy; [how we rate](docs/HOW_WE_RATE.md) explains each line and what it does not claim.

<!-- rating:begin -->
- **Files read:** 83 of 83 files in `DAT` (1,915.6 of 1,915.6 MiB) have their whole layout read by a tool here: every byte belongs to a known header, directory, entry, chunk, segment or resource, or to zero padding between them; the DOS part of `SETUP.EXE` is counted by its length (what is inside an entry may still be only partly understood).
- **Rules traced:** the pages mark 706 statements CONFIRMED (proved from the program code or the files) and 166 UNCONFIRMED (a reading not yet proved), on 112 current pages; old notes kept as history are not counted.
- **Seen in the running game:** 4 of 9 probes that need the original game running are answered (a question can have more than one probe); 0 of them rest on edited saves only.
- **Open questions:** 20 numbered questions: 5 answered, 14 mostly answered, 1 partly answered.
<!-- rating:end -->

## Tools at a glance

What you can look at with your own copy of the game. Run from the clone with `export LOL2_DAT=/path/to/your/LOL2/DAT` (and `LOL2_SLOT` set to one of your own save files for the last line); pictures and files go only where you point them (here `../lol2-out`, outside the clone). Every tool and option is in [`tools/README.md`](tools/README.md), with a table of every format and how to look at it.

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

- **Format and engine pages** in [`docs/`](docs): archives, level scripts, level geometry, walls and textures, items, sound, music and movies. Short pages, one per format with worked examples: [`docs/formats/`](docs/formats/README.md). One sheet per level, generated from the level archives: [`docs/levels/`](docs/levels/README.md).
- **Tools** in [`tools/`](tools/README.md): archive reader, name hashing, decompressors, entity and level analysers, audio and video decoders, and the wall and level-geometry tools in `tools/draracle/`.
- **[Start here, by goal](docs/START_HERE.md)**, a **[glossary](docs/GLOSSARY.md)** and the **[open questions](docs/OPEN_QUESTIONS.md)**.

## Quick start

You need Python 3.10+ and your own copy of the game: the English GOG release, DOS version 1.30 (program `LOLG.DAT`, SHA-256 starting `b27a35341c6e877e`; some tools refuse other editions). Most files are in its `DAT/` folder; seven MIX files sit in the game folder next to it (`LOCAL`, `LOCALLNG`, `DMUSIC`, `SETUP`, `GLOBAL`, `CACHEBAK` and the game-written `CDCACHE`), and the tools find them there from `$LOL2_DAT`. Install the system LZO library (`apt install liblzo2-2` on Debian/Ubuntu) to run the full checks and read packed textures and saves.

```bash
git clone https://github.com/KForestland/lands-of-lore-2-re.git
cd lands-of-lore-2-re
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export LOL2_DAT=/path/to/your/LOL2/DAT          # the game's DAT folder
python3 tools/check_all.py                      # 32 checks, ends with ALL 32 CHECKS PASSED
python3 tools/lol2_mix_parser.py L1_DC.MIX      # list the entries of level 1's archive
```

The last command prints `Entries: 3` and one line per entry with its name key, offset and size.

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

- [`docs/`](docs): format and engine pages, status, open questions, glossary; older closure notes kept as history
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
