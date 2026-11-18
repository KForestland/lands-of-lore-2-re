# L5_HC script records

**CONFIRMED.** `L5_HC.MIX+0x585061` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 1,897 commands in 625 groups. 623 groups have at least one direct event reference. The four placement tables supply 1,127 rows and the region table supplies 137 descriptor rows. Their lists contain 869 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L5_HC`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 20 | `0x5A12FB` | `0x5A344` | CONFIRMED |
| 2 | 26 | `0x5A12A7` | `0xB8BA0` | CONFIRMED |
| 3 | 64 | `0x5A181F` | `0xAD7F4` | CONFIRMED |
| 4 | 24 | `0x5A1733` | `0xADD36` | CONFIRMED |
| 5 | 18 | `0x5A14BD` | `0xAD8E0` | CONFIRMED |
| 6 | 237 | `0x5A12B1` | `0xADDE0` | CONFIRMED |
| 7 | 2 | `0x5A1AB7` | `0xAE134` | CONFIRMED |
| 8 | 3 | `0x5A1415` | `0xAE510` | CONFIRMED |
| 9 | 37 | `0x5A1407` | `0xAE2C8` | CONFIRMED |
| 10 | 5 | `0x5A1D43` | `0xAE608` | CONFIRMED |
| 11 | 30 | `0x5AEC5B` | `0xF2FC0` | CONFIRMED |
| 12 | 180 | `0x5AEB85` | `0xF2D87` | CONFIRMED |
| 19 | 223 | `0x5A12B7` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 0 / kind 12 `0x5AEB85` / pred. 17 | `0x5AD0DD` | reload for kind-2 timer 0 (argument 0) | `0xB49BA` |
| 0:0 | descriptor 0 / kind 12 `0x5AEB85` / pred. 17 | `0x5AD0E5` | set 1 at local byte 3 | `0x64887` |
| 0:122 | descriptor 19 / kind 12 `0x5AEBB9` | `0x5AD139` | set 0 at shared byte 36 | `0x64A8C` |
| 0:162 | descriptor 27 / kind 12 `0x5AEBE1` / pred. 32 | `0x5AD15B` | set object state +0x25 to 2 | `0xB5A3C` |
| 0:222 | descriptor 28 / kind 11 `0x5AEC5B` | `0x5AD1A7` | move ceiling, target height -185, rate operand 20 | `0x64DDC` |
| 0:860 | descriptor 43 / kind 12 `0x5AECED` | `0x5AD415` | request level 4, arrival 3 | `0xD8797` |
| 1:84 | prop 71 / kind 6 `0x5A130B` / pred. 184 | `0x59E95D` | grant actor 20 item definition 72, instance byte +4 = 1 | `0xA6334` |
| 1:1680 | prop 233 / kind 9 `0x5A1763` | `0x59EFF1` | set behavior pair to 7 for admitted actor | `0xA6365` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×95, 2 ×51, 5 ×113, 6 ×46, 7 ×11, 8 ×45, 9 ×52, 12 ×107, 13 ×15, 15 ×18, 197 ×102, 210 ×2.
