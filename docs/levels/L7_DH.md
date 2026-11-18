# L7_DH

Made by `tools/lol2_level_report.py` from `DAT/L7_DH.MIX` and `DAT/L7_DHI.MIX`. Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), [texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). How to read it: [README](README.md).

## Archive entries

`L7_DH.MIX` is 5,057,658 bytes with 3 entries.

| Entry | Key | File offset | Size | What it is |
|---:|---|---:|---:|---|
| 0 | 0xC9205816 | 5,027,789 | 29,869 | holds the entity records from entry byte 26,588 |
| 1 | 0xC92A5514 | 4,704,936 | 322,853 | level data (header dword 0 = 18, dword 4 = 5300) |
| 2 | 0xC939591B | 42 | 4,704,894 | texture container: key = `ww_hash_v1("SPHERE1\L7_DH\L7_DH.TE_")` |

## Geometry and objects

Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).

| Table | Count |
|---|---:|
| actors | 76 |
| props | 487 |
| controls | 1,062 |
| movables | 60 |
| region descriptors | 261 |
| objects with an event list | 387 |

## Regions and portals

From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose neighbour word names another region (a portal); a side without one is a wall.

| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3,221 | 2,014 | 5,820 | 5,820 | 5,732 | 2,236 | 134 | 252 |

## Scripts

| Stream | Commands | Groups | Bytes |
|---:|---:|---:|---:|
| 0 | 108 | 45 | 1,130 |
| 1 | 1,825 | 570 | 15,812 |

1,933 commands in 615 groups use 27 distinct opcodes (meanings: [script format](../lol2-level-script-format.md)). Predicate table: 255 entries of 5 bytes. Commands outside the opcode size table: 0.

Opcode use: 9 ×530, 16 ×370, 20 ×217, 5 ×146, 15 ×105, 14 ×98, 13 ×82, 7 ×74, 204 ×47, 18 ×46, 6 ×44, 1 ×33, 2 ×28, 3 ×19, 198 ×19, 207 ×15, 196 ×13, 199 ×12, 17 ×11, 8 ×10, 210 ×4, 197 ×3, 206 ×3, 19 ×1, 23 ×1, 201 ×1, 208 ×1.

## Exits

Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the high 3 bits of byte 5). "Started by" lists the objects whose event list names the command's group directly; a dash means the group is reached another way (not traced here).

| To level | Entry | Stream | Group | Started by |
|---|---:|---:|---:|---|
| L4_HJ | 6 | 0 | 856 | region:1394 |
| L4_HJ | 6 | 0 | 874 | region:1408 |
| L4_HJ | 6 | 0 | 892 | region:1409 |
| L4_HJ | 6 | 0 | 910 | region:1410 |
| L4_HJ | 6 | 0 | 928 | region:1411 |
| L4_HJ | 6 | 0 | 946 | region:1412 |
| L4_HJ | 6 | 0 | 964 | region:1413 |

## Held-item tests

None in this level.

## Entity records

5 records of 147 bytes, by name tag: `B_HUMAN` ×2, `RIX` ×1, `Rat` ×1, `SHADE` ×1.

## Companion archive

`L7_DHI.MIX`, 6,468,050 bytes: 2 VQA movie.

## Open

- Which entries marked "not identified" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).
- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic ([Q18](../OPEN_QUESTIONS.md)).
