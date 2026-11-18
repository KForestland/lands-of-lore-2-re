# L20_BB

Made by `tools/lol2_level_report.py` from `DAT/L20_BB.MIX` and `DAT/L20_BBI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L20_BB.MIX` is 15,779,290 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xBA791382 | 15,362,198 | 356,155 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xC07D1378 | 15,718,353 | 60,937 | holds the entity records from entry byte 13,847 |
| 2 | 0xC2871391 | 42 | 15,362,156 | texture container: key = `ww_hash_v1("SPHERE3\L20_BB\L20_BB.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 79 |
| props | 286 |
| controls | 72 |
| movables | 100 |
| region descriptors | 120 |
| objects with an event list | 316 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 390 | 277 | 3,948 |
| 1 | 3,444 | 927 | 30,048 |

3,834 commands in 1,204 groups use 27 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 8 ×733, 9 ×675, 13 ×352, 198 ×340, 2 ×315, 196 ×304, 16 ×202, 14 ×166, 5 ×155, 1 ×145, 7 ×87, 15 ×70, 18 ×68, 22 ×54, 3 ×43, 20 ×41, 204 ×27, 207 ×16, 21 ×12, 6 ×9, 197 ×5, 210 ×5, 206 ×4, 23 ×2, 199 ×2, 17 ×1, 208 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L19_BC | 2 | 0 | 3786 | region:1475 |
| L19_BC | 2 | 0 | 3792 | region:1476 |
| L19_BC | 2 | 0 | 3798 | region:1477 |
| L19_BC | 2 | 0 | 3804 | region:1478 |
| L19_BC | 2 | 0 | 3810 | region:1479 |
| L19_BC | 2 | 0 | 3816 | region:1484 |
| L19_BC | 2 | 0 | 3822 | region:1485 |
| L19_BC | 2 | 0 | 3828 | region:1486 |
| L19_BC | 2 | 0 | 3834 | region:1487 |
| L19_BC | 2 | 0 | 3840 | region:1488 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 0 | 0x0583F6F3 | control:0, control:1, control:2 |
| 69 | 0xFBF884D7 | actor:47, actor:48, actor:65 |

## Entity records

19 records of 147 bytes, by name tag: `BELIAL` ×9, `B_HUMAN` ×2, `EYE` ×2, `HIVEGRD` ×2, `DRARACLE` ×1, `DRAR_PH` ×1, `IMP_BEL` ×1, `SCOTIA` ×1.

## Companion archive

`L20_BBI.MIX`, 222,331,235 bytes: 61 AUD sound, 407 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
