# L12_CM

Made by `tools/lol2_level_report.py` from `DAT/L12_CM.MIX` and `DAT/L12_CMI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L12_CM.MIX` is 10,064,381 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xBE79639C | 9,580,528 | 458,603 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xC47D6392 | 10,039,131 | 25,250 | holds the entity records from entry byte 14,255 |
| 2 | 0xC68763AB | 42 | 9,580,486 | texture container: key = `ww_hash_v1("SPHERE2\L12_CM\L12_CM.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 46 |
| props | 438 |
| controls | 138 |
| movables | 74 |
| region descriptors | 238 |
| objects with an event list | 161 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4,639 | 3,644 | 12,496 | 12,496 | 12,496 | 2,080 | 632 | 134 |

Following the portal links, the regions fall into 14 connected groups: 3,424, 195, 14, 1, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 306 | 84 | 2,448 |
| 1 | 739 | 187 | 6,842 |

1,045 commands in 271 groups use 21 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×208, 8 ×136, 16 ×103, 2 ×100, 13 ×79, 198 ×56, 196 ×53, 20 ×50, 197 ×47, 14 ×43, 18 ×37, 3 ×36, 7 ×29, 206 ×21, 210 ×11, 5 ×10, 204 ×9, 1 ×8, 21 ×3, 199 ×3, 208 ×3.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 20 | 14-byte record; native consumer open |
| object | 2 | 19 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 4 | 31 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 14 | event and value match (0xAD8E0) |
| object | 6 | 96 | value match (0xADDE0) |
| object | 8 | 2 | word match with 0xFFFF wildcard (0xAE510) |
| object | 9 | 25 | hit filter (0xAE2C8) |
| object | 19 | 99 | predicate trailer (0x66AB0) |
| region | 11 | 12 | region selector and event (0xF2FC0) |
| region | 12 | 72 | region event (0xF2D87) |
| region | 19 | 51 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L8_SJ | 4 | 0 | 0 | region:734 |
| L13_RC | 1 | 1 | 2808 | control:74 |

## Held-item tests

None in this level.

## Entity records

10 records of 147 bytes, by name tag: `B_HUMAN` ×2, `GGUARD` ×2, `STIGER` ×2, `APE` ×1, `BACL12` ×1, `DAWNL12` ×1, `TIG_ROG` ×1.

## Companion archive

`L12_CMI.MIX`, 70,077,968 bytes: 56 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
