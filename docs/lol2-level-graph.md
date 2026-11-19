# LoL2 levels, room archives and the exit graph

Date: 2026-10-31

Labels used here:

- **DECODED**: read from level-transition commands in the original level archives
  (see [`lol2-level-script-format.md`](lol2-level-script-format.md)). Reproducible with
  `tools/lol2_export_scripts.py` (the `transitions` list).
- **LONGPLAY (observed)**: seen in a full recorded playthrough of the original game. This is play order,
  not a decode. Times are minutes into that recording.
- **UNKNOWN**: not settled.

## The 15 level archives

The game has 15 level archives, `DAT/L<n>_<xx>.MIX`. Numbers 2, 6, 11, 15 and 18 do not exist. Every level
except L17_HC has a companion media archive `L<n>_<xx>I.MIX`. Counts are from the archives (actors/props
from the geometry header, commands from both streams).

| Level | Short name | Actors | Props | Geometry regions | Commands | Longplay (LONGPLAY, binding test below) |
|---|---|---:|---:|---:|---:|---|
| L1_DC | Draracle's cave | 57 | 1559 | 1954 | 1982 | 5:06-13:24 |
| L3_DH | museum / halls | 33 | 393 | 1499 | 1793 | 16:21-32:33 |
| L4_HJ | Huline jungle | 67 | 6295 | 4787 | 6047 | 32:33-109:44 |
| L5_HC | Hive caves | 37 | 848 | 1292 | 1897 | inside the jungle span |
| L7_DH | Dark Halls | 76 | 487 | 2014 | 1933 | 73:18-89:58 |
| L8_SJ | darker (night) jungle | 117 | 1695 | 3961 | 2708 | from 109:46 |
| L9_DR | - | 80 | 2712 | 6829 | 2938 | UNKNOWN binding |
| L10_DC | - | 102 | 524 | 4320 | 3106 | UNKNOWN binding |
| L12_CM | - | 46 | 438 | 3644 | 1045 | UNKNOWN binding |
| L13_RC | - | 41 | 429 | 1449 | 1661 | UNKNOWN binding |
| L14_HT | - | 96 | 412 | 4275 | 3222 | UNKNOWN binding |
| L16_CA | - | 47 | 681 | 10582 | 6983 | UNKNOWN binding |
| L17_HC | - | 82 | 313 | 1340 | 655 | UNKNOWN binding |
| L19_BC | - | 68 | 270 | 2870 | 2790 | UNKNOWN binding |
| L20_BB | - | 79 | 286 | 1853 | 3834 | UNKNOWN binding |

The first five are Act 1. Short names for L1-L8 are descriptive labels, not names stored in the files. For the
later levels the longplay shows a dragon lair, a stone dungeon, a statue hall, a lava cave, a snow level, a
large Ruloi cavern, a city with a lava moat and "Subterranean Caverns".

### Matching a recorded segment to an archive

Each `UNKNOWN binding` above refers to the match against
the recording. **CONFIRMED.** The level index `i` is stored by the script at `0xD87AE`,
and the level loader uses the name pointer at `LOLG.DAT+0x1CDA44 + 8*i`
(`0x9BE08`). To settle each binding, capture the first level load in that
segment and compare its filename with that row, or read the level index
at slot +0x17C from an original save made at the same point. Compare
the slot's index with the specific level ID in the table above.

Longplay order after Act 1 (LONGPLAY, minutes): night jungle 109:40 -> dragon segment 119:10-128:40 ->
stone dungeon 137:40 -> ruins and statue hall 149:40 -> lava cave 155:10 -> snow level 194:10 -> Ruloi
cavern 202:40 -> sandstone temple 233:40 -> city 257:10-288:10 -> "Subterranean Caverns - Layer 1" 288:40
-> end 304:40, credits to 309:10. The night jungle recurs between several of these.

## Exit graph (DECODED)

Level-transition commands are `02 01 00 00 1C xx`: destination level = `xx & 31`, arrival entry =
`xx >> 5`. Every such command in the retail archives:

