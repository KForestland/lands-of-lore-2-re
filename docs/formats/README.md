# LoL2 file formats, one page each

Each page: what the file is, its layout, a worked example with real bytes from the game files, the tool that reads it, and what is open. The older long pages in [`../`](..) hold the detailed notes; these pages are the short entry points. Conventions as in the [glossary](../GLOSSARY.md): CONFIRMED = checked on the game files or in the program; UNCONFIRMED = not yet.

| Page | Files | Tool | State |
|------|-------|------|-------|
| [mix.md](mix.md) | `*.MIX` | `lol2_mix_parser.py`, `lol2_westwood_hash.py`, `lol2_mix_writer.py` | CONFIRMED on all 87 shipped archives (signed key order; each rebuilds byte for byte); `CDCACHE.MIX` is run-time state; the shipped files are `CACHEBAK.MIX` and `CDCACHE.LS_` (Q20) |
| [level-data.md](level-data.md) | level data entry in `L<n>_<xx>.MIX` | `lol2_source_format.py`, `lol2_export_scripts.py` | header tables CONFIRMED on 3 levels; rest open (Q4, Q5) |
| [texture-container.md](texture-container.md) | `<LEVEL>.TE_` | `lol2_texture_container.py` | raw flags and movie-name records CONFIRMED; non-raw payloads open, layout unknown (Q14) |
| [room-sections.md](room-sections.md) | `LOCAL.MIX` entry 1 | `lol2_decompress_sphere.py` | 39 `options.shp` shapes, including two stored, CONFIRMED (Q2) |
| [entity-records.md](entity-records.md) | 147-byte records in level archives | `lol2_entity_field_analyzer.py` | records and their containing structure CONFIRMED (Q19 answered) |
| [items.md](items.md) | `GLOBAL.MIX` item table | `lol2_mix_parser.py` | header and counts CONFIRMED; Q8 |
| [sound.md](sound.md) | `LOCALLNG.MIX` sound bank, music, movies | `lol2_sound_bank.py`, `lol2_aud_decode.py`, `lol2_vqa_v2_decode.py` | bank, 453 AUD entries in `DAT/` and 64 in the game-folder archives CONFIRMED; Q12, Q15; movies on [vqa.md](vqa.md) |
| [xmi.md](xmi.md) | 33 XMIDI scores in `LOCAL.MIX` | `lol2_xmi_reader.py` | original IFF extents, TIMB pairs and EVNT event streams checked |
| [compression.md](compression.md) | LZO1X blocks, Westwood LZ77 | `lol2_texture_container.py`, `lol2_decompress_westwood.py`, `lol2_decompress_sphere.py` (the `options.shp` shapes) | LZO CONFIRMED on the data; LZ77 code and its eleven callers' buffers CONFIRMED, source files partly open (Q1) |
| [geometry.md](geometry.md) | vertex and region tables of the level data entry | `lol2_level_report.py` | region neighbours, corners, heights, slope flags CONFIRMED (code + 15 levels); other words open (Q16) |
| [maps.md](maps.md) | top-down map drawn from the region table | `lol2_level_map.py` | 52,669 polygons CONFIRMED; native marker input traced at `0x64DB7 → 0x145F2C`; visited-area shading open |
| [walls.md](walls.md) | wall table of the level data entry | `lol2_level_report.py` | table, runs, code bits CONFIRMED; 88,994 rows partition exactly; Q16 |
| [vqa.md](vqa.md) | `WVQA` movies | `lol2_vqa_v2_decode.py` | 1,109 pointer tables CONFIRMED; 837 pointer streams open |
| [loose.md](loose.md) | `AUTOPLAY.WAV`, `SETUP.EXE` | `lol2_loose.py` | both files walked to the last byte; what opens them is open |

Script streams and opcodes: [opcode reference](../lol2-script-opcodes.md). Movies by scene id, sound cues, music selection and the 46 room archives: [movie scenes](../lol2-movie-scenes.md), [sound cues](../lol2-sound-cues.md), [music selection](../lol2-music-selection.md), [room archives](../lol2-room-archives.md). Still to write: sprites.
