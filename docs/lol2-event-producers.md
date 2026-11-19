# LoL2 object kind 1 and event producers

Addresses use the DOS 1.30 [analysis convention](lol2-executable-tables.md).
The companion [event reference](lol2-script-events.md#event-records) gives
matching behavior after the event is produced.

## Object kind 1

**CONFIRMED.** Kind 1 is a 14-byte object render parameter record. The
object method at `0xB3C5C` obtains the event list through vtable +0xB8
and requests kind **1** at `0xB3C7A`. The common lookup `0x5A344`
walks by u8 +0, stops when the kind at +1 reaches the requested kind and
returns the record only on equality. A zero length or zero kind terminates the walk. The updater at `0xB46E8` requests
the same record at `0xB4704`, passes it to `0x9F600`, then prepares a
24-byte row at `0xB4740–0xB478B`. Caller `0x9FB08` maintains arrays of
those rows (`0x9FB28`, `0x9FB70`, step `0x18` at `0x9FB35`, `0x9FB7D`).

**CONFIRMED.** The value helper `0x9F8C8` returns the live +0xD byte
when flags u16 +2 contain bit `0x80`. With that bit clear it uses
`flags & 0x0F00` (`0x9F962–0x9F9A2`). Mode 0 returns s8 +0xA. Mode
`0x200` chooses s8 +9 or +0xA using the direction bit `0x20`. Mode
`0x300` interpolates between those endpoints using the signed progress
word +4 and a divisor based on u8 +0xB, scaled by 60 if bit `0x10`
is set (`0x9F8E7–0x9F948`). Modes `0x100`, `0x400` and `0x500`
read +0xD. The writer `0x9F600` updates that live byte at `0x9F64D`, `0x9F670`, `0x9F6A8`, `0x9F6BB`, `0x9F7B3` or `0x9F802`, depending on flags. The zero transition
at `0x9F6B9–0x9F6CD` emits object kind-6 value 18.

| Record input | Verified use |
|---|---|
| +2 low byte | Copied to derived row +0x17 (`0xB475A–0xB475D`). Bit `0x40` also selects one of two renderer accumulation paths (`0xF1B0B–0xF1B2A`, `0x131C62–0x131C87`). |
| s16 +4 | Live countdown or interpolation progress (`0x9F887–0x9F892`, `0x9F905–0x9F930`). |
| u16 +6, u8 +8 | Copied to derived row +0x14 and +0x16 respectively (`0xB474C–0xB4757`). |
| s8 +9 and +0xA | Endpoints for `0x9F8C8`. Also the endpoints used to compute byte +0xD at `0x9F77E–0x9F7B3`. |
| u8 +0xB | Mode-dependent period and interpolation denominator (`0x9F7C3–0x9F7CD`, `0x9F8EC–0x9F930`). |
| s8 +0xC | Object Z offset in 16.16, added to object dword +8 and written to derived row +4 (`0xB4764–0xB4772`). |
| u8 +0xD | Live value for the flagged path (`0x9F8D1–0x9F8E6`). The render path at `0xF1B19` independently calls the value helper and writes `value << 16` to `[0xFD8C0]` at `0xF1B2A`. |

**CONFIRMED.** `L10_DC.MIX+0xC8296B` is actor 4's kind-1 row. It has
flags `0x0041`, progress 0, word +6 `0x0400`, byte +8 `0x40`, and zero
bytes +9 through +0xD. With these values `0x9F8C8` uses mode zero and returns
zero. The packed flag is used by the native method and is separate from
any stream offset. Following object lists across the 15 MIX archives gives
1,369 visits to kind 1: 209 actor, 49 control, 1 movable and 1,110 prop.
In those rows, on-disk u16 +4 is zero at every site.

### Attenuation of the derived render row

**CONFIRMED.** The evaluator `0x1319B4` walks 24-byte rows from data
`0xFD8C4`. It admits only nonzero magnitude at row +0x0C and skips the
row that matches the supplied object key when no direction is supplied
(`0x1319F4–0x131A15`). It dispatches on row +0x17 & 3
(`0x131C0B–0x131C3A`). Types 2 and 3 apply opposite signed height tests
at `0x131A17–0x131A43` before the same distance calculation as type 1.
Type 0 goes to a separate direction-dot-product path at `0x131BA8`.

For types 1–3, `d = max(|dx|, |dy|, |dz|) + ((other1 + other2) >> 2)`
in 16.16 (`0x131A59–0x131ABA`). The original kind-1 byte +8 is the
inner distance `I` (derived row +0x16) and u16 +6 is the fade width
`W` (derived row +0x14). Both are shifted left 16. At `d >= I + W`
the row contributes zero. For `I < d < I + W`, the contribution
already computed from magnitude and direction is multiplied by
`1 - (d-I)/W` in 16.16. Inside `I` that contribution passes directly.
The branches are `0x131ABE–0x131AEA` and `0x131B72–0x131BA1`.
`0x131EC7–0x131EEC` repeats the cutoff in the three-channel path.

The row flag `0x40` sends the contribution to the second sum at
`0x131C42–0x131C59`. Only the first sum is subsequently attenuated
by the view distance calculation at `0x131C8B–0x131D12`. The function
adds the scaled sums and clamps to 0 through `0x3F0000`
(`0x131D16–0x131D4D`). In the L10_DC witness above the inner distance is
64 and the fade width is 1024. With flags 0x0041 and starting
magnitude +0xA zero, the value helper returns 0, so this row adds
nothing while +0xA stays 0. **UNCONFIRMED.** Colour channel and
surface selection for this particular object. Trace the values returned
by `0x1319B4` and the three-channel routine `0x131D58` into the first
render primitive whose source is that actor's view or surface.

### Scalar shade row and packed colour

**CONFIRMED.** In the scalar caller at `0x129C23`, the shade-row
offset from the clamped 16.16 return `S` is `(S >> 8) & 0xFF00`.
The arithmetic and store at `0x129C28–0x129C33` make this the
256-byte row offset for index `S >> 16`, in 0–63. The draw call at
`0x129C48` passes the local primitive at stack +0x60 before the push,
so the computed field is primitive +0x28. Its consumer
`0x12AA4B–0x12AA6E` selects the shaded branch for a nonzero offset,
and the lookup at `0x12AA89–0x12AAA8` inserts the source pixel into
the low address byte before fetching the translated palette index.
The other three direct scalar callers at `0x126E82`, `0x127BD6` and
`0x1288DA` store a result per 24-byte vertex before clipping through
`0x133C68` and `0x133FF4`. Their final span-row interpolation remains
**UNCONFIRMED**. To settle it, track the first surviving clipped
vertex's shade into its span setup and compare the first byte lookup.

**CONFIRMED.** The parallel `0x131D58` path packs three channel values.
At `0x132178–0x1321E8` it scales the first sum triplet by the
product of the factor at `0xFD8A8` and the view-dependent factor
(`0x132178–0x132181`), and the second by `0xFD8A8` alone. It adds channel pairs, arithmetically shifts each sum right
14 and clamps it to 0–255 (`0x1321EC–0x13227F`). The stores at
`0x13227F–0x132297` put the first, second and third values in return
bits 24–31, 16–23 and 8–15. Direct callers at `0x139254`, `0x13A732`
and `0x13BD50` store the packed dword per vertex before clipping;
`0x13C845` stores a single result before the call at `0x13C872`.
For the actor-4 witness at `L10_DC.MIX+0xC8296B`, zero contribution
from that row alone leaves the total from other rows and view terms
undetermined. Match one original primitive's coordinate and excluded
object key at `0x129C23` or `0x13C845` before assigning it a shade.

## Confirmed event sources

A constant or a named field in the following table describes each call site.
It can be shared with other producers of the same event number.

| Matcher | Event or operand | Producing branch |
|---|---|---|
| Object kind 3 | New requested byte | `0x5D510` adds the current object byte when the relative argument is set. When the requested byte differs and object flags contain `0x400`, it calls `0xAD7F4` at `0x5D550` before writing object +0x3D (`0x5D51A–0x5D558`). |
| Object kind 3 | New u8 object +0x30 | `0xF2984–0xF29BA` checks the old byte and object flag `0x400`, calls `0xAD7F4` at `0xF29AE`, then stores the requested byte. |
| Object kind 5 | 1, value 0xFF | `0x5BAB8–0x5BAD5` compares the other object with the player address `0x22574` before issuing the event on the first object's list. `0xB230E` is a second producer. |
| Object kind 5 | 2, value 0xFF | Hit path at `0xB4315`. Other direct calls include `0xD757A`, `0xD7746` and `0xF6C87`. |
| Object kind 5 | 3, event value from hit context +0x15 | `0xB4323–0xB433C`, after the hit filter at `0xB42D9`. |
| Object kind 5 | 5, value 0xFF | On change of player +0x7D relative to +0x79, call on the new non-null +0x7D object's list (`0xD39C3–0xD39E6`). |
| Object kind 5 | 6, values 0, 1, 2 or 4 | `0xD4B39` uses angular difference above `0x4000`, `0xD4AD1` and `0xD4AF4` use distance thresholds, and `0xD0C22` supplies 2. |
| Object kind 5 | 13, 14, 15 | At `0xD0889`, `0xD0847`, `0xD0868` respectively. Player byte +0x1AB chooses 14 for zero, 15 for one, 13 for two (`0xD0895–0xD08AB`). These call sites pass value 0xFF. |
| Object kind 5 | 16 and 20, value 0xFF | `0xD08C5` issues 16 on the object held in context +8 of that code path. `0xB435F` issues 20 in the hit path. |
| Object kind 6 | 0, 1 | Callback `0x9EBFC` sends event 0 at `0x9EC31` when resource update `0x113BF0` returns 5, or event 1 at `0x9EC60` when it returns 4. The update can return 5 or 4 with resource +0x30 equal to zero or nonzero respectively at `0x113CA8–0x113CB6`. Example rows (kind 6 with +4 = 0 and 1; 715 and 18 such rows exist) are `L10_DC.MIX+0xC802BF` and `+0xC804FD`. |
| Object kind 6 | 19 | `0xB2B97` sends after accumulating and clearing nonzero +0x1A when countdown +0x23 is clear. `0xB2C84` sends when `0x68124` returns nonzero with +0x1A zero. `0xB2CFA` sends after the other countdown path reaches zero with +0x1A zero. The four-table event scan found no +4=19 rows. |
| Object kind 6 | 6, 8, 10, 18, 20, 22 | Opcode-18 reset (`0xB5A0E`), actor nonpositive-path arm (`0xA29FA`), actor terminal branch (death interpretation **UNCONFIRMED**; a break at `0xA77A1` when a creature is killed in a running game settles it) (`0xA77A1–0xA77EB`), kind-1 live byte reaching zero (`0x9F6CD`), opcode 9 property 21 (`0xB5458`), and creature behavior branch (`0xA3CFA–0xA3D0E`), respectively. |
| Object kind 6 | 9 with additional byte +5 | Calls at `0xAECEB` and `0xAEEFF` reach `0xADF34`, which checks kind 6, +4 = 9 and the value at +5, with a special wildcard case at `0xADF6B–0xADF7C`. |
| Object kind 6 | 21 with additional byte +5 | Calls at `0x62FA9`, `0xFA3CF` and `0xFA591` reach `0xAE034`, which checks kind 6, +4 = 21 and the value at +5 (`0xAE050–0xAE06E`). |
| Object kind 8 | Slot-provided word | The caller `0xE3829–0xE3841` forwards the voice’s cue at +4 and walks kind-8 records through `0xAE510` (**CONFIRMED**, same field consumed by the bank lookup at `0xE4CEF–0xE4CF8`). The matcher uses the low word. |
| Region kind 11 | 0–7, 12, 13, 16, 17 | Opcode 196 issues start and finish events on region floor/ceiling motion. See the native calls at `0x6500B`, `0x6501F`, `0x65047`, `0x6505B`, `0x65200`, `0x65236` and `0x6524A`. Cancellation also calls it at `0x64F6A`. |
| Region kind 12 | 0 | `0xD7049–0xD70BA` requires object +0x24 to be zero and copies a nonzero byte from +0x43 before the virtual +0x48 call. It sets object +0x16 bit `0x40` and submits event 0, v=0, to the resolved region. Original row `L19_BC.MIX+0x5E9618`. |
| Region kind 12 | 5 | `0xD5FDC–0xD607C` requires a nonzero +0x16D value at least as large as `u8(+0x3F)<<16`, a clear +0x229 bit `0x10` and a resolved region. Sends event 5, v=0, then sets that bit. Original row `L14_HT.MIX+0xB3D834`. |
| Region kind 12 | 1 and 9 | Branches in the same player action path pass `[EBP-4]` with event 9 at `0xD679C–0xD67E0` or event 1 at `0xD6895–0xD68DC`. |
| Region kind 12 | 2, 3 and 4 | Region transition code at `0xD383C`, `0xD38D1`, `0xD38ED`, `0xD38FE`, `0xD394A`, `0xD39BB`. The call sites distinguish destination and old/alternate region pointers. |
| Region kind 12 | 7 and 8 | Event 7 is called with final argument zero in the player update branch at `0xDB449–0xDB4A1`. Event 8 is passed with the computed argument from `0xD6969–0xD69C9`. |

**UNCONFIRMED.** The caller families above establish the IDs they can
produce. Several kind-5/6/12 call inputs and the gameplay meanings of computed operands still need provenance. The direct-call scan found two kind-3 matcher calls,
17 kind-5 calls and 50 kind-6 calls to `0xADDE0`, and 16 calls to the region kind-12 entry `0xF2D2C`. The
per-level [event rows](levels/notes/README.md) provide the original dispatch
IDs and offsets to pair with them. To settle callers with computed operands,
trace each reaching assignment to the argument and the selection of its
object or region before the call. The caller list covers direct calls.

## Placed-item event lists

**CONFIRMED.** Header +0x20 and +0x6C locate a fifth table of event-list
hosts (37-byte placed-item rows). The seek at `0x9D43C–0x9D442` and
count at `0x9D44A–0x9D450` feed `0x94078`. The base constructor
copies placement u16 +0x0C to live object +0x18 at `0xAE9CE–0xAE9D2`.
The placed-item vtable at data `0x573C` has +0xB8 -> `0xB71A0`
(`LOLG.DAT+0x1C6818`), which adds that u16 to `[0xB7D74]` when
object +0x15 bit `0x10` is clear. The level loader reads the object
event blob into that base at `0x9CF6B–0x9CF95`.

**CONFIRMED.** Across the 15 levels the new join walks 663 placed-item
rows, 56 with nonempty lists. It finds 40 kind-4 records, 17 kind-6
records and 21 predicate trailers across those visits. The 57
group-bearing records all name stream-1 groups outside the references
of the four earlier placement tables. The level report's `--check`
verifies the group boundaries, total and L1_DC witness.

For `L1_DC`, placed item 2 (definition 42, file `+0x6FBDC8`) has
list offset `0x1A12` in the blob at `+0x6E96AD`. Its kind-4 record at
`+0x6EB0BF` is `0a 04 10 35 00 00 00 00 00 00`. The native mode-0 arm
requires an empty held-item context (`0xADBDB–0xADC05`, `0xADC41–0xADC59`).
There is no predicate trailer. The group at `+0x6E9277` grants seven
definitions through opcode 3. The placed item vtable +0x64 points to
`0x95200` (dword at `LOLG.DAT+0x1C67C4`). The method calls
`0xB5000` at `0x95218` before the transfer path, and
`0xADDA3–0xADDB0` adds the event's u16 group `0x3510` to stream 1.

**CONFIRMED.** After the 57 placed-item joins, a review count over
both streams, the four event tables, the region lists and the placed
items finds no group without a serialized reference. The 57 joins come
from the placed-item table at level header +0x20/+0x6C.

### Empty-hand left click on L1_DC placement 16

**CONFIRMED.** In a separate run of original DOS 1.30,
with one instance on a private Xvfb display, a disposable copy
and null audio, the trial restored the
[opening-cave before slot](lol2-save-sections.md#original-opening-cave-pickup-in-l1_dc)
and left-clicked the floor sprite with an empty cursor. The native
pick at `0x110ACD` passed row `0x1128C304` through the vtable
to `0x95200`, then `0x95218 → 0xB5000`. This was row 16
at `L1_DC.MIX+0x6FBFCE`, definition `0xA4C5CBD3`. Object +0x18
was `0x1ADA`. Added to live object-event base `0x111E37FC`,
it selected `0x111E52D6`, the kind-4 record at
`L1_DC.MIX+0x6EB187`.

Execution reached the predicate word load at `0xADD80` (predicate
41 at `L1_DC.MIX+0x70628A`, call at `0xADD8A`) and then the group call `0xADDB0 → 0x646EC`.
The argument was `0x1122773C`, stream-1 base `0x112240F4` plus
`0x3648`, whose group starts at `L1_DC.MIX+0x6E93AF`.
The subsequent `0x64887` command had value 1 and points to the
group's local-byte-16 write at `L1_DC.MIX+0x6E93BB`.
The click also called `0x95A64` to transfer the item to the player.
Thus an ordinary empty-hand left click reaches a placed-item
group and can pick up the same item on the same input.

## Close-out

### Q5

**What was measured.** `L10_DC.MIX` holds 119 distinct kind-1 records on the object and placed-item lists, and actor 4's record at `+0xC8296B` is `0E 01 41 00 00 00 00 04 40 00 00 00 00 00`. Of those 119, byte +9 is nonzero in 96, byte +0xA is nonzero in 98, and byte +0xD is zero in every one.

**What was tried.** This walk counted the endpoint bytes of each kind-1 record in that archive. The page already records that actor 4's value helper returns zero and names the shade callers at `0x129C23` and `0x13C845`.

**What would settle it.** The running-game test is not yet run ([probes not yet run](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run)). Match a primitive to that actor at `0x129C23` (scalar, 256-byte shade row) or `0x13C845` (three packed channels).
