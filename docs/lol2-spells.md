# LoL2 spells

Evidence uses the DOS 1.30 executable and the
[address convention](lol2-executable-tables.md). An effect ID selects a
cast, while the acquired-school list uses the IDs passed to the lesson
routine. The fields are documented at their respective readers below.

## Cast tables and resource costs

**CONFIRMED.** The cast dispatcher `0xD0F2C` computes
`effect = u8([0xBB20 + 2*school]) + zero_based_charge` at
`0xD0F4D–0xD0F5E`. The executable has a 16-entry loop bound at `0xFB931`. The checked
interval at `0xFB913–0xFB92A` uses row 0 throughout that loop. Each effect row at
object-5 `0xB95C + 4*effect` is four bytes.

| Row | Fields used here | Evidence |
|---|---|---|
| School at object-5 +0xBB20 | +0 first effect | `0xD0F4D` |
| Same | +1 is a candidate effect count based on contiguous stored ranges | **UNCONFIRMED** per-row use |
| Effect at object-5 +0xB95C | +0 stored cost byte | `0x7C1AB`, `0xD1060` |
| Same | +1 base magic experience for damage feedback | `0xD0CDF` |
| Same | +3 bit 0 selects whether cast state +0x1B2 gets 2 or 3 | `0xD1035–0xD1050` |
| Same | +2 and the remaining +3 bits need further decoding | **UNCONFIRMED** |

**CONFIRMED.** These are the 16 descriptors at
`LOLG.DAT+0x1CCB44` (row `2*school`) and their stored costs.
Cost byte `j` of a school is at
`LOLG.DAT+0x1CC980+4*(first_effect+j)`, using zero-based `j`.
The +1 bytes tile effects 0–112 when used as counts. Their role
as per-school counts and player availability for each range are
**UNCONFIRMED**.

| Cast school index | First effect | Row byte +1 | Stored costs in order |
|---:|---:|---:|---|
| 0 | 0 | 5 | 50, 75, 120, 150, 200 |
| 1 | 5 | 5 | 5, 25, 40, 80, 200 |
| 2 | 10 | 5 | 10, 30, 50, 80, 250 |
| 3 | 15 | 5 | 30, 80, 120, 150, 255 |
| 4 | 20 | 5 | 25, 50, 75, 150, 250 |
| 5 | 25 | 5 | 50, 50, 100, 100, 150 |
| 6 | 30 | 5 | 5, 25, 40, 80, 125 |
| 7 | 35 | 4 | 10, 10, 30, 50 |
| 8 | 39 | 6 | 10, 20, 30, 50, 80, 100 |
| 9 | 45 | 4 | 10, 30, 80, 110 |
| 10 | 49 | 3 | 10, 50, 250 |
| 11 | 52 | 6 | 5, 20, 25, 50, 100, 255 |
| 12 | 58 | 6 | 30, 50, 60, 60, 100, 200 |
| 13 | 64 | 26 | All zero |
| 14 | 90 | 23 | All zero |
| 15 | 0 | 0 | Empty |

**CONFIRMED.** Admission at `0x7C19F–0x7C1E7` compares the cost against
controller word +0x40A. It uses the full stored cost when byte
`[0x23C2D]` is 1, 3, 8 or 9, otherwise `cost >> 1`. Even when
the word is below this amount a nonzero controller byte +0x426 and
charge 5 can pass this gate. Other cast gates are in the surrounding
function.

**CONFIRMED.** Debit at `0xD1056–0xD110F` reloads the unshifted cost.
For effects 0–4, player +0x19A bit 0x20 subtracts a quarter (rounded
down) from that cost. For effects 0x1E–0x22, all three bits 0x20, 0x40
and 0x80 of player +0x19B halve it. Player form byte +0x1AB equal to 2
then halves the adjusted cost. The dispatcher sets its local debit flag
at `0xD0F61`, clears it on the form-1 path at `0xD1030` and on
effect 24 at `0xD1C46`. On a later effect-24 path it can set it
again at `0xD1C9B`. If the flag is set, player
dword +0x145 is reduced by the result, floored at zero
(`0xD1105`, `0xD256A–0xD2574`). The words displayed by the controller
are refreshed at `0x7CE80` (pool word write `0x7CECD`).

### Worked cast

**CONFIRMED.** School 4 charge 1 is effect 20 and its four bytes at
`LOLG.DAT+0x1CC9D0` are `19 0C 00 21`. The ordinary admission check
compares 25 or 12 against the resource word according to `[0x23C2D]`.
On the debit path, effect 20 bypasses the two effect-specific ranges.
With the debit flag set, cost is 25 in form 0, or 12 in form 2. The
effect row's second byte is 12 and is used in the damage reward below.

