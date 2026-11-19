# L19_BC script records

**CONFIRMED.** `L19_BC.MIX+0x5ADE2D` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 2,790 commands in 496 groups. 496 groups have at least one direct event reference. The four placement tables supply 569 rows and the region table supplies 222 descriptor rows. Their lists contain 2,388 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L19_BC`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 115 | `0x5DEB75` | `0x5A344` | CONFIRMED |
| 2 | 10 | `0x5DED4B` | `0xB8BA0` | CONFIRMED |
| 4 | 44 | `0x5DED93` | `0xADD36` | CONFIRMED |
| 5 | 6 | `0x5DEE01` | `0xAD8E0` | CONFIRMED |
| 6 | 113 | `0x5DEB51` | `0xADDE0` | CONFIRMED |
| 9 | 9 | `0x5DEDD9` | `0xAE2C8` | CONFIRMED |
| 10 | 2 | `0x5DF3E5` | `0xAE608` | CONFIRMED |
| 11 | 64 | `0x5E940C` | `0xF2FC0` | CONFIRMED |
| 12 | 965 | `0x5E9402` | `0xF2D87` | CONFIRMED |
| 19 | 1,060 | `0x5DEB57` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 4 / kind 12 `0x5E9402` | `0x5E564C` | request level 17, arrival 2 | `0xD8797` |
| 0:6 | descriptor 9 / kind 11 `0x5E940C` | `0x5E5652` | update region bytes +0x20/+0x27 from 14 | `0xF44CC` |
| 0:486 | descriptor 146 / kind 12 `0x5E95F4` / pred. 2 | `0x5E5840` | set 1 at local byte 1 | `0x64887` |
| 0:486 | descriptor 146 / kind 12 `0x5E95F4` / pred. 2 | `0x5E5846` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 1:0 | prop 2 / kind 6 `0x5DEB51` / pred. 206 | `0x5DC999` | set object state +0x25 to 1 | `0xB5A3C` |
| 1:1500 | prop 78 / kind 6 `0x5DEDE3` / pred. 211 | `0x5DCF75` | add -1 at shared byte 0 (clamped to 0–10) | `0x64B1C` |
| 1:1566 | prop 78 / kind 6 `0x5DEDF7` / pred. 226 | `0x5DCFB7` | grant player item definition 69, instance byte +4 = 0 | `0xD78D9` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×119, 2 ×19, 5 ×22, 7 ×2, 8 ×36, 9 ×28, 13 ×7, 15 ×364, 210 ×1.
