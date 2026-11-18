# LoL2 timer clocks and elapsed units

Addresses use the DOS 1.30 [executable convention](lol2-executable-tables.md).
The [timer record and service](lol2-script-events.md#object-timers) describes
how a callback spends the stored countdown.

## Counter families

**CONFIRMED.** The startup code stores 60 in `[0x223A8]` at `0x14E7F1`.
For a fixed timer (`flags & 0x20`) the reload argument is u8 record +6.
Otherwise `0xB8AE8` calls the RNG with the two endpoints at +6/+7. The
reload and decrement paths give three formulas. Counts below are visits to
kind-2 records when walking object placements in all 15 original archives
using the event-list pointer at placement +0xC.

| `flags & 0x90` | Visits | Reload u16 at `0xB8AF0–0xB8B21` | Runtime input at `0xB8BDF–0xB8C16` |
|---:|---:|---|---|
| `0x10` | 461 | Low word of `selected × 60` | Dword `[0x22C5A]` |
| `0x80` | 95 | Low word of `u8(+6) × 60 × 60` | Dword `[0x22C5A]` |
| `0x00` | 60 | Low word of `selected << 8` | Sign-extended word `[0x22C58]` |

**CONFIRMED.** In `L1_DC.MIX+0x6EB311`, actor 24's timer flags are `0x30`,
its fixed value is 2 and its original count is 120. In `L1_DC.MIX+0x6E9F3B`,
prop 398 has `0x80`, fixed operand 1 and count 3600. In
`L4_HJ.MIX+0xC2CC4E`, prop 2700 has `0x20`, fixed value 50 and count
12800. These are direct file witnesses for the reload scaling.
`0xA055B` calls `0xB30AC`, which services the timer lists at `0xB30BD`.

## Registered 60 Hz source

**CONFIRMED.** The executable constructs 60 Hz timer objects at `0x645CA`
(object-5 `0x2B524`), `0xB8D2A` (`0xB7EF4`) and elsewhere. `0x14F9BC`
passes the requested frequency and the address of the structure's +8
counter pointer to `0x15CD06` (`0x14F9CA–0x14F9DA`). The latter reuses
or installs one of four frequency records and registers an ISR callback at
`0x15CDAF → 0x167C56`. That routine divides 1,193,180 (`0x1234DC`) by
the requested frequency (`0x167CD0–0x167D0C`). The callback updates the divisor only when the candidate is below `[0x1C62C]` (`0x167CD8–0x167CDE`). The 60 Hz rate would set it to 19,886 when 60 Hz is the fastest active rate. Other call sites register 1,500 Hz (`0x169C6B`) and 120 Hz (`0x59A6D`, `0x5F1ED`). The hardware writer sends the divisor low byte
then high byte to PIT port `0x40` after writing mode `0x36` to port `0x43`
(`0x17877B–0x17878C`). At that divisor, the nominal period is
`19886 / 1193180 ≈ 0.0166664 s`. Slower registered callbacks use a 16.16
phase accumulator and invoke their registered function on overflow
(`0x167CF3–0x167D0E`, `0x1681A7–0x168213`).

**CONFIRMED.** Menu paths stop and restart the clock object at `0x22C44`
through `0x14FAA1` and `0x14FABD`, e.g. `0xA0234–0xA0243` and
`0xA0345–0xA034F`. The generic update at `0x14FA79–0x14FA99` accumulates
`current_counter - (previous_marker - 1)` at object +4 and saves marker
`current_counter+1` at object +0. The hardware rate above and this generic
clock arithmetic have separate native call sites.

## Saved frame witness and open producer

**CONFIRMED.** Per-level save selector 67 starts at `0x22C40` and writes
0x51 bytes (`0xE9123–0xE9137`). In the native reference save with SHA-256
prefix `a97f9c4782d4` (level-1 block at slot `0x6EA8`), the decoded delta
at slot `0x19D6F` holds three values at section offsets +0x14/+0x18/+0x1A
(a runtime baseline written by the game, not shipped, is zero at these bytes).
See the [save sections](lol2-save-sections.md). The values are
`[0x22C54]=225280`, `[0x22C58]=880`, and `[0x22C5A]=4`.

**UNCONFIRMED.** Treating the first two as 16.16 and 8.8 gives 3.4375 in both cases. The third value is 4. The arithmetic alone leaves the representation, rounding path and relationship among these saved values open.

**CONFIRMED.** Two clock operations about 0x110 bytes before the
main service `0xA055B`, with other calls between them (among them the restart
`0x14FABD(0x22C44)` at `0xA0457`, which writes object +0/+4 only), belong to separate storage. At `0xA042F–0xA0445`,
`0x14FA79(0x22C99)` returns the accumulated clock into
`[0x22CA9]`. The reset of object `0x22C44` at `0xA044A`
passes two zero arguments. Its helper clears object +0 and
writes object +4 at `0x14FADE–0x14FAEA`. The alternate
wrapper at `0xA0D0F → 0x748C4` also calls that reset
helper. Neither reset writes the frame cells +0x10/+0x14/+0x16
relative to the second clock object. At `0xA0508–0xA055B`
the first helper `0x62FC4` returns immediately, and
two calls before the timer service take the list-pointer pairs
`0x67460([0x22D44], [0x22D64])` at `0xA053E` and `0x110754([0x22D54], [0x22D74])` at `0xA0553`.
This identifies which clock and dispatch paths were inspected.

**UNCONFIRMED.** The live frame writer is still open. The
word and dword loads at `0xB8C0D` and `0xB8BE5`
identify the countdown inputs. Checking LE references and
absolute write operands overlapping the three frame cells
in the retail main code object found no direct store. The
level save can restore them together (`0xE9123–0xE9137`).
To distinguish a computed live write from a restore, capture
the first store to each cell after the main update restarts,
before `0xA055B`. Record the previous/current value
from the producing counter and include a long frame to test
fractional carry. Wall-clock delay across pauses and frame
boundaries remains open.
