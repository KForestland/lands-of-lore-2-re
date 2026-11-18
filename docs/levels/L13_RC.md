# L13_RC

Made by `tools/lol2_level_report.py` from `DAT/L13_RC.MIX` and `DAT/L13_RCI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L13_RC.MIX` is 6,992,017 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xFA891800 | 6,731,475 | 246,056 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0x008D17F7 | 6,977,531 | 14,486 | holds the entity records from entry byte 10,186 |
| 2 | 0x02971810 | 42 | 6,731,433 | texture container: key = `ww_hash_v1("SPHERE2\L13_RC\L13_RC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 41 |
| props | 429 |
| controls | 109 |
| movables | 85 |
| region descriptors | 147 |
| objects with an event list | 256 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 222 | 98 | 2,302 |
| 1 | 1,439 | 389 | 11,096 |

1,661 commands in 487 groups use 25 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×331, 7 ×260, 16 ×209, 5 ×179, 6 ×128, 20 ×71, 14 ×63, 196 ×62, 1 ×51, 13 ×51, 8 ×43, 2 ×41, 197 ×33, 198 ×28, 3 ×22, 15 ×20, 207 ×19, 18 ×14, 210 ×13, 19 ×9, 204 ×7, 12 ×2, 21 ×2, 199 ×2, 208 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L12_CM | 2 | 0 | 706 | region:489 |

## Entity records

4 records of 147 bytes, by name tag: `B_HUMAN` ×2, `HL1` ×1, `RULOI` ×1.

## Companion archive

`L13_RCI.MIX`, 33,447,212 bytes: 19 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
