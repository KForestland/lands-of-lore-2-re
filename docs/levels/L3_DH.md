# L3_DH

Made by `tools/lol2_level_report.py` from `DAT/L3_DH.MIX` and `DAT/L3_DHI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L3_DH.MIX` is 5,951,189 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xB9203816 | 5,919,193 | 31,996 | holds the entity records from entry byte 26,559 |
| 1 | 0xB92A3514 | 5,717,016 | 202,177 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xB939391B | 42 | 5,716,974 | texture container: key = `ww_hash_v1("SPHERE1\L3_DH\L3_DH.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 33 |
| props | 393 |
| controls | 191 |
| movables | 85 |
| region descriptors | 115 |
| objects with an event list | 316 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 217 | 91 | 1,878 |
| 1 | 1,576 | 446 | 13,126 |

1,793 commands in 537 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 6 ×282, 9 ×282, 5 ×182, 20 ×177, 16 ×157, 14 ×90, 2 ×87, 1 ×77, 198 ×64, 3 ×58, 19 ×57, 24 ×50, 7 ×40, 8 ×40, 13 ×35, 196 ×28, 197 ×24, 210 ×20, 18 ×13, 207 ×10, 204 ×9, 12 ×5, 21 ×2, 206 ×2, 199 ×1, 208 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L4_HJ | 1 | 1 | 7306 | control:82 |

## Entity records

5 records of 147 bytes, by name tag: `B_HUMAN` ×2, `skel` ×2, `Rat` ×1.

## Companion archive

`L3_DHI.MIX`, 34,615,570 bytes: 14 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
