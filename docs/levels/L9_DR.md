# L9_DR

Made by `tools/lol2_level_report.py` from `DAT/L9_DR.MIX` and `DAT/L9_DRI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L9_DR.MIX` is 23,611,578 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xD144683E | 23,543,177 | 68,401 | holds the entity records from entry byte 59,142 |
| 1 | 0xD14E653C | 22,719,810 | 823,367 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xD15D6943 | 42 | 22,719,768 | texture container: key = `ww_hash_v1("SPHERE2\L9_DR\L9_DR.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 80 |
| props | 2,712 |
| controls | 508 |
| movables | 135 |
| region descriptors | 600 |
| objects with an event list | 645 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 700 | 290 | 7,218 |
| 1 | 2,238 | 630 | 20,908 |

2,938 commands in 920 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 196 ×565, 204 ×397, 9 ×320, 5 ×267, 20 ×254, 6 ×173, 16 ×130, 2 ×113, 197 ×106, 3 ×99, 7 ×72, 21 ×67, 198 ×63, 14 ×59, 1 ×57, 18 ×55, 13 ×48, 8 ×38, 208 ×25, 12 ×9, 15 ×5, 199 ×5, 210 ×5, 207 ×3, 23 ×2, 209 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L8_SJ | 5 | 1 | 2168 | prop:104 |
| L8_SJ | 6 | 0 | 572 | region:2301 |
| L8_SJ | 7 | 0 | 5582 | region:5340 |
| L10_DC | 2 | 0 | 548 | region:2299 |

## Entity records

8 records of 147 bytes, by name tag: `B_HUMAN` ×2, `SSAR` ×2, `BELSTAT` ×1, `SSAR_P` ×1, `StSquid` ×1, `WORM` ×1.

## Companion archive

`L9_DRI.MIX`, 71,243,700 bytes: 25 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
