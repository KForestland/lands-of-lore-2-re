# L8_SJ script records

**CONFIRMED.** `L8_SJ.MIX+0xC899A1` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 2,708 commands in 877 groups. 876 groups have at least one direct event reference. The four placement tables supply 2,032 rows and the region table supplies 491 descriptor rows. Their lists contain 1,446 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L8_SJ`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 44 | `0xCD6D84` | `0x5A344` | CONFIRMED |
| 2 | 34 | `0xCD6B58` | `0xB8BA0` | CONFIRMED |
| 3 | 83 | `0xCD6EDA` | `0xAD7F4` | CONFIRMED |
| 4 | 72 | `0xCD6B66` | `0xADD36` | CONFIRMED |
| 5 | 30 | `0xCD6ECA` | `0xAD8E0` | CONFIRMED |
| 6 | 463 | `0xCD6B30` | `0xADDE0` | CONFIRMED |
| 7 | 4 | `0xCD79E8` | `0xAE134` | CONFIRMED |
| 8 | 21 | `0xCD81F4` | `0xAE510` | CONFIRMED |
| 9 | 34 | `0xCD6BD6` | `0xAE2C8` | CONFIRMED |
| 10 | 1 | `0xCD849A` | `0xAE608` | CONFIRMED |
| 11 | 2 | `0xCECD6F` | `0xF2FC0` | CONFIRMED |
| 12 | 132 | `0xCECC6F` | `0xF2D87` | CONFIRMED |
| 19 | 526 | `0xCD6B36` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 3 / kind 12 `0xCECC6F` | `0xCEC3D5` | stop for kind-2 timer 0 (argument 0) | `0xB494B` |
| 0:70 | descriptor 16 / kind 12 `0xCECC9B` / pred. 84 | `0xCEC41B` | set 2 at local byte 3 | `0x64887` |
| 0:100 | descriptor 16 / kind 12 `0xCECCA7` / pred. 82 | `0xCEC439` | set object state +0x25 to 1 | `0xB5A3C` |
| 0:148 | descriptor 21 / kind 12 `0xCECCC1` | `0xCEC469` | activate the region-indexed automap marker if present | `0x64DB7` |
| 0:564 | descriptor 79 / kind 12 `0xCECDE7` | `0xCEC60F` | request level 10, arrival 1 | `0xD8797` |
| 0:1950 | descriptor 388 / kind 12 `0xCED0F7` / pred. 176 | `0xCECB6D` | set secondary action pair to 9 for admitted actor | `0xA639A` |
| 1:186 | prop 0 / kind 4 `0xCD6B66` / pred. 189 | `0xCD16A2` | add 2 at shared byte 12 (clamped to 0–2) | `0x64B1C` |
| 1:1780 | prop 2 / kind 6 `0xCD6CFA` / pred. 206 | `0xCD1CEA` | grant player item definition 142, instance byte +4 = 4 | `0xD78D9` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×15, 2 ×148, 3 ×5, 5 ×148, 7 ×23, 8 ×512, 9 ×61, 12 ×19, 13 ×224, 210 ×1.