## Acquisition

**CONFIRMED.** Scroll handlers call `0x8619C` with the acquired-school ID,
after the held-item removal path. Calls at `0x96C8F`, `0x96D4A`,
`0x96E3F`, and `0x96F04` supply respectively 2, 1, 0 and 3. The associated item name rows in
`GLOBAL.MIX` are at `+0x5BD94F`, `+0x5BD0C1`, `+0x5BD96D`
and `+0x5BD9A9`. They identify the four scrolls. The mapping between
these acquisition IDs and named schools in the cast table is
**UNCONFIRMED**. The helper scans dwords at object +0xA0,
using dword +0x9C as count. ID 1 also matches a stored 6
(`0x861CD–0x861E1`). A match returns zero, allowing the normal scroll
effect. ID 5 instead requests message 0x24 and returns 1. When the
requested ID is absent the native table at object-2 +0x2D15C
maps IDs 0, 3, 4 and 6 to message IDs 0x21, 0x22, 0x23 and 0x25.
These branches return nonzero.

When controller +0x29F bit 0x08 is set, message handler `0x81820`
enters the switch at `0x81AB2`. Messages 0x21 through 0x24 call
`0x86418` with IDs 0, 3, 4 and 5 respectively
(`0x81A23`, `0x81A39`, `0x81A4F`, `0x81A65`).
Messages 0x25 and 0x26 call helper `0x8651C` with IDs 6 and 1
(`0x81A7B`, `0x81A91`). Routine `0x86418` appends a dword
school ID and increments the count (`0x86455–0x86473`). It suppresses
a duplicate ID 5 (`0x86423–0x86450`). **UNCONFIRMED.** The full message
timing and all producers of acquisitions need separate call tracing.
The [item effects](lol2-item-effects.md#selected-item-use-handlers)
page documents the original scroll calls individually.

## Hit requests and experience

**CONFIRMED.** The dispatch at `0xD24B1` (object-2 table +0x77E5C)
sends effect IDs 20–23 to `0xD1AB9`, `0xD1B1C`, `0xD1B7F`
and `0xD1BE1`. Their calls to `0x104850`, `0x1049A4`, `0x104AF8`
and `0x104C4C` reach constructors that write pairs of input amounts 10/20, 20/30, 40/35 and 40/60 to
hit-context dword +0x16. The stores are at `0x10495A/0x104985`,
`0x104AAE/0x104AD9`, `0x104C02/0x104C2D` and
`0x104D56/0x104D81`. Both the mode and the target's mitigation
participate in final health change. Effect 24 resolves template 0x5E
at `0xD1CBA`. The scroll handler at `0x96F19` requests the same
template. This identifies a shared input to the two paths.

Damage feedback `0xD0C3E–0xD0E78` skips zero damage. In mode 2, it
loads the effect ID from context +0x15 and base experience from
effect byte +1, and triples the base for signed damage greater than 1
(`0xD0CD8–0xD0CF9`). It compares the context scale dword +0x1A
against the relevant skill byte at player +0x162 (`0xD0CFB–0xD0D13`).
Let `v` be the base after the possible tripling. The original adjustment
switch applies the following integer rules and credits a positive result
through the mode-2 branch at `0xD0E56`.

| Scale minus skill | Award | Branch |
|---:|---|---|
| Below −3 | 0 | `0xD0E28` |
| −3 | `v/4` | `0xD0D3D` |
| −2 | `v - v/2` | `0xD0D61` |
| −1 | `v - v/4` | `0xD0D7D` |
| 0 | `v` | `0xD0D52` |
| 1 | `v + v/4` | `0xD0D9D` |
| 2 | `v + v/2` | `0xD0DBD` |
| 3 | `2*v - v/4` | `0xD0DD9` |
| 4 | `2*v` | `0xD0DFD` |
| Above 4 | `2*v + v/2` | `0xD0E0E–0xD0E1B` |

Division of these nonnegative inputs truncates. For example, effect 20 with
scale 8 and skill 1 awards `2*12 + 12/2 = 30` for one damage, or 90
when damage exceeds one. An odd value `v=13` awards 32 on this branch.

**UNCONFIRMED.** The gameplay labels for the complete effect roster, complete projectile paths for the higher charges, the context-build choices for all targets, and the
native level or quest conditions for each lesson remain open. Trace an
effect's constructor through its frame-event payload and the receiver
described in [combat](lol2-combat-ai.md) to obtain a complete worked hit.
