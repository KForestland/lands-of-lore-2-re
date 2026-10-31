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

| Level | Short name | Actors | Props | Geometry regions | Commands | Longplay (LONGPLAY) |
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

The first five are Act 1. Short names for L1-L8 come from the Godot rebuild's playtested levels. For the
later levels the longplay shows a dragon lair, a stone dungeon, a statue hall, a lava cave, a snow level, a
large Ruloi cavern, a city with a lava moat and "Subterranean Caverns", but which archive each segment uses
has not been traced (UNKNOWN; matching by archive name or content is only a guess).

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
selection not traced). Owners for the other ten levels' transitions are not listed here (UNKNOWN in this
note).

## Room archives

Rooms are separate archives `DAT/<ROOM>.MIX`. 45 of them contain a room module at the name hash of
`WOMS\<ROOM>_.WOM` plus VQA movies and sprites; SPKSTON1, SPKSTON2 and SPKSTON4 hold only movies. Counts
below were checked against the retail files.

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

Which level opens which room is UNKNOWN in general. In L4_HJ a room is opened through a control of type
0x10 (op12 sets the room index, event 20 fires it); the other levels' controls were not read for this.
