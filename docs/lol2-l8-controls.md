# L8_SJ controls 69 and 114

MIX offsets below are in `L8_SJ.MIX`. Native addresses use the
[retail 1.30 convention](lol2-executable-tables.md).

## Control 69

**CONFIRMED.** Placement 69 starts at `0xCE8868`. Geometry header
`0xC899A1` fields +0x18 and +0x64 give the 33-byte control table
and its count. Row +0x0C links to the kind-4 record at `0xCD7E66`.
This is the only event on that list. It is mode 0, inversion 0, and has
no trailing predicate. The common interaction method checks object
flags at `0xB5004`, obtains the event list through vtable +0xB8 and
calls `0xADBCC` at `0xB501D`. Mode 0 takes the null-selection test
set at `0xADBDD–0xADC04` and read at `0xADC41`. At
`0xADDA9–0xADDB0` the event's u16 +2 queues stream 1 group 12668.

| MIX site | Confirmed action on an admitted command |
|---|---|
| `0xCD4764` | Opcode 20 sends audio index `0x030C` and control 69 to `0xE3924` at `0xB5C0D`. Selector 0x10 resolves controls through `0x5FC91`. |
| `0xCD476E` | Opcode 18 queues the player sequence if the slot is vacant (`0xB59CE–0xB59E8`). Flags `0x0304` select the direct-position path, including Z. The native sequence update writes X = −1004, Y = 2590, Z = 100, each multiplied by 65536, and returns orientation `0x4FA4` (`0x65C3C–0x65CC5`, `0xB2A96`). |

**CONFIRMED.** The placement's signed region index at +0x0A is 678.
Its polygon at `0xCAE12E` contains the initial position and has floor
−10. The sequence destination (−1004, 2590) falls inside region 657,
whose polygon is at `0xCADD92` and floor is 100, exactly the sequence's
Z. The action therefore moves the player up 110 height units between
those polygons. Region 678 has no portal on side 0 (word at +4 =
0xFFFF). The exact visible climbing surface remains **UNCONFIRMED**.

## Control 114

**CONFIRMED.** Placement 114 starts at `0xCE8E35`. Its only event
is a mode-0, uninverted kind-4 test at `0xCD7EF2`, with no predicate.
The same null-selection path queues stream 1 group 13090.

| MIX site | Confirmed action on an admitted command |
|---|---|
| `0xCD490A` | Opcode 9 property 21 issues kind-6 value 20 on prop 115 (`0xB5448–0xB5458`). Its record at `0xCD72A6` directly links to group 4914. That group submits opcode 2 action 0x15 with operand 20 at `0xCD2914`. The arm tests player +0x228 bit `0x10` at `0xD8044`. On the set-bit path it calls `0xD6B20` with form ID 2 if player +0x1AB differs (`0xD8059–0xD806F`). |
| `0xCD4910` | Sends the same kind-6 value to prop 1014. Its record at `0xCD767E` queues group 8706, whose opcode 20 requests audio `0x015F` on that prop at `0xCD37E4`. |
| `0xCD4916` | Opcode 20 requests audio `0x030C` on prop 1014 (`0xB5C0D`). |
| `0xCD4920` | Property 3 links control 116 through `0xB511A → 0xB49EC` with second argument 1. Control 116's placement is at `0xCE8E77` and its event list at `0xCD6B2E` is empty. |
| `0xCD4926` | Property 2 unlinks control 114 through `0xB50E9 → 0xB49EC` with second argument 0. |

**CONFIRMED.** Control 114 is attached to region 3206
(`0xCC93AE`). Prop 1014 (`0xCE1D16`) is in region 3209
(`0xCC9432`), whose side 0 connects back to side 2 of region 3206.
Those sides share vertices 833 and 909. Prop 115 (`0xCD9B27`) is in
region 3747 (`0xCCF0AA`), with all four neighbour words 0xFFFF.
Control 116 (`0xCE8E77`) is in region 3300 (`0xCCA3D6`).
The clear-bit form branch at `0xD804B` enters `0xD7EE0`, calling
`0x80064(0x23819,1)`. Its path sets the feedback timer
+0x2EC to `0x30000` and may play the cue at table byte +0x20E
(`0x800CB–0x80100`). It does not reach the form-change call.
The visible geometry and feedback remain **UNCONFIRMED** in play.

