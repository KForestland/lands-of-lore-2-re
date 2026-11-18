# L8_SJ

Made by `tools/lol2_level_report.py` from `DAT/L8_SJ.MIX` and `DAT/L8_SJI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L8_SJ.MIX` is 13,831,538 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0x45347E1D | 13,767,768 | 63,770 | holds the entity records from entry byte 40,407 |
| 1 | 0x453E7B1B | 13,146,529 | 621,239 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0x454D7F22 | 42 | 13,146,487 | texture container: key = `ww_hash_v1("SPHERE2\L8_SJ\L8_SJ.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 117 |
| props | 1,695 |
| controls | 165 |
| movables | 55 |
| region descriptors | 491 |
| objects with an event list | 339 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 254 | 134 | 2,206 |
| 1 | 2,454 | 743 | 21,836 |

2,708 commands in 877 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 8 ×512, 9 ×369, 16 ×331, 13 ×257, 2 ×161, 5 ×148, 14 ×138, 3 ×135, 198 ×132, 20 ×130, 196 ×86, 204 ×70, 7 ×39, 206 ×39, 18 ×30, 197 ×30, 199 ×27, 12 ×19, 1 ×15, 17 ×10, 23 ×7, 210 ×7, 6 ×6, 207 ×5, 21 ×4, 19 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L4_HJ | 7 | 0 | 1492 | region:2352 |
| L4_HJ | 7 | 0 | 1498 | region:2353 |
| L4_HJ | 7 | 0 | 1504 | region:2360 |
| L9_DR | 1 | 0 | 1670 | region:3132 |
| L9_DR | 2 | 0 | 2076 | region:3569 |
| L9_DR | 2 | 0 | 2082 | region:3570 |
| L9_DR | 2 | 0 | 2088 | region:3573 |
| L10_DC | 1 | 0 | 564 | region:908 |
| L12_CM | 1 | 0 | 1908 | region:3277 |
| L14_HT | 1 | 1 | 11612 | prop:1198 |

## Entity records

18 records of 147 bytes, by name tag: `LAMPLT` ×4, `DANIEL` ×3, `WILD` ×3, `B_HUMAN` ×2, `BACL8` ×1, `DAWNL8` ×1, `LAMP_QN` ×1, `LARKHON` ×1, `SHAMAN` ×1, `WILD2` ×1.

## Companion archive

`L8_SJI.MIX`, 104,371,246 bytes: 161 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
