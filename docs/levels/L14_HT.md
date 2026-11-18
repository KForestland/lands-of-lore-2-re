# L14_HT

Made by `tools/lol2_level_report.py` from `DAT/L14_HT.MIX` and `DAT/L14_HTI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L14_HT.MIX` is 11,912,452 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xD299A3D2 | 11,406,344 | 465,607 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xD89DA3C8 | 11,871,951 | 40,501 | holds the entity records from entry byte 34,336 |
| 2 | 0xDAA7A3E1 | 42 | 11,406,302 | texture container: key = `ww_hash_v1("SPHERE2\L14_HT\L14_HT.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 96 |
| props | 412 |
| controls | 168 |
| movables | 104 |
| region descriptors | 254 |
| objects with an event list | 548 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 412 | 203 | 3,864 |
| 1 | 2,810 | 859 | 24,190 |

3,222 commands in 1,062 groups use 28 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×695, 196 ×429, 16 ×419, 5 ×302, 7 ×218, 14 ×195, 13 ×133, 2 ×119, 20 ×113, 207 ×99, 198 ×74, 6 ×65, 1 ×59, 15 ×54, 3 ×51, 204 ×51, 199 ×37, 8 ×28, 208 ×26, 18 ×24, 19 ×10, 24 ×7, 210 ×5, 197 ×3, 12 ×2, 17 ×2, 23 ×1, 209 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L8_SJ | 3 | 0 | 1462 | region:863 |
| L8_SJ | 3 | 0 | 3836 | region:4176 |
| L16_CA | 1 | 1 | 9210 | prop:170 |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `HIVEW` ×2, `HL2` ×1, `LAMPLT` ×1.

## Companion archive

`L14_HTI.MIX`, 4,898,048 bytes: 13 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
