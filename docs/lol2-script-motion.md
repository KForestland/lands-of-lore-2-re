# LoL2 deferred sequence and region motion

The addresses below use the DOS 1.30 [analysis convention](lol2-executable-tables.md).
Command offsets are relative to the start of the command. Screen and world
updates here are read from native instructions.

## Opcode 18

**CONFIRMED.** The command occupies `[0xB7D5E]` only when vacant
(`0xB59CE–0xB59E8`). If command word +0xA has `0x20` set, this queue path
calls `0x660F8`, clears the slot and sends object kind-6 value 6
(`0xB59ED–0xB5A0E`). `0x660F8` clears +0x10/+0x11 and clears `0x20`.
It also clears `0x10` unless `0x02` is set. Thus the immediate path is a
reset/completion path. The deferred motion path takes the live command from
`[0xB7D5E]` at `0xB2A54` and passes the object's XYZ, orientation and other
motion inputs to `0x65BB0` at `0xB2A88`. It writes the returned orientation
word to object +0x1E (`0xB2A96`). If the object method at vtable +0 returns class 1, it also writes the returned
dword to `[0x22CB1]` and calls `0x7C908` (`0xB2A9E–0xB2ABD`). The caller
clears the slot and dispatches return codes 0–3 at `0xB2ADA`. Return 1 calls
vtable +0x18 with argument 0, return 2 with 1, and 0/3 share the continuation
(table VA `0xB285C`, object-2 `0x59838`, arms `0xB2AE2`, `0xB2AF4`, `0xB2B07`).

**CONFIRMED.** `0x65BB0` calculates these parts of deferred motion.

| Fields or inputs | Calculation | Native evidence |
|---|---|---|
| Progress byte +0x10 | Add the low byte of `[0x22C5A]`. If the resulting byte is below the old value, set it to 255. | `0x65BDB–0x65BEE` |
| X/Y target, s16 +4/+6 | Convert to 16.16 and subtract current X/Y before calling the direction/distance helper `0x111C34`. That helper writes direction and distance at result +0/+4. | `0x65D27–0x65D7B`, `0x111C42–0x111C9F` |
| Z target, s16 +8 | Used when flags & `0x100` is set. The difference from current Z is converted into a Z contribution through `0xDD8F4`, then bounded by the same step magnitude as X/Y. | `0x65D86–0x65DB0`, `0x65E47–0x65EDE` |
| Target speed u8 +0xF | If flags & `0x80`, use it directly. Otherwise move the current speed parameter toward it by at most u8 +0x10. The 16.16 step magnitude is `trunc([0x22C54] * floor(5*speed/2)/60)`, with the native signed multiply and quotient. | `0x65CCF–0x65D27`, `0x65DB2–0x65DC1`, `0x1118F4–0x111937` |
| Orientation u16 +0xC | Flag `0x800` copies it directly. Otherwise, if flag `0x08` is clear, the orientation steps by the shortest wrapped direction selected at `0x65F60–0x65F9D`. The target selection uses +0xC or the motion heading depending on the movement and flags. | `0x65F0E–0x66015` |
| Player-specific dword | For command byte +1 equal to 1, target = `s8([0x225B0]) - 2*s8(command+0xE)`. The returned dword moves toward it by up to `u8(+0x10)>>2`. | `0x65BF2–0x65C1B`, `0x6601B–0x66086` |
| Snap and completion | Flag `0x04` writes the destination coordinates directly, sets `0x20` and returns 2. The completion branch at `0x66088` also writes the destination, sets `0x20` and returns 1. A Z write in either case requires `0x100`. | `0x65C3C–0x65CC5`, `0x66088–0x660E3` |

**CONFIRMED.** `L1_DC.MIX+0x6FD8E1` commands the player toward X 536 and
Y 11154 with speed 10 and flags `0x0885`. With a vacant sequence slot and
ordinary deferred dispatch it takes the direct-coordinate path, because
`0x04` is set and `0x20` is clear. X/Y become `536<<16` and `11154<<16`.
The absence of `0x100` leaves Z unchanged on that path.

