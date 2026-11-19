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

## Saved frame witness and live producer

**CONFIRMED.** Per-level save selector 67 starts at `0x22C40` and writes
0x51 bytes (`0xE9123–0xE9137`). In the native reference save with SHA-256
prefix `a97f9c4782d4` (level-1 block at slot `0x6EA8`), the decoded delta
at slot `0x19D6F` holds three values at section offsets +0x14/+0x18/+0x1A
(a runtime baseline written by the game, not shipped, is zero at these bytes).
See the [save sections](lol2-save-sections.md). The values are
`[0x22C54]=225280`, `[0x22C58]=880`, and `[0x22C5A]=4`.

**CONFIRMED.** The first two saved values represent 3.4375 ticks in
16.16 and 8.8 (ring sum 110). By the formula below, a whole-tick value
of 4 on that frame needs the whole-tick carry to be at least `0x9000`;
the save's carry cell was not checked.

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

### Live write and conversion

**CONFIRMED.** The program registers the frame clock at 480 Hz: `0xE00D0` pushes `0x1E0` and `0xE00E8` calls the registration routine `0x14F9BC`; a 60 Hz registration follows at `0xE00F0–0xE00F8`.

**CONFIRMED.** A fresh L1_DC run of DOS 1.30 (`LOLG.DAT` SHA-256 prefix
`b27a3534`) under DOSBox 0.74-3 (a build instrumented to log guest
linear-address writes, normal CPU core, with GDB attached to the emulator
as a host debugger; 140,000 fixed cycles, later lowered to 46,884 for the
slow-frame samples) reached the timer service after the
restart at `0xA0457`. Guest write watches saw `0xE0C5C`, `0xE0C82` and
`0xE0CD2` write the three cells before the call at `0xA055B`. The
stores address `EBX+0x4B0/+0x4B4/+0x4B6`. `EBX` was object-5 `+0x227A4`,
which explains why a scan for absolute operands missed these stores. In that run the object-2 base was `0x10068000` (found from a code signature and the page tables) and the relocated operand at `0xB8C0D` was `0x101D0C58`, so the object-5 base was `0x101AE000`; these bases differ between runs.
The same base gives the timer at `EBX+0x4A0` (object-5 `+0x22C44`).
Its counter pointer at +8 matched row 1 of the live `0x1962C` frequency
table. That row's frequency was 480, while rows 0 and 2 held 60 and
120. The program's table compares frequency at `0x15CD30` and installs
the row's counter pointer at `0x15CD4C–0x15CD53`.

| Step | Native computation in the observed positive range | Original DOS instruction |
|---|---|---|
| Frame sample | Read the clock at `0x22C44`. Replace slot `frame_index & 3` in a four-entry ring with the sample capped at 480. Subtract the old slot and add the new one to the sum `S`. | `0xE0BE4–0xE0C3E` |
| Base elapsed `F` at `0x22C54` | `min(0x80000, (S << 16) / 32)` using signed dword arithmetic and truncation toward zero. Four equal samples of 24 from the 480 Hz clock yield `F=0x30000`, or 3 units of the 60 Hz timer. | `0xE0C43–0xE0C73` |
| 8.8 elapsed `W` at `0x22C58` | `W = (F + C8) >> 8`. The carry at object-5 `0x22CCD` becomes `(C8 & 0xFF) + F - (sign_extend16(W) << 8)`. | `0xE0C73–0xE0CB8` |
| Whole ticks `T` at `0x22C5A` | `T = (F + C16) >> 16`. The carry at object-5 `0x22CD1` becomes `(C16 & 0xFFFF) + F - (T << 16)`. | `0xE0CBA–0xE0CF3` |

**CONFIRMED.** After resuming L1_DC from the menu, adjacent samples at
`0xE0BE9` read clock counts `0x34BF` and `0x34D7` (the stored marker
is count plus one). The returned count increments were 24. In a
steady sample the ring held `24,24,24,24`. During the initial run
the same `F=0x34000` and `W=0x340` produced `T=4` on one frame
and `T=3` on the next. This is consistent with the carry formula (a whole-tick carry of `0xC000` would give 4); the carry cell was not logged.

**CONFIRMED.** Reducing the emulator's fixed CPU cycles produced longer
frames. One sample at `0xE0BE9` was 63. Its running sum 246 gave
`F=0x7B000`, `W=0x7B0`, `T=7` before `0xA055B`. At `0xB8CE1`,
the service entered the short countdown path with a previously read
count of `0x25` and decrement 7. The store at `0xB8CE4` subtracts
that decrement from the timer's word at +8. A later sample had
sum 269 and the uncapped `0x86800` at `0xE0C5C`. After the cap at
`0xE0C62–0xE0C69`, the service saw `0x80000`, `0x800` and 8.

The counts, samples and sums above (`0x34BF`/`0x34D7`, 63, 246, 269, `0x25`) were observed in one run and are not constants. Because `F` is always a multiple of `0x800` (or exactly `0x80000`), its low byte is zero, so `W = F >> 8` exactly and the 8.8 carry does not change in the positive range.

## Save restore and menu pause

`tools/lol2_save_native.py --check` (part of `check_all.py`) re-reads the instructions cited in this section.

