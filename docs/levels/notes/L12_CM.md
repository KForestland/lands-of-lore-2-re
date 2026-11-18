# L12_CM script records

**CONFIRMED.** `L12_CM.MIX+0x922FF0` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 1,045 commands in 271 groups. 268 groups have at least one direct event reference. The four placement tables supply 696 rows and the region table supplies 238 descriptor rows. Their lists contain 441 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L12_CM`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 20 | `0x95F6B6` | `0x5A344` | CONFIRMED |
| 2 | 19 | `0x95F67E` | `0xB8BA0` | CONFIRMED |
| 4 | 31 | `0x95F654` | `0xADD36` | CONFIRMED |
| 5 | 14 | `0x95F938` | `0xAD8E0` | CONFIRMED |
| 6 | 96 | `0x95F64C` | `0xADDE0` | CONFIRMED |
| 8 | 2 | `0x95F688` | `0xAE510` | CONFIRMED |
| 9 | 25 | `0x95F756` | `0xAE2C8` | CONFIRMED |
| 11 | 12 | `0x9679B0` | `0xF2FC0` | CONFIRMED |
| 12 | 72 | `0x967982` | `0xF2D87` | CONFIRMED |
| 19 | 150 | `0x95F65E` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 100 / kind 12 `0x967982` | `0x966FFC` | request level 8, arrival 4 | `0xD8797` |
| 0:18 | descriptor 107 / kind 12 `0x96798C` / pred. 32 | `0x967008` | stop for kind-2 timer 0 (argument 0) | `0xB494B` |
| 0:18 | descriptor 107 / kind 12 `0x96798C` / pred. 32 | `0x967010` | set 1 at local byte 11 | `0x64887` |
| 0:398 | descriptor 131 / kind 11 `0x967A68` | `0x96717E` | update region bytes +0x20/+0x27 from 4 | `0xF44CC` |
| 1:6 | prop 4 / kind 4 `0x95F654` / pred. 206 | `0x95DBAC` | set object state +0x25 to 1 | `0xB5A3C` |
| 1:140 | prop 4 / kind 4 `0x95F694` / pred. 209 | `0x95DC2A` | grant player item definition 81, instance byte +4 = 1 | `0xD78D9` |
| 1:4336 | actor 30 / kind 9 `0x95FB36` / pred. 30 | `0x95EC98` | add -1 at shared byte 0 (saturating at 0–255) (runtime ceilings 10/2/2 for the three capped indexes) | `0x64B1C` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×8, 2 ×98, 5 ×10, 7 ×29, 8 ×136, 9 ×34, 13 ×79, 18 ×37, 197 ×4, 208 ×3, 210 ×11.