### Deferred continuations

**CONFIRMED.** The original object-update switch calls vtable +0x18
with 0 for the end-of-movement return and 1 for the direct-coordinate
return (`0xB2AE2–0xB2AFA`). Player vtable +0x18 at
`LOLG.DAT+0x1C6C5C` resolves to `0xD0204`. Argument 1 clears
player +0x227 bit 0x10. If player dwords +0xB5 and +0xB9 are
both zero the wrapper sets them to `0x3FFFFFFF` and `0xC0000000`
and clears byte +0x1E5, then forwards to `0xAF260`
(`0xD0204–0xD024E`). Creature vtable +0x18 at
`LOLG.DAT+0x1C690C` goes directly to `0xAF260`.
The 0/3 continuation calls `0xAF9A4` with the object after setting
`[0xB7D68]` to 1 (`0xB2B07–0xB2B15`).

**CONFIRMED.** `[0x22CB1]` contributes to vertical projection. The
renderer arithmetic at `0x137719–0x137735` adds the product of
`(s32([0x22CB1]) >> 1)` and its local scale factor to the vertical
term before testing the viewport. The paired write to object +0x1E
is passed to `0x7C908` and stored in controller word +0x3FC
(`0xB2AB3–0xB2ABD`, `0x7C95F–0x7C96A`).

**UNCONFIRMED.** Presentation units, downstream `0xDD8F4` corner
cases and dynamic +0x18 receivers in the other selector pools. For one
Z-enabled command, follow `0xDD8F4` to its region/object rejection
branches and record the XYZ result. Follow the indirect call at
`0xB2AE7` or `0xB2AFA` with a selected object from each remaining pool.

## Opcode 196

**CONFIRMED.** `0x64DDC` uses u16 +2 as a region index with stride 44.
Bit 0 of command +6 selects the region's ceiling word +0x16 when set or
floor word +0x14 when clear. The equivalent code reads the high word of
a dword from +0x14 or +0x12, respectively (`0x64FBA–0x64FC9`). Region
byte +0x28 uses active bit `0x80` for ceiling and `0x40` for floor. This
also explains the conflict test at `0x64E20–0x64E52`. `+4` is the signed
height operand. For initial admitted commands, the engine stores it as
remaining movement in +0xA if +6 bit 3 is set, or subtracts the current
height first when that bit is clear (`0x64FCC–0x64FE3`). +0xA is live state.

**CONFIRMED.** For a nonzero speed +7, let `A` be accumulator u16 +8 and
`F` be `[0x22C54]`. Each motion pass adds `trunc(F * floor(5*u8(+7)/2)/60)`
to `A`, stores the low word and takes the signed high word as the step
magnitude (`0x6507B–0x650CB`). With speed zero the magnitude is the native
signed-word absolute value of the remaining delta (`0x650CD–0x650DC`).
The sign of +0xA sets the direction. The resident-object/neighbor check
at `0x65111 → 0xB861C` gates movement. A passing step reduces the remaining
amount and clamps to the last step when it would cross zero (`0x6512A–0x65162`).
When +0xA reaches zero, the handler resets the accumulator and returns 1
(`0x651CF–0x65268`). A nonzero remaining amount returns 0 (`0x65275`).

### Eight stores after calls

**CONFIRMED.** The store numbering counts native memory destinations
including stack slots, with the first at `0x64E10`. The event callback
`0xF2FC0` can run a kind-11 group (`0xF3018–0xF30C6`). The geometry helper
`0xF3A5C` sets region +0x28 bit 5 and can mark or visit adjacent regions
(`0xF3A69–0xF3AF9`). The following stores derive their values from reloads
or preserved locals, without using either callback's return value.

