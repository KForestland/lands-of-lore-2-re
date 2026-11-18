# L5_HC

Made by `tools/lol2_level_report.py` from `DAT/L5_HC.MIX` and `DAT/L5_HCI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L5_HC.MIX` is 6,030,400 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xE1165002 | 5,999,778 | 30,622 | holds the entity records from entry byte 25,893 |
| 1 | 0xE1204D00 | 5,787,745 | 212,033 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xE12F5107 | 42 | 5,787,703 | texture container: key = `ww_hash_v1("SPHERE1\L5_HC\L5_HC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 37 |
| props | 848 |
| controls | 157 |
| movables | 85 |
| region descriptors | 137 |
| objects with an event list | 388 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,001 | 1,292 | 3,974 | 3,754 | 3,732 | 1,194 | 266 | 176 |

Following the portal links, the regions fall into 9 connected groups: 1,270, 12, 4, 1, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Walls

2,597 wall rows of 8 bytes, owned by 1,024 regions, each row by exactly one region ([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.

| Side | Class 0 | Class 4 | Class 8 | Class 12 |
|---|---:|---:|---:|---:|
| wall side | 8 | 1,194 | 8 | 0 |
| portal side | 679 | 78 | 600 | 15 |

Special rows (code bit 4): 15.

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 707 | 210 | 6,858 |
| 1 | 1,190 | 415 | 10,682 |

1,897 commands in 625 groups use 27 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×342, 20 ×303, 16 ×166, 18 ×129, 5 ×113, 12 ×107, 197 ×106, 1 ×95, 196 ×95, 14 ×77, 2 ×53, 6 ×46, 8 ×45, 198 ×45, 208 ×34, 204 ×32, 13 ×22, 3 ×19, 15 ×18, 7 ×11, 207 ×9, 19 ×8, 210 ×6, 199 ×5, 206 ×5, 23 ×4, 201 ×2.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 20 | 14-byte record; native consumer open |
| object | 2 | 26 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 64 | event byte match (0xAD7F4) |
| object | 4 | 24 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 18 | event and value match (0xAD8E0) |
| object | 6 | 237 | value match (0xADDE0) |
| object | 7 | 2 | health threshold (0xAE134) |
| object | 8 | 3 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 37 | hit filter (0xAE2C8) |
| object | 10 | 5 | region-or-object match (0xAE608) |
| object | 19 | 169 | predicate trailer (0x66AB0) |
| region | 11 | 30 | region selector and event (0xF2FC0) |
| region | 12 | 180 | region event (0xF2D87) |
| region | 19 | 54 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L4_HJ | 3 | 0 | 860 | region:460 |
| L4_HJ | 4 | 0 | 6400 | region:835 |

## Movie scenes

No opcode-21 command in this level's scripts.

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 96 | 0xB40E38C4 | control:122 |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `DAWNL4` ×1, `EXEC` ×1, `HIVEW` ×1, `WORM` ×1.

## Companion archive

`L5_HCI.MIX`, 26,388,138 bytes: 13 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
