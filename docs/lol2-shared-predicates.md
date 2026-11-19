# LoL2 shared bytes and predicate type 7

Addresses use the DOS 1.30 [executable convention](lol2-executable-tables.md).
Archive offsets are absolute. See the [evaluator](lol2-script-events.md#predicates-and-shared-bytes)
for ordinary operand types and operators.

## Type 7

**CONFIRMED.** The left-type-7 arm at `0x66B5C` compares **EBP**, the
predicate table index loaded at `0x66AB4`, with 1. It does not consult the
left operand argument byte. For an index at least 1, it goes to `0x66CB7`
and returns false immediately. For index zero, it pushes the incoming
ESI and calls table entry 0 at object-5 `0xBBB8`. For that entry, the dword
at `LOLG.DAT+0x1CCBDC` is `0xDA24`, and LE fixup `LOLG.DAT+0x8B809`
relocates it to `0x66A48`. The callee copies its first argument to EAX and
returns (`0x66A48–0x66A4C`). The evaluator uses that result as the left
operand (`0x66B70`). The value is the inherited ESI at evaluator entry
because the type-7 left arm executes before ESI is assigned a right operand.
Right type 7 falls through to the operator path at `0x66B7B` without
assigning ESI (object-2 table `0xDA4C`, entry 7).

**CONFIRMED.** Neither operand column contains type 7 among the 3,825
retail predicate entries. To reproduce, read 255 five-byte rows per archive
from the geometry header's u32 +0xBC pointer and compare bytes +1 and +3
with 7. Thus the fallback can be described from the executable. A gameplay
producer and intended value at the hypothetical index-zero use remain
**UNCONFIRMED**. To settle them, find an original data edition that stores
type 7 or a caller that writes such a predicate at runtime, then trace ESI
before `0x66AB0`.

## Shared indexes with native names

**CONFIRMED.** The lookup `0x61514` advances 41-byte rows in
`[0x2B4C0]`, bounded by `[0x26E60]`. The reference name table begins at
`GLOBAL.MIX+0x667C18`. The shared data loader at `0x9F0DC` reads the
shared bytes and looks up the named slots before returning. The caller at
`0x9E835` supplies object-5 base `0x22CD8`. Its cached indexes below are checked
against the original executable strings and corresponding archive rows.

| Index | Name row in GLOBAL.MIX | Cache cell and loader write | Native use |
|---:|---|---|---|
| 37 | `0x668205`, `GV_BRACERS_OF_THE_DEAD` | `0x2333F`, `0x9F15A` | Reads the indexed byte at `0x99BB3` and `0x99BCB`. |
| 45 | `0x66834D`, `GV_LUTHER_FORM` | `0x23340`, `0x9F16D` | The paths at `0x79539`, `0x79559` and `0x79572` write 2, 0 and 1 to the indexed byte. |
| 50 | `0x66841A`, `GV_RUBY_OF_TRUTH` | `0x23341`, `0x9F180` | Equip handler 101 reads this index at `0x9B55B` and stores at `0x9B560`. The unequip path reads at `0x9B58F` and can clear the byte at `0x9B594`. |
| 0 | `0x667C18`, `GV_LUTHERS_SOUL` | `0x23342`, `0x9F193` | Shared setter caps this slot at 10 (`0x64A91–0x64AB3`). |
| 12 | `0x667E04`, `GV_DAWN_RELATIONSHIP` | `0x23343`, `0x9F1A6` | Shared setter caps this slot at 2 (`0x64AB7–0x64AD9`). |
| 13 | `0x667E2D`, `GV_BACATTA_RELATIONSHIP` | `0x23344`, `0x9F1B6` | Shared setter caps this slot at 2 (`0x64ADD–0x64AFF`). |

Executable string offsets for indexes 37, 45, 50, 0, 12 and 13 are
`LOLG.DAT+0x1C1CF9` for index 50, `+0x1C1CD3` for index 37,
`+0x1C1CEA` for index 45, `+0x1C1D0A` for index 0, `+0x1C1D1A`
for index 12 and `+0x1C1D2F` for index 13. The target array in the
setter is `[0x26E58]` (`0x64B05–0x64B11`). The signed add path also
uses those three ceilings (`0x64B39–0x64B9E`).

## Branch and producer witnesses

**CONFIRMED.** A shared leaf is operand type 2 (`0x66B2A` or `0x66BAF`).
When a trailer names a recursive predicate, follow operand-type-4 edges
before interpreting a single leaf. The examples below identify their original groups and guards.

| Shared index | Original event and predicate | Effect in linked group |
|---:|---|---|
| 52 | `L19_BC.MIX+0x5EC32A`, region kind 12, region 2369 and event 2. Predicate 204 at `+0x5F6D60` is `shared[52] == 0`. | Stream 0 group 15784 issues the level-20 transition to arrival 1 at `+0x5E93F4`. |
| 52 | Same region and event at `L19_BC.MIX+0x5EC336`. Predicate 205 at `+0x5F6D65` is `shared[52] == 1`. | Stream 0 group 15790 issues the level-20 transition to arrival 2 at `+0x5E93FA`. |
| 52 | `L20_BB.MIX+0xECE285`, prop 242, stream 1 group 7704. Predicate 206 tests bound object state zero at `+0xEE16C0`. | Opcode 199 sets `shared[52] = 1` at `+0xEC7D19`. The original name row starts at `GLOBAL.MIX+0x66846C`. |
| 13 | `L4_HJ.MIX+0xC2C3A4`, prop 552, kind 4, stream 1 group 10816. Predicate 39 includes leaf 25 at `+0xC8BD0D`, which tests `shared[13] >= 1`. | Updates shared byte 0 at `+0xC26236`, adds 1 to byte 13 at `+0xC2623C`, and sets local 51 to 1 at `+0xC26242`. |
| 37 | `L9_DR.MIX+0x162ABFA`, prop 1201, kind 2. Predicate 45 at `+0x166EB13` tests `shared[37] == 1`. | Stream 1 group 9392 issues opcode-2 subcommand `0x26` at `+0x1627524`. The reset continuation is traced below. |

Use `0x66C43` for the equality arms above, `0x66C7F` for >=,
`0xD8797–0xD87C5` for level/entry splitting, and `0x64887`, `0x64A8C`,
`0x64B1C` for the named array writes. The per-level indexes retain each
root predicate offset and linked command site.

**CONFIRMED.** Opcode-2 subcommand 0x26 (`cmp ah,0x26` at `0xD869C`, then `0xD7A9B–0xD7B0B`) sets the receiving object's +0x228 bit 0x80 and clears bit 0x10, clears byte +5 of the objects at +0x97 and +0x9B(+0x2C) and the pointers to them, and clears +0x9F, +0x21E and bit 0x08 of +0x19F. Its plot meaning is open.

## Exit predicate census

**CONFIRMED.** The command streams of the 15 levels contain 72 level-transition
commands with prefix `02 01 00 00 1c`. Each links directly to one
original event among the four principal object tables and region lists.
Twenty-four of those pairs have a kind-19 predicate trailer. Following
every type-4 predicate edge from those roots, the only type-2
shared-array slot is 52. It occurs twice, for the two L19_BC exits (to L20 arrivals 1 and 2)
in the table above. `lol2_level_report.py --check` uses geometry header +0x38/+0x40 for event
blobs, +0x3C/+0x44 for commands and +0xBC for predicate rows. It pins both
event and command offsets. Recursive operand readers are `0x66B47` and
`0x66BEC`, with shared reads at `0x66B2A` and `0x66BAF`.
The check covers the directly linked exit commands. Other plot
branches can use shared slots elsewhere in the scripts.

### Shared predicates outside exits

**CONFIRMED.** The same 15 geometry headers and the same four object
tables and region lists yield 289 distinct event offsets linked to
287 groups per level and stream in aggregate, after excluding groups
that contain a level transition. Their kind-19 predicate roots refer
to 28 distinct shared slots through evaluator reads `0x66B2A` and
`0x66BAF`. The counts are per stored event record, deduplicating
object lists that point to the same record. `lol2_level_report.py --check`
rebuilds the counts and checks the four joins below.

| Original event | Shared part of guard and other relevant inputs | Linked non-exit action |
|---|---|---|
| `L1_DC.MIX+0x6FDB2F`, group 432 | Root 51 at +0x7062BC checks shared form 45 = 0 (leaf +0x7062B2) and local 34 = 0 (+0x7062B7). | At +0x6FD293, set local 34 to 1; +0x6FD299 and +0x6FD2A1 run creature opcode 13 subcommands 13 and 7 on actor 39. |
| `L8_SJ.MIX+0xCD7FDA`, group 13416 | Root 108 at +0xD11095 reduces to Dawn 12 ≥ 1, Bacatta 13 ≥ 1 and translated-runes slot 46 = 1 (leaves +0xD11077, +0xD11234 and +0xD1121B). | At +0xCD4A50 actor 20 gets creature opcode 13 subcommand 4 with argument 9. At +0xCD4A5E opcode 16 writes actor +0x25 = 1. |
| `L12_CM.MIX+0x95FC40`, group 5510 | Root 7 at +0x98CB63 checks Dawn 12 = 0 (+0x98CB59) and bound object byte +0x25 = 0 (+0x98CF46). | At +0x95F11C actor 35 gets +0x25 = 1. At +0x95F128 player opcode 2 subcommand 0x26 enters the clear path documented below. |
| `L20_BB.MIX+0xECE1E3`, group 6886 | Root 1 at +0xEE12BF compares shared soul 0 against 5 with operator 5 (less than). | At +0xEC79D5 and +0xEC79DB opcode 198 sets local 6 to 2 and local 4 to 1. |

The archive name for slot 46 is at `GLOBAL.MIX+0x668376`. The other
names are in the shared-index table above. Operator comparisons are
listed in the [predicate reference](lol2-script-events.md#predicates-and-shared-bytes).
The encounter reachability of these branches remains **UNCONFIRMED**.
For each row, compare the live shared and bound-object operands at
`0x66AB0` with the archive predicate and record whether the named group
enters `0x646EC`. The placed-item directory and other indirect group
producers need their own admission witness.

## The slot-37-guarded event

**CONFIRMED.** The player subcommand `0x26` at `0xD7ABC` passes
argument 1 to `0xD0138`. That argument clears player bytes +0x1B6
through +0x1BD. The common tail clears +0x22/+0x23, +0x1BE through
+0x1C1, word +0x20A and the low ten bits of word +0x226. It clears
+0x22A bit 1 (`0xD0144–0xD01CB`). If player +0x229 contains bit
`0x04` or `0x08`, and +0x85 is null, it also sends signed words at
+0x206 and +0x208 to `0x151DAE` (`0xD01D3–0xD01FA`). The latter
clamps the coordinates to the current bounds at context
+0x42B/+0x42F and +0x433/+0x437. Its native mouse-service branch
requests DOS mouse function 4 through the DPMI wrapper
(`0x151B88–0x151C11`, interrupt `0x31`, simulated interrupt `0x33`).
The slot-37-guarded event clears player bytes +0x1B6–+0x1C1 and the
low bits of +0x226 and can write the pointer position; reading this as
an input reset is an interpretation (**UNCONFIRMED**).

**UNCONFIRMED.** The user-facing change of the original L9 prop and
the other plot branches. For slot 37, trace the first subsequent read
of player +0x228 mask `0x80` after `0xD7ABC` and see whether player
+0x229 and +0x85 admit the pointer write. For branches other than the
72 exits, identify each event's linked command effect and all the
leaves of its root predicate before assigning a narrative role.

## Close-out

### Q6

**What was measured.** A disassembly of the code in `LOLG.DAT` finds eight `test byte [reg+0x228], 0x80` instructions, and all eight sit below `0xD7ABC`. From that address through the end of the code object the same scan finds zero, and the next mask of bit 0x80 on `[ebx+0x228]` is the seven bytes `80 A3 28 02 00 00 7F` at `0xD7B21`.

**What was tried.** This scan looked for memory-immediate tests of that bit. The page already records the set of bit 0x80 at `0xD7ABC` and the clears through `0xD0138`.

**What would settle it.** Follow the first read of player +0x228 bit `0x80` after `0xD7ABC`, and check the pointer-position gate at `0xD01D3`.
