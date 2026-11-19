# Progression

Made by `tools/lol2_progression.py` from the level-transition commands in the 15 level archives. One row is one command whose first five bytes are `02 01 00 00 1c`. Byte 5 stores the destination level in the low 5 bits and the destination entry in the high 3 bits. The event column is the one object or region record whose list names that command's group ([level sheets](levels/README.md)), with the fields its matcher reads ([record kinds](lol2-script-events.md#event-records)). The slots column is the kind-19 predicate on that record, from the 5-byte predicate table ([predicates](lol2-script-events.md), [exit census](lol2-shared-predicates.md#exit-predicate-census)). `shared N` is byte N of the plot array at `[0x26E58]`. `local N` is byte N of the level array at `[0x26E54]`. `object+0x25` is the byte at `[0xB7D80]+0x25`. A type-4 operand is another row of the same table. `none` means that record has no predicate trailer. Slot numbers are table indexes, not names.

72 exit commands, 24 with a predicate. Shared slots named on those rows: 52 (2). Local slots named on those rows: 2 (9), 11 (1), 13 (1), 22 (1), 55 (8). Levels with no exit command: none. Levels no exit command leads to: L1_DC.

Locked doors are not on this page. It lists level-transition commands only.

**CONFIRMED.** Every matcher an exit row uses runs all matching records in list order, not only the first: the region walker `0xF2D2C` and the kind 5, 6 and 8 matchers `0xAD8E0`, `0xADDE0` and `0xAE510` advance to the next record after each run (back edges `0xF2FAD`, `0xAD9EF`, `0xADF26`, `0xAE5FA`). Each guard is checked after earlier matching groups in the same walk have run, and when two exits fire the later one wins, because the exit arm only stores the pending level (`0xD87AE`, `mov [0x223C8],eax`).

## What a row does not show

