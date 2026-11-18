# L19_BC

Made by `tools/lol2_level_report.py` from `DAT/L19_BC.MIX` and `DAT/L19_BCI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L19_BC.MIX` is 6,329,528 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xBB092F80 | 5,955,117 | 361,922 | level data (header dword 0 = 18, dword 4 = 5300) |
| 1 | 0xC10D2F76 | 6,317,039 | 12,489 | holds the entity records from entry byte 8,571 |
| 2 | 0xC3172F8F | 42 | 5,955,075 | texture container: key = `ww_hash_v1("SPHERE3\L19_BC\L19_BC.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 68 |
| props | 270 |
| controls | 153 |
| movables | 78 |
| region descriptors | 222 |
| objects with an event list | 308 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3,648 | 2,870 | 9,986 | 9,922 | 9,894 | 1,494 | 31 | 27 |

Following the portal links, the regions fall into 14 connected groups: 2,367, 360, 132, 1, 1, 1, 1, 1 … regions ([maps](../formats/maps.md)).

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 1,892 | 312 | 15,796 |
| 1 | 898 | 184 | 8,636 |

2,790 commands in 496 groups use 22 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 14 ×1074, 198 ×389, 15 ×364, 196 ×265, 1 ×119, 16 ×106, 9 ×86, 197 ×78, 20 ×68, 204 ×60, 8 ×36, 3 ×32, 18 ×23, 2 ×22, 5 ×22, 6 ×16, 207 ×10, 13 ×7, 21 ×5, 210 ×5, 7 ×2, 206 ×1.

Event records by kind ([native matchers](../lol2-script-events.md#event-records)):

| List | Kind | Records | What the game does with it |
|---|---:|---:|---|
| object | 1 | 115 | 14-byte record; native consumer open |
| object | 2 | 10 | periodic timer (0xB47B4 / 0xB8BA0) |
| object | 4 | 44 | held-item test (0xADD23, mode table VA 0xADBAC) |
| object | 5 | 6 | event and value match (0xAD8E0) |
| object | 6 | 113 | value match (0xADDE0) |
| object | 9 | 9 | hit filter (0xAE2C8) |
| object | 10 | 2 | region-or-object match (0xAE608) |
| object | 19 | 101 | predicate trailer (0x66AB0) |
| region | 11 | 64 | region selector and event (0xF2FC0) |
| region | 12 | 965 | region event (0xF2D87) |
| region | 19 | 959 | predicate trailer (0x66AB0) |

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L17_HC | 2 | 0 | 0 | region:22 |
| L20_BB | 1 | 0 | 15784 | region:2369 |
| L20_BB | 2 | 0 | 15790 | region:2369 |

## Held-item tests

None in this level.

## Entity records

7 records of 147 bytes, by name tag: `B_HUMAN` ×2, `BELSTAT` ×1, `DAWNL19` ×1, `IMP_BEL` ×1, `SEWER` ×1, `SWARMER` ×1.

## Companion archive

`L19_BCI.MIX`, 46,269,474 bytes: 7 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
