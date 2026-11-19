# LoL2 combat and creature decisions

The code references below use the DOS 1.30
[address convention](lol2-executable-tables.md). The common combat
routine uses a temporary hit context. Actors and the player take
different receiver paths around that routine. The
[creature transition reference](lol2-creature-transitions.md) follows
the behavior dispatch, state updates and animation changes.

## Hit context and reduction

**CONFIRMED.** The common path `0x62728` uses the following fields.
The creature receiver seeds both health fields from actor
u16 +0x88 at `0xA6C69–0xA6C85` and calls the common routine at
`0xA6CBE`. The player table's +0x80 slot at
`LOLG.DAT+0x1C6CC4` resolves to `0xD03B8`, whose corresponding
health input is player dword +0x14D (`0xD03C9–0xD03E1`).

| Context field | Type | Use and evidence |
|---|---|---|
| +0, +2 | u16 each | Mask and flags. Set by melee from definition +0x3B/+0x3D, read by the accumulation loop `0x62ADC–0x62E72`. |
| +4, +8 | pointers | Target and attacker, read at `0x62890` and `0x628BF`. |
| +0x14, +0x15 | u8 each | Kind and effect or subtype. Kind branches at `0x62926`. Effect drives magic reward at `0xD0CD8`. |
| +0x16 | s32 | Input magnitude. Negative values are replaced by starting health (`0x62737–0x62744`). |
| +0x1A | s32 | Experience scaling input at `0xD0C75`. Its effect on reward is in [spells](lol2-spells.md#hit-requests-and-experience). |
| +0x1E | s32 | Final loss, clamped to starting health at `0x62ED0–0x62EE4`. |
| +0x22, +0x26 | s32 each | Health before and after. After is floored at zero (`0x62F58–0x62F67`). |

**CONFIRMED.** The ordinary player strike at `0x88D2C` first offers
the equipped item a mode-5 hook (`0x88F7F`). A zero return takes the
ordinary hit path. At `0x89045–0x8916D` that path assembles damage
input from dwords `[0x236DC]+[0x236E4]+[0x236EC]+[0x236F4]` and a
sign-extended high byte from `[0x2372C]`, places it in +0x16 and
dispatches target vtable +0x80. The full set of summand roles remains **UNCONFIRMED**. Handler 4’s temporary contribution at `0x236E4` is verified at `0x961C7` and `0x9633C`. For the others, follow structure-relative stores to the four dwords and high byte of `0x2372C` before a strike at `0x88D2C`.

**CONFIRMED.** Difficulty uses byte `[0xB7FB2]` read at `0x62868`.
Its configuration value is clamped to 0–2 at `0xCC0C3–0xCC0F7`
and copied at `0xCCD5C–0xCCD61`. Apply target scaling before
attacker scaling on the adjusted input amount.

| Difficulty | Player target | Player attacker | Source |
|---:|---|---|---|
| 0 | Divide by 3 toward zero if amount >3 | Double | `0x6288C–0x628D4` (entered from `0x6294D`) |
| 1 | Keep | Keep | `0x6286D–0x62875` |
| 2 | Double | Halve toward zero if amount >2 | `0x628D9–0x6291F` |

**CONFIRMED.** After initial modifiers the routine computes an intermediate
signed 16.16 amount. For kinds 0, 1, 3, 4 and 5, let `A` be the
current amount and `S` the target scalar, using 1 when supplied as
zero. With context flag 0x08 or mask zero it uses `A << 16`.
Otherwise, for positive `A`, use
`A * ((A << 15) / S)` when `S ≥ A`, or
`A * (0x10000 - (S << 15) / A)` when `S < A`.
These branches are in `0x62922–0x629D2`. Kind 2 at
`0x629D2–0x62A9C` uses a different path. It scales by the ratio of the
attacker and target vtable +0xE8 bytes when the attacker is present,
and subtracts scalar-weighted excess above the original 16.16 amount.

**CONFIRMED.** The mask loop divides the amount among the set mask bits
and, when there is more than one, the set bits of flag word & 0xE7
(`0x62A9C–0x62BCF`). With a descriptor present and a nonempty mask,
matching descriptor rows can modify each contribution. The selector
table begins at `LOLG.DAT+0x99704`, with index `selector - 2` and the
slot fixups at `0x3E391–0x3E3C9`. Mask and flag tests immediately precede
the switch at `0x62C68–0x62CA7`. Selectors 0, 1 and above 10 skip the
row at `0x62C49–0x62C62` and `0x62E54–0x62E60`.

| Selector | Effect on a matching contribution | VA |
|---|---|---|
| 2, 3, 4 | Multiply by 2, 3, 4 respectively | `0x62CE6`, `0x62CF8`, `0x62D0B` |
| 5, 6 | Halve or multiply by three-quarters, respectively, under the flag test | `0x62D4C`, `0x62D76` |
| 7 | Record the matched bit, set the working contribution to zero and stop scanning this bit, under the flag test | `0x62DA7` |
| 8, 9 | Call target vtable +0x84 with the rounded half or full contribution, respectively, then zero that contribution | `0x62DDC`, `0x62E1F` |
| 10 | Take the signed quarter, under the flag test | `0x62D1E` |

Nonpositive combat edge cases and exact semantics of every descriptor
flag remain **UNCONFIRMED**. The final slot is converted with
`sar(fixed + 0xFFFF, 16)` at `0x62EB9–0x62EC9`, which rounds a
positive fractional loss upward. The creature receiver runs its script
handler and then sets health from +0x26 at `0xA6CC8–0xA6CDF`.
The health setter calls the death handler for a zero result unless one
of its gates applies (`0xA7A9C–0xA7AD4`).

## Scripted hits and thresholds

**CONFIRMED.** Opcode 19's `0x66130` copies command u16 +4/+6 into
context mask and flags, then sends a hit through target vtable +0x80
at `0x661DF`. Command +9 = 0 uses u8 +8 directly. Values 1 and 2
multiply u8 +8 by the target's vtable +0x8C or +0x88 return and divide
by 100 respectively (`0x66174–0x661BB`).

**CONFIRMED.** Object kind 9 at `0xAE2C8` applies two masks. A zero
record mask is a wildcard. A nonzero u16 +4 or +6 must overlap context
u16 +0 or +2 respectively (`0xAE313–0xAE353`). The lower three bits
of record +9 select a threshold test against u8 +8. The mode table
is at object-2 +0x55290.

| Mode | Threshold test | VA |
|---:|---|---|
| 0 | Reject | `0xAE369` |
| 1 | Loss ≥ threshold | `0xAE358` |
| 2 | Subtract loss from the threshold in a temporary and accept if the remainder is ≤0 | `0xAE38D` |
| 3 | `health_after <= threshold < health_before` | `0xAE3A6` |
| 4 | `health_after <= threshold`, subject to a special pool check on level 5 | `0xAE3BA–0xAE42F` |

At `0xAE49D–0xAE4FD`, the first matching record that passes its
predicate enters the command queue. +9 bit 0x80 clears the whole mode
byte after that success. Otherwise the temporary threshold is written
back. The mode-2 failure with a positive remainder bypasses that store
(`0xAE39A → 0xAE369 → 0xAE4E3`).

## Creature state and attack output

**CONFIRMED.** The actor constructor reads the definition u16 +0x63 into
actor +0xB0, which vtable +0x8C uses as a health cap
(`0xA2197–0xA21A0`, `0xA7B8C`). The live actor state byte +0xA8
becomes 0x0F on the death path at `0xA77DF`. Actor +0x88 becomes
zero at `0xA77EB`. The actor element survives in save section 21,
as shown in the [save format](lol2-save-format.md#level-blocks).

**CONFIRMED.** The actor update at `0xAA208` refreshes the target
observations at actor +0x9C/+0x9D/+0x9E. It clears two invalid target
pointers at +0x38 and +0x34 on the corresponding refresh failures
(`0xAA26A–0xAA279`, `0xAA2B6–0xAA2C9`). Bits 4–5 of actor dword
+0xB8 select preparation paths at `0xAA2D6–0xAA305`. In the
constructor and this update, u8 actor +0x4F (`p`) and u8 +0x4E
(`q`) feed `0xA1F2C`. Let `B` be definition byte +0x81 and
`M=max(1, floor(B/10))`, written to definition +0x82 by
`0xA1D28–0xA1D46`. The returned value is:

| Input | Result at `0xA1F2C` |
|---|---|
| `p=0` | `max(M, 1)` |
| `p>0, q=0` | `B` |
| `p>0, q>0` | `max(M, floor(B*p/(p+q)))` |

The updater stores that value into actor +0xA6, and its complement
from `B` into +0xA7 at `0xAA3F7–0xAA427`. Nonzero actor byte
+0xA3 reduces both by their integer quarter (`0xAA42D–0xAA47E`).
The frame timer at `0xA55C4–0xA560C` subtracts the elapsed word
`[0x22C58]` and adds the current state's dword +4 shifted right 8 after
expiry. A kind-1 frame event produces `floor(actor.A6 * event.u8(+2) / 100)`
at `0xA5783–0xA5799`. When the hit has a nonzero
quotient, `0xA57DB` stores it as the hit input and `0xA57E6`
delivers it to the target. Frame event +4/+6 supply mask and flags.

### Worked creature attack

**CONFIRMED.** Hive executioner definition byte +0x81 is 30 at
`L5_HC.MIX+0x5BF2DB`. The CSV-style entry at `GLOBAL.MIX+0x6A3AC0`
(key 0xCC491243) contains 50 in each of the third and fourth data
rows. The constructor copies the source profile into the actor at
`0xA231A`. The [profile loader](lol2-creature-transitions.md#profile-source)
links this definition to the CSV entry. With 50 in each relevant actor byte, +0xA6 is 15, or 12 on the +0xA3 nonzero
branch. A native frame record at `L5_HC.MIX+0x5C014F` is
`01 08 32 00 08 00 24 00`: frame 8, 50 percent, mask 8 and flags
0x24. The input is 7 or 6 before target handling. It varies with
actor state and the target's eventual health loss can differ.

**UNCONFIRMED.** The complete AI mode transitions, the first producer of
actor +0xA3, and all condition-driven changes to the profile need additional
caller tracing. The places to inspect first are the two branches from
`0xAA2FC/0xAA305`, the remaining state changes to actor +0xA8 (the frame
reconciliation is traced in [creature transitions](lol2-creature-transitions.md)) and each call to
`0x5A1A0` that adjusts the 30 active stat bytes.
