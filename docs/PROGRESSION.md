# Progression

Made by `tools/lol2_progression.py` from the level-transition commands in the 15 level archives. One row is one command whose first five bytes are `02 01 00 00 1c`. Byte 5 stores the destination level in the low 5 bits and the destination entry in the high 3 bits. The event column is the one object or region record whose list names that command's group ([level sheets](levels/README.md)), with the fields its matcher reads ([record kinds](lol2-script-events.md#event-records)). The slots column is the kind-19 predicate on that record, from the 5-byte predicate table ([predicates](lol2-script-events.md), [exit census](lol2-shared-predicates.md#exit-predicate-census)). `shared N` is byte N of the plot array at `[0x26E58]`. `local N` is byte N of the level array at `[0x26E54]`. `object+0x25` is the byte at `[0xB7D80]+0x25`. A type-4 operand is another row of the same table. `none` means that record has no predicate trailer. Slot numbers are table indexes, not names.

72 exit commands, 24 with a predicate. Shared slots named on those rows: 52 (2). Local slots named on those rows: 2 (9), 11 (1), 13 (1), 22 (1), 55 (8). Levels with no exit command: none. Levels no exit command leads to: L1_DC.

Locked doors are not on this page. It lists level-transition commands only.

**CONFIRMED.** Four exit handlers run all matching records in list order: the region walker `0xF2D2C` and the kind 5, 6 and 8 matchers `0xAD8E0`, `0xADDE0` and `0xAE510` advance to the next record after each run (back edges `0xF2FAD`, `0xAD9EF`, `0xADF26`, `0xAE5FA`). Each guard is checked after earlier matching groups in the same walk have run, and when two exits fire the later one wins, because the exit arm only stores the pending level (`0xD87AE`, `mov [0x223C8],eax`). For the kind-2 timer exit, the countdown service queues its timer group when it expires.

## What a row does not show

8 exits run from an object's event list. A row with `none` for slots still needs its event or timer to fire. The following upstream commands are from the original DOS 1.30 files. Archive offsets are file offsets and executable addresses are in the analysis convention. [Record kinds](lol2-script-events.md#event-records) · [Executable addresses](lol2-executable-tables.md)

| Exit owner | What sends or arms the exit |
|---|---|
| L1_DC prop 447 | **CONFIRMED.** With local 2 = 0, entering any of regions 1190 or 1217–1224 requests cue 973 on prop 447. The first request is `L1_DC.MIX+0x6FD5B1`. Opcode 20 passes the object and cue through `0xB5C0D`. A voice slot keeps both, and the cleanup path at `0xE3824–0xE3841` can forward them to the kind-8 matcher. Its record at `+0x6EA117` runs group 4030. [Cue path](lol2-sound-cues.md) |
| L3_DH control 82 | **CONFIRMED.** Region 1419 event 4 sets state 1 at `L3_DH.MIX+0x59C864`. On kind-6 value 1, the earlier record at `+0x5947E0` tests for 1 and sets 3 at `+0x5922F4`. The later record at `+0x5947F6` sees 3 and requests L4_HJ. The resource callback at `0x9EC60` sends this event value to its owner. **UNCONFIRMED.** Which resource instance supplies control 82 to that callback. Read the callback context +0x14 and resource +0x30 when entering region 1419. [Callback](lol2-event-producers.md#confirmed-event-sources) |
| L8_SJ prop 1198 | **CONFIRMED.** Entry into regions 1514, 1515, 1519, 1523, 1527 or 1530 sends kind-6 value 20 through opcode 9 property 21 (`L8_SJ.MIX+0xCEC80D` through `+0xCEC8FD`, stride `0x30`). The record at `+0xCD7C4A` tests local 13 = 1. [Property 21](lol2-event-producers.md#confirmed-event-sources) |
| L9_DR prop 104 | **CONFIRMED.** Control 82 kind-5 event 4 with state 2 starts timer 0 at `L9_DR.MIX+0x1628758`. Group 2140 starts timer 1 at `+0x16258D8`. Timer 1 runs group 2168 and requests L8_SJ. **UNCONFIRMED.** The sender of control 82's event 4. [Timer actions](lol2-script-events.md#object-timers) |
| L14_HT prop 170 | **CONFIRMED.** Controls 78 and 79 have empty-hand records guarded by state 1. Both send kind-6 value 20 to prop 170 at `L14_HT.MIX+0xB2FD28` and `+0xB2FD3A`. The record at `+0xB322F0` tests local 22 = 1. [Held-item test](lol2-script-events.md#event-records) |
| L17_HC movable 50 | **CONFIRMED.** Hit records on props 307–310 each send kind-6 value 20 to movable 50 (`L17_HC.MIX+0x490384`, `+0x4903A8`, `+0x4903CC`, `+0x4903F0`). With local 0 = 10, group 3878 sets its state to 1 at `+0x49053A`. The later kind-5 event 4 exit requires state 1. **UNCONFIRMED.** The sender of that event 4. |

**UNCONFIRMED.** The kind-5 event 4 sends that trigger the L12_CM and L16_CA control 74 exits and advance the L9_DR and L17_HC chains are still open. At the kind-5 entry `0xAD8E0`, filter on event 4 and compare the incoming list pointer with the listed owner. The call return address will identify where that known owner gets its event.

**CONFIRMED.** 1 region exit uses region event 4 (L4_HJ region 3205). The player region update tests region +0x28 bit 1 (mask 2), sets it on first contact and passes event 4 at `0xD394A` before event 2 at `0xD39BB`. The alternate-region path sends event 4 at `0xD38D1` and sets the same bit. The L4_HJ exit record uses argument byte 0, so the matcher accepts either value of the incoming height comparison. No predicate follows it ([region event arms](lol2-script-events.md#region-event-arms)).

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
