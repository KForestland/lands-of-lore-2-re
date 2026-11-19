# Format quick reference

Run the commands from the repository root with `LOL2_DAT` set to your
original installation's `DAT` folder. `LOL2_SLOT` is an optional path to
a save produced while playing. The evidence links give original offsets,
measured layouts and open fields.

| File or entry | What it contains | Format and evidence | Tool | Command |
|---|---|---|---|---|
| `.MIX`, including `CACHEBAK.MIX` | Keyed archive and shipped cache seed | [MIX](formats/mix.md) | MIX directory reader | `python3 tools/lol2_mix_parser.py L1_DC.MIX` |
| `AUTOPLAY.WAV`, `SETUP.EXE` | The two `DAT` files that are not MIX archives: a PCM wave, and an NE setup program | [Loose files](formats/loose.md) | Loose-file checker | `python3 tools/lol2_inspect.py loose` |
| `.WOM` in room MIX files | Room module with an executable code entry | [Room archives](lol2-room-archives.md) | Room module inspector | `python3 tools/lol2_inspect.py wom TCEL` |
| Level data entry | Geometry, placements and script-table offsets | [Level data](formats/level-data.md), [geometry](formats/geometry.md), [walls](formats/walls.md) | Level report | `python3 tools/lol2_level_report.py --check` |
| Level map drawing | Top-down region polygons, walls and portals from the level data entry | [Level maps](formats/maps.md) | Level schematic | `python3 tools/lol2_level_schematic.py --level 1 --out /tmp/l1.png` |
| Object definitions in a level entry | 147-byte definition rows | [Entity records](formats/entity-records.md) | Entity checker | `python3 tools/lol2_entity_field_analyzer.py --check` |
| Event and command tables in a level entry | Triggers, predicate references and commands | [Script layout](lol2-level-script-format.md), [opcodes](lol2-script-opcodes.md) | Event browser | `python3 tools/lol2_event_browser.py L1_DC --stream 1 --group 0x228e` |
| Item table in `GLOBAL.MIX` | Item definition records and their use-handler indexes | [Items](formats/items.md), [item format](lol2-item-format.md) | Item inspector | `python3 tools/lol2_inspect.py item 68` |
| `.TE_`, `.TEX` | Compressed level texture container and expanded bank | [Texture bank](formats/texture-container.md), [compression](formats/compression.md) | Texture container checker | `python3 tools/lol2_texture_container.py --check` |
| `CDCACHE.LS_`, `CDCACHE.LST`, `CDCACHE.MIX` | Shipped seed list (`CDCACHE.LS_`); list and allocator archive (`CDCACHE.LST`, `CDCACHE.MIX`) written by the game at run time, not shipped | [Cache initializer](lol2-cache-initializer.md), [MIX](formats/mix.md) | Cache seed checker | `python3 tools/lol2_cache_seed.py --data "$LOL2_DAT" --check` |
| Options interface shapes in `LOCAL.MIX` | Stored and compressed shapes in `options.shp` | [Shape format](formats/room-sections.md) | Section checker | `python3 tools/lol2_decompress_sphere.py --check` |
| Native LZ77 blocks | A compression path called by the VQA node reader | [Compression](formats/compression.md) | Decoder self-test and witness scan | `python3 tools/lol2_decompress_westwood.py --check` |
| `.AUD` | Digital sound or music in Westwood audio chunks | [Sound](formats/sound.md) | AUD checker | `python3 tools/lol2_aud_decode.py --check` |
| Sound banks in `LOCALLNG.MIX` | Indexed cue entries and their audio | [Sound cues](lol2-sound-cues.md) | Sound bank reader | `python3 tools/lol2_sound_bank.py LOCALLNG.MIX` |
| `.HMI` | Sequenced music in the LOCAL archive | [HMI and music](lol2-music-2026-11.md) | HMI track inspector | `python3 tools/lol2_inspect.py hmi CREDITS` |
| `.VQA` or a MIX member with the `WVQA` tag | Movies with codebooks and pointer streams | [VQA](formats/vqa.md) | VQA checker | `python3 tools/lol2_vqa_v2_decode.py --check` |
| `.TRR` | Indexed localized text tables, both loose and in archives | [Text tables](lol2-text-tables.md) | TRR inspector | `python3 tools/lol2_inspect.py trr help` |
| DOS save slots, `.LSV`, `.IMG` | Save directories, per-level state and its baseline bytes | [Native slots](lol2-save-format.md), [levels and sections](lol2-save-sections.md) | Save inspector | `python3 tools/lol2_save_inspect.py "$LOL2_SLOT"` |
| `LOLG.EXE`, `LOLG.DAT` | DOS 1.30 executable with an embedded LE image | [Address conventions and tables](lol2-executable-tables.md) | LE inspector | `python3 tools/lol2_inspect.py native` |
