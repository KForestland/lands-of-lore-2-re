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

**UNCONFIRMED.** The display role of each copied +6/+8 field and the
full mode/presentation table remain open. The first consumers, byte
copies, value update branches and final accumulation inputs above were
checked. Follow the derived 24-byte row's +0x14/+0x16 through the renderer
and compare the accumulation paths selected by flag `0x40` to name them.

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
| Object kind 6 | 6, 8, 10, 18, 20, 22 | Opcode-18 reset (`0xB5A0E`), actor nonpositive-path arm (`0xA29FA`), actor terminal branch (death interpretation **UNCONFIRMED**) (`0xA77A1–0xA77EB`), kind-1 live byte reaching zero (`0x9F6CD`), opcode 9 property 21 (`0xB5458`), and creature behavior branch (`0xA3CFA–0xA3D0E`), respectively. |
| Object kind 6 | 9 with additional byte +5 | Calls at `0xAECEB` and `0xAEEFF` reach `0xADF34`, which checks kind 6, +4 = 9 and the value at +5, with a special wildcard case at `0xADF6B–0xADF7C`. |
| Object kind 6 | 21 with additional byte +5 | Calls at `0x62FA9`, `0xFA3CF` and `0xFA591` reach `0xAE034`, which checks kind 6, +4 = 21 and the value at +5 (`0xAE050–0xAE06E`). |
| Object kind 8 | Slot-provided word | The caller `0xE3829–0xE3841` forwards a state dword at +4 (audio association **UNCONFIRMED**) and walks kind-8 records through `0xAE510`. The matcher uses the low word. |
| Region kind 11 | 0–7, 12, 13, 16, 17 | Opcode 196 issues start and finish events on region floor/ceiling motion. See the native calls at `0x6500B`, `0x6501F`, `0x65047`, `0x6505B`, `0x65200`, `0x65236` and `0x6524A`. Cancellation also calls it at `0x64F6A`. |
| Region kind 12 | 1 and 9 | Branches in the same player action path pass `[EBP-4]` with event 9 at `0xD679C–0xD67E0` or event 1 at `0xD6895–0xD68DC`. |
| Region kind 12 | 2, 3 and 4 | Region transition code at `0xD383C`, `0xD38D1`, `0xD38ED`, `0xD38FE`, `0xD394A`, `0xD39BB`. The call sites distinguish destination and old/alternate region pointers. |
| Region kind 12 | 7 and 8 | Event 7 is called with final argument zero in the player update branch at `0xDB449–0xDB4A1`. Event 8 is passed with the computed argument from `0xD6969–0xD69C9`. |

**UNCONFIRMED.** The caller families above establish the IDs they can
produce. Remaining kinds 5/6/12 IDs and some contexts in the table still
need input provenance. The direct-call scan found two kind-3 matcher calls,
17 kind-5 calls and 50 kind-6 calls to `0xADDE0`, and 16 calls to the region kind-12 entry `0xF2D2C` (including `0xD607C` and `0xD70BA`). The
per-level event rows (`tools/lol2_export_scripts.py`) provide the original
dispatch IDs and offsets to pair with them. To settle callers with computed operands,
trace each reaching assignment to the argument and the selection of its
object or region before the call. The caller list covers direct calls.
