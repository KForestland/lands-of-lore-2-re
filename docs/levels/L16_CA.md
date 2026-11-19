# L16_CA

Made by `tools/lol2_level_report.py` from `DAT/L16_CA.MIX` and `DAT/L16_CAI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

Related references: [Progression rows for L16_CA](../PROGRESSION.md#level-l16_ca) and [item, spell and creature numbers](../NUMBERS.md).

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

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12,399 | 10,582 | 38,882 | 38,842 | 38,774 | 3,446 | 384 | 1,053 |

Following the portal links, the regions fall into 37 connected groups: 8,667, 849, 569, 240, 214, 12, 1, 1 … regions ([maps](../formats/maps.md)).

## Walls

15,263 wall rows of 8 bytes, owned by 7,661 regions, each row by exactly one region ([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.

| Side | Class 0 | Class 4 | Class 8 | Class 12 |
|---|---:|---:|---:|---:|
| wall side | 68 | 3,259 | 68 | 0 |
| portal side | 5,568 | 45 | 6,221 | 34 |

Special rows (code bit 4): 0.

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 755 | 259 | 8,428 |
| 1 | 6,228 | 1,877 | 55,292 |

6,983 commands in 2,136 groups use 26 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 16 ×1346, 5 ×1112, 9 ×920, 196 ×789, 7 ×687, 204 ×339, 1 ×331, 14 ×297, 3 ×294, 20 ×212, 2 ×155, 13 ×119, 15 ×93, 18 ×77, 198 ×70, 8 ×69, 17 ×17, 197 ×17, 6 ×9, 208 ×9, 207 ×8, 210 ×5, 199 ×3, 21 ×2, 23 ×2, 12 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 76 | 14-byte record; native consumer open |
| object | 2 | 107 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 3 | 21 | event byte match (0xAD7F4) |
| object | 4 | 426 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 18 | event and value match (0xAD8E0) |
| object | 6 | 1,204 | value match (0xADDE0) |
| object | 8 | 5 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 84 | hit filter (0xAE2C8) |
| object | 10 | 12 | region-or-object match (0xAE608) |
| object | 19 | 1,466 | predicate trailer (0x66AB0) |
| region | 11 | 131 | region selector and event (0xF2FC0) |
| region | 12 | 128 | region event (0xF2D87) |
| region | 19 | 41 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L17_HC | 1 | 1 | 42056 | control:74 |
| L17_HC | 3 | 0 | 7268 | region:9822 |

## Movie scenes

Opcode 21 commands name a scene id from the executable's 86-name table ([movie scenes](../lol2-movie-scenes.md)); the movie file is `<name>.vqa`.

| Scene id | Name | Commands |
|---:|---|---:|
| 27 | `elevator` | 1 |
| 82 | `1320516e` | 1 |

## Held-item tests

Event records of kind 4 with mode 3: the object's event runs when the held item has this identity ([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.

| Item | Identity | Objects (inverted marked !) |
|---:|---|---|
| 55 | 0x84D4248D | movable:66 |
| 57 | 0xE7B89177 | movable:66 |
| 60 | 0xF40E4E1D | movable:66 |
| 63 | 0x8B59F903 | prop:1, prop:2, prop:3, prop:4, prop:419, prop:483, prop:484, prop:485 … |
| 65 | 0x9B5B0719 | movable:66 |
| 68 | 0xE0649CBA | movable:66 |
| 94 | 0x178B0A33 | control:62, control:63, control:64, control:65, control:66, control:67, control:68, control:69 … |
| 107 | 0x042E0C09 | control:0, control:70, control:95, control:173, control:174, control:175, control:176 |
| 109 | 0xBFDDCCA3 | control:148, control:149, control:150, control:151, control:152, control:153, control:154, control:155 … |
| 110 | 0xDE73C93C | control:148, control:149, control:150, control:151, control:152, control:153, control:154, control:155 … |
| 111 | 0x64C08B10 | control:148, control:149, control:150, control:151, control:152, control:153, control:154, control:155 … |
| 117 | 0x0E347A01 | control:75 |
| 118 | 0xE320E8D1 | prop:418, control:148, control:149, control:150, control:151, control:152, control:153, control:154 … |
| 122 | 0xCA4DEBCC | control:148, control:149, control:150, control:151, control:152, control:153, control:154, control:155 … |

## Entity records

6 records of 147 bytes, by name tag: `B_HUMAN` ×2, `VISC` ×2, `HL3` ×1, `bacl16` ×1.

## Companion archive

`L16_CAI.MIX`, 17,836,202 bytes: 29 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