| Store | VA | Value after the call |
|---:|---|---|
| 20 | `0x6501C` | Reload region byte +0x28, OR `0x80` and store it after the initial ceiling event 2 or 3 (`0x6500B`). The second ceiling event is 13 (`0x6501F`). |
| 22 | `0x65058` | Reload region byte +0x28, OR `0x40` and store it after initial floor event 0 or 1 (`0x65047`). The second floor event is 12 (`0x6505B`). |
| 30 | `0x6517C` | After `0xF3A5C`, load ceiling word +0x16 and add the preserved, signed step in ESI, retaining the low word. |
| 34 | `0x651A3` | After `0xF3A5C`, load floor word +0x14 and add the preserved, signed step reloaded from `[EBP-0x10]`, retaining the low word. |
| 36 | `0x651C0` | With floor option `0x10`, store `min(255, u8(region+0x27)+step)` in a stack local. |
| 37 | `0x651CC` | With the same option, store `max(0, min(255, u8(region+0x27)+step))` to region +0x27. |
| 40 | `0x65211` | After completion ceiling event 6 or 7 (`0x65200`), reload region byte +0x28, clear `0x80` and store the result. Then emit event 17. |
| 43 | `0x65247` | After completion floor event 4 or 5 (`0x65236`), reload region byte +0x28, clear `0x40` and store the result. Then emit event 16. |

**CONFIRMED.** Cancellation during the queued-command lookup requires the
same region index and side bit (`0x64EF1–0x64F25`). It clears the corresponding
region mask, emits the side's event 16 or 17, zeroes the older command's
+0xA and removes that node (`0x64F50–0x64F8E`). The event following
completion uses the sign of the entry value of +0xA at
`0x651E1` or `0x65216`. In the start path the jump from `0x64E1A` and
those from `0x65027` or `0x65063` keep initialization and tick updates distinct.

**CONFIRMED.** `L1_DC.MIX+0x6E716F` has region index 7, +4 = −367, flags
zero and +7 = 100. The original region row at `+0x6D0D2B` has a floor
of −395 at +0x14 and has +0x28 clear. Using the unmodified row for the
native initialization makes remaining delta −367 − (−395) = 28 and
sets the floor-active bit. The per-update numerator uses `floor(5*100/2)`
= 250. Event scripts or prior commands may change the row before this site runs.

### Admission and reversing commands

**CONFIRMED.** The start request's second argument must be nonzero
and the chosen region side's active bit must be clear for a new
initialization (`0x64E13–0x64E56`). On the conflicting-start path
with nonzero remaining delta and both option bits `0x04` and `0x08`
set, the low-word arithmetic changes the signed height operand `H`
to `−H` and the remaining delta `R` to `R − H` in both sign arms
(`0x64E6E–0x64EB8`). This is a modulo-65536 update to both words.
On normal completion with those bits set, `0x6525F` negates the
height operand again. Original examples with those options are
`L14_HT.MIX+0xB300DA` (floor, options `0x0C`) and `+0xB300F8`
(ceiling, options `0x0D`), both with a zero initial remaining word.

**CONFIRMED.** The gate at `0xB861C` checks every resident node,
then follows a list of up to four nonnull neighboring regions only
when all resident calls passed (`0xB862B–0xB86B9`). The routine
`0xB6D98` receives object, region, step and side. Its early filters
include zero step, object flag `0x80` clear, nonzero class slot +0x78,
object flag `0x200000` set, or region +0x1C bit `0x80` set
(`0xB6D9F–0xB6DF6`). These branches bypass the obstruction comparison.
The comparison path derives upper and lower surfaces from the region
words or coordinate-dependent helpers, applies the signed step on the
selected side and compares clearance to class slot +8 shifted left 16
(`0xB6DFC–0xB6E9A`). Remaining obstruction goes to the class path
at `0xB6EA0`, which can return zero or deliver a hit through slot
+0x80 (`0xB6F41–0xB6FA8`). Passing paths can add the shifted step to
object +0x1A and set its update flag, depending on its side and region
binding (`0xB6FB2–0xB70C1`).

**UNCONFIRMED.** Which nearby objects make the same geometry command
stop in play. Isolate a floor or ceiling command while changing only
one resident object, then compare the virtual methods at `0xB6DCC`,
`0xB6E8F` and the returned gate at `0x65111–0x65118`.
