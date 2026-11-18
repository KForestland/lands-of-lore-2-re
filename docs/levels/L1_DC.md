# L1_DC

Made by `tools/lol2_level_report.py` from `DAT/L1_DC.MIX` and `DAT/L1_DCI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L1_DC.MIX` is 7,424,548 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xB1162802 | 7,389,520 | 35,028 | holds the entity records from entry byte 27,723 |
| 1 | 0xB1202500 | 7,091,978 | 297,542 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xB12F2907 | 42 | 7,091,936 | texture container: key = `ww_hash_v1("SPHERE1\L1_DC\L1_DC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 57 |
| props | 1,559 |
| controls | 174 |
| movables | 80 |
| region descriptors | 173 |
| objects with an event list | 426 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 282 | 98 | 2,380 |
| 1 | 1,700 | 568 | 14,662 |

1,982 commands in 666 groups use 28 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×323, 20 ×230, 16 ×221, 5 ×218, 2 ×141, 7 ×117, 3 ×115, 198 ×108, 13 ×93, 1 ×65, 8 ×63, 6 ×57, 19 ×46, 14 ×37, 207 ×31, 18 ×24, 21 ×24, 197 ×17, 196 ×16, 204 ×8, 208 ×6, 15 ×5, 23 ×5, 12 ×3, 17 ×3, 210 ×3, 206 ×2, 24 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L3_DH | 1 | 0 | 1194 | region:1190 |
| L3_DH | 1 | 0 | 1246 | region:1217 |
| L3_DH | 1 | 0 | 1298 | region:1218 |
| L3_DH | 1 | 0 | 1350 | region:1219 |
| L3_DH | 1 | 0 | 1402 | region:1220 |
| L3_DH | 1 | 0 | 1454 | region:1221 |
| L3_DH | 1 | 0 | 1506 | region:1222 |
| L3_DH | 1 | 0 | 1558 | region:1223 |
| L3_DH | 1 | 0 | 1610 | region:1224 |
| L3_DH | 1 | 1 | 4030 | prop:447 |

## Entity records

11 records of 147 bytes, by name tag: `B_HUMAN` ×3, `GGUARD` ×2, `WORM` ×2, `GGCAPT` ×1, `Kenneth` ×1, `ROACH` ×1, `Roach` ×1.

## Companion archive

`L1_DCI.MIX`, 103,374,072 bytes: 36 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
