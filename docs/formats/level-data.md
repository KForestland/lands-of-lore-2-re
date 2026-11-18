# Level data entry (geometry, objects, scripts)

**What:** each level archive `DAT/L<n>_<xx>.MIX` holds one entry with the level's geometry (vertices, regions), its object tables (props, controls, actors, movables), the event-record lists and the two script command streams, and the predicate table. Other pages call it the geometry entry. Full field notes: [lol2-level-script-format.md](../lol2-level-script-format.md).

**Read:** all 15 level archives. Tools: `tools/lol2_source_format.py` (`level_geometry`), `tools/lol2_export_scripts.py` (streams and tables).

## How it is found

It is the one entry whose header starts with dword 18 (0x12) and dword 5300, and that has at least 0x244 bytes; the native loader reads 0x244 header bytes and continues only when dword +0 is 0x12 ([lol2-level-script-format.md](../lol2-level-script-format.md#finding-the-geometry-entry), loader around file offset 0xD3CBC). Exactly one such entry exists in each of the 15 level archives. CONFIRMED (`lol2_source_format.py --check`).

## Header tables

All offsets relative to the start of the entry; "offset / count".

| Offset field | Count field | Row size | Contents |
|---|---|---|---|
| +0x04 | +0x50 | 8 | vertices (two s32) |
| +0x0C | +0x58 | 44 | geometry regions |
| +0x14 | +0x60 | 37 | props |
| +0x18 | +0x64 | 33 | controls |
| +0x1C | +0x68 | 56 | actors |
| +0x24 | +0x70 | 41 | movables |
| +0x38 / +0x80 | bytes | | region event-record lists |
| +0x3C / +0x84 | bytes | | command stream 0 |
| +0x40 / +0x88 | bytes | | object event-record lists |
| +0x44 / +0x8C | bytes | | command stream 1 |
| +0xA4 | +0xAC | 26 | region descriptors |
| +0xBC | +0xB8 | 5 | predicate table (offset field after the count field) |

Source and checks: [lol2-level-script-format.md](../lol2-level-script-format.md#header-fields-proven-by-consistent-reading-on-all-15-levels). Other header dwords are not decoded (UNCONFIRMED).

## Worked example

Header dwords of the L1_DC entry (entry 1 of `L1_DC.MIX`, 297,542 bytes), and two consistency checks re-run on 2026-11-18:

| Field | L1_DC | L7_DH | L20_BB |
|---|---:|---:|---:|
| +0x00 | 18 | 18 | 18 |
| vertices: offset +0x04 / count +0x50 | 5300 / 2695 | 5300 / 3221 | 5300 / 2322 |
| regions: offset +0x0C / count +0x58 | 54,509 / 1,954 | 66,679 / 2,014 | 47,055 / 1,853 |
| props: offset +0x14 / count +0x60 | 163,927 / 1,559 | 179,091 / 487 | 169,033 / 286 |
| props end = offset + 37 x count | **221,610** | **197,110** | **179,615** |
| controls: offset +0x18 | **221,610** | **197,110** | **179,615** |
| predicate table count +0xB8 | 255 | 255 | 255 |

The prop table ends exactly where the control table starts in all three levels, which fixes the 37-byte prop row; every level has 255 predicates. CONFIRMED.

## Open

[Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md) (opcodes and record kinds), [Q16](../OPEN_QUESTIONS.md) (geometry details).
