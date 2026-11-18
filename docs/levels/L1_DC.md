# L1_DC

Made by `tools/lol2_level_report.py` from `DAT/L1_DC.MIX` and `DAT/L1_DCI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L1_DC.MIX` is 7,424,548 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xB1162802 | 7,389,520 | 35,028 | holds the entity records from entry byte 27,723 |
| 1 | 0xB1202500 | 7,091,978 | 297,542 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xB12F2907 | 42 | 7,091,936 | texture container: key = `ww_hash_v1("SPHERE1\L1_DC\L1_DC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 57 |
| props | 1,559 |
| controls | 174 |
| movables | 80 |
| region descriptors | 173 |
| objects with an event list | 426 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,695 | 1,954 | 6,478 | 6,446 | 6,392 | 1,338 | 301 | 270 |

Following the portal links, the regions fall into 9 connected groups: 1,933, 14, 1, 1, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Walls

3,052 wall rows of 8 bytes, owned by 1,471 regions, each row by exactly one region ([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.

| Side | Class 0 | Class 4 | Class 8 | Class 12 |
|---|---:|---:|---:|---:|
| wall side | 4 | 1,336 | 4 | 0 |
| portal side | 861 | 29 | 790 | 28 |

Special rows (code bit 4): 0.

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 282 | 98 | 2,380 |
| 1 | 1,700 | 568 | 14,662 |

1,982 commands in 666 groups use 28 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×323, 20 ×230, 16 ×221, 5 ×218, 2 ×141, 7 ×117, 3 ×115, 198 ×108, 13 ×93, 1 ×65, 8 ×63, 6 ×57, 19 ×46, 14 ×37, 207 ×31, 18 ×24, 21 ×24, 197 ×17, 196 ×16, 204 ×8, 208 ×6, 15 ×5, 23 ×5, 12 ×3, 17 ×3, 210 ×3, 206 ×2, 24 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 141 | 14-byte record; native consumer open |
| object | 2 | 19 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 49 | event byte match (0xAD7F4) |
| object | 4 | 95 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 44 | event and value match (0xAD8E0) |
| object | 6 | 229 | value match (0xADDE0) |
| object | 8 | 6 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 85 | hit filter (0xAE2C8) |
| object | 10 | 21 | region-or-object match (0xAE608) |
| object | 19 | 298 | predicate trailer (0x66AB0) |
| region | 11 | 1 | region selector and event (0xF2FC0) |
| region | 12 | 97 | region event (0xF2D87) |
| region | 19 | 53 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L3_DH | 1 | 0 | 1194 | region:1190 |
| L3_DH | 1 | 0 | 1246 | region:1217 |
| L3_DH | 1 | 0 | 1298 | region:1218 |
| L3_DH | 1 | 0 | 1350 | region:1219 |
| L3_DH | 1 | 0 | 1402 | region:1220 |
| L3_DH | 1 | 0 | 1454 | region:1221 |
| L3_DH | 1 | 0 | 1506 | region:1222 |
| L3_DH | 1 | 0 | 1558 | region:1223 |
| L3_DH | 1 | 0 | 1610 | region:1224 |
| L3_DH | 1 | 1 | 4030 | prop:447 |

## Movie scenes

Opcode 21 commands name a scene id from the executable's 86-name table ([movie scenes](../lol2-movie-scenes.md)); the movie file is `<name>.vqa`.

| Scene id | Name | Commands |
|---:|---|---:|
| 11 | `bst-die` | 1 |
| 21 | `e029e` | 9 |
| 22 | `e030e` | 1 |
| 23 | `e031e` | 10 |
| 29 | `flood` | 1 |
| 35 | `liz-die` | 1 |
| 74 | `luthrdie` | 1 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 110 | 0xDE73C93C | movable:0, movable:1, movable:2, movable:3, movable:4 |

## Entity records

11 records of 147 bytes, by name tag: `B_HUMAN` ×3, `GGUARD` ×2, `WORM` ×2, `GGCAPT` ×1, `Kenneth` ×1, `ROACH` ×1, `Roach` ×1.

## Companion archive

`L1_DCI.MIX`, 103,374,072 bytes: 36 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
