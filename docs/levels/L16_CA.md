# L16_CA

Made by `tools/lol2_level_report.py` from `DAT/L16_CA.MIX` and `DAT/L16_CAI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L16_CA.MIX` is 19,106,900 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xBED91384 | 17,959,024 | 1,094,640 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xC4DD137A | 19,053,664 | 53,236 | holds the entity records from entry byte 47,328 |
| 2 | 0xC6E71393 | 42 | 17,958,982 | texture container: key = `ww_hash_v1("SPHERE3\L16_CA\L16_CA.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 47 |
| props | 681 |
| controls | 326 |
| movables | 201 |
| region descriptors | 373 |
| objects with an event list | 688 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 755 | 259 | 8,428 |
| 1 | 6,228 | 1,877 | 55,292 |

6,983 commands in 2,136 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 16 ×1346, 5 ×1112, 9 ×920, 196 ×789, 7 ×687, 204 ×339, 1 ×331, 14 ×297, 3 ×294, 20 ×212, 2 ×155, 13 ×119, 15 ×93, 18 ×77, 198 ×70, 8 ×69, 17 ×17, 197 ×17, 6 ×9, 208 ×9, 207 ×8, 210 ×5, 199 ×3, 21 ×2, 23 ×2, 12 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L17_HC | 1 | 1 | 42056 | control:74 |
| L17_HC | 3 | 0 | 7268 | region:9822 |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `VISC` ×2, `HL3` ×1, `bacl16` ×1.

## Companion archive

`L16_CAI.MIX`, 17,836,202 bytes: 29 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
