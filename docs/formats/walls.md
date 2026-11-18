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
| 4 | special row | CONFIRMED as a separate path (`0x11463C–0x11463F` tests bit 4); its geometry is UNCONFIRMED |

**Classes on the data.** Counted over all 15 levels:
- **Class 4** stands on wall sides: 31,645 rows, nearly all of the wall-side rows.
- **Classes 0 and 8** stand on portal sides. Class 8 mostly appears where the neighbour's floor is higher. Class 0 mostly appears where the neighbour's ceiling is lower. Many rows sit next to sloped regions, where the flat heights alone do not decide.
- **Class 12** is rare. Classes 4 and 12 also stand on some portal sides, as in the worked example below; the cave page traces them there as connector middle walls.

The earlier native replays on L1_DC ([native wall verification](../native-wall-verification.md)) treat classes 4 and 12 as the middle (full) wall and 0 and 8 as the upper and lower pieces. They follow the original routines `F4504`, `F4590` and `F49FC`.

**Which of 0 and 8 is upper:** the counts above fit class 0 = upper piece (above the opening) and class 8 = lower piece (below it). That pairing is a reading of the data, UNCONFIRMED until traced in the constructor.

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

Read with the neighbour's heights, the opening into region 37 runs from height 55 to 75:
- the lower piece closes 0 to 55;
- the upper piece closes 75 to 80.

So the side is a window into a raised room, not a doorway at floor level.

Across the Huline Temple, 5,951 of its 8,117 rows stand on portal sides (classes 0: 3,090; 8: 2,734; 4: 97; 12: 30), against 2,134 class-4 rows on wall sides ([level sheet](../levels/L14_HT.md)). Most of the temple's walls are therefore pieces around openings, not full walls.

This is why the temple's interior cannot be drawn by treating every portal as fully open, nor every region side as a wall. The rows say how much of each opening is closed. CONFIRMED for the row data; the drawing rule is UNCONFIRMED.

## Open ([Q16](../OPEN_QUESTIONS.md))

- The other row bytes: bytes 0–1 look like a texture or resource word, bytes 2–4 hold setup values the constructor copies (replayed on L1_DC by `tools/draracle/lol2_extract_wall_records.py`), and bytes 6–7 hold flags (bit 7 of byte 6 selects connector heights, per the cave page).
- The geometry of special rows (code bit 4).
- Which of classes 0 and 8 is the upper piece, traced in the constructor.
- How the drawer clips at a partly closed portal, and the full UV mapping.
