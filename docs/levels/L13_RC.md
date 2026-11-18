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

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,957 | 1,449 | 4,948 | 4,696 | 4,722 | 848 | 151 | 179 |

Following the portal links, the regions fall into 6 connected groups: 1,038, 289, 99, 21, 1, 1 regions ([maps](../formats/maps.md)).

## Walls

2,369 wall rows of 8 bytes, owned by 1,113 regions, each row by exactly one region ([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.

| Side | Class 0 | Class 4 | Class 8 | Class 12 |
|---|---:|---:|---:|---:|
| wall side | 4 | 848 | 4 | 0 |
| portal side | 707 | 9 | 793 | 3 |

Special rows (code bit 4): 1.

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 222 | 98 | 2,302 |
| 1 | 1,439 | 389 | 11,096 |

1,661 commands in 487 groups use 25 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×331, 7 ×260, 16 ×209, 5 ×179, 6 ×128, 20 ×71, 14 ×63, 196 ×62, 1 ×51, 13 ×51, 8 ×43, 2 ×41, 197 ×33, 198 ×28, 3 ×22, 15 ×20, 207 ×19, 18 ×14, 210 ×13, 19 ×9, 204 ×7, 12 ×2, 21 ×2, 199 ×2, 208 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 93 | 14-byte record; native consumer open |
| object | 2 | 20 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 4 | 39 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 6 | event and value match (0xAD8E0) |
| object | 6 | 258 | value match (0xADDE0) |
| object | 8 | 1 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 65 | hit filter (0xAE2C8) |
| object | 19 | 226 | predicate trailer (0x66AB0) |
| region | 11 | 13 | region selector and event (0xF2FC0) |
| region | 12 | 71 | region event (0xF2D87) |
| region | 15 | 14 | region comparison (0xF37C8) |
| region | 19 | 17 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L12_CM | 2 | 0 | 706 | region:489 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 8 | 0x8E6CF237 | prop:325 |
| 20 | 0x815B1C01 | prop:325 |
| 136 | 0xCE20AEE3 | prop:326, control:104 |

## Entity records

4 records of 147 bytes, by name tag: `B_HUMAN` ×2, `HL1` ×1, `RULOI` ×1.

## Companion archive

`L13_RCI.MIX`, 33,447,212 bytes: 19 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