| From | To (level / entry) x number of commands |
|---|---|
| L1_DC | L3_DH/1 x10 |
| L3_DH | L4_HJ/1 |
| L4_HJ | L5_HC/1, L5_HC/2, L7_DH/1, L8_SJ/1 x8 |
| L5_HC | L4_HJ/3, L4_HJ/4 |
| L7_DH | L4_HJ/6 x7 |
| L8_SJ | L4_HJ/7 x3, L9_DR/1, L9_DR/2 x3, L10_DC/1, L12_CM/1, L14_HT/1 |
| L9_DR | L8_SJ/5, L8_SJ/6, L8_SJ/7, L10_DC/2 |
| L10_DC | L8_SJ/2, L9_DR/3 |
| L12_CM | L8_SJ/4, L13_RC/1 |
| L13_RC | L12_CM/2 |
| L14_HT | L8_SJ/3 x2, L16_CA/1 |
| L16_CA | L17_HC/1, L17_HC/3 |
| L17_HC | L16_CA/2, L16_CA/3, L19_BC/1 x2 |
| L19_BC | L17_HC/2, L20_BB/1, L20_BB/2 |
| L20_BB | L19_BC/2 x10 |

In this table only the command bytes are decoded. It does not show which object or region runs each
command, under which predicate, or whether the player can reach it. Some commands could be unused.

L8_SJ is the hub after Act 1: it links to L4_HJ, L9_DR, L10_DC, L12_CM and L14_HT, and all five link
back to it. L16_CA -> L17_HC -> L19_BC -> L20_BB form a chain with links back.

### Owner-bound exits for L9, L12, L14, L17 and L20 (DECODED)

For these five levels every transition command (23) was also tied to the event record that names its group
(a static audit; each destination has exactly one matching arrival selector record).
"Region" owners are region kind-12 records; others are object records.

| From | Owner | Group | To / entry |
|---|---|---:|---|
| L9_DR | prop 104 | 2168 | L8_SJ / 5 |
| L9_DR | region 2299 | 548 | L10_DC / 2 |
| L9_DR | region 2301 | 572 | L8_SJ / 6 |
| L9_DR | region 5340 | 5582 | L8_SJ / 7 |
| L12_CM | control 74 (kind 5, value 4) | 2808 | L13_RC / 1 |
| L12_CM | region 734 | 0 | L8_SJ / 4 |
| L14_HT | prop 170 (kind 6, predicate 50) | 9210 | L16_CA / 1 |
| L14_HT | region 863 | 1462 | L8_SJ / 3 |
| L14_HT | region 4176 | 3836 | L8_SJ / 3 |
| L17_HC | movable 50 | 3896 | L16_CA / 2 |
| L17_HC | regions 1312, 1313 | 1632, 1638 | L19_BC / 1 |
| L17_HC | region 1318 | 1644 | L16_CA / 3 |
| L20_BB | regions 1475-1479, 1484-1488 | 3786-3840 | L19_BC / 2 |

