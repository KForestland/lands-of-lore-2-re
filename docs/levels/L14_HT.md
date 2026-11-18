# L14_HT

Made by `tools/lol2_level_report.py` from `DAT/L14_HT.MIX` and `DAT/L14_HTI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L14_HT.MIX` is 11,912,452 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xD299A3D2 | 11,406,344 | 465,607 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xD89DA3C8 | 11,871,951 | 40,501 | holds the entity records from entry byte 34,336 |
| 2 | 0xDAA7A3E1 | 42 | 11,406,302 | texture container: key = `ww_hash_v1("SPHERE2\L14_HT\L14_HT.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 96 |
| props | 412 |
| controls | 168 |
| movables | 104 |
| region descriptors | 254 |
| objects with an event list | 548 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5,415 | 4,275 | 14,954 | 14,954 | 14,894 | 2,146 | 254 | 815 |

Following the portal links, the regions fall into 24 connected groups: 3,963, 206, 70, 16, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Walls

8,117 wall rows of 8 bytes, owned by 3,441 regions, each row by exactly one region ([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.

| Side | Class 0 | Class 4 | Class 8 | Class 12 |
|---|---:|---:|---:|---:|
| wall side | 8 | 2,134 | 8 | 0 |
| portal side | 3,090 | 97 | 2,734 | 30 |

Special rows (code bit 4): 16.

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 412 | 203 | 3,864 |
| 1 | 2,810 | 859 | 24,190 |

3,222 commands in 1,062 groups use 28 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×695, 196 ×429, 16 ×419, 5 ×302, 7 ×218, 14 ×195, 13 ×133, 2 ×119, 20 ×113, 207 ×99, 198 ×74, 6 ×65, 1 ×59, 15 ×54, 3 ×51, 204 ×51, 199 ×37, 8 ×28, 208 ×26, 18 ×24, 19 ×10, 24 ×7, 210 ×5, 197 ×3, 12 ×2, 17 ×2, 23 ×1, 209 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 133 | 14-byte record; native consumer open |
| object | 2 | 39 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 55 | event byte match (0xAD7F4) |
| object | 4 | 68 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 25 | event and value match (0xAD8E0) |
| object | 6 | 563 | value match (0xADDE0) |
| object | 7 | 24 | health threshold (0xAE134) |
| object | 8 | 1 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 26 | hit filter (0xAE2C8) |
| object | 10 | 57 | region-or-object match (0xAE608) |
| object | 19 | 457 | predicate trailer (0x66AB0) |
| region | 11 | 21 | region selector and event (0xF2FC0) |
| region | 12 | 178 | region event (0xF2D87) |
| region | 15 | 4 | region comparison (0xF37C8) |
| region | 19 | 22 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L8_SJ | 3 | 0 | 1462 | region:863 |
| L8_SJ | 3 | 0 | 3836 | region:4176 |
| L16_CA | 1 | 1 | 9210 | prop:170 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 96 | 0xB40E38C4 | movable:76 |
| 103 | 0x23F81E25 | control:126 |
| 105 | 0xD0421BDE | prop:405, prop:405, prop:406, prop:406, control:71 |
| 108 | 0x1200015E | movable:85, movable:85, movable:86, movable:86, movable:87, movable:87 |
| 109 | 0xBFDDCCA3 | prop:285, prop:370 |
| 125 | 0x0A02A378 | prop:284, prop:369 |
| 136 | 0xCE20AEE3 | movable:72 |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `HIVEW` ×2, `HL2` ×1, `LAMPLT` ×1.

## Companion archive

`L14_HTI.MIX`, 4,898,048 bytes: 13 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
