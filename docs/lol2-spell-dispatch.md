# LoL2 player spell dispatch and lesson conditions

Addresses use the DOS 1.30 [analysis convention](lol2-executable-tables.md).
The [spell table page](lol2-spells.md) gives costs and experience formulas.

## Player effect switch

**CONFIRMED.** The player checks its computed effect byte against `0x22`
at `0xD24A4–0xD24AD` and uses the 35-entry switch at `0xD24B1`
(object-2 `0x77E5C`, file `LOLG.DAT+0x107E80`). Each target below matches
both the on-disk table word and its internal LE code fixup. A value above
34 branches to the common continuation at `0xD1134`. The stored school
ranges above 34 require separate caller analysis.

| Effect | Arm | Verified first effects and calls |
|---:|---|---|
| 0, 1, 3 | `0xD12DA` | Enter common helper `0x10C6BC` at `0xD12E1` with the active effect byte. |
| 2 | `0xD1453` | Call `0x10F660` and set player byte +0x19F in the branch at `0xD1495`. |
| 4 | `0xD1312` | Two paths can call `0x10C6BC` at `0xD132C` and `0xD13C5`. Writes player +0x19F at `0xD137A` or `0xD1409`. |
| 5 | `0xD14E1` | Find a target and check distance (`0xD14F0`, `0xD1537`). Can enter `0x1028A4` or `0x109898` (`0xD1593`, `0xD15CC`). |
| 6 | `0xD15D9` | Find a target and check distance (`0xD1602`, `0xD1649`). Can enter `0x1028A4` or `0x10A330` (`0xD1693`, `0xD16CC`). |
| 7 | `0xD16D9` | Find target, resolve template `0xC2`, call `0x10A9D0` (`0xD16E8`, `0xD172C`, `0xD1746`). |
| 8 | `0xD1753` | Resolve target, call `0x10A4BC` at `0xD17B0`, and write player +0x19E at `0xD17C4` on its branch. |
| 9 | `0xD17DF` | Call `0x10B4C4` at `0xD17FA`. |
| 10 | `0xD1114` | Call `0x7EB40` and `0xD8B94` at `0xD111C` and `0xD112C`. |
| 11 | `0xD120D` | Store `0x0E100000` at player +0x179 and update +0x228 (`0xD121A`, `0xD122D`). |
| 12 | `0xD11C4` | Clear player +0x1B5, store `0x0E100000` at +0x175 and update +0x228 (`0xD11C9–0xD11E5`). |
| 13 | `0xD1240` | Call `0x7EB40` at `0xD124D`. |
| 14 | `0xD125A` | Store `0x02580000` at +0x171 and `0x0E100000` at +0x175. Update +0x227/+0x228 and clear +0x1B5 (`0xD1281–0xD12CD`). |
| 15 | `0xD183B` | Find target, check distance and call `0x1028A4` or `0x107498` (`0xD1864`, `0xD18AB`, `0xD18F5`, `0xD192F`). |
| 16 | `0xD193C` | Call `0x79310`, set a returned object's +0x1D2 to `0x07080000` and update +0x228 (`0xD1971–0xD1998`). |
| 17 | `0xD19E0` | Template lookup at `0xD1A06`, then `0x1080F0` at `0xD1A18`. |
| 18 | `0xD1A25` | Template lookup at `0xD1A4C`, then `0x107C44` at `0xD1A5A` and set player +0x19E bit 1 at `0xD1A62`. |
| 19 | `0xD1A6E` | Clear player +0x217 and write +0x19E at `0xD1AA1–0xD1AAE`. |
| 20–23 | `0xD1AB9`, `0xD1B1C`, `0xD1B7F`, `0xD1BE1` | The constructors at `0x104850`, `0x1049A4`, `0x104AF8` and `0x104C4C` feed the [worked hit formulas](lol2-spells.md#hit-requests-and-experience). |
| 24 | `0xD1C44` | Calls `0x79310` if player +0x195 is zero, then resolves template `0x5E` for `0x104DA0` if +0x17D is zero (`0xD1C77`, `0xD1CC3–0xD1CD1`). The debit can be suppressed. |
| 25 | `0xD1D8D` | When +0x195 ≠ 0, +0x228 & 0x20 is set and +0x1F2 = 0 (`0xD1D8D–0xD1DA6`): call `0x7FE0C` at `0xD1DCA` and store player +0x195 at `0xD1DE1`. Otherwise update +0x19F at `0xD1DEC–0xD1DF7`. |
| 26 | `0xD1E3D` | Calls `0xD6B20`, `0x7FE0C`, `0x7FF34` and `0x80064` at `0xD1E55`, `0xD1E65`, `0xD1E93`, `0xD1EA2`. |
| 27 | `0xD1EC8` | The same four helper destinations as 26, in the order `0x7FE0C`, `0xD6B20`, `0x7FF34`, `0x80064` (`0xD1EFF–0xD1F33`). |
| 28 | `0xD1F59` | Calls `0x7FE0C` and `0xD6B20` at `0xD1F98` and `0xD1FA9`. |
| 29 | `0xD1FB6` | Calls `0xFA5C4`. A zero result sets player +0x19F bit 0 at `0xD207E`. The other path can use template `0x66` and call `0xF9E88`, then jumps to `0xD1134` (`0xD2057–0xD2079`). |
| 30, 31 | `0xD20C5`, `0xD21B5` | Target/distance handling and template `0x5E` fallback to `0x109A24` or `0x109C64` (`0xD218E–0xD21A8`, `0xD227E–0xD2298`). |
| 32, 33 | `0xD22A5`, `0xD2305` | Resolve template `0x6E` and call `0x101F74` (`0xD22DF–0xD22F8`, `0xD233E–0xD2357`). |
| 34 | `0xD2364` | Checks target and distance, then can create the `0x5E` or `0x6E` template path through `0x1028A4` or `0x102EA4` (`0xD23C6–0xD2444`). |

**CONFIRMED.** Effect byte +3 is read by multiple callers. Bit 0 selects
cast state 2/3 at `0xD1048–0xD1050`. The actor path substitutes the player
as target when bit 0 is clear (`0xA4409–0xA4416`). Bit 2, when clear,
sets actor +0xB8 mask 0x1000 (`0xA4435–0xA4463`). Bit 5 gates the actor
cast path at `0xA7E9C–0xA7EB4`, which can record failure 4. A later cost
check compares cost byte +0 with actor word +0x8A (`0xA7EBC–0xA7EDD`).
Bits 6 and 7 are tested as a pair before the `0x5A1F4` call
(`0xAAC81–0xAACBC`).

## Downstream effects 30–33

**CONFIRMED.** Effect 30's template constructor at `0x109A24`
installs vtable `0x6670` and sets effect bytes +0x58 to 8
and +0x56 to zero (`0x109A3D–0x109A51`). With a target,
it positions effect Z at its target Z plus
`(u8(target virtual +0xEC) - floor(u8(animation row +0x0F)/2)) << 16`
(`0x109AB5–0x109AED`). A zero result from slot +0x18
sets bit 1 in effect +0x59 (`0x109AF0–0x109B00`).

The update slot +0x38 (`LOLG.DAT+0x1C76CC`, fixup
`+0x80DC5`) is `0x109718`. It requests removal when
+0x59 bit 1 is set or animation state +0x56 has reached +0x57.
At state 1 it calls slot +0xFC (`0x10975B`), whose fixup
`+0x80B82` at file `+0x1C7790` resolves to
`0x109B0C`. That helper requests sound and, if target
pointer +0x42 exists, dispatches its hit-receiver slot +0x80
with mask `0x10`, flags 5, kind 2, effect 30 and magnitude 5
(`0x109B42–0x109B9D`). The same state then calls
`0x109790`, which checks nearby candidates, rejects the
primary target/source and requires horizontal distance below
0x200000 before calling effect slot +0x100
(`0x1097A1–0x1097F1`, `0x109861–0x109877`).
These are hit inputs. The [combat receiver](lol2-combat-ai.md#hit-context-and-reduction)
applies the target's reduction and health rules.

**CONFIRMED.** Effect 31's constructor `0x109C64`
uses vtable `0x6574`, copies the supplied XYZ and attempts
the same placement slot (`0x109C80–0x109CB7`). It can
also construct the effect-30 object with template 0x5E at
`0x109CC4–0x109CDC`. Its own update slot +0x38 is
`0x109CF0` (file `LOLG.DAT+0x1C75D0`, fixup
`+0x80C10`). With state +0x56 = 3 that handler can
construct another effect-30 object (`0x109CFD–0x109D09`,
`0x109E8B–0x109EA4`).

**CONFIRMED.** Effects 32 and 33 share `0x101F74` with
item handler 2’s successful cast path. The constructor
installs object-5 vtable `0x8734`, copies origin XY,
writes the caller’s mode byte to +0x68/+0x58, and
initializes +0x69 to 4 (`0x101F8E–0x101FC0`,
`0x102027–0x10202A`). A non-null aim argument runs
`0xAF4A8` with 0xC8 and bit 1 of +0x59 is set on
failure (`0x102079–0x10209B`). Slot +0x38 is
`0x10230C` and slot +0xF0 is `0x1021F4` (fixups
`+0x853A0` and `+0x8553C`). The update calls the
latter with flag 2 on failed placement or when +0x69 is
zero (`0x102314–0x102327`, `0x10238F–0x1023A1`).

**UNCONFIRMED.** The visible outcomes of every launch, pulse,
collision and stalled placement are still open. The constructor
and update fields give bounded entry points. Start with the effect
32/33 collision slot +0x30 (`0x102718`) and record writes to
its target before the +0xF0 exit. For effects 30 and 31, compare
the primary and nearby hit receiver results under the same target
definition and difficulty.

## Lessons from native producers

**CONFIRMED.** Item handlers request the lesson via `0x8619C`. The
ID test compares the learned list, and accepts stored 6 as a match for
requested 1 (`0x861C8–0x861E1`). Request ID 5 enters the message-0x24
arm (`0x861E3–0x861F4`). Known call sites include `0x96C8F` (2),
`0x96D4A` (1), `0x96E3F` (0), `0x96F04` (3), `0x96FEC` (4),
and the ID-5 calls at `0x84BE4`, `0x97A4C`, `0x97B04`, `0x97BBC`,
`0x97C74`. For a concrete ID-4 path, handler 34 first removes the held
item and calls `0x8619C` at `0x96FEC`. If that call returns zero, the
ordinary effect continues through `0x7C528` and `0x1049A4`
(`0x97001`, `0x97028`). The request path for an absent ID 4 uses message
0x23 at `0x86230`.

**CONFIRMED.** Two direct producers bypass `0x8619C`:

- Item handler 64 at `0x99820` admits request mode 1, clears the hand
  through `0x77ACC`, then requests message 0x25 at `0x998A7`.
- The player update subtracts `[0x22C54]` from nonzero player +0x185.
  On a result at or below zero, it clears +0x185 and requests message
  0x26 (`0xD2E30–0xD2E61`).

**CONFIRMED.** The message update at `0x81C35` subtracts `[0x22C54]`
from controller +0x310. When negative it adds `4<<16` per advancement
and increases +0x3E0. On reaching half of +0x378, the branch at `0x81C79`
goes to `0x81DD1`, which dispatches messages 0x21–0x26 again at
`0x81DF4`. The calls go to `0x86418` for IDs 0, 3, 4 and 5 (`0x81CB1`, `0x81D04`, `0x81D25`, `0x81D46`) and to `0x8651C` for IDs 6 and 1 (`0x81D67`, `0x81DB7`).
`0x8651C` can replace a learned 1 with 6 (`0x86557–0x86564`). Handler 65
calls it with 6 on equip and with 1 on removal (`0x998E3`, `0x99912`).

**UNCONFIRMED.** A complete named spell roster, the exact downstream
constructor payloads for every target, and the quest producer of each
lesson remain open. The actor entry only proves the listed bit tests.
Effect-row byte +2 has values 0, 1, 2, 3, 4, 5, 7, 10, 30 and 60
among 113 rows at `LOLG.DAT+0x1CC980+4*i`. The direct LE references to
`0xB95C–0xB95F` yielded base pointers and the +1 experience read. A full
trace of every derived pointer is needed to name byte +2. The cast-school
row +1 is read at `0xFB91F` for the row-0 exclusive upper bound. The
non-advancing pointer in that loop leaves general per-school use open.
