# L4_HJ script records

**CONFIRMED.** `L4_HJ.MIX+0xBD5AEA` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 6,047 commands in 1,874 groups. 1,873 groups have at least one direct event reference. The four placement tables supply 6,670 rows and the region table supplies 368 descriptor rows. Their lists contain 2,739 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L4_HJ`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 57 | `0xC2B21C` | `0x5A344` | CONFIRMED |
| 2 | 159 | `0xC2B204` | `0xB8BA0` | CONFIRMED |
| 3 | 45 | `0xC2C484` | `0xAD7F4` | CONFIRMED |
| 4 | 108 | `0xC2B2C8` | `0xADD36` | CONFIRMED |
| 5 | 114 | `0xC2B4E0` | `0xAD8E0` | CONFIRMED |
| 6 | 355 | `0xC2B1FA` | `0xADDE0` | CONFIRMED |
| 8 | 13 | `0xC2B80A` | `0xAE510` | CONFIRMED |
| 9 | 133 | `0xC2B2BC` | `0xAE2C8` | CONFIRMED |
| 10 | 2 | `0xC2D93A` | `0xAE608` | CONFIRMED |
| 11 | 79 | `0xC703D2` | `0xF2FC0` | CONFIRMED |
| 12 | 866 | `0xC70372` | `0xF2D87` | CONFIRMED |
| 19 | 808 | `0xC2B200` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 0 / kind 12 `0xC70372` | `0xC6B702` | randomize up to 1 at local byte 38 | `0x64906` |
| 0:6 | descriptor 4 / kind 12 `0xC7037C` / pred. 89 | `0xC6B744` | set object state +0x25 to 1 | `0xB5A3C` |
| 0:204 | descriptor 14 / kind 11 `0xC703D2` | `0xC6B7CE` | update region bytes +0x20/+0x27 from 2 | `0xF44CC` |
| 0:798 | descriptor 28 / kind 12 `0xC70546` | `0xC6BA20` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 0:3926 | descriptor 101 / kind 12 `0xC70BC4` / pred. 152 | `0xC6C65E` | add 2 at shared byte 0 (saturating at 0–255) (runtime ceilings 10/2/2 for the three capped indexes) | `0x64B1C` |
| 0:4846 | descriptor 142 / kind 12 `0xC70E70` | `0xC6C9F0` | request level 5, arrival 2 | `0xD8797` |
| 1:140 | prop 65 / kind 6 `0xC2B2DE` / pred. 206 | `0xC23896` | grant player item definition 29, instance byte +4 = 4 | `0xD78D9` |
| 1:11736 | prop 552 / kind 6 `0xC2C46E` / pred. 219 | `0xC265FE` | set behavior pair to 7 for admitted actor | `0xA6365` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×87, 2 ×814, 5 ×345, 6 ×4, 7 ×214, 8 ×482, 9 ×278, 12 ×18, 13 ×67, 15 ×24, 18 ×72, 197 ×18, 208 ×8, 210 ×11.
