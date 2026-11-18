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
0x51 bytes (`0xE9123–0xE9137`). In the original game directory’s root `L1_DC.IMG` and paired
`L1_DC.LSV` documented in [save sections](lol2-save-sections.md), the
baseline bytes at `.IMG+0x4AF92` and the raw delta at `.LSV+0x12EC7` give
three reconstructed values at section offsets +0x14/+0x18/+0x1A:
`[0x22C54]=225280`, `[0x22C58]=880`, and `[0x22C5A]=4`.

**UNCONFIRMED.** Treating the first two as 16.16 and 8.8 gives 3.4375 in both cases. The third value is 4. The arithmetic alone leaves the representation, rounding path and relationship among these saved values open.

**UNCONFIRMED.** The live writer linking the two elapsed cells to a
particular registered 60 Hz counter was not found. Direct LE references
normalized to object-5 offsets `0x22C58` and `0x22C5A` yielded 13 and 28
load sites respectively. None was a direct write. The stop/start calls
on `0x22C44` update the beginning of that clock object. They do not store
at +0x14 or +0x16, the relative locations of `0x22C58` and `0x22C5A`.
The save format can restore those bytes in bulk, with no evidence that it
produces live frame elapsed time. A trace of the first writes after the
menu clock restarts would settle the link. Capture both cells and the
previous/current counter values immediately before `0xA055B` in two frames,
including one long frame or rollover to test fractional carry. Until that
join is established, the reload scalars and the hardware period are
confirmed individually. Exact wall-clock delay for a kind-2 timer,
including pause and frame boundaries, remains open.