**CONFIRMED.** The level loader (`0xE7418`) asks the same selector `0xE8914`
as the writer (`0xE8125`). For an admitted raw XOR section it
reads the delta with `0x118820` at `0xE74B7`. It XORs dwords and
then the trailing bytes into the selector's data block at
`0xE751D–0xE7521` and `0xE7552–0xE7559`. For section 67 the
selector returns data `0x22C40`, length `0x51`, flags 3
(`0xE9123–0xE9137`). The three elapsed cells are therefore
restored from section offsets +0x14/+0x18/+0x1A by that XOR.
The adjustment table entry at file `0x1206E4`, dispatched at
`0xEA137`, leads to the common return `0xE97AC`. The sample ring starts at `0x22C62`
and lies inside this section. The index at `0x22CB6` and the
two carry cells lie outside it: `0xE0149` initializes the index,
`0xE0A5A–0xE0A67` increments it, and `0xE0BE9` selects its low
two bits for the ring. The address base used by those instructions
is `0x227A4`, as passed at `0xA05B8`.

**CONFIRMED.** Sections 61 and 63 save each list header, with
pointer, capacity and active count at +0/+4/+8
(`0xB8B54–0xB8B95`, `0xE9142–0xE9198`). Sections 62 and 64
save their capacity-sized arrays of 32-bit pointers. The loader reads
those two arrays directly at `0xE765B` and runs their adjustment
arms at `0xEA077` and `0xEA0C5`. The adjustment is
`new_base + (saved_pointer - saved_base)` within the matched
save-header range (`0xEB2EC–0xEB32E`); a zero pointer remains zero.
The list elements point to event and object records. The service reads
and updates the countdown at event +8 (`0xB8BD1–0xB8C18`,
`0xB8CE4`). For example, placed-item event lists come from
`[0xB7D74] + item.u16(+0x18)` (`0xB71A0–0xB71C7`); their
countdowns are in the section-9 data overlaid from the saved delta
(`0xE8A74`, flags 7; read and decompress at `0xE749C`).

**CONFIRMED for the normal menu open and resume branch.**
The menu at `0xB9204` calls pause at `0xB9321`, dispatches its
menu loop at `0xB9597`, and calls resume at `0xB96A7`.
Pause stops the clock object `0x22C99` (`0xA021F`) and the frame clock
`0x22C44` (`0xA023E`). When `[0xB85C]` is nonzero the menu then calls
`0xE066C(0x227A4, 0x22574)` at `0xB938C`; that pass contains the frame
update, so it can take one more sample, write one ring slot and restart
`0x22C44` while the menu is open. The stop helper consumes the current interval and clears
the marker (`0x14FAA8–0x14FAB3`). Resume reanchors `0x22C99` to the current count at `0xA031A`. It resets the frame accumulator
to zero at `0xA033D` and reanchors it at `0xA034A`.
A stopped clock omits the subtraction from its update (`0x14FA80–0x14FA99`);
reanchoring sets the marker to the new count plus one
(`0x14FAC3–0x14FAD1`). The reset at `0xA033D` is what excludes the menu wall time (and the
partial frame before the pause) from the next clock sample. The frame update still uses the existing ring
samples (`0xE0BE9–0xE0C3E`). The timer service consumes an elapsed
value only when called (`0xB8BDF–0xB8C21`); the menu loop does
not directly invoke it.

### First countdown after save-load and menu pause

**CONFIRMED, saved timer.** DOS 1.30 loaded the game-written L20_BB
autosave with SHA-256 prefix `e2393dbe4d2b`. In that slot, the
L61 active-count XOR at slot `+0x189819` is 1 and the first
L62 pointer at `+0x189825` is `0x1120284C`. The rebasing
arms `0xEA077/0xEA0C5` executed. The first live event was at
`0x11202774`, or L9 buffer +0x18 in this run (L9 stored span
starts at slot `+0x183669`). Its first six bytes
`0A 02 18 00 30 80` identify kind 2, command offset 0x18 and
flag byte 0x30. Mask 0x90 is present, so the service loads the
whole-tick cell at `0xB8BE5`.

**CONFIRMED, first service after load.** The three cells were zero
at the section-67 reader entry (`0xE7418`, selector 67). The
first service at `0xA055B` saw `0x30000/0x300/3`, which
matches L67 XOR at slot `+0x189BDC`, decoded offsets
+0x14/+0x18/+0x1A. That same service changed event +8 from
`0x0A0B` to `0x0A08` with AX=3 at `0xB8CE4`. Only then
did `0xE0BE9` take the first new sample, 43. The first
countdown therefore uses the restored triplet.

**CONFIRMED, first service after pause.** A separate restore of
the same slot used Escape and Resume Game with the same event
active. During an eight-second menu interval the event was
`0x0A05` at both snapshots, the frame-clock marker was zero,
and the ring stayed `[24, 43, 27, 24]`. The resume path
`0xB96A7 → 0xA033D → 0xA034A` cleared the frame accumulator
from 3 to zero and reanchored the marker at `0x0F31`
(`0x14FACE`, read back at `0xA034F`).
The first countdown ran before the first new sample. It
subtracted the existing whole-tick cell 4 at `0xB8CE4`,
taking +8 from `0x0A05` to `0x0A01`. The subsequent frame
sample at `0xE0BE9` was 24, with marker `0x0F49`.
That marker is 24 counts after the resume anchor. The observed
menu interval did not advance the countdown or enter the next
raw frame sample. The first debit and the new clock sample
are distinct points in the update order.
