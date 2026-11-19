# Lands of Lore II: file formats and game rules

*Lands of Lore: Guardians of Destiny* is a first-person role-playing game by Westwood Studios (1997). This repository documents how its original data files and rules work, and gives you Python tools that read them from your own copy of the game.

It contains documentation, tools and small tables of numbers. It contains no game files and no extracted game pictures, sounds, movies or text dumps.

## At a glance

- **What this is:** documentation of the original 1997 DOS game's data files and engine (archives, levels, scripts, items, spells, creatures, sound, movies, saves), checked against the game files and the original program.
- **What you can do today:** list and unpack every archive, decode sounds, music and movies, read every level's geometry and scripts, follow one event from a click to its result, and look up what each item handler and spell does.
- **Start in five minutes:** the [Quick start](#quick-start) below, then [Start here, by goal](docs/START_HERE.md), [How the game works](docs/HOW_THE_GAME_WORKS.md) or the [worked example](docs/tutorial-one-event.md).
- **What is still unknown:** the [open questions](docs/OPEN_QUESTIONS.md): 2 of 20 answered, 11 mostly, 7 partly; most open points are the meaning of specific fields and effects. Some were tried in the [running game](docs/NEEDS_A_RUNNING_GAME.md) (the clock writer and a pickup's save changes are answered); the rest need later-game saves.
- **The three games:** [LoL1](https://github.com/KForestland/lands-of-lore-1-re) · [LoL2](https://github.com/KForestland/lands-of-lore-2-re) · [LoL3](https://github.com/KForestland/Lands-of-lore-3-re) ([what they share](docs/series-formats.md), [how the engine changed](docs/engine-evolution.md)).

## What you get

- **Format and engine pages** in [`docs/`](docs): archives, level scripts, level geometry, walls and textures, items, sound, music and movies. Short pages, one per format with worked examples: [`docs/formats/`](docs/formats/README.md). One sheet per level, generated from the level archives: [`docs/levels/`](docs/levels/README.md).
- **Tools** in [`tools/`](tools/README.md): archive reader, name hashing, decompressors, entity and level analysers, audio and video decoders, and the wall/geometry pipeline in `tools/draracle/`.
- **[Start here, by goal](docs/START_HERE.md)**, a **[glossary](docs/GLOSSARY.md)** and the **[open questions](docs/OPEN_QUESTIONS.md)**.

## Quick start

You need Python 3.10+ and your own copy of the game: the English GOG release, DOS version 1.30 (program `LOLG.DAT`, SHA-256 starting `b27a35341c6e877e`; some tools refuse other editions). Most files are in its `DAT/` folder; seven MIX files sit in the game folder next to it (`LOCAL`, `LOCALLNG`, `DMUSIC`, `SETUP`, `GLOBAL`, `CACHEBAK` and the game-written `CDCACHE`), and the tools find them there from `$LOL2_DAT`. Optional: the system LZO library (`apt install liblzo2-2`) for the texture tool.

```bash
git clone https://github.com/KForestland/lands-of-lore-2-re.git
cd lands-of-lore-2-re
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export LOL2_DAT=/path/to/your/LOL2/DAT          # the game's DAT folder
python3 tools/check_all.py                      # 20 checks, ends with ALL 20 CHECKS PASSED
python3 tools/lol2_mix_parser.py L1_DC.MIX      # list the entries of level 1's archive
```

## Status

Full table with evidence: [`docs/STATUS.md`](docs/STATUS.md).

| Area | State |
|------|-------|
| Archives (MIX), entry names, compression | [Format page](docs/formats/mix.md); readers check all 81 archives in `DAT/` (`check_all`) and the 6 shipped ones in the game folder (`lol2_mix_parser.py --check --data <game folder>` gives 6/7: the seventh, `CDCACHE.MIX`, is written by the game); the game-written cache `CDCACHE.MIX` is not one (Q20) |
| Levels, geometry, walls, textures | Documented for the traced parts; geometry entry found in all 15 levels; wall spans and UVs partly open (Q16) |
| Level scripts | Opcode dispatch and event layouts documented. Disassembler checks all 15 levels (Q4–Q7). |
| Entities, items, combat | Item definitions, native grants, selected effects and combat formulas documented (Q8, Q10). |
| Sound, music, movies | AUD sounds, the HMI songs (converted to standard MIDI, Q15) and VQA v2 headers decoded; some movie codebook layouts and the `FORM` music entries open (Q12) |
| Spells and saves | Native spell costs, selected effects, save directories and mapped sections documented (Q9, Q11). |
| Text | Message tables (help, options, automap, credits, errors) documented with a reader; character dialogue open (Q13). |

## Repository layout

- [`docs/`](docs): format and engine pages, status, open questions, glossary; older closure notes kept as history
- [`tools/`](tools/README.md): readers and analysers
- [`evidence/`](evidence): trace references and evidence indexes from earlier work
- [`data/`](data): machine-readable inventory summaries
- [`examples/`](examples/README.md): small images made by the tools

## Asset policy

No game files and no dumps of extracted game media are included; short byte excerpts appear in the documentation as examples. `tools/check_all.py` includes `repo_guard.py`, which fails if a game file, media file or stray image is committed. To run the tools you need your own copy of the game.

## Sources

Facts are checked against the original files and the original program (`LOLG.DAT`), with addresses or file offsets cited on each page. This is independent documentation.