## Placement and input selection

**CONFIRMED.** The constructor reads 33-byte placements at
`0x5B72C–0x5B75D`. The common constructor takes signed row +0x0A
as a geometry region, with `-1` for none, and links the object to the
selected 44-byte row via `0xAF0E0`
(`0xAEA30–0xAEA5C`). The control constructor takes u8 +0x20
as a 60-byte definition index from `[0x22D4C]` and stores that
pointer at object +0x2C (`0x5B654–0x5B677`).
The three control rows above name definitions 32, 12 and 10
respectively. The [level report check](../tools/lol2_level_report.py)
recomputes the joins, portal neighbours and destination polygon.

**CONFIRMED.** The input handler at `0x75D98` reads the current
pointer coordinates at `0x75DE2/0x75DE9` and `0x75E60/0x75E67`
and calls the viewport picker with action argument 1 at
`0x75DFF/0x75E7D`. The picker checks viewport bounds
(`0xE10A1–0xE10C5`), renders the pick query at `0xE1159`,
and stores horizontal distance at request +0x28
(`0xE118C–0xE1194`). The action wrapper's picked object at request
+0x20 must be of pick kind 4 and within `0x01000000` (256 in 16.16).
Its object +0x14 mask 0x04000000 must be clear
(`0x110A9F–0x110AC2`). The wrapper then calls its vtable +0x64 at
`0x110ACD`, which is the control interaction below. A kind-4 mode-0
event treats request +0x0C as null when no item is selected
(`0x110F3D–0x110F68`, `0xADBDD–0xADC04`).

**UNCONFIRMED in play.** Which visible pixels return each object from
the pick query. To settle that, start close to the cited region, use the
empty-hand action inside the viewport and log kind, selected object and
distance at `0x110ACD`; check the object event offset before reading
the selected group.

## Live binding of both L8 controls

**CONFIRMED.** The DOS 1.30 run loaded L8_SJ from a player slot (a save written by the game, not shipped) with
SHA-256 prefix `9a46a2bdecb4`. The control pool `0x273E0` had 168
64-byte elements, read through the fields the save writer uses at
`0xE8BF8–0xE8C10`. Its indices 69 and 114 matched the placements:

| Index | Live X, Y, Z | Object +0x18 | Record at `[0xB7D74]` plus that offset |
|---|---|---:|---|
| 69 | −1034, 2606, −10 | `0x1338` | `0A 04 7C 31 00 00 00 00`, group 12668 |
| 114 | 5096, −1916, 0 | `0x13C4` | `0A 04 22 33 00 00 00 00`, group 13090 |

Both objects had byte +0x15=`0x04` and vtable object-5 `0x5484`,
installed statically at `0x5B64D`. The relocated vtable +0x64 was
`0x5DA48`. That entry directly calls `0xB5000` at `0x5DAAD`, after
checking that the requester dword +0x28 is at most `0x1000000` and
the control +0x15 mask 0x80 is clear (`0x5DA51–0x5DA70`). Its event
getter at vtable +0xB8 was `0xB71A0`, which bound the object and used
the +0x18 offset at `0xB71A4–0xB71C7`.

**UNCONFIRMED.** The run created both controls and the player moved
from the save's starting point. The empty-hand input there left both groups
unobserved. `0x5DA48` was not hit in that input. For a closer save, condition the breakpoint at `0x5DA51`
on `word [EBX+0x18]` equal to `0x1338` or `0x13C4`. `0xB5000` has two other direct callers (`0x95218`, `0xA74CB`), so also break at its entry with the object at `[esp+4]` and the same +0x18 test. Record the requester,
group and visible change for the matched control. The destination and
linked props in the tables above identify the two expected outcomes.
