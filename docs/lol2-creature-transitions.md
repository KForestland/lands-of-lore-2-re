# LoL2 creature behavior and animation transitions

This page uses the DOS 1.30 [executable address convention](lol2-executable-tables.md).
The [combat reference](lol2-combat-ai.md) covers damage and health. Behavior
dispatch, selected action, and animation frame use different fields.

## Live state and initialization

**CONFIRMED.** The placement reader at `0xA2283–0xA2292` reads a
56-byte actor row. The constructor at `0xA22AF–0xA22BE` uses its
byte +0x20 to index the 139-byte runtime creature definitions.
It initializes the following fields on the new actor.

| Placement field | Actor field | Confirmed initialization |
|---|---|---|
| u8 +0x25 | +0xA8 and +0xA9 | Copy behavior byte to +0xA8, with values ≥0x10 replaced by 6, then mirror to +0xA9 (`0xA23BD–0xA23E3`, `0xA242C–0xA2438`). |
| u8 +0x26 | +0xAA and +0xAB | Copy to +0xAA, with values ≥0x12 replaced by 0, then mirror to +0xAB (`0xA23C6–0xA23F7`, `0xA2441–0xA244D`). |
| — | +0xB8 | Set low bit 0 at `0xA2432–0xA2447`. |

A worked placement is actor 36 in `L5_HC.MIX+0x5ABBBA`. Its bytes at
`+0x5ABBDA`, `+0x5ABBDF` and `+0x5ABBE0` are 1, 6 and 9. The
constructor therefore selects definition 1, behavior 6 and secondary
state 9. The definition's tag is `EXEC` at `L5_HC.MIX+0x5BF2E1`.

## Behavior dispatch

**CONFIRMED.** `0xA267C` reads actor +0xA8 and dispatches values
0–14 via `0xA3DC2`. Values 15 and above return from the range test
(`0xA269D–0xA26AB`). The table starts at `LOLG.DAT+0xD9640`
(object-2 offset `0x4961C`). These are the entry effects. Each arm
can take additional branches.

| Mode | Handler VA | Confirmed first path or field decision |
|---:|---|---|
| 0, 12 | `0xA2704` | If +0xB8 bit 0 is set, set bit 1. Then use actor u16 +0x80 to index an 8-byte waypoint row in `[0x22D1C]` (`0xA2719–0xA272B`). |
| 1, 11 | `0xA24AC` | Return via the common epilogue. |
| 2 | `0xA329A` | Fill null target +0x34 with the player, then branch on +0xB4 bit 0x20 (`0xA32A7`). |
| 3 | `0xA26AD` | Check actor +0xB5 bit 0x10 and target +0x34. Common waypoint path is `0xA2704`. |
| 4 | `0xA3688` | Fill null +0x38 with the player. Check observation byte +0x9E and +0xB8 bit 0x40 (`0xA3695–0xA36AB`). |
| 5 | `0xA3681` | Set +0x38 to the player and enter mode 4's continuation. |
| 6 | `0xA3BB6` | Call `0xA9720(actor, 0, 3)`. |
| 7 | `0xA3BCA` | Check path byte +0xA4 against 0xFF. Only when `(+0xB8 & 0x30) == 0x30` (`0xA3BDF–0xA3BEB`) it uses the distance result and vtable +0x14 at `0xA3BFE–0xA3C15`; otherwise it goes straight to the +0xA5 path at `0xA3C27`. After the distance path, +0xA5 is read at `0xA3CD0` only when esi = 1. |
| 8 | `0xA2C63` | Fill null +0x38 with the player. Check +0x9E and +0xB9 bit 0 (`0xA2C70–0xA2C81`). |
| 9 | `0xA2F1D` | Fill null +0x38 with the player. Branch on +0xB9 bit 0 at `0xA2F2A`. |
| 10 | `0xA315B` | Fill null +0x38 with the player. Check low three bits of +0x9E at `0xA3168`. |
| 13 | `0xA31B5` | Same initial target and observation fields as mode 10. With the observation bits set, copies the target XYZ dwords through `0xA31CB–0xA31DE`. |
| 14 | `0xA3D24` | Write +0xAA = 9, clear +0xB8 bits 4–5 and clear update flags `0x9699D/0x9699F`; the following clauses can request action 0 (`0xA3D50–0xA3D72`). |

The observation update at `0xAA208` can be called by the actor's frame
update at `0xA4C55`, when +0xB9 bit 0x08 is set and +0xA8 differs
from 0x0F. It then clears the flag at `0xA4C66`. Separately, the actor
death path writes behavior 0x0F and health zero
(`0xA77DF–0xA77EB`), and sets +0xAA = 0x0F and +0xAB = 0x10 (`0xA77D1–0xA77D8`). The frame update uses a creature vtable
at object-5 +0x58D0, installed at `0xA22DE`. Its +0x38 slot is
fixed up at `LOLG.DAT+0x7F0BA` to `0xA4934`.

