# L3_DH script records

**CONFIRMED.** `L3_DH.MIX+0x573C18` is the base for the geometry header. Both streams (`+0x3C` and `+0x44` header fields) frame 1,793 commands in 537 groups. 537 groups have at least one direct event reference. The four placement tables supply 702 rows and the region table supplies 115 descriptor rows. Their lists contain 864 distinct event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.

- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT --out <folder outside the repository> L3_DH`; they are not part of the repository.
- [Schema, commands and matcher evidence](README.md)

## Matchers in this archive

| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |
|---:|---:|---:|---|---|
| 1 | 115 | `0x5939D6` | `0x5A344` | CONFIRMED |
| 2 | 27 | `0x593B36` | `0xB8BA0` | CONFIRMED |
| 3 | 53 | `0x594064` | `0xAD7F4` | CONFIRMED |
| 4 | 103 | `0x593FA0` | `0xADD36` | CONFIRMED |
| 5 | 7 | `0x593C64` | `0xAD8E0` | CONFIRMED |
| 6 | 126 | `0x593A92` | `0xADDE0` | CONFIRMED |
| 8 | 55 | `0x593C44` | `0xAE510` | CONFIRMED |
| 9 | 75 | `0x593A84` | `0xAE2C8` | CONFIRMED |
| 11 | 6 | `0x59CBA8` | `0xF2FC0` | CONFIRMED |
| 12 | 85 | `0x59C8B0` | `0xF2D87` | CONFIRMED |
| 19 | 212 | `0x593A8E` | `0x66AB0` | CONFIRMED |

## Traced command sites

| Group | First linked event examined | Command MIX offset | Effect | Code VA |
|---|---|---|---|---|
| 0:60 | descriptor 8 / kind 12 `0x59C8C4` / pred. 62 | `0x59C19A` | set 1 at local byte 25 | `0x64887` |
| 0:78 | descriptor 8 / kind 12 `0x59C8D0` / pred. 99 | `0x59C1A6` | start for kind-2 timer 0 (argument 0) | `0xB485C` |
| 0:738 | descriptor 34 / kind 12 `0x59CA3C` | `0x59C454` | set object state +0x25 to 5 | `0xB5A3C` |
| 0:1364 | descriptor 75 / kind 12 `0x59CBB2` / pred. 45 | `0x59C6B2` | add -1 at shared byte 0 (clamped to 0–10) | `0x64B1C` |
| 0:1834 | descriptor 111 / kind 11 `0x59CC58` | `0x59C888` | set region bits 0x3 at +0x1C | `0x64D5F` |
| 1:1498 | prop 93 / kind 5 `0x593C64` | `0x590C6E` | grant player item definition 94, instance byte +4 = 4 | `0xD78D9` |
| 1:7306 | control 82 / kind 6 `0x5947F6` / pred. 209 | `0x592324` | request level 4, arrival 1 | `0xD8797` |
| 1:7596 | control 92 / kind 4 `0x594864` / pred. 206 | `0x592460` | set behavior pair to 4 for admitted actor | `0xA6365` |

The table shows **CONFIRMED** static effects at admitted command sites. For a row with a predicate, evaluate the trailer before treating the event as eligible. Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).

## Open behavior

**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands below any unresolved effects. An empty direct-trigger list leaves the producer open. For virtual calls, resolve the target placement’s runtime class and its table slot, then trace that implementation. For unresolved event IDs, trace callers to the matcher addresses listed above.

Opcode sites with effects still open: 1 ×77, 2 ×86, 5 ×182, 6 ×282, 7 ×40, 8 ×40, 9 ×87, 12 ×5, 13 ×27, 197 ×7, 210 ×1.
