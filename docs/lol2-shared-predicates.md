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
| 37 | `L9_DR.MIX+0x162ABFA`, prop 1201, kind 2. Predicate 45 at `+0x166EB13` tests `shared[37] == 1`. | Stream 1 group 9392 issues opcode-2 subcommand `0x26` at `+0x1627524`. Its deeper effect remains **UNCONFIRMED** here. |

Use `0x66C43` for the equality arms above, `0x66C7F` for >=,
`0xD8797–0xD87C5` for level/entry splitting, and `0x64887`, `0x64A8C`,
`0x64B1C` for the named array writes. The per-level indexes retain each
root predicate offset and linked command site.

**UNCONFIRMED.** The full branch catalog and native producers for the
other shared indexes remain open. The census followed shared readers through
recursive type-4 edges and the original opcode 199/206 write sites.
The two L19 guards give a complete pair for values 0 and 1 at that exit.
For a different branch, trace every leaf of the root predicate, then
follow the matching command sites and native writers of the same index.
