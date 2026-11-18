# L8_SJ

Made by `tools/lol2_level_report.py` from `DAT/L8_SJ.MIX` and `DAT/L8_SJI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L8_SJ.MIX` is 13,831,538 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0x45347E1D | 13,767,768 | 63,770 | holds the entity records from entry byte 40,407 |
| 1 | 0x453E7B1B | 13,146,529 | 621,239 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0x454D7F22 | 42 | 13,146,487 | texture container: key = `ww_hash_v1("SPHERE2\L8_SJ\L8_SJ.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 117 |
| props | 1,695 |
| controls | 165 |
| movables | 55 |
| region descriptors | 491 |
| objects with an event list | 339 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5,453 | 3,961 | 12,892 | 12,892 | 12,836 | 2,952 | 946 | 775 |

Following the portal links, the regions fall into 31 connected groups: 3,792, 70, 54, 18, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Walls

8,017 wall rows of 8 bytes, owned by 2,956 regions, each row by exactly one region ([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.

| Side | Class 0 | Class 4 | Class 8 | Class 12 |
|---|---:|---:|---:|---:|
| wall side | 20 | 2,923 | 20 | 0 |
| portal side | 2,553 | 410 | 2,040 | 27 |

Special rows (code bit 4): 24.

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 254 | 134 | 2,206 |
| 1 | 2,454 | 743 | 21,836 |

2,708 commands in 877 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 8 ×512, 9 ×369, 16 ×331, 13 ×257, 2 ×161, 5 ×148, 14 ×138, 3 ×135, 198 ×132, 20 ×130, 196 ×86, 204 ×70, 7 ×39, 206 ×39, 18 ×30, 197 ×30, 199 ×27, 12 ×19, 1 ×15, 17 ×10, 23 ×7, 210 ×7, 6 ×6, 207 ×5, 21 ×4, 19 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 44 | 14-byte record; native consumer open |
| object | 2 | 34 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 83 | event byte match (0xAD7F4) |
| object | 4 | 72 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 30 | event and value match (0xAD8E0) |
| object | 6 | 463 | value match (0xADDE0) |
| object | 7 | 4 | health threshold (0xAE134) |
| object | 8 | 21 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 34 | hit filter (0xAE2C8) |
| object | 10 | 1 | region-or-object match (0xAE608) |
| object | 19 | 480 | predicate trailer (0x66AB0) |
| region | 11 | 2 | region selector and event (0xF2FC0) |
| region | 12 | 132 | region event (0xF2D87) |
| region | 19 | 46 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L4_HJ | 7 | 0 | 1492 | region:2352 |
| L4_HJ | 7 | 0 | 1498 | region:2353 |
| L4_HJ | 7 | 0 | 1504 | region:2360 |
| L9_DR | 1 | 0 | 1670 | region:3132 |
| L9_DR | 2 | 0 | 2076 | region:3569 |
| L9_DR | 2 | 0 | 2082 | region:3570 |
| L9_DR | 2 | 0 | 2088 | region:3573 |
| L10_DC | 1 | 0 | 564 | region:908 |
| L12_CM | 1 | 0 | 1908 | region:3277 |
| L14_HT | 1 | 1 | 11612 | prop:1198 |

## Movie scenes

Opcode 21 commands name a scene id from the executable's 86-name table ([movie scenes](../lol2-movie-scenes.md)); the movie file is `<name>.vqa`.

| Scene id | Name | Commands |
|---:|---|---:|
| 12 | `cem_apr` | 1 |
| 30 | `gla_apr` | 1 |
| 37 | `ruin_app` | 1 |
| 80 | `4025108e` | 1 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 29 | 0xEBFE13F0 | actor:93, actor:113, actor:113 |
| 59 | 0xD37D861A | actor:20, actor:20, actor:20, prop:0, prop:0, prop:0 |
| 104 | 0xDC2A401E | control:64 |
| 105 | 0xD0421BDE | control:66, control:66, control:70, control:70 |
| 117 | 0x0E347A01 | control:51 |
| 119 | 0x049A8E70 | control:50 |
| 128 | 0x58C85701 | actor:115 |

## Entity records

18 records of 147 bytes, by name tag: `LAMPLT` ×4, `DANIEL` ×3, `WILD` ×3, `B_HUMAN` ×2, `BACL8` ×1, `DAWNL8` ×1, `LAMP_QN` ×1, `LARKHON` ×1, `SHAMAN` ×1, `WILD2` ×1.

## Companion archive

`L8_SJI.MIX`, 104,371,246 bytes: 161 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
