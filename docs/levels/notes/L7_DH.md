# L7_DH script records

**CONFIRMED.** `L7_DH.MIX+0x47CAA8` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 1,933 commands in 615 groups. 599 groups have at least one direct event reference. The four placement tables supply 1,685 rows and the region table supplies 261 descriptor rows. Their lists contain 1,010 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L7_DH`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 83 | `0x4A67D5` | `0x5A344` | CONFIRMED |
| 2 | 48 | `0x4A67C9` | `0xB8BA0` | CONFIRMED |
| 3 | 90 | `0x4A7557` | `0xAD7F4` | CONFIRMED |
| 4 | 44 | `0x4A6887` | `0xADD36` | CONFIRMED |
| 5 | 18 | `0x4A687F` | `0xAD8E0` | CONFIRMED |
| 6 | 143 | `0x4A67BD` | `0xADDE0` | CONFIRMED |
| 8 | 5 | `0x4A6B73` | `0xAE510` | CONFIRMED |
| 9 | 206 | `0x4A6995` | `0xAE2C8` | CONFIRMED |
| 10 | 3 | `0x4A848F` | `0xAE608` | CONFIRMED |
| 12 | 45 | `0x4B889C` | `0xF2D87` | CONFIRMED |
| 19 | 325 | `0x4A67C3` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:48 | descriptor 9 / kind 12 `0x4B88AE` | `0x4B8476` | set 1 at shared byte 44 | `0x64A8C` |
| 0:76 | descriptor 12 / kind 12 `0x4B88B8` / pred. 19 | `0x4B8488` | set object state +0x25 to 3 | `0xB5A3C` |
| 0:214 | descriptor 74 / kind 12 `0x4B88FA` | `0x4B850C` | move floor, target height 488, rate operand 30 | `0x64DDC` |
| 0:856 | descriptor 217 / kind 12 `0x4B89FE` | `0x4B8794` | request level 4, arrival 6 | `0xD8797` |
| 0:1066 | descriptor 246 / kind 12 `0x4B8A42` | `0x4B8866` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 1:0 | prop 0 / kind 6 `0x4A67BD` / pred. 28 | `0x4A2A03` | set 0 at local byte 10 | `0x64887` |
| 1:328 | prop 212 / kind 5 `0x4A695F` | `0x4A2B45` | grant player item definition 55, instance byte +4 = 5 | `0xD78D9` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×33, 2 ×21, 5 ×146, 6 ×44, 7 ×74, 8 ×10, 9 ×149, 13 ×82, 15 ×105, 197 ×2, 210 ×1.
