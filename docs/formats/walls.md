# Wall rows

**What:** each level's walls are 8-byte rows in one table of the [level data entry](level-data.md). Every [region](geometry.md) owns a run of these rows. A row names a side of its region and a class.

The classes:
- **Wall side** (no neighbour): a full wall, class 4.
- **Portal side** (a neighbour region): the pieces that close the gap between the two regions' heights, so an opening can be a doorway, a step, a window or a lintel.

Tool: `tools/lol2_level_report.py` checks the table and counts the rows per level, in the sheets' "Walls" section. Earlier native replays on L1_DC: [native wall verification](../native-wall-verification.md).

## Where the rows are

| Where | Meaning | Evidence |
|---|---|---|
| level data header +0x08 / +0x54 | wall table offset / row count | CONFIRMED on the data: in all 15 levels the table ends exactly where the region table starts (+0x0C) |
| region word 13 (+0x1A) | first row of the region's run; `0xFFFF` when it has none | CONFIRMED in code: `0xF4370–0xF438E` reads +0x1A, multiplies by 8 and adds the table pointer `[0x22D08]` |
| region byte 30 (+0x1E, low byte of word 15) | number of rows in the run | CONFIRMED in code: same routine, loop count |
| row byte 5 & 0x1F | the row's code | CONFIRMED in code: `0xF4394–0xF4399` (the routine searches the run for a code) and the constructor at `0x114632–0x114637` |

The table pointer `[0x22D08]` is the same 8-byte-row table that the [opcode reference](../lol2-script-opcodes.md) names for opcode 204.

**Partition.** `lol2_level_report.py --check` re-ran on 2026-11-18. In all 15 levels every row belongs to exactly one region's run, and no run reaches past the table. Regions without walls have first row `0xFFFF`. That is 88,994 rows in all. CONFIRMED.

## The code

| Bits | Meaning | Evidence |
|---|---|---|
| 0–1 | the side of the region the row stands on | CONFIRMED on the data (below) |
| 2–3 | class: 0, 4, 8 or 12 | values CONFIRMED; meanings below |
| 4 | special row | CONFIRMED as a fractional side segment (`0x11471C–0x114724` dispatches to `0x11511C` when region +0x1C bit 7 is clear; otherwise `0x115250`) |

**Classes on the data.** Counted over all 15 levels:
- **Class 4** stands on wall sides: 31,645 rows, nearly all of the wall-side rows.
- **Classes 0 and 8** stand on portal sides. Class 8 mostly appears where the neighbour's floor is higher. Class 0 mostly appears where the neighbour's ceiling is lower. Many rows sit next to sloped regions, where the flat heights alone do not decide.
- **Class 12** is rare. Classes 4 and 12 also stand on some portal sides, as in the worked example below; the cave page traces them there as connector middle walls.

The earlier native replays on L1_DC ([native wall verification](../native-wall-verification.md)) treat classes 4 and 12 as the middle (full) wall and 0 and 8 as the upper and lower pieces. They follow the original routines `F4504`, `F4590` and `F49FC`.

**CONFIRMED.** On the ordinary geometry path, `0x114B45–0x114B64`
switches on class. For class 0, `0x114C73–0x114CA8` puts the owning
region's ceiling at the top, using the slope helper when flagged.
`0x114CCE–0x114D20` obtains the bottom from the neighbour's ceiling,
clamped at the owning floor for flat geometry. Class 8 obtains its
bottom from the owning floor at `0x114D48–0x114D86`, then its top from
the neighbour floor at `0x114D89–0x114E62`; when region byte +0x22 is
not `0xFF` and that floor is above the owning ceiling, the top becomes
the owning ceiling and byte +0x31 advances by
`diff >> (((+0x3E >> 14) & 3) - 1)`, a V offset (`0x114DEC–0x114E51`). The live record stores
top heights at +4 and +0x10, bottom heights at +0x28 and +0x1C. The
ordinary constructor passes row +6 bit 7 at `0x11472B–0x114738`, which
lets the connector path choose endpoints or height sources separately.

## Special rows

**CONFIRMED.** On the `0x11511C` constructor path, let `P0` and `P1`
be the two selected side vertices, and `F` and `C` the owning region's
signed floor and ceiling. Let `bN` be unsigned wall row byte N. The
horizontal endpoints in each fixed-point component are
`P0 + ((P1 - P0) >> 8) * t`, with `t = b2` and `t = b2 + b4`.
The top and bottom fixed-point heights are:

```text
top = (C << 16) - ((C - F - b7) << 8) * b3
bottom = top - (b7 << 16)
```

