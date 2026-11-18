# L16_CA script records

**CONFIRMED.** `L16_CA.MIX+0x1120870` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 6,983 commands in 2,136 groups. 2,134 groups have at least one direct event reference. The four placement tables supply 1,255 rows and the region table supplies 373 descriptor rows. Their lists contain 3,719 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L16_CA`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 76 | `0x11D8320` | `0x5A344` | CONFIRMED |
| 2 | 107 | `0x11D7EE0` | `0xB8BA0` | CONFIRMED |
| 3 | 21 | `0x11D98CC` | `0xAD7F4` | CONFIRMED |
| 4 | 426 | `0x11D7EF6` | `0xADD36` | CONFIRMED |
| 5 | 18 | `0x11DB8AA` | `0xAD8E0` | CONFIRMED |
| 6 | 1,204 | `0x11D7EF0` | `0xADDE0` | CONFIRMED |
| 8 | 5 | `0x11D96B2` | `0xAE510` | CONFIRMED |
| 9 | 84 | `0x11D7F04` | `0xAE2C8` | CONFIRMED |
| 10 | 12 | `0x11DB9DC` | `0xAE608` | CONFIRMED |
| 11 | 131 | `0x11EBAD3` | `0xF2FC0` | CONFIRMED |
| 12 | 128 | `0x11EB93D` | `0xF2D87` | CONFIRMED |
| 19 | 1,507 | `0x11D7EEA` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 1 / kind 12 `0x11EB93D` / pred. 19 | `0x11E9855` | set 1 at shared byte 51 (runtime ceilings 10/2/2 for the three capped indexes) | `0x64A8C` |
| 0:0 | descriptor 1 / kind 12 `0x11EB93D` / pred. 19 | `0x11E985B` | set 1 at local byte 12 | `0x64887` |
| 0:0 | descriptor 1 / kind 12 `0x11EB93D` / pred. 19 | `0x11E986D` | stop for kind-2 timer 0 (argument 0) | `0xB494B` |
| 0:1714 | descriptor 65 / kind 11 `0x11EBAD3` | `0x11E9F07` | move floor, target height 0, rate operand 8 | `0x64DDC` |
| 0:7268 | descriptor 330 / kind 12 `0x11EC273` | `0x11EB4B3` | request level 17, arrival 3 | `0xD8797` |
| 1:0 | prop 0 / kind 2 `0x11D7EE0` / pred. 206 | `0x11CA6E8` | set object state +0x25 to 1 | `0xB5A3C` |
| 1:744 | prop 6 / kind 6 `0x11D8082` / pred. 206 | `0x11CA9DE` | grant player item definition 111, instance byte +4 = 4 | `0xD78D9` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×331, 2 ×153, 5 ×1112, 6 ×9, 7 ×687, 8 ×69, 9 ×205, 12 ×1, 13 ×119, 15 ×93, 18 ×77, 197 ×4, 208 ×9, 210 ×5.
