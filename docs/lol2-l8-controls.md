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

**UNCONFIRMED.** The spatial interpretation as a ladder and the
input path that reaches the common interaction method for this exact
control remain open. The archive records establish the player destination
and the interaction test. To settle the input path statically, resolve
control 69's constructed vtable and trace the caller of its
`0xB5000` interaction entry.

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

**UNCONFIRMED.** The visible geometry changes associated with the two
props and the linked control remain open. The command list was traced
through each direct group target. Match the three placements to their
render or world-region consumers and follow the form branch at `0xD7EE0`
for the clear-bit case to settle the remaining presentation and condition.