The arrival entry's binding to a specific arrival record and region is LIKELY (bytes agree; runtime
selection not traced). All 72 commands now join to one original event each across the 15 archives. The [exit predicate census](lol2-shared-predicates.md#exit-predicate-census) documents the table offsets, counts and repro command.

## Room archives

Rooms are separate archives `DAT/<ROOM>.MIX`. 47 of them contain a room module at the name hash of
`WOMS\<ROOM>_.WOM`: the 46 names in the executable's table ([room archives](lol2-room-archives.md))
plus `ARENA`, which that table does not name. SPKSTON1, SPKSTON2 and SPKSTON4 do not have the module;
they hold only movies. Counts below were checked against the retail files. Both counts are right:
the dword table names 46 rooms, and 47 archives contain the `WOMS\<ROOM>_.WOM` key. `ARENA` is the
extra archive. How `ARENA.MIX` is opened is open. The executable has no `ARENA.MIX` string and no
`arena_` string, and the dword `ww_hash_v1("ARENA.MIX")` (`0xCBAFA5DF`) is not stored. The movie-scene
stem `arenaapr` is at file `0x1C3D1A`, between `a_cam` and `b_cam`.

| Room | Entries | VQA movies | | Room | Entries | VQA movies |
|---|---:|---:|---|---|---:|---:|
| ALTAR | 6 | 4 | | MOFF | 121 | 85 |
| ARENA | 2 | 0 | | POOL | 7 | 2 |
| BALCONY | 3 | 1 | | RUNECL | 3 | 1 |
| CAN | 70 | 45 | | SETTLE1 | 5 | 3 |
| CAVE | 3 | 1 | | SETTLE2-4 | 3 each | 1 each |
| CFALL | 3 | 1 | | SEVER | 10 | 8 |
| CHUT | 40 | 28 | | SHAMAN | 155 | 93 |
| CHV | 7 | 5 | | SHBAK | 17 | 11 |
| DANIEL | 112 | 77 | | SKEL | 4 | 1 |
| DRAGON | 27 | 10 | | SLAVES | 39 | 18 |
| DSLAVE | 78 | 42 | | SPKSTON1 / 2 / 4 | 1 / 10 / 1 | 1 / 10 / 1 |
| EMPT | 57 | 45 | | STAT | 15 | 11 |
| HERB | 72 | 49 | | TCEL | 4 | 2 |
| HIVE1-4 | 4 / 7 / 9 / 12 | 2 / 5 / 6 / 9 | | TDOOR | 11 | 4 |
| HUT1, HUT2 | 20, 30 | 13, 22 | | TEXT | 3 | 1 |
| MAGIC | 63 | 43 | | TINT | 92 | 66 |
| MCEL | 28 | 18 | | TMPLDOR | 9 | 7 |
| MENT | 7 | 2 | | VILLAGE | 4 | 2 |
| MGAR | 63 | 46 | | WPN | 108 | 78 |
| MLIB | 79 | 60 | | WPNEXT | 5 | 2 |

`LIZ.MIX`, `RUNES.MIX`, `MOVIES.MIX` and `GLOBAL.MIX` are other archives, not part of this survey.

**CONFIRMED.** The 174 opcode-12 commands in the 15 indexed level
streams resolve directly by u8 +4 to the native names at
`LOLG.DAT+0x1CFA90`. The command entry `0xB5AA2` forwards
that index into `0xED6D0`, which checks bit 25 at `0x2279A`
before calling the room archive builder at `0xED72A → 0xED470`.
The table lists requests stored in the two script streams. A
request can be suppressed or never reached during play.

| Original level | Opcode-12 requests by room | Example command offset |
|---|---|---|
| L1_DC | CFALL ×3 | +0x6FD8DB |
| L3_DH | DRAGON ×5 | +0x59C56C |
| L4_HJ | POOL ×7, MENT, MCEL, MGAR, VILLAGE, CHUT, MAGIC, WPNEXT ×4, TEXT | +0xC6BA90 |
| L5_HC | SEVER, RUNECL, RUNES ×105 | +0x5AD509 |
| L8_SJ | SHAMAN, DANIEL ×3, TMPLDOR ×6, SETTLE1 ×9 | +0xCD1D74 |
| L9_DR | STAT, ALTAR ×8 | +0x164DE20 |
| L10_DC | EMPT | +0xC8DD20 |
| L13_RC | DSLAVE, SLAVES | +0x687B15 |
| L14_HT | CHV ×2 | +0xB2FD22 |
| L16_CA | BALCONY | +0x11EA3F3 |
| L17_HC | HIVE1 ×3, HIVE4 ×4 | +0x496725 |
| L7_DH, L12_CM, L19_BC, L20_BB | Zero opcode-12 requests | Geometry header +0x3C/+0x44 selects both streams. |

**CONFIRMED.** A room module can request the next room by name, outside
opcode 12. The direct archive-builder call at `0xEDB5A` takes the index
resolved by `0xEDADD–0xEDB43`. Original calls include the MCEL import at
`MCEL.MIX+0x9DF`, passing `MENT_` from +0xAC1, and the SHAMAN and SETTLE1
imports at `SHAMAN.MIX+0xDC5` and `SETTLE1.MIX+0x615`. The original
arguments and host import are traced in [Room archives](lol2-room-archives.md#the-extra-arena-archive).
**UNCONFIRMED.** The encounter conditions that reach these module
calls, and an admitted caller of the indexed entry `0xED59C`. Follow
the three stored branch conditions to the calls above. To identify an
indirect native entry into `0xED59C`, capture the return address and
index at `0xED5B5`; match the index to the room-name table.

## Close-out

### Q3

**What was measured.** `LOLG.DAT` contains 28 direct `E8` calls whose target is `0x11C654`. The one at `0xED54A` is the five bytes `E8 05 F1 02 00`.

**What was tried.** This scan counted direct relative calls into that constructor. The page already records that the 46-name table at file `0x1CFA90` does not include `ARENA`, and that `ARENA.MIX` is not a stored string.

**What would settle it.** The running-game test is not yet run ([probes not yet run](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run)). Trace an indirect host wrapper into constructor `0x11C654` with the name `ARENA.MIX`.
