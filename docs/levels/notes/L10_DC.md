# L10_DC script records

**CONFIRMED.** `L10_DC.MIX+0xC2D829` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 3,106 commands in 1,193 groups. 1,192 groups have at least one direct event reference. The four placement tables supply 1,028 rows and the region table supplies 893 descriptor rows. Their lists contain 1,853 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L10_DC`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 119 | `0xC7F999` | `0x5A344` | CONFIRMED |
| 2 | 41 | `0xC7F987` | `0xB8BA0` | CONFIRMED |
| 3 | 141 | `0xC802AD` | `0xAD7F4` | CONFIRMED |
| 4 | 227 | `0xC7FB9D` | `0xADD36` | CONFIRMED |
| 5 | 7 | `0xC80205` | `0xAD8E0` | CONFIRMED |
| 6 | 361 | `0xC7F991` | `0xADDE0` | CONFIRMED |
| 7 | 11 | `0xC82AFD` | `0xAE134` | CONFIRMED |
| 8 | 4 | `0xC82CC5` | `0xAE510` | CONFIRMED |
| 9 | 284 | `0xC80107` | `0xAE2C8` | CONFIRMED |
| 11 | 2 | `0xC8E2E4` | `0xF2FC0` | CONFIRMED |
| 12 | 115 | `0xC8E226` | `0xF2D87` | CONFIRMED |
| 19 | 541 | `0xC7FAC1` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:0 | descriptor 0 / kind 12 `0xC8E226` | `0xC8D96E` | request level 8, arrival 2 | `0xD8797` |
| 0:24 | descriptor 0 / kind 12 `0xC8E236` / pred. 89 | `0xC8D9C2` | set 2 at local byte 11 | `0x64887` |
| 0:156 | descriptor 51 / kind 12 `0xC8E290` | `0xC8DA16` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 0:514 | descriptor 733 / kind 12 `0xC8E3E6` | `0xC8DB70` | move floor, target height 0, rate operand 40 | `0x64DDC` |
| 0:586 | descriptor 770 / kind 12 `0xC8E40E` / pred. 108 | `0xC8DBDC` | set object state +0x25 to 0 | `0xB5A3C` |
| 0:874 | descriptor 770 / kind 12 `0xC8E43E` / pred. 107 | `0xC8DCDE` | set 2 at shared byte 34 | `0x64A8C` |
| 1:448 | prop 83 / kind 4 `0xC7FB9D` / pred. 206 | `0xC79AAF` | grant player item definition 118, instance byte +4 = 4 | `0xD78D9` |
| 1:23794 | actor 28 / kind 6 `0xC82A45` / pred. 207 | `0xC7F5D9` | set behavior pair to 4 for admitted actor | `0xA6365` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×22, 2 ×75, 5 ×474, 6 ×2, 7 ×225, 8 ×155, 9 ×62, 12 ×1, 13 ×71, 15 ×3, 210 ×1.
