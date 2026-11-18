# L4_HJ

Made by `tools/lol2_level_report.py` from `DAT/L4_HJ.MIX` and `DAT/L4_HJI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L4_HJ.MIX` is 13,304,101 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xDD24481E | 13,241,303 | 62,798 | holds the entity records from entry byte 47,286 |
| 1 | 0xDD2E451C | 12,409,578 | 831,725 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xDD3D4923 | 42 | 12,409,536 | texture container: key = `ww_hash_v1("SPHERE1\L4_HJ\L4_HJ.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 67 |
| props | 6,295 |
| controls | 228 |
| movables | 80 |
| region descriptors | 368 |
| objects with an event list | 1,136 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 6,211 | 4,787 | 16,362 | 16,362 | 16,332 | 2,786 | 1,243 | 97 |

Following the portal links, the regions fall into 23 connected groups: 4,712, 43, 12, 1, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 2,382 | 945 | 19,566 |
| 1 | 3,665 | 929 | 31,240 |

6,047 commands in 1,874 groups use 29 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×942, 2 ×825, 198 ×599, 16 ×582, 14 ×564, 8 ×482, 21 ×456, 5 ×345, 20 ×238, 7 ×214, 204 ×145, 196 ×140, 1 ×87, 3 ×72, 18 ×72, 13 ×71, 197 ×41, 206 ×38, 199 ×32, 15 ×24, 19 ×22, 12 ×18, 210 ×11, 17 ×9, 208 ×8, 6 ×4, 207 ×3, 23 ×2, 201 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 57 | 14-byte record; native consumer open |
| object | 2 | 159 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 45 | event byte match (0xAD7F4) |
| object | 4 | 108 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 114 | event and value match (0xAD8E0) |
| object | 6 | 355 | value match (0xADDE0) |
| object | 8 | 13 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 133 | hit filter (0xAE2C8) |
| object | 10 | 2 | region-or-object match (0xAE608) |
| object | 19 | 648 | predicate trailer (0x66AB0) |
| region | 11 | 79 | region selector and event (0xF2FC0) |
| region | 12 | 866 | region event (0xF2D87) |
| region | 19 | 160 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L5_HC | 1 | 0 | 5208 | region:2809 |
| L5_HC | 2 | 0 | 4846 | region:2604 |
| L7_DH | 1 | 0 | 6292 | region:3205 |
| L8_SJ | 1 | 0 | 6100 | region:3186 |
| L8_SJ | 1 | 0 | 6124 | region:3186 |
| L8_SJ | 1 | 0 | 6130 | region:3187 |
| L8_SJ | 1 | 0 | 6154 | region:3187 |
| L8_SJ | 1 | 0 | 6160 | region:3188 |
| L8_SJ | 1 | 0 | 6184 | region:3188 |
| L8_SJ | 1 | 0 | 6190 | region:3189 |
| L8_SJ | 1 | 0 | 6214 | region:3189 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 74 | 0xB45B2813 | actor:63 |
| 85 | 0x87F22ADE | control:0, control:83 |
| 95 | 0x9EF322DA | movable:64, movable:65, movable:67, movable:68, movable:70 |
| 111 | 0x64C08B10 | control:0, control:83 |
| 112 | 0x7F859FB9 | control:0, control:83 |

## Entity records

13 records of 147 bytes, by name tag: `BACL4` ×1, `B_HUMAN` ×1, `DINO` ×1, `DawnL4` ×1, `GGuard` ×1, `Kelsrick` ×1, `L4WW` ×1, `SSAR` ×1, `TIG_CUB` ×1, `TIG_FEM` ×1, `TIG_MAL` ×1, `TIG_ROG` ×1, `VILLAGER` ×1.

## Companion archive

`L4_HJI.MIX`, 177,101,356 bytes: 129 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