The height stores are `0x115173–0x11518F`, the endpoint loads and stores
`0x115192–0x115243`, and `0x11523A` marks the quad active. The
arithmetic uses signed right shifts and 32-bit results. The caller loop
sets wall object +0x40 to `0x7F` (`0x11464D`), replaces it with byte 4
of the first earlier ordinary row in the region whose code equals the
special row's code with bit 4 cleared, and then zeros the byte offsets
at +0x30/+0x31 (`0x114644–0x11467F`). Across the 15 archives, 45 of 67 special rows
have that earlier ordinary row, and 22 use the fallback under this path.
The level report rechecks both counts from header +0x08 and +0x0C.

For example, `L14_HT.MIX+0xAFC4D2` (row 7471, region 17) has bytes
`3d 04 1e ff e5 15 60 42`. Its region at `+0xAFDBEE` has floor 0 and
ceiling 125. The horizontal parameters are 30 and 259. The fixed-point
top and bottom are 4,340,480 and 15,104, respectively. The earlier
ordinary code-5 row gives byte 4 equal to `0x80`.

## Worked example: a window in the Huline Temple

`L14_HT.MIX`, region 0:
- floor 0, ceiling 80, no slopes;
- neighbours 37, 12, 1, 14;
- run of 4 rows from row 7,448.

All four rows stand on side 0, which opens into region 37 (floor 55, ceiling 75):

| Row | File offset | Bytes | Code | Class |
|---:|---:|---|---:|---:|
| 7,448 | 11,519,002 | `b5 00 2b 6c 80 00 10 00` | 0 | 0 |
| 7,449 | 11,519,010 | `ef 01 00 4e 80 04 10 00` | 4 | 4 |
| 7,450 | 11,519,018 | `ef 01 2b 00 80 08 10 00` | 8 | 8 |
| 7,451 | 11,519,026 | `ef 01 4c 4e 80 0c 10 00` | 12 | 12 |

**CONFIRMED.** A bounded replay of original `0x114AA4` instructions
with the on-disk regions at `+0xAFD902` and `+0xAFDF5E`, and the level's
vertex table, gives the following four active quads. The replay supplies
table pointers and reports the constructor output. Heights below are in
map units. X/Z positions are shown as stored 16.16 integers.

```bash
python3 tools/draracle/verify_huline_wall_spans.py --data DAT --check
```

This check requires Capstone. It writes nothing.

| Row | Bottom to top | First endpoint (X, Z) | Second endpoint (X, Z) |
|---:|---|---|---|
| 7,448 | 75 to 80 | (214302720, 227475456) | (204800000, 217382912) |
| 7,449 | 0 to 80 | (214302720, 227475456) | (212074496, 225050624) |
| 7,450 | 0 to 55 | (214302720, 227475456) | (204800000, 217382912) |
| 7,451 | 0 to 80 | (207834407, 220581341) | (204800000, 217382912) |

The upper and lower rows bound the opening vertically. The connector
(neighbour region flag `0x10` at `0x114AF6`) supplies the inner endpoints
of the two full-height pieces at either end. Together the four quads
leave a raised opening in the middle of the side.

Across the Huline Temple, 5,951 of its 8,117 rows stand on portal sides (classes 0: 3,090; 8: 2,734; 4: 97; 12: 30), against 2,150 rows on wall sides (2,134 of class 4 and 16 of classes 0 and 8) and 16 special rows ([level sheet](../levels/L14_HT.md)). Most of the temple's walls are therefore pieces around openings, not full walls.

The constructed opening has both horizontal and vertical bounds. UNCONFIRMED. Raster clipping and the screen-space texture coordinates of this opening need a draw-path witness.

## Open ([Q16](../OPEN_QUESTIONS.md))

- The other row bytes: bytes 0–1 look like a texture or resource word, bytes 2–4 hold setup values the constructor copies (replayed on L1_DC by `tools/draracle/lol2_extract_wall_records.py`), and bytes 6–7 hold flags (bit 7 of byte 6 selects connector endpoints for classes 0/8 and the height source for classes 4/12, as traced above).
- The preceding replay stops at the constructed quad. To link the Huline Temple witness to the one sampled L20_BB span, pass the four output quads, via the call at `0x114753`, into `0x1322A4`. Follow the three stored setup words at runtime wall +0x32/+0x34/+0x36 (`0x114763–0x11478B`) to the clipping and sampler initialization for each surviving span. Full UV mapping remains UNCONFIRMED.
- The alternate constructor `0x115250` is selected when region +0x1C bit 7 is set (`0x1145CE–0x1145DC`, call at `0x114710`); none of the 67 special rows sits in such a region. Its behaviour remains UNCONFIRMED.
