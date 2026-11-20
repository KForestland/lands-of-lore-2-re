# Start here, by goal

[Format quick reference](QUICK_REFERENCE.md) pairs each documented game format with a command and its evidence; the [format pages](formats/README.md) give one short page per format, each with a worked example.

You need Python 3.10 or later, the packages in `requirements.txt`, `liblzo2` and your
own copy of *Lands of Lore: Guardians of Destiny*. Point the tools at its
`DAT` folder once.

```bash
export LOL2_DAT=/path/to/your/LOL2/DAT
python3 tools/check_all.py         # the last line should read ALL 49 CHECKS PASSED
```

Words you do not know are in the [glossary](GLOSSARY.md). Short worked commands, with the first lines they print, are in the [cookbook](COOKBOOK.md). What is known and checked is in [STATUS.md](STATUS.md). Examples that write files (pictures, JSON) should write outside the clone, so nothing from your game ends up in the repository. To contribute, see [CONTRIBUTING](../CONTRIBUTING.md).

Follow the engine from startup to saving in [How Lands of Lore II works](HOW_THE_GAME_WORKS.md).

## I want to look inside the archives

- List a MIX file: `python3 tools/lol2_mix_parser.py L1_DC.MIX`; extract an entry with `--out`.
- Hash an entry name: `python3 tools/lol2_westwood_hash.py 'SPHERE1\L1_DC\L1_DC.TE_'`.
- Formats: [lol2-level-texture-container.md](lol2-level-texture-container.md), [lol2-level-script-format.md](lol2-level-script-format.md), [lol2-item-format.md](lol2-item-format.md).

## I want to understand the levels

- [lol2-level-graph.md](lol2-level-graph.md): the 15 levels, the room archives and the exits.
- [Progression](PROGRESSION.md): each exit command and the shared or local slot it tests.
- Options interface shapes in `LOCAL.MIX`: `python3 tools/lol2_decompress_sphere.py --check`.
- Objects in each level: `python3 tools/lol2_entity_field_analyzer.py --out ../lol2-out/entities.json` (outside the downloaded folder).

## I want to understand the scripts

- Run `python3 tools/lol2_disassemble_scripts.py --data "$LOL2_DAT" L1_DC` to list commands and their MIX offsets.
- Read the [stream format](lol2-level-script-format.md), [opcode table](lol2-script-opcodes.md) and [event and timer reference](lol2-script-events.md).

## I want to understand items, combat or saves

- [Item format](lol2-item-format.md) and [item grants and effects](lol2-item-effects.md) cover definitions, script grants and selected item-use handlers.
- [Spells](lol2-spells.md) covers costs, acquisition and magic rewards. [Combat and creature decisions](lol2-combat-ai.md) covers hit calculation and the actor update.
- [Native save slots](lol2-save-format.md) covers directories, compression and runtime sections. [Edited saves](EDITED_SAVES.md) lists the runs where the original game loaded a hand-edited copy, each with a link to its byte table. [Executable addresses](lol2-executable-tables.md) maps code and data references to file offsets.

## I want sound, music or movies

- [audio-inventory.md](audio-inventory.md), [lol2-music-2026-11.md](lol2-music-2026-11.md), [lol2-vqa-v2.md](lol2-vqa-v2.md); tools `lol2_sound_bank.py` (lists `LOCALLNG.MIX`, found next to `DAT/`), `lol2_aud_decode.py DMUSIC.MIX 0 --info`, `lol2_vqa_v2_decode.py L4_HJI.MIX --entry 67`. Names are looked up in `$LOL2_DAT` and the game folder above it.

## I want walls and textures

- [lol2-level-texture-container.md](lol2-level-texture-container.md), [lol2-wall-material-provenance.md](lol2-wall-material-provenance.md), [draracle-restoration.md](draracle-restoration.md) and the pipeline in `tools/history/draracle/`.

## I want to help

Pick a question in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).