## Explicit changes and animation completion

**CONFIRMED.** The creature table's +0xAC slot has fixup
`LOLG.DAT+0x7EDC3` to `0xA62F4`. Opcode 13 can call this slot
via the low script dispatcher `0xB5937`. Creature opcode 13 first
checks for behavior 0x0F at `0xA6348`, then uses command +4 to
select the secondary dispatch at `0xA678B`.

| Command +4 | Active fields written | Evidence |
|---:|---|---|
| 0 | +0xA8 and +0xA9 get u8 command +5. Set +0xB8 bit 0 and clear +0x7C. | `0xA6365–0xA6388` |
| 1 | +0xAA and +0xAB get u8 command +5. Clear +0x7C. | `0xA639A–0xA63AE` |

For example, `L1_DC.MIX+0x6E65C3` holds
`0D 02 26 00 00 0A 00 00`. The actor selector resolves index 38 via
`0x5FD54 → 0x5FC1B`, and the command requests behavior 10. The
following command at `+0x6E65CB` sets the secondary byte to 1.
There are 34 opcode-13 actor-selector commands with subcommand 0
and 39 with subcommand 1 in the 15 framed level archives.

**CONFIRMED.** For animation, `0xA7D4C` takes an action number and
uses `0xA1E44` to select a state row. The variant argument is actor
byte +0xAC (`mov eax,[ebx+0xA9]; sar eax,0x18` at `0xA7D69`), or 1 when
`(+0xB4 & 0x6000000) > 0x2000000` (`0xA7D57–0xA7D7D`). A failed lookup is
retried with 1 only when byte +0xAC is not 1 (`0xA7D93–0xA7DB8`). The
constructor sets +0xAC = 1 at `0xA23F7`. A successful state install through
`0xA7DC4 → 0xF2944` writes the selector to actor +0x30
(`0xF29BA`). It resets countdown word +0x7C and derives the
terminal-frame byte +0x32 from `0xF1F94` (`0xA7DE9–0xA7DF9`).

The frame update decrements +0x7C by `[0x22C58]` and replenishes
it from the active state's fixed-point interval
(`0xA55C4–0xA560C`). On the terminal branch it sends kind-6 event
value 3 through `0xADDE0` (`0xA56A3–0xA56B3`).
When update byte `[0x9699F]` is 1, the earlier frame path at
`0xA5551–0xA55A8` copies +0xA9 into +0xA8 and +0xAB into +0xAA
(`0xA5589`, `0xA55A8`). Value 2 permits the same copies at the
terminal-frame path (`0xA56CD–0xA571B`; `0xA56FC`, `0xA571B`). When behavior
differs, both paths clear dword +0xB8 and set bit 0. The dispatcher sets
`[0x9699D]` and `[0x9699F]` to 1 on every entry (`0xA2688–0xA2697`); mode 14
clears them. The early path also clears +0xB8 bit 0 (`0xA5556`).

## Profile source

**CONFIRMED.** Each disk creature definition consists of the 135-byte
body and 12-byte tag, read separately at `0xA1C72` and `0xA1C82`.
The loader passes the tag to `0x5A268` at `0xA1C94` and writes
the returned profile to definition +0x87 at `0xA1CAF`.
The lookup can load a profile via `0x5A2D9 → 0x59C0C`.
At `0x59C5A–0x59CAA`, that routine formats the profile directory
and joins the stat filename. Source operands point to
`global\ai\%s` and `stat.csv` at
`LOLG.DAT+0x1C1028` and `+0x1C1035`. The calls at
`0x59CA1` and `0x59CAA` select and parse 32 rows of one numeric
byte each into profile +8. The parser skips the header and initial
text column (`0x59B11–0x59B26`, `0x59B56–0x59BD9`).

The `EXEC` source name `global\ai\EXEC\stat.csv` gives MIX key 0xCC491243
with the archive name hash (`tools/lol2_westwood_hash.py`, case-insensitive), at
`GLOBAL.MIX+0x6A3AC0`. Data rows 2 and 3, counting from zero after
the header, are 50 and 50. The copy at `0xA230F–0xA231A` puts
the profile's 32 stat bytes starting at actor +0x4C, so the two
values land at actor +0x4E and +0x4F. Those are the inputs in the
[worked attack](lol2-combat-ai.md#worked-creature-attack).

## What is still open

**UNCONFIRMED.** The 15 behavior destinations and the current/requested
state updates are mapped. The full decisions within modes 2–5 and
7–10, the semantics of each observation bit and the initial producer
of actor +0xA3 remain open. The latter was checked by looking for
direct operand writes to +0xA3 in the actor code range
`0xA0000–0xADE00`. The verified write is the nonzero decrement
at `0xAB63F–0xAB64D`. This search can miss writes through a separate
pointer or a wider copy. A write trace through the first change from
zero would distinguish such a producer. For unresolved decisions,
the dispatch and setter addresses above give the inputs and outputs
to capture for one mode at a time.
