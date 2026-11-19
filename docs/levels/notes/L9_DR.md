# L9_DR script records

**CONFIRMED.** `L9_DR.MIX+0x15AAD42` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 2,938 commands in 920 groups. 919 groups have at least one direct event reference. The four placement tables supply 3,435 rows and the region table supplies 600 descriptor rows. Their lists contain 1,470 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L9_DR`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 250 | `0x162A30E` | `0x5A344` | CONFIRMED |
| 2 | 15 | `0x162A21C` | `0xB8BA0` | CONFIRMED |
| 3 | 114 | `0x162A8AA` | `0xAD7F4` | CONFIRMED |
| 4 | 70 | `0x162A25E` | `0xADD36` | CONFIRMED |
| 5 | 41 | `0x162A9C4` | `0xAD8E0` | CONFIRMED |
| 6 | 215 | `0x162A232` | `0xADDE0` | CONFIRMED |
| 7 | 8 | `0x162C7B8` | `0xAE134` | CONFIRMED |
| 8 | 4 | `0x162C608` | `0xAE510` | CONFIRMED |
| 9 | 155 | `0x162A4F0` | `0xAE2C8` | CONFIRMED |
| 10 | 7 | `0x162AFD6` | `0xAE608` | CONFIRMED |
| 11 | 108 | `0x164EC0E` | `0xF2FC0` | CONFIRMED |
| 12 | 182 | `0x164EB90` | `0xF2D87` | CONFIRMED |
| 19 | 301 | `0x162A238` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 5 / kind 12 `0x164EB90` | `0x164CF62` | stop for kind-2 timer 0 (argument 0) | `0xB494B` |
| 0:20 | descriptor 7 / kind 12 `0x164EB9A` | `0x164CF70` | set object state +0x25 to 1 | `0xB5A3C` |
| 0:128 | descriptor 31 / kind 12 `0x164EBEC` | `0x164CFDC` | activate the region-indexed automap marker if present | `0x64DB7` |
| 0:248 | descriptor 43 / kind 11 `0x164EC0E` / pred. 48 | `0x164D05A` | set 1 at local byte 18 | `0x64887` |
| 0:548 | descriptor 181 / kind 12 `0x164EC4E` | `0x164D180` | request level 10, arrival 2 | `0xD8797` |
| 0:5918 | descriptor 499 / kind 12 `0x164F3C4` / pred. 54 | `0x164E6A0` | set 1 at shared byte 16 | `0x64A8C` |
| 1:7964 | prop 1084 / kind 5 `0x162A9C4` | `0x1626F90` | grant player item definition 95, instance byte +4 = 4 | `0xD78D9` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×57, 2 ×92, 5 ×267, 6 ×24, 7 ×44, 8 ×38, 9 ×40, 12 ×9, 13 ×48, 15 ×5, 208 ×6, 210 ×1.
