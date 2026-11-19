# L20_BB script records

**CONFIRMED.** `L20_BB.MIX+0xEA6896` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 3,834 commands in 1,204 groups. 1,200 groups have at least one direct event reference. The four placement tables supply 537 rows and the region table supplies 120 descriptor rows. Their lists contain 2,069 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L20_BB`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 58 | `0xECD51F` | `0x5A344` | CONFIRMED |
| 2 | 38 | `0xECD461` | `0xB8BA0` | CONFIRMED |
| 4 | 18 | `0xECD4BF` | `0xADD36` | CONFIRMED |
| 5 | 52 | `0xECE027` | `0xAD8E0` | CONFIRMED |
| 6 | 697 | `0xECD44B` | `0xADDE0` | CONFIRMED |
| 8 | 29 | `0xECDD43` | `0xAE510` | CONFIRMED |
| 9 | 89 | `0xECDF6B` | `0xAE2C8` | CONFIRMED |
| 11 | 173 | `0xED64DA` | `0xF2FC0` | CONFIRMED |
| 12 | 104 | `0xED65DA` | `0xF2D87` | CONFIRMED |
| 19 | 811 | `0xECD451` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 1 / kind 11 `0xED64DA` | `0xED556C` | move floor, delta 20, rate operand 4 | `0x64DDC` |
| 0:462 | descriptor 2 / kind 12 `0xED661C` / pred. 12 | `0xED5740` | stop for kind-2 timer 0 (argument 0) | `0xB494B` |
| 0:462 | descriptor 2 / kind 12 `0xED661C` / pred. 12 | `0xED5766` | set 3 at local byte 4 | `0x64887` |
| 0:3786 | descriptor 88 / kind 12 `0xED6E4A` | `0xED6436` | request level 19, arrival 2 | `0xD8797` |
| 1:24 | prop 2 / kind 2 `0xECD461` | `0xEC5F07` | add 1 to object state +0x25 (0–255) | `0xB5A76` |
| 1:304 | prop 15 / kind 6 `0xECD509` / pred. 2 | `0xEC6019` | add 1 at shared byte 0 (clamped to 0–10) | `0x64B1C` |
| 1:7410 | prop 241 / kind 5 `0xECE269` | `0xEC7BE1` | grant player item definition 0, instance byte +4 = 1 | `0xD78D9` |
| 1:28700 | actor 70 / kind 6 `0xECF4CB` / pred. 210 | `0xECCF1F` | set secondary action pair to 1 for admitted actor | `0xA639A` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×145, 2 ×305, 3 ×3, 5 ×155, 6 ×4, 7 ×44, 8 ×733, 9 ×185, 13 ×341, 15 ×70, 22 ×54, 210 ×1.
