# Level geometry: vertices, regions and portals

**What:** each level's world is a set of four-sided regions, which are floor and ceiling polygons over a shared vertex table. Regions connect to their neighbours across their sides; the open sides are the portals. Both tables sit in the [level data entry](level-data.md):
- vertices: offset at +0x04, count at +0x50;
- regions: offset at +0x0C, count at +0x58.

Tool: `tools/lol2_level_report.py` writes per-level counts and checks the layout.

## Vertex table

Each vertex is 8 bytes, two s32 (x, y) in 16.16 fixed point; see the [cave page](../draracle-restoration.md). For L1_DC: 2,695 vertices at entry offset 5,300.

## Region record (44 bytes = 22 u16 words)

| Word | Offset | Meaning | Evidence |
|---:|---:|---|---|
| 2–5 | +0x04 | neighbouring region on side 0–3; `0xFFFF` = none (a wall) | CONFIRMED in code: `0xF4504` reads word `2 + side` and treats `0xFFFF` as no neighbour |
| 6–9 | +0x0C | the four corner vertices; side *s* runs from corner *s* to corner *s*+1 (mod 4) | CONFIRMED on the data (shared edges, below) |
| 10 | +0x14 | floor height (signed; larger values are higher: the ceiling word is at least the floor word in 52,495 of 52,669 regions) | CONFIRMED in code: `0xF4504` takes its base and the neighbour's height from this word |
| 11 | +0x16 | ceiling height (signed); also the raised edge of a sloped floor that has no neighbour | CONFIRMED in code: the `0xFFFF` path of `0xF4504` |
| 14 | +0x1C | flags: bit 2 = sloped floor, bit 3 = sloped ceiling; bits 12–13 = side of the floor slope, bits 14–15 = side of the ceiling slope | CONFIRMED in code for the floor (`0xF4510–0xF4519`); ceiling by the matching routine `0xF4590` (UNCONFIRMED here) |
| others | | wall-record slice, subdivision links and more | UNCONFIRMED; see the [cave page](../draracle-restoration.md) |

The routine `0xF4504` multiplies the region number by 44 and adds the table pointer `[0x22D0C]`, the same 44-byte region table the [opcode reference](../lol2-script-opcodes.md) names for opcodes 196 and 197.

**Sloped floor.** The two corners on the slope side take the neighbour's floor height, or the region's own word 11 when that side has no neighbour. The other two corners keep word 10.

## Portals

A side whose neighbour word is not `0xFFFF` is an opening into the neighbouring region. Checked on all 15 levels with `lol2_level_report.py --check` (re-run 2026-11-18). CONFIRMED:
- Every vertex index is in range, and every neighbour index is a valid region.
- The 15 levels hold 52,669 regions with 178,728 neighbour links. 177,774 of them (99.5%) are reciprocal: the neighbour names the region back.
- 177,318 links (99.2%) share the side's two vertices with the neighbour.
  - In L1_DC, 6,392 of 6,478 links share them.
  - The remaining 86 are the connector and subdivision links described on the [cave page](../draracle-restoration.md).

## Worked example

L1_DC region 156 (file offset 7,153,351):

```
00 00 00 00 9b 00 a8 00 9d 00 8b 00 b8 06 94 06 92 06 b6 06 fc fe 7c ff 20 00 b6 06 0c 52 …
```

- **Neighbours** (words 2–5): 155, 168, 157, 139. All four sides are open.
- **Corners** (words 6–9): vertices 1720, 1684, 1682, 1718.
- **Heights:** floor (word 10) is −260 (`fc fe`); word 11 is −132 (`7c ff`).
- **Flags** (word 14): `0x520C`. Bits 2 and 3 are set, so both the floor and the ceiling are sloped. Bits 12–13 are 1, so the floor slopes on side 1; bits 14–15 are also 1.

Side 1 runs from vertex 1684 to vertex 1682, toward region 168. Region 168 holds the same two vertices on its side 0, and its side 0 names region 156, so the link is a reciprocal shared-edge portal.

Region 168's floor is −255. The floor of region 156 therefore rises from −260 at corners 0 and 3 to −255 at corners 1 and 2.

## Open

- Words 0–1, 12–13 and 15–21 (wall records, subdivisions, light and more): [Q16](../OPEN_QUESTIONS.md).
- What the non-reciprocal links mean in levels other than L1_DC.
- Where the drawer stops at a portal: low walls, windows and drops ([Q16](../OPEN_QUESTIONS.md)).
