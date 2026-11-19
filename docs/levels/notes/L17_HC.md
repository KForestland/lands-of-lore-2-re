# L17_HC script records

**CONFIRMED.** `L17_HC.MIX+0x474278` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 655 commands in 234 groups. 234 groups have at least one direct event reference. The four placement tables supply 496 rows and the region table supplies 150 descriptor rows. Their lists contain 396 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L17_HC`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 45 | `0x49079C` | `0x5A344` | CONFIRMED |
| 2 | 14 | `0x49070A` | `0xB8BA0` | CONFIRMED |
| 4 | 13 | `0x490876` | `0xADD36` | CONFIRMED |
| 5 | 3 | `0x490794` | `0xAD8E0` | CONFIRMED |
| 6 | 93 | `0x490704` | `0xADDE0` | CONFIRMED |
| 9 | 32 | `0x490B58` | `0xAE2C8` | CONFIRMED |
| 11 | 58 | `0x4967A5` | `0xF2FC0` | CONFIRMED |
| 12 | 21 | `0x496977` | `0xF2D87` | CONFIRMED |
| 19 | 117 | `0x490852` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 8 / kind 11 `0x4967A5` | `0x496137` | move ceiling, target height 150, rate operand 8 | `0x64DDC` |
| 0:1632 | descriptor 144 / kind 12 `0x496A11` | `0x496791` | request level 19, arrival 1 | `0xD8797` |
| 1:0 | prop 0 / kind 6 `0x490704` | `0x48F60E` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 1:478 | prop 71 / kind 6 `0x490862` / pred. 206 | `0x48F7E6` | set object state +0x25 to 1 | `0xB5A3C` |
| 1:514 | prop 71 / kind 4 `0x490876` / pred. 208 | `0x48F81A` | grant player item definition 122, instance byte +4 = 4 | `0xD78D9` |
| 1:3422 | prop 307 / kind 9 `0x490EDA` / pred. 206 | `0x49036C` | add 2 at local byte 0 (clamped to 0–255) | `0x648AF` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×2, 2 ×11, 3 ×4, 5 ×79, 6 ×4, 7 ×70, 9 ×42, 13 ×31, 210 ×1.
