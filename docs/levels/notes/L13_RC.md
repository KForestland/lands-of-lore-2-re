# L13_RC script records

**CONFIRMED.** `L13_RC.MIX+0x66B6D3` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 1,661 commands in 487 groups. 487 groups have at least one direct event reference. The four placement tables supply 664 rows and the region table supplies 147 descriptor rows. Their lists contain 823 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L13_RC`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 93 | `0x6886DF` | `0x5A344` | CONFIRMED |
| 2 | 20 | `0x688893` | `0xB8BA0` | CONFIRMED |
| 4 | 39 | `0x68892B` | `0xADD36` | CONFIRMED |
| 5 | 6 | `0x689185` | `0xAD8E0` | CONFIRMED |
| 6 | 258 | `0x68887D` | `0xADDE0` | CONFIRMED |
| 8 | 1 | `0x688977` | `0xAE510` | CONFIRMED |
| 9 | 65 | `0x68886F` | `0xAE2C8` | CONFIRMED |
| 11 | 13 | `0x6922E4` | `0xF2FC0` | CONFIRMED |
| 12 | 71 | `0x6922A0` | `0xF2D87` | CONFIRMED |
| 15 | 14 | `0x692366` | `0xF37C8` | CONFIRMED |
| 19 | 243 | `0x688879` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:300 | descriptor 18 / kind 11 `0x6922E4` | `0x691AE4` | update region bytes +0x20/+0x27 from 27 | `0xF44CC` |
| 0:572 | descriptor 25 / kind 12 `0x69231E` | `0x691BE2` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 0:706 | descriptor 38 / kind 12 `0x69235C` | `0x691C62` | request level 12, arrival 2 | `0xD8797` |
| 1:0 | prop 151 / kind 9 `0x68886F` / pred. 206 | `0x685B85` | set object state +0x25 to 1 | `0xB5A3C` |
| 1:36 | prop 151 / kind 6 `0x688887` / pred. 208 | `0x685BAF` | set 1 at local byte 5 | `0x64887` |
| 1:296 | prop 174 / kind 4 `0x68892B` / pred. 207 | `0x685CBF` | grant player item definition 71, instance byte +4 = 4 | `0xD78D9` |
| 1:6406 | prop 326 / kind 4 `0x689467` / pred. 206 | `0x6874B5` | set 1 at shared byte 15 | `0x64A8C` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×51, 2 ×39, 5 ×179, 6 ×112, 7 ×192, 8 ×43, 9 ×75, 13 ×51, 15 ×20, 210 ×3.
