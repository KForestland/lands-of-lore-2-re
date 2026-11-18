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

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 6,190 | 4,320 | 13,612 | 13,544 | 13,524 | 3,668 | 387 | 30 |

Following the portal links, the regions fall into 8 connected groups: 4,229, 36, 30, 21, 1, 1, 1, 1 regions ([maps](../formats/maps.md)).

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 283 | 117 | 2,230 |
| 1 | 2,823 | 1,076 | 24,746 |

3,106 commands in 1,193 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 7 ×518, 5 ×474, 9 ×470, 16 ×420, 20 ×302, 8 ×155, 204 ×147, 6 ×116, 14 ×100, 2 ×77, 13 ×72, 196 ×67, 3 ×61, 198 ×23, 1 ×22, 18 ×21, 17 ×13, 197 ×13, 207 ×10, 208 ×10, 210 ×5, 15 ×3, 199 ×3, 19 ×2, 12 ×1, 23 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 119 | 14-byte record; native consumer open |
| object | 2 | 41 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 141 | event byte match (0xAD7F4) |
| object | 4 | 227 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 7 | event and value match (0xAD8E0) |
| object | 6 | 361 | value match (0xADDE0) |
| object | 7 | 11 | health threshold (0xAE134) |
| object | 8 | 4 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 284 | hit filter (0xAE2C8) |
| object | 19 | 516 | predicate trailer (0x66AB0) |
| region | 11 | 2 | region selector and event (0xF2FC0) |
| region | 12 | 115 | region event (0xF2D87) |
| region | 19 | 25 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L8_SJ | 2 | 0 | 0 | region:0 |
| L9_DR | 3 | 0 | 108 | region:42 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 78 | 0xCFE9BC82 | prop:155 |
| 97 | 0xE791578D | control:66, control:143 |
| 98 | 0xF38DCC87 | prop:242, prop:247 |
| 99 | 0x438E1086 | control:87, control:91, control:95, control:99, control:105, control:108, control:126, control:152 … |
| 100 | 0x3B8E1486 | control:109, control:127 |
| 101 | 0xE78E1887 | control:125, control:154, control:156 |
| 102 | 0xC5DA9D44 | control:70 |
| 168 | 0xD9475D01 | prop:156 |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `DRACOID` ×1, `PDRACOID` ×1, `RAT` ×1, `SKEL` ×1.

## Companion archive

`L10_DCI.MIX`, 17,040,820 bytes: 58 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
