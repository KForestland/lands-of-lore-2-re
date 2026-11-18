# L10_DC

Made by `tools/lol2_level_report.py` from `DAT/L10_DC.MIX` and `DAT/L10_DCI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L10_DC.MIX` is 13,813,440 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xC2590B90 | 12,769,321 | 989,312 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xC85D0B86 | 13,758,633 | 54,807 | holds the entity records from entry byte 50,801 |
| 2 | 0xCA670B9F | 42 | 12,769,279 | texture container: key = `ww_hash_v1("SPHERE2\L10_DC\L10_DC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 102 |
| props | 524 |
| controls | 274 |
| movables | 128 |
| region descriptors | 893 |
| objects with an event list | 523 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 283 | 117 | 2,230 |
| 1 | 2,823 | 1,076 | 24,746 |

3,106 commands in 1,193 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 7 ×518, 5 ×474, 9 ×470, 16 ×420, 20 ×302, 8 ×155, 204 ×147, 6 ×116, 14 ×100, 2 ×77, 13 ×72, 196 ×67, 3 ×61, 198 ×23, 1 ×22, 18 ×21, 17 ×13, 197 ×13, 207 ×10, 208 ×10, 210 ×5, 15 ×3, 199 ×3, 19 ×2, 12 ×1, 23 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L8_SJ | 2 | 0 | 0 | region:0 |
| L9_DR | 3 | 0 | 108 | region:42 |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `DRACOID` ×1, `PDRACOID` ×1, `RAT` ×1, `SKEL` ×1.

## Companion archive

`L10_DCI.MIX`, 17,040,820 bytes: 58 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
