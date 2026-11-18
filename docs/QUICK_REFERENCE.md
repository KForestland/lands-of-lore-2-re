# Format quick reference

Run the commands from the repository root with `LOL2_DAT` set to your
original installation's `DAT` folder. `LOL2_SLOT` is an optional path to
a save produced while playing. The evidence links give original offsets,
measured layouts and open fields.

| File or entry | What it contains | Format and evidence | Tool | Command |
|---|---|---|---|---|
| `.MIX`, including `CACHEBAK.MIX` | Keyed archive and shipped cache seed | [MIX](formats/mix.md) | MIX directory reader | `python3 tools/lol2_mix_parser.py L1_DC.MIX` |
| `.WOM` in room MIX files | Room module with an executable code entry | [Room archives](lol2-room-archives.md) | Media checker | `python3 tools/lol2_media_check.py --check` |
| Level data entry | Geometry, placements and script-table offsets | [Level data](formats/level-data.md), [geometry](formats/geometry.md), [walls](formats/walls.md) | Level report | `python3 tools/lol2_level_report.py --check` |
| Level map drawing | Top-down region polygons, walls and portals from the level data entry | [Level maps](formats/maps.md) | Level map checker | `python3 tools/lol2_level_map.py --check` |
| Object definitions in a level entry | 147-byte definition rows | [Entity records](formats/entity-records.md) | Entity checker | `python3 tools/lol2_entity_field_analyzer.py --check` |
| Event and command tables in a level entry | Triggers, predicate references and commands | [Script layout](lol2-level-script-format.md), [opcodes](lol2-script-opcodes.md) | Script disassembler | `python3 tools/lol2_disassemble_scripts.py L1_DC` |
| Item table in `GLOBAL.MIX` | Item definition records and their use-handler indexes | [Items](formats/items.md), [item format](lol2-item-format.md) | MIX index lists the keyed entry | `python3 tools/lol2_mix_parser.py GLOBAL.MIX` |
| `.TE_`, `.TEX` | Compressed level texture container and expanded bank | [Texture bank](formats/texture-container.md), [compression](formats/compression.md) | Texture container checker | `python3 tools/lol2_texture_container.py --check` |
| `CDCACHE.LS_`, `CDCACHE.LST`, `CDCACHE.MIX` | Shipped seed list (`CDCACHE.LS_`); list and allocator archive (`CDCACHE.LST`, `CDCACHE.MIX`) written by the game at run time, not shipped | [Cache initializer](lol2-cache-initializer.md), [MIX](formats/mix.md) | Python reads the shipped list's initial index offset | `python3 -c 'import sys; print(int.from_bytes(open(sys.argv[1], "rb").read(4), "little"))' "$LOL2_DAT/../CDCACHE.LS_"` |
| Room sections in `LOCAL.MIX` | Stored and compressed sections in entry 1 | [Room sections](formats/room-sections.md) | Section checker | `python3 tools/lol2_decompress_sphere.py --check` |
| Native LZ77 blocks | A compression path called by the VQA node reader | [Compression](formats/compression.md) | Decoder self-test and witness scan | `python3 tools/lol2_decompress_westwood.py --check` |
| `.AUD` | Digital sound or music in Westwood audio chunks | [Sound](formats/sound.md) | AUD checker | `python3 tools/lol2_aud_decode.py --check` |
| Sound banks in `LOCALLNG.MIX` | Indexed cue entries and their audio | [Sound cues](lol2-sound-cues.md) | Sound bank reader | `python3 tools/lol2_sound_bank.py LOCALLNG.MIX` |
| `.HMI` | Sequenced music in the LOCAL archive | [HMI and music](lol2-music-2026-11.md) | HMI reader | `python3 tools/lol2_hmi_midi.py --check` |
| `.VQA` or a MIX member with the `WVQA` tag | Movies with codebooks and pointer streams | [VQA](formats/vqa.md) | VQA checker | `python3 tools/lol2_vqa_v2_decode.py --check` |
| `.TRR` | Indexed localized text tables, both loose and in archives | [Text tables](lol2-text-tables.md) | TRR checker | `python3 tools/lol2_text_tables.py --check` |
| DOS save slots, `.LSV`, `.IMG` | Save directories, per-level state and its baseline bytes | [Native slots](lol2-save-format.md), [levels and sections](lol2-save-sections.md) | Save header reader | `python3 tools/lol2_save_header.py "$LOL2_SLOT"` |
| `LOLG.EXE`, `LOLG.DAT` | DOS 1.30 executable with an embedded LE image | [Address conventions and tables](lol2-executable-tables.md) | Python reads the LE signature | `python3 -c 'import sys; f=open(sys.argv[1], "rb"); f.seek(0x3bcb4); print(f.read(4))' "$LOL2_DAT/../LOLG.DAT"` |
