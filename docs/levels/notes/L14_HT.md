# L14_HT script records

**CONFIRMED.** `L14_HT.MIX+0xAE0C08` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 3,222 commands in 1,062 groups. 1,061 groups have at least one direct event reference. The four placement tables supply 780 rows and the region table supplies 254 descriptor rows. Their lists contain 1,673 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L14_HT`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 133 | `0xB316EA` | `0x5A344` | CONFIRMED |
| 2 | 39 | `0xB3187A` | `0xB8BA0` | CONFIRMED |
| 3 | 55 | `0xB318B0` | `0xAD7F4` | CONFIRMED |
| 4 | 68 | `0xB31702` | `0xADD36` | CONFIRMED |
| 5 | 25 | `0xB321C0` | `0xAD8E0` | CONFIRMED |
| 6 | 563 | `0xB316C6` | `0xADDE0` | CONFIRMED |
| 7 | 24 | `0xB32562` | `0xAE134` | CONFIRMED |
| 8 | 1 | `0xB3343E` | `0xAE510` | CONFIRMED |
| 9 | 26 | `0xB329AE` | `0xAE2C8` | CONFIRMED |
| 10 | 57 | `0xB324EA` | `0xAE608` | CONFIRMED |
| 11 | 21 | `0xB3D54C` | `0xF2FC0` | CONFIRMED |
| 12 | 178 | `0xB3D4DA` | `0xF2D87` | CONFIRMED |
| 15 | 4 | `0xB3D6B8` | `0xF37C8` | CONFIRMED |
| 19 | 479 | `0xB316D4` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 15 / kind 12 `0xB3D4DA` | `0xB3C5C6` | move floor, target height 108, rate operand 5 | `0x64DDC` |
| 0:102 | descriptor 16 / kind 12 `0xB3D4F4` | `0xB3C62C` | change flags for kind-2 timer 0 (argument 0) | `0xB482C` |
| 0:1122 | descriptor 22 / kind 12 `0xB3D51A` / pred. 10 | `0xB3CA58` | set 1 at local byte 3 | `0x64887` |
| 0:1462 | descriptor 29 / kind 12 `0xB3D55E` | `0xB3CB76` | request level 8, arrival 3 | `0xD8797` |
| 0:2906 | descriptor 182 / kind 12 `0xB3D9A8` | `0xB3D128` | set 0 at shared byte 36 (runtime ceilings 10/2/2 for the three capped indexes) | `0x64A8C` |
| 1:0 | prop 0 / kind 6 `0xB316C6` | `0xB2B84C` | set object state +0x25 to 50 | `0xB5A3C` |
| 1:470 | prop 82 / kind 4 `0xB31894` / pred. 207 | `0xB2BA28` | grant player item definition 109, instance byte +4 = 4 | `0xD78D9` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×59, 2 ×116, 5 ×302, 6 ×65, 7 ×218, 8 ×28, 9 ×152, 12 ×2, 13 ×133, 15 ×54, 18 ×24, 24 ×7, 197 ×3, 208 ×26, 210 ×5.
