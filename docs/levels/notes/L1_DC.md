# L1_DC script records

**CONFIRMED.** `L1_DC.MIX+0x6C370A` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 1,982 commands in 666 groups. 641 groups have at least one direct event reference. The four placement tables supply 1,870 rows and the region table supplies 173 descriptor rows. Their lists contain 1,138 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L1_DC`; they are not part of the repository.
- [Worked excerpt: the first 20 groups with a direct trigger](L1_DC.excerpt.md)
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 141 | `0x6E96C7` | `0x5A344` | CONFIRMED |
| 2 | 19 | `0x6E9799` | `0xB8BA0` | CONFIRMED |
| 3 | 49 | `0x6E97D9` | `0xAD7F4` | CONFIRMED |
| 4 | 95 | `0x6E96AF` | `0xADD36` | CONFIRMED |
| 5 | 44 | `0x6E9E69` | `0xAD8E0` | CONFIRMED |
| 6 | 229 | `0x6E96BB` | `0xADDE0` | CONFIRMED |
| 8 | 6 | `0x6E97CF` | `0xAE510` | CONFIRMED |
| 9 | 85 | `0x6E97B3` | `0xAE2C8` | CONFIRMED |
| 10 | 21 | `0x6EAD39` | `0xAE608` | CONFIRMED |
| 11 | 1 | `0x6FDA2B` | `0xF2FC0` | CONFIRMED |
| 12 | 97 | `0x6FDA33` | `0xF2D87` | CONFIRMED |
| 19 | 351 | `0x6E96C1` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 2 / kind 11 `0x6FDA2B` | `0x6FD0DD` | set 1 at local byte 7 | `0x64887` |
| 0:184 | descriptor 41 / kind 12 `0x6FDAB5` / pred. 12 | `0x6FD19B` | set object state +0x25 to 1 | `0xB5A3C` |
| 0:296 | descriptor 44 / kind 12 `0x6FDAE9` / pred. 89 | `0x6FD211` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 0:1194 | descriptor 122 / kind 12 `0x6FDC4B` / pred. 179 | `0x6FD59F` | request level 3, arrival 1 | `0xD8797` |
| 0:2328 | descriptor 167 / kind 12 `0x6FDE3D` / pred. 48 | `0x6FDA11` | grant actor 38 item definition 4, instance byte +4 = 1 | `0xA6334` |
| 1:264 | prop 83 / kind 3 `0x6E97D9` | `0x6E5E7B` | move floor, target height -290, rate operand 5 | `0x64DDC` |
| 1:2064 | prop 152 / kind 6 `0x6E9AFD` / pred. 200 | `0x6E65C3` | set behavior pair to 10 for admitted actor | `0xA6365` |
| 1:11004 | control 136 / kind 9 `0x6EAF73` / pred. 60 | `0x6E8869` | add -1 at shared byte 0 (saturating at 0–255) (runtime ceilings 10/2/2 for the three capped indexes) | `0x64B1C` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×65, 2 ×131, 5 ×218, 6 ×57, 7 ×117, 8 ×63, 9 ×67, 12 ×3, 13 ×84, 15 ×5, 18 ×24, 24 ×1, 197 ×3, 208 ×6, 210 ×3.
