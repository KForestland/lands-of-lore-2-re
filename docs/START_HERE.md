# Start here, by goal

You need Python 3.8+, Pillow (`pip install -r requirements.txt`) and your own copy of *Lands of Lore: Guardians of Destiny*. Point the tools at its `DAT` folder once:

```bash
export LOL2_DAT=/path/to/your/LOL2/DAT
python3 tools/check_all.py         # the last line should read ALL 17 CHECKS PASSED
```

Words you do not know are in the [glossary](GLOSSARY.md); what is known and checked is in [STATUS.md](STATUS.md).

## I want to look inside the archives

- List a MIX file: `python3 tools/lol2_mix_parser.py L1_DC.MIX`; extract an entry with `--out`.
- Hash an entry name: `python3 tools/lol2_westwood_hash.py 'SPHERE1\L1_DC\L1_DC.TE_'`.
- Formats: [lol2-level-texture-container.md](lol2-level-texture-container.md), [lol2-level-script-format.md](lol2-level-script-format.md), [lol2-item-format.md](lol2-item-format.md).

## I want to understand the levels

- [lol2-level-graph.md](lol2-level-graph.md): the 15 levels, the room archives and the exits.
- Room layouts in `LOCAL.MIX`: `python3 tools/lol2_decompress_sphere.py 11 --png room11.png`.
- Objects in each level: `python3 tools/lol2_entity_field_analyzer.py --out entities.json`.

## I want to understand the scripts

- Run `python3 tools/lol2_disassemble_scripts.py --data <DAT> L1_DC` to list commands and their MIX offsets.
- Read the [stream format](lol2-level-script-format.md), [opcode table](lol2-script-opcodes.md) and [event and timer reference](lol2-script-events.md).

## I want to understand items, combat or saves

- [Item format](lol2-item-format.md) and [item grants and effects](lol2-item-effects.md) cover definitions, script grants and selected item-use handlers.
- [Spells](lol2-spells.md) covers costs, acquisition and magic rewards. [Combat and creature decisions](lol2-combat-ai.md) covers hit calculation and the actor update.
- [Native save slots](lol2-save-format.md) covers directories, compression and runtime sections. [Executable addresses](lol2-executable-tables.md) maps code and data references to file offsets.

## I want sound, music or movies

- [audio-inventory.md](audio-inventory.md), [lol2-music-2026-11.md](lol2-music-2026-11.md), [lol2-vqa-v2.md](lol2-vqa-v2.md); tools `lol2_sound_bank.py`, `lol2_aud_decode.py`, `lol2_vqa_v2_decode.py`.

## I want walls and textures

- [lol2-level-texture-container.md](lol2-level-texture-container.md), [lol2-wall-material-provenance.md](lol2-wall-material-provenance.md), [draracle-restoration.md](draracle-restoration.md) and the pipeline in `tools/draracle/`.

## I want to help

Pick a question in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).
