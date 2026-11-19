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
and update fields give bounded entry points; the effect 32/33
contact packet is traced in [effect 32/33 contact](#effect-3233-contact).
For effects 30 and 31, compare
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

## Payloads of the 35 player slots

**CONFIRMED.** These are downstream native results for the 35
player-dispatch switch slots at `0xD24B1`. Some results are
conditional on target, form, animation phase or template availability.
The listed hit amounts are inputs to the receiver, and are reduced
by the [combat rules](lol2-combat-ai.md#hit-context-and-reduction).
Each four-byte source row starts at `LOLG.DAT+0x1CC980+4*effect`.
The 35 dispatch slots cover IDs 0–34. The data table extends to 112.

The first spell helper uses a second five-slot jump table at
VA `0x10C6A8` (disk `LOLG.DAT+0x1436A8`), dispatched at `0x10C82F`. It performs the
target search at `0x10C6D1`. With no target and `[0xEDD4]`
clear it sets `[0x22713]&1` and can play failure feedback.
Its index-2 entry returns based on target presence. The player
effect switch calls the independent constructor described in
row 2 for that ID (`0x10C6D1–0x10C738`,
`0x10C761–0x10C772`, `0xD1453`).

| ID | Confirmed downstream payload |
|---:|---|
| 0 | Template 0x7A selects constructor `0x10CF60`. It initializes effect byte +0x58 to 0x1F and a base `300<<16` at +0x6A on its nonzero-duration branch. The +0x38 update at `0x10D174` can set +0x66, clear the linked object's +0x38, and modify its +0xB6 and +0x59 (`0x10C739–0x10C75E`, `0x10CF87–0x10D008`, `0x10D199–0x10D1FA`). |
| 1 | Template 0x7A selects `0x10DA10`, with +0x58 = 0x20 and base `360<<16` at +0x6A. Its +0x38 update at `0x10DC68` has the corresponding linked-object writes (`0x10C773–0x10C794`, `0x10DA36–0x10DAA8`, `0x10DC8D–0x10DCF4`). |
| 2 | `0x10F660` creates the effect only when `[0xEDD4]` and `[0xDF6B4]` admit it. It uses vtable 0x9908, selects target +0x42, sets animation byte +0x58 to 0x17 and resets +0x56. Its update picks +0x58 values 0x1D, 0x1E or 0x19 on separate paths (`0x10F660–0x10F6AB`, `0x10F6D8–0x10F794`, `0x10FD44–0x10FD97`). |
| 3 | Template 0x7E selects `0x10E8C0`, +0x58 = 0x2B and base `420<<16` at +0x6A. The update at `0x10EDD0` can write +0x66 and modify the linked object's +0x38, +0xB6 and +0x59 (`0x10C7E9–0x10C808`, `0x10E8E5–0x10E963`, `0x10EDF5–0x10EE56`). |
| 4 | With a target, the secondary switch selects template 0x7A and `0x10E2F8`, setting +0x58 to 0x2A. The constructor can use `0x1028A4`. It also has a target-hit path at `0x10E414` followed by `0xAB948` and timer +0x6E = `10<<16` (`0x10C7A9–0x10C7D8`, `0x10E31A–0x10E37C`, `0x10E3B7–0x10E436`). |
| 5 | The normal targeted branch uses the `0x109898` object. Its shared update's +0xFC callback submits hit words 1/1, kind 2, ID 5 and magnitude 5 to target +0x80 (`0x1098BB`, `0x109718–0x10975B`, `0x109956–0x1099AC`). |
| 6 | Corresponding `0x10A330` object, hit words 1/1, kind 2, ID 6 and magnitude 15 (`0x10A353`, `0x10A3EE–0x10A444`). |
| 7 | Template 0xC2 constructs vtable 0x6478 with +0x58 = 4 and +0x66/+0x68 zero. Update `0x10B044` has an animation reset and cleanup at `0x10B09E–0x10B0B9` (`0xD172C–0xD1746`, `0x10A9FE–0x10AA3F`, fixup `LOLG.DAT+0x8064D`). |
| 8 | Vtable 0x637C update submits two kind-2 ID-8 hits: mask/flags 1/1 magnitude 40, then 0x100/4 magnitude 20 (`0x10A4ED`, `0x10A89A–0x10A923`, fixup `LOLG.DAT+0x80484`). |
| 9 | `0x10B4C4` can select the vtable-0x6280 object. Its update submits two kind-2 ID-9 hits with flags 0x12 both times. Mask 1 has magnitude 5 on the player or 10 on another target. Mask 0x100 has magnitude 1 on the player or 3 on another target (`0x10B558–0x10B569`, `0x10B5F0`, `0x10BA2F–0x10BAF2`). |
| 10 | The `0x7EB40` arm sets controller +0x29C bit 0 and advances a shared byte. The player skill helper changes dword +0x15D and can increase skill byte +0x162 and rebuild resource values (`0xD111C–0xD112C`, `0x7EB54–0x7EB8B`, `0xD8BAF–0xD8C59`). |
| 11 | Arms player +0x179 with `3600<<16`, changes +0x228 and calls `0x7F200` (`0xD121A–0xD1233`). |
| 12 | Clears player +0x1B5, arms +0x175 with `3600<<16`, changes +0x228 and calls `0x7C7DC`. One continuation calls `0x7EFB0` (`0xD11C9–0xD1200`). |
| 13 | Controller effect through `0x7EB40`. It sets +0x29C bit 0, selects +0x427 according to whether the argument is at least 11, and can set +0x298 and issue feedback (`0xD124D`, `0x7EB54–0x7EB8B`, `0x7EC28–0x7EC5C`). |
| 14 | Combines player +0x171 = `600<<16` and +0x175 = `3600<<16`, changes +0x227/+0x228, clears +0x1B5 and uses refresh paths `0x7F444` and `0x7C7DC` (`0xD1281–0xD12CD`). |
| 15 | Constructor `0x107498` sets vtable 0x7278 and places the effect. Update +0x38 is `0x107A84` and can remove it through `0xFBC54` (`0x1074BC–0x10756B`, `0x107A84–0x107AAA`, fixup `LOLG.DAT+0x8268D`). |
| 16 | Returned object from `0x79310` receives +0x1D2 = `1800<<16`; player updates byte +0x228 (`0xD1971–0xD1998`). |
| 17 | Vtable 0x7080 effect initializes +0x5E = `1800<<16`, +0x62 and +0x58 to zero, and tries placement. The update and incoming-hit handlers change stage +0x63; in stages 2 and 4 the contact handler counts +0x64 down and, below 10, clears creature +0x38 links and sets flag +0x62. See [effect 17 callbacks](#effect-17-callbacks). |
| 18 | Vtable 0x717C update dispatches mask/flags 0x40/1, kind 2, ID 18 and magnitude 1 to the live +0x5E target (`0x107C6A`, `0x107FCB–0x108026`, fixup `LOLG.DAT+0x824C4`). |
| 19 | Clears player +0x217 and changes +0x19E after the `0x7C5DC` and `0x7C528` feedback calls (`0xD1A6E–0xD1AAE`). |
| 20 | Constructor `0x104850` submits magnitude inputs 10/20 (`0x10495A/0x104985`). |
| 21 | Constructor `0x1049A4` submits 20/30 (`0x104AAE/0x104AD9`). |
| 22 | Constructor `0x104AF8` submits 40/35 (`0x104C02/0x104C2D`). |
| 23 | Constructor `0x104C4C` submits 40/60 (`0x104D56/0x104D81`). |
| 24 | Template 0x5E constructs vtable 0x7A58 and selects its context via `0x104DD4`. The constructor uses the target's +0x88 virtual operation and range checks. Update at `0x104FA0` tests `[0x226F1]` (`0xD1CC3–0xD1CD1`, `0x104DBE–0x104E7A`, fixup `LOLG.DAT+0x838C5`). |
| 25 | When +0x195 is set, +0x228 bit 5 set and +0x1F2 zero, it uses controller `0x7FE0C`, changes `[0x23AB6]` and stores the local value in +0x195. Otherwise updates player +0x19F (`0xD1D8D–0xD1DF7`). |
| 26 | With nonzero form and +0x228 bit 4 set, passes zero mode to `0xD6B20` and enables controller state through `0x7FE0C(1)`. Otherwise calls `0x7FF34(1)` and `0x80064(1)` (`0xD1E3D–0xD1EA2`). |
| 27 | Same condition, but calls `0xD6B20(player, 2, 60)`; same alternate controller state as 26 (`0xD1EC8–0xD1F33`). |
| 28 | Admitted path uses `0x7FE0C(1)` and `0xD6B20(player, 1, 60)` (`0xD1F59–0xD1FA9`). |
| 29 | Template 0x66 constructor `0xF9E88` installs vtable 0xA4D8 and starts +0x58 at 1. Update `0xFA148` can reset +0x56 and call the effect removal and follow-up helpers `0xFBC54` and `0xFBAF0` (`0xF9EB8–0xF9F1F`, `0xFA1C9–0xFA1E4`, fixup `LOLG.DAT+0x8A7A9`). |
| 30 | Primary hit mask/flags 0x10/5, kind 2, ID 30 and magnitude 5. See the primary and nearby-target arms above (`0x109B42–0x109B9D`). |
| 31 | Its vtable-0x6574 object can create one effect-30 object immediately and another at +0x56 = 3 (`0x109CC4–0x109CDC`, `0x109CFD–0x109D09`, `0x109E8B–0x109EA4`). |
| 32, 33 | Share the vtable-0x8734 projectile. At `0x102718`, nonzero byte +0x6A is cleared and returns 1 immediately. An initially zero byte reaches `0xFB9A0`. If animation byte +0x58 is 4 after that call, the routine sets it to 5 for a second call and decrements it afterwards. The helper updates +0x57 from its returned animation record (`0x10271D–0x102757`, `0xFBA2F–0xFBA43`, fixup `LOLG.DAT+0x8578A`). |
| 34 | Vtable-0x8344 update submits kind-2 ID-34 hits with mask/flags 0x10/2 and 0x100/4. With effect byte +0x5E nonzero the amounts are 20/20, otherwise 50/30 (`0x102EDC`, `0x103753–0x103820`, fixup `LOLG.DAT+0x84C7E`). |

The two controller helpers in 26 and 27 set up distinct controller
dwords. `0x7FF34` writes +0x3B8 and +0x2E8, with the latter's
initial value `6<<16` (`0x7FF4C–0x7FF8E`).
`0x80064` writes +0x3BC at `0x80080`. The `0x7FE0C`
path similarly writes +0x3B4 and +0x2E4, initially `4<<16`
(`0x7FE24–0x7FE61`). The game-facing names of those
controller channels are **UNCONFIRMED**.

### Effect 17 callbacks

**CONFIRMED.** The constructor at `0x1080F0` installs vtable `0x7080`
at `0x10810E`. At `0x108119–0x10812F` it sets stage byte +0x63 and
flag byte +0x62 to zero and starts the +0x5E timer at `1800<<16`.
Bytes +0x64 and +0x65 start at `0x38` and `0x50`
(`0x108251`, `0x10824D`). The vtable starts at `LOLG.DAT+0x1C80A4`.

| Vtable slot | Native behavior |
|---|---|
| +0x30, `0x108418` (fixup `LOLG.DAT+0x822EB`) | If +0x62 is set, return 0 immediately. In stages 2 and 4, decrement +0x64 and +0x65. If the resulting unsigned +0x64 is below 10, scan active entries of the creature pool `[0x9696C]` and clear a creature's +0x38 when it points at this effect and the creature's +0x15 bit 0x10 is clear. Then set effect +0x62 to 1, set timer +0x5E to `900<<16`, and return 0 (`0x108420–0x1084EE`). Other accepted paths call `0xFBA48`, set animation row bytes +0xE/+0xF to `0x38/0x50`, and return 1 (`0x108437–0x10844E`, `0x1084EF–0x10851A`). |
| +0x38, `0x1082C4` (fixup `LOLG.DAT+0x822FD`) | Subtract `[0x22C54]` from timer +0x5E. When it is at or below `60<<16` and stage is neither 2 nor 4, try a template-0x5E follow-up and set stage 2. A stage-3 value that reaches the later test similarly tries the follow-up and sets stage 4. With timer at or below zero and +0x62 set, call vtable +0xF0 with argument 2 (`0x1082CE–0x108366`). |
| +0x80, `0x1083E0` (fixup `LOLG.DAT+0x8239F`) | Inspect the hit context's attacker pointer at +8. A nonnull attacker whose vtable +0 returns type 2 sets stage 3, provided the stage was neither 2 nor 4 (`0x1083E0–0x108416`). The creature type callback returns 2 at `0xA6ACC` (vtable `LOLG.DAT+0x1C68F4`, fixup `+0x7F03C`). |

**UNCONFIRMED.** What the contact looks like during play and which
encounter supplies it. Watch the effect's +0x62/+0x63 and a linked
creature's +0x38 at `0x108418` and `0x1083E0`. Compare a contact with
no incoming hit to a creature hit before the timer crosses `60<<16`.

### Original level inputs to lesson items

**CONFIRMED.** The following file offsets are native opcode-3,
selector-1 grants. The command's identity dword +4 matches
definition +0x18, then the definition byte +0x42 selects the
item-use handler. It is use of the item that calls the lesson
helper, after the grant has created an instance
(`0xD78D9`, `0x9585B–0x95865`). The census used both framed
command streams of each of the 15 original level archives.

| Lesson input | Original producer evidence |
|---|---|
| School 0, definition 149 | `L4_HJ.MIX+0xC276F0` from prop 1913, kind 5 value 19, predicate 206 at event `+0xC2CBD0`. Also `L7_DH.MIX+0x4A5A41` from control 976 with predicate 207 at event `+0x4A7F01`. |
| School 1, definition 75 | `L7_DH.MIX+0x4A59D5` from control 974, kind 4 value 0, predicate 207, event `+0x4A7EC5`. The acquired list also treats stored 6 as satisfying requested 1 (`0x861D3–0x861E1`). |
| School 2, definition 148 | Three grants in `L7_DH.MIX` at `+0x4A592F`, `+0x4A5947`, `+0x4A5A29`. Control 968 uses predicate 206 or 207 at `+0x4A7E73/81`; control 976 also uses predicate 206 at `+0x4A7EF3`. |
| School 3, definition 151 | `L7_DH.MIX+0x4A595F/0x4A59ED/0x4A5A0B`, from controls 971 and 975 with original events `+0x4A7E91/0x4A7ED5/0x4A7EE3`. |
| School 4, definition 150 | `L20_BB.MIX+0xEC7C11` from prop 241, kind 5 value 19, event `+0xECE269`. |
| School 5, definition 76 | `L8_SJ.MIX+0xCD1D02` and `+0xCD26E2` from props 2 and 102, kind 6 value 20, predicate 207 (event `+0xCD6D04/0xCD71F2`). Definition 76 sets bit 1 of `[0x23ABD]` when used. Definitions 72, 79 and 80 supply the other three bits. A shared stream-1 group in `L1_DC.MIX` contains original grant offsets `+0x6E927D/0x6E9289/0x6E9295/0x6E92A1`. |
| Message 0x25, definition 132 | `L1_DC.MIX+0x6E6843` and `L3_DH.MIX+0x590C7A` from props 343 and 93, kind 5 value 19, events `+0x6E9E69` and `+0x593C64`. The mode-1 use producer is `0x998A7`. |

The state-test witnesses for predicates 206 and 207 in L7 are
`L7_DH.MIX+0x4C239C/0x4C23A1`, whose entries compare the
bound object's state with 0 and 1, respectively. The level with
the L8 grants uses predicate 207 at `L8_SJ.MIX+0xD11284`.
L1 group 13584 has no incoming object or region event in the four
exported tables; it is entered through placed item 2's empty-hand
interaction ([placed-item event lists](lol2-event-producers.md#placed-item-event-lists)).

**UNCONFIRMED.** The numeric payload table establishes one
downstream path for all 35 effect IDs. Effects 32 and 33 write back to their target only through one hit
packet ([below](#effect-3233-contact)).

### Effect 32/33 contact

**CONFIRMED.** The vtable-0x8734 projectile's contact slot +0x40 is
`0x1024B4` (the 0xF7030 projectile family uses the same slot). It sets
byte +0x6A to 1. When the projectile is the moving object of the
collision pass (`[0xB7CA1]`) and its +0x14 bit `0x100` is set, it adds
a step along heading `[0xB7C8D]` scaled by `[0xB7C91]` to the pass's
position cells `[0xB7C75]`/`[0xB7C79]` (`0x1024DA–0x10254B`). A
collision code `0x80` in `[0xB7C74]` clears +0x69 and the target +0x42;
a repeat contact with the current target only decrements +0x69;
another contact becomes the target (`0x102555–0x10258C`). Once per
projectile (+0x67 still zero, set to 1 at `0x102709`), it decrements
+0x69 and, when the distance to its +0x5E point exceeds u8 +0x66 << 16
and a target exists, turns heading `[0xB7C68]` toward `[0xB7C8D]` by at
most `0x1000`, copies it to +0x1E, and sends one 0x36-byte packet to the
target's vtable +0x80 (`0x1025A7–0x102700`):

| Mode +0x58 | Packet: word 0, word 2, kind, ID, magnitude |
|---:|---|
| 4 | `0x100`, 4, 5, `0x51`, 5 |
| 6 | `0x100`, 4, 5, `0x20`, 5 |
| other | `0x100`, 4, 2, `0x20`, 10 |

The packet's +4 is the target, +8 the owner (+0x3E) and +0x10 the
projectile.

**CONFIRMED (effect 15's hit).** The effect-15 object (vtable 0x7278)
sends its hit from `0x107ADA–0x107BF7` only when its byte +0x56 is 1
and its target +0x42 has +0x14 bit `0x4000`. Stage +0x58 = 2 first
plays the cue at `[0x269CC]+0x324`, other stages the cue at
`[0x269CC]+0x134`, unless `[0x269C4]` bit 0 is set (`0x107AE8–0x107B31`).
The 0x36-byte packet carries target +4, owner +8, the effect +0x10,
kind 2 and ID 0xF, and by stage: 1 gives words `0x1040`/1 and
magnitude 0x10; 2 gives `0x1080`/4 and 0x10; 3 gives `0x1040`/1 and
10; any other stage leaves words and magnitude zero
(`0x107B52–0x107BE9`). It goes to the target's vtable +0x80
(`0x107BF7`): for the player `0xD03B8`, for a creature the receiver
that calls the common routine `0x62728`
([combat](lol2-combat-ai.md#hit-context-and-reduction)). For the timed message 0x26,
the direct +0x185 store scan found player initialization at
`0xCFB8B` and the expiration zero-store at `0xD2E57`.
An original playthrough trace filtered to its first nonzero
write would identify the producer and its quest or item input.

### Timed-message runtime control

**CONFIRMED.** In the DOS 1.30 executable (`LOLG.DAT` SHA-256 prefix
`b27a3534`), a copy of a level-20 autosave written by the original game during play
(a player save, not shipped; SHA-256 prefix `e2393dbe4d2b`) entered the player update at `0xD2E30` with +0x185
equal to zero. A spell input reached the effect switch `0xD24B1`
with effect `0x0A`. The field was zero there and at `0xD1048` in
the same test window. A write watch on player +0x185 captured the
zero write at `0xCFB8B` and zero-valued bytes during startup and
load. Every watched write in the trial was zero, and the expiry
breakpoint at `0xD2E57` stayed idle.

**CONFIRMED.** In that slot, the live controller at object-5
`0x23348` had a handler-34 instance (definition identity `0x5BD621C2`)
at inventory array +0x280, index 6. The native inventory routine
uses that array at `0x8AA82–0x8AA8B` and the item dispatcher reads
the handler at `0x9584E`. **UNCONFIRMED.** The click trial left
handler `0x96F64` unobserved, and player form +0x1AB stayed zero at
the sampled points. The controlled lesson use and form change remain
open. Confirm entry at `0x96FEC` for that lesson or a change of
player +0x1AB while the write watch is armed, then follow any first
nonzero store through the expiry call at `0xD2E61`.
