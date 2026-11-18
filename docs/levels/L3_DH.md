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

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,162 | 1,499 | 4,918 | 4,770 | 4,718 | 1,078 | 34 | 38 |

Following the portal links, the regions fall into 3 connected groups: 1,486, 12, 1 regions ([maps](../formats/maps.md)).

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 217 | 91 | 1,878 |
| 1 | 1,576 | 446 | 13,126 |

1,793 commands in 537 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 6 ×282, 9 ×282, 5 ×182, 20 ×177, 16 ×157, 14 ×90, 2 ×87, 1 ×77, 198 ×64, 3 ×58, 19 ×57, 24 ×50, 7 ×40, 8 ×40, 13 ×35, 196 ×28, 197 ×24, 210 ×20, 18 ×13, 207 ×10, 204 ×9, 12 ×5, 21 ×2, 206 ×2, 199 ×1, 208 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 115 | 14-byte record; native consumer open |
| object | 2 | 27 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 53 | event byte match (0xAD7F4) |
| object | 4 | 103 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 7 | event and value match (0xAD8E0) |
| object | 6 | 126 | value match (0xADDE0) |
| object | 8 | 55 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 75 | hit filter (0xAE2C8) |
| object | 19 | 169 | predicate trailer (0x66AB0) |
| region | 11 | 6 | region selector and event (0xF2FC0) |
| region | 12 | 85 | region event (0xF2D87) |
| region | 19 | 43 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L4_HJ | 1 | 1 | 7306 | control:82 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 11 | 0x74C22E7C | control:181 |
| 58 | 0xDDC02377 | control:117, control:118, control:119, control:120, control:121, control:122, control:123, control:124 … |
| 70 | 0xA65AA1BF | movable:55 |
| 94 | 0x178B0A33 | control:78, control:87, control:88, control:113, control:114, control:140, control:141, control:142 … |

## Entity records

5 records of 147 bytes, by name tag: `B_HUMAN` ×2, `skel` ×2, `Rat` ×1.

## Companion archive

`L3_DHI.MIX`, 34,615,570 bytes: 14 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