**UNCONFIRMED.** 8 rows hang on an object record, not on a region record. Such a record runs only when another command or the engine sends that event to that object or starts that timer, so `none` on those rows does not mean the exit is open. The senders are not traced here. To settle it, list for each of those objects the stored commands that send to it (opcode 9 property 21 sends 20 at `0xB5448`, opcode 18 sends 6 at `0xB5A0E`, opcode 14 starts a kind-2 timer through `0xB47B4`) and the callers of the kind-5 matcher `0xAD8E0` and the kind-8 matcher `0xAE510` ([record kinds](lol2-script-events.md#event-records)).

**UNCONFIRMED.** 1 region row uses region event 4 (L4_HJ region 3205). The player's region path sends events 2 and 3; the sender of event 4 is not traced. To settle it, list the callers of the region walker `0xF2D2C` and the event byte each passes ([region event arms](lol2-script-events.md#region-event-arms)).

`selector` marks 10 rows: rows of one record owner and one destination level that test one slot for 0 and for 1. While the slot holds 0 or 1, one of them runs whenever that record fires, so the slot picks the group or the arrival and does not close the way to that level. L4_HJ local 55: the stored writes to local 55 in the L4_HJ scripts are set 1. L19_BC shared 52: the stored writes to shared 52 in the 15 archives are set 1.

## Level to level

One row per pair of levels, from the table below. Only command bytes and their linked records are counted; whether the player can reach each record is not part of this table. The [level graph](lol2-level-graph.md#exit-graph-decoded) has the same commands by arrival entry.

| From | To | Commands | With predicate | Selector | Object record |
|---|---|---:|---:|---:|---:|
| L1_DC | L3_DH | 10 | 9 | 0 | 1 |
| L3_DH | L4_HJ | 1 | 1 | 0 | 1 |
| L4_HJ | L5_HC | 2 | 0 | 0 | 0 |
| L4_HJ | L7_DH | 1 | 0 | 0 | 0 |
| L4_HJ | L8_SJ | 8 | 8 | 8 | 0 |
| L5_HC | L4_HJ | 2 | 0 | 0 | 0 |
| L7_DH | L4_HJ | 7 | 0 | 0 | 0 |
| L8_SJ | L4_HJ | 3 | 0 | 0 | 0 |
| L8_SJ | L9_DR | 4 | 0 | 0 | 0 |
| L8_SJ | L10_DC | 1 | 0 | 0 | 0 |
| L8_SJ | L12_CM | 1 | 0 | 0 | 0 |
| L8_SJ | L14_HT | 1 | 1 | 0 | 1 |
| L9_DR | L8_SJ | 3 | 0 | 0 | 1 |
| L9_DR | L10_DC | 1 | 0 | 0 | 0 |
| L10_DC | L8_SJ | 1 | 0 | 0 | 0 |
| L10_DC | L9_DR | 1 | 1 | 0 | 0 |
| L12_CM | L8_SJ | 1 | 0 | 0 | 0 |
| L12_CM | L13_RC | 1 | 0 | 0 | 1 |
| L13_RC | L12_CM | 1 | 0 | 0 | 0 |
| L14_HT | L8_SJ | 2 | 0 | 0 | 0 |
| L14_HT | L16_CA | 1 | 1 | 0 | 1 |
| L16_CA | L17_HC | 2 | 0 | 0 | 1 |
| L17_HC | L16_CA | 2 | 1 | 0 | 1 |
| L17_HC | L19_BC | 2 | 0 | 0 | 0 |
| L19_BC | L17_HC | 1 | 0 | 0 | 0 |
| L19_BC | L20_BB | 2 | 2 | 2 | 0 |
| L20_BB | L19_BC | 10 | 0 | 0 | 0 |

## Exit commands

| From | To | Entry | Stream | Group | Event | Slots |
|---|---|---:|---:|---:|---|---|
| <a name="level-l1_dc"></a>[L1_DC](levels/L1_DC.md) | L3_DH | 1 | 0 | 1194 | region 1190 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1246 | region 1217 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1298 | region 1218 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1350 | region 1219 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1402 | region 1220 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1454 | region 1221 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1506 | region 1222 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1558 | region 1223 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 0 | 1610 | region 1224 kind 12 event 2 | (local 2 == 5) |
| L1_DC | L3_DH | 1 | 1 | 4030 | prop:447 kind 8 match 973 | none |
| <a name="level-l3_dh"></a>[L3_DH](levels/L3_DH.md) | L4_HJ | 1 | 1 | 7306 | control:82 kind 6 value 1 | (object+0x25 == 3) |
| <a name="level-l4_hj"></a>[L4_HJ](levels/L4_HJ.md) | L5_HC | 1 | 0 | 5208 | region 2809 kind 12 event 2 | none |
| L4_HJ | L5_HC | 2 | 0 | 4846 | region 2604 kind 12 event 2 | none |
| L4_HJ | L7_DH | 1 | 0 | 6292 | region 3205 kind 12 event 4 | none |
| L4_HJ | L8_SJ | 1 | 0 | 6100 | region 3186 kind 12 event 2 | (local 55 == 0) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6124 | region 3186 kind 12 event 2 | (local 55 == 1) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6130 | region 3187 kind 12 event 2 | (local 55 == 0) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6154 | region 3187 kind 12 event 2 | (local 55 == 1) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6160 | region 3188 kind 12 event 2 | (local 55 == 0) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6184 | region 3188 kind 12 event 2 | (local 55 == 1) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6190 | region 3189 kind 12 event 2 | (local 55 == 0) selector |
| L4_HJ | L8_SJ | 1 | 0 | 6214 | region 3189 kind 12 event 2 | (local 55 == 1) selector |
| <a name="level-l5_hc"></a>[L5_HC](levels/L5_HC.md) | L4_HJ | 3 | 0 | 860 | region 460 kind 12 event 2 | none |
| L5_HC | L4_HJ | 4 | 0 | 6400 | region 835 kind 12 event 2 | none |
| <a name="level-l7_dh"></a>[L7_DH](levels/L7_DH.md) | L4_HJ | 6 | 0 | 856 | region 1394 kind 12 event 2 | none |
| L7_DH | L4_HJ | 6 | 0 | 874 | region 1408 kind 12 event 2 | none |
| L7_DH | L4_HJ | 6 | 0 | 892 | region 1409 kind 12 event 2 | none |
| L7_DH | L4_HJ | 6 | 0 | 910 | region 1410 kind 12 event 2 | none |
| L7_DH | L4_HJ | 6 | 0 | 928 | region 1411 kind 12 event 2 | none |
| L7_DH | L4_HJ | 6 | 0 | 946 | region 1412 kind 12 event 2 | none |
| L7_DH | L4_HJ | 6 | 0 | 964 | region 1413 kind 12 event 2 | none |
| <a name="level-l8_sj"></a>[L8_SJ](levels/L8_SJ.md) | L4_HJ | 7 | 0 | 1492 | region 2352 kind 12 event 2 | none |
| L8_SJ | L4_HJ | 7 | 0 | 1498 | region 2353 kind 12 event 2 | none |
| L8_SJ | L4_HJ | 7 | 0 | 1504 | region 2360 kind 12 event 2 | none |
| L8_SJ | L9_DR | 1 | 0 | 1670 | region 3132 kind 12 event 2 | none |
| L8_SJ | L9_DR | 2 | 0 | 2076 | region 3569 kind 12 event 2 | none |
| L8_SJ | L9_DR | 2 | 0 | 2082 | region 3570 kind 12 event 2 | none |
| L8_SJ | L9_DR | 2 | 0 | 2088 | region 3573 kind 12 event 2 | none |
| L8_SJ | L10_DC | 1 | 0 | 564 | region 908 kind 12 event 2 | none |
| L8_SJ | L12_CM | 1 | 0 | 1908 | region 3277 kind 12 event 2 | none |
| L8_SJ | L14_HT | 1 | 1 | 11612 | prop:1198 kind 6 value 20 | (local 13 == 1) |
| <a name="level-l9_dr"></a>[L9_DR](levels/L9_DR.md) | L8_SJ | 5 | 1 | 2168 | prop:104 kind 2 timer flags 0x30 | none |
| L9_DR | L8_SJ | 6 | 0 | 572 | region 2301 kind 12 event 2 | none |
| L9_DR | L8_SJ | 7 | 0 | 5582 | region 5340 kind 12 event 2 | none |
| L9_DR | L10_DC | 2 | 0 | 548 | region 2299 kind 12 event 2 | none |
| <a name="level-l10_dc"></a>[L10_DC](levels/L10_DC.md) | L8_SJ | 2 | 0 | 0 | region 0 kind 12 event 2 | none |
| L10_DC | L9_DR | 3 | 0 | 108 | region 42 kind 12 event 2 | (local 11 == 1) |
| <a name="level-l12_cm"></a>[L12_CM](levels/L12_CM.md) | L8_SJ | 4 | 0 | 0 | region 734 kind 12 event 2 | none |
| L12_CM | L13_RC | 1 | 1 | 2808 | control:74 kind 5 event 4 value 0 | none |
| <a name="level-l13_rc"></a>[L13_RC](levels/L13_RC.md) | L12_CM | 2 | 0 | 706 | region 489 kind 12 event 2 | none |
| <a name="level-l14_ht"></a>[L14_HT](levels/L14_HT.md) | L8_SJ | 3 | 0 | 1462 | region 863 kind 12 event 2 | none |
| L14_HT | L8_SJ | 3 | 0 | 3836 | region 4176 kind 12 event 2 | none |
| L14_HT | L16_CA | 1 | 1 | 9210 | prop:170 kind 6 value 20 | (local 22 == 1) |
| <a name="level-l16_ca"></a>[L16_CA](levels/L16_CA.md) | L17_HC | 1 | 1 | 42056 | control:74 kind 5 event 4 value 0 | none |
| L16_CA | L17_HC | 3 | 0 | 7268 | region 9822 kind 12 event 2 | none |
| <a name="level-l17_hc"></a>[L17_HC](levels/L17_HC.md) | L16_CA | 2 | 1 | 3896 | movable:50 kind 5 event 4 value 0 | (object+0x25 == 1) |
| L17_HC | L16_CA | 3 | 0 | 1644 | region 1318 kind 12 event 2 | none |
| L17_HC | L19_BC | 1 | 0 | 1632 | region 1312 kind 12 event 2 | none |
| L17_HC | L19_BC | 1 | 0 | 1638 | region 1313 kind 12 event 2 | none |
| <a name="level-l19_bc"></a>[L19_BC](levels/L19_BC.md) | L17_HC | 2 | 0 | 0 | region 22 kind 12 event 2 | none |
| L19_BC | L20_BB | 1 | 0 | 15784 | region 2369 kind 12 event 2 | (shared 52 == 0) selector |
| L19_BC | L20_BB | 2 | 0 | 15790 | region 2369 kind 12 event 2 | (shared 52 == 1) selector |
| <a name="level-l20_bb"></a>[L20_BB](levels/L20_BB.md) | L19_BC | 2 | 0 | 3786 | region 1475 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3792 | region 1476 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3798 | region 1477 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3804 | region 1478 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3810 | region 1479 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3816 | region 1484 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3822 | region 1485 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3828 | region 1486 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3834 | region 1487 kind 12 event 2 | none |
| L20_BB | L19_BC | 2 | 0 | 3840 | region 1488 kind 12 event 2 | none |
