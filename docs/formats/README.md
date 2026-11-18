# LoL2 file formats, one page each

Each page: what the file is, its layout, a worked example with real bytes from the game files (re-checked on 2026-11-18), the tool that reads it, and what is open. The older long pages in [`../`](..) hold the detailed notes; these pages are the short entry points. Conventions as in the [glossary](../GLOSSARY.md): CONFIRMED = checked on the game files or in the program; UNCONFIRMED = not yet.

| Page | Files | Tool | State |
|------|-------|------|-------|
| [mix.md](mix.md) | `*.MIX` | `lol2_mix_parser.py`, `lol2_westwood_hash.py` | CONFIRMED (87 of 88 archives; signed key order); Q20 |
| [level-data.md](level-data.md) | level data entry in `L<n>_<xx>.MIX` | `lol2_source_format.py`, `lol2_export_scripts.py` | header tables CONFIRMED on 3 levels; rest open (Q4, Q5) |
| [texture-container.md](texture-container.md) | `<LEVEL>.TE_` | `lol2_texture_container.py` | container CONFIRMED; flags open (Q14) |
| [room-sections.md](room-sections.md) | `LOCAL.MIX` entry 1 | `lol2_decompress_sphere.py` | 37/37 CONFIRMED; Q2 |
| [entity-records.md](entity-records.md) | 147-byte records in level archives | `lol2_entity_field_analyzer.py` | records CONFIRMED; containing structure open (Q19) |
| [items.md](items.md) | `GLOBAL.MIX` item table | `lol2_mix_parser.py` | header and counts CONFIRMED; Q8 |
| [sound.md](sound.md) | `LOCALLNG.MIX` sound bank, music, movies | `lol2_sound_bank.py`, `lol2_aud_decode.py`, `lol2_vqa_v2_decode.py` | bank and 517 AUD entries CONFIRMED; Q12, Q15 |
| [compression.md](compression.md) | LZO1X blocks, LCW variant, LZ77 with mode byte | `lol2_texture_container.py`, `lol2_decompress_sphere.py`, `lol2_decompress_westwood.py` | two schemes CONFIRMED; Q1, Q2 |
| [geometry.md](geometry.md) | vertex and region tables of the level data entry | `lol2_level_report.py` | region neighbours, corners, heights, slope flags CONFIRMED (code + 15 levels); other words open (Q16) |
| [maps.md](maps.md) | top-down map drawn from the region table | `lol2_level_map.py` | 52,669 polygons CONFIRMED; in-game automap data not located |
| [vqa.md](vqa.md) | `WVQA` movies | `lol2_vqa_v2_decode.py` | 1,948 headers CONFIRMED; 948 decoded; 14 unsupported layouts |

Script streams and opcodes: [opcode reference](../lol2-script-opcodes.md). Still to write: sprites.
