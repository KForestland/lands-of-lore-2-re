# L17_HC

Made by `tools/lol2_level_report.py` from `DAT/L17_HC.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L17_HC.MIX` is 4,867,303 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xD2E927B0 | 4,670,072 | 183,784 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xD8ED27A6 | 4,853,856 | 13,447 | holds the entity records from entry byte 9,140 |
| 2 | 0xDAF727BF | 42 | 4,670,030 | texture container: key = `ww_hash_v1("SPHERE3\L17_HC\L17_HC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 82 |
| props | 313 |
| controls | 50 |
| movables | 51 |
| region descriptors | 150 |
| objects with an event list | 129 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 129 | 79 | 1,650 |
| 1 | 526 | 155 | 4,346 |

655 commands in 234 groups use 20 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 16 ×111, 196 ×106, 9 ×93, 7 ×83, 5 ×79, 20 ×38, 13 ×31, 3 ×30, 14 ×25, 2 ×15, 197 ×13, 6 ×8, 12 ×7, 207 ×4, 208 ×4, 210 ×3, 1 ×2, 18 ×1, 23 ×1, 198 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L16_CA | 2 | 1 | 3896 | movable:50 |
| L16_CA | 3 | 0 | 1644 | region:1318 |
| L19_BC | 1 | 0 | 1632 | region:1312 |
| L19_BC | 1 | 0 | 1638 | region:1313 |

## Entity records

4 records of 147 bytes, by name tag: `B_HUMAN` ×2, `HIVEGRD` ×1, `HIVEW` ×1.

## Companion archive

None.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
