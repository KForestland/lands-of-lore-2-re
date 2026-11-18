# LoL2 item handler catalog and instance effects

The [item grant reference](lol2-item-effects.md) explains how a 91-byte
definition creates a live item. This page follows the handler index at
definition +0x42 into the DOS 1.30 executable. Addresses and source
editions are given in the [address guide](lol2-executable-tables.md).

## Charges and use modes

**CONFIRMED.** Script grants copy command +8 into the new instance's
byte +4 (`0x95B91–0x95B99`, `0x9B8DF → 0x95804`). The direct
constructor also sets +4 from a supplied byte and clears +5
(`0x95824–0x9583A`). In handlers 2 and 8, instance +4 specifically
acts as a charge counter. This is established by the decrement and
zero branch in each body.

| Handler and definition | Mode | Native effect |
|---|---:|---|
| 2, definition 57 at `GLOBAL.MIX+0x5B8D2C` | 1 | Decrements a positive charge **before** target search (`0x96095–0x960AD`). A zero finder return leaves EAX zero and leaves the decrement in place (`0x960B5–0x960B7`). If the finder succeeds, template 0x6E can lead to `0x101F74` at `0x960DC`. Charge zero then triggers the definition-pointer replacement at `0x9611F`. |
| 8, definition 55 at `GLOBAL.MIX+0x5B8C76` | 1 | Resolves a target context, looks up template 0x62 and can call `0x10A4BC` (`0x96703–0x96732`). It sets bit 0 of player byte `[0x22712]` on every mode-1 path (`0x9673A`). A zero target returns 1 without a decrement. A nonzero target decrements a positive charge and replaces the held definition pointer when the counter is zero (`0x96741–0x96797`). |
| 10 and 11, definitions 125 and 129 at `GLOBAL.MIX+0x5BA558` and `+0x5BA6C4` | 12 | Tests the sum of coating bytes `[0x23C43]+[0x23C44]` against 9 at `0x968B6` and `0x96A7A`. Below 9, the handler clears the hand and releases any returned item, then calls `0x82DCC` or `0x82E10` at `0x9692D` or `0x96AF1`. |
| Same | 1 | Clears the hand, builds a hit on the player and calls the receiver `0xD03B8` at `0x969D5` or `0x96B99`, then releases any item returned by the hand clear (`0x969DD–0x96A2F`, `0x96BA1–0x96BF3`). |
| 16, definition 96 at `GLOBAL.MIX+0x5B9B09` | 1 | Optionally submits sound at `0x97250`. If the shared-array pointer is present, writes 1 to `[0x26E58][u8([0x2333E])]` at `0x97269`. Returns 1. |
| 36, definitions 13 and 154 | 6, 13 | Compares target distance with 0x800000 at `0x97D41`. On the admitted path, template 0x6A can enter `0x1050AC` at `0x97D92`. Other mode values return zero at `0x97D1D`. |
| 43, definition 133 at `GLOBAL.MIX+0x5BA830` | 1 | Clears the hand at `0x983D4`, releases any returned item at `0x98430`, then calls `0xD6A88(player, 50)` at `0x9846E`. That helper adds 50 to player +0x145, applies the cap at +0x141, and floors a negative sum at zero when the cap branch does not apply (`0xD6A93–0xD6AC3`). |
| 68, definitions 27 and 155 | 6, 13 | Can play a sound at `0x99A88`. Resolves template 0x6A through `0x99A99` and, on success, calls `0xFC0D8` at `0x99AB7`. |
| 107, definition 12 at `GLOBAL.MIX+0x5B7D2D` | 16 | Returns 1 on mode 16 and zero otherwise (`0x9B8B0–0x9B8C0`). |

For handlers 10, 11 and 43, any item returned by `0x77ACC` is passed to
`0x5F830` for release. The address-range test chooses `[0x96918]` when
the item lies in the player pool and `[0x9691C]` otherwise. The mode-12
release calls are at `0x9691E` and `0x96AE2`, the mode-1 coating release
calls are at `0x96A2F` and `0x96BF3`, and handler 43 uses `0x98430`.

The final results of the two replacement identity lookups are
**UNCONFIRMED**. Handler 2 uses a loaded index from `[[0x96904]]+0x8C`
at `0x960EA–0x96111`, and handler 8 uses `[[0x96904]]+0x7C`
at `0x96761–0x96787`. Both convert that index to a definition
identity before lookup. Resolving the loaded indexes at those sites
would confirm the replacements for the pinned edition.

### Worked recharge script

**CONFIRMED.** The kind-4 mode-3 record for control 134 at
`L3_DH.MIX+0x594C3A` matches held identity 0xDDC02377 by
`0xADC84–0xADC8F` and points to stream 1 group 9510. Its trailer at
`+0x594C44` selects predicate 207. At `+0x5A11F5`, predicate 207
contains `00 05 00 00 01`, requiring the current object's state
byte to be 1. That group contains opcode 2 with subcommand 0x18
at `+0x592BBA` and an opcode-3 player grant
`03 01 00 00 77 91 B8 E7 01 00 00 00` at `+0x592BC0`.
Opcode 2 arm 0x18 dispatches the detach and release path through
`0x91C0C` and `0x95C24` at `0xD87EB–0xD8803`. The next
command grants identity 0xE7B89177, definition 57
(`GLOBAL.MIX+0x5B8D2C`), with charge 1 through `0xD78D9`.
The replacement grant creates a new charged instance on this path.

## Equipment modes

**CONFIRMED.** Incoming and outgoing equip notices use request bytes 10
and 11. The player code writes mode 10 before calling the dispatcher
at `0x8FFE0`. The outgoing notice can be seen at `0x8E57D`. Category calls are at `0x8FDBB` and
`0x8FE07`. The category query uses mode 16 and tests the handler result
at `0x8FE0F`. Mode 16 can have another caller-specific use.

| Handler | Mode 10 | Mode 11 | Mode 16 |
|---|---|---|---|
| 19 at `0x97310` | Set player flag `[0x2270E]&0x20` (`0x972F5`) | Clear bit 0x20 (`0x972FC`) | Return category 2 (`0x97309`) |
| 23 at `0x97884` | Set player flag `[0x2270E]&0x80` (`0x97868`) | Clear bit 0x80 (`0x9786F`) | Return category 2 (`0x9787C`) |
| 97 at `0x9B28C` | Set `[0x22711]` bit 0x02 (`0x9B265`) | Clear that bit if `0x91868` returns zero (`0x9B273–0x9B27F`) | Generic reject, returns 0 (`0x9B29C`) |
| 101 at `0x9B538` | Store 1 in the shared byte indexed by `[0x23341]` when the array exists (`0x9B55B–0x9B560`) | Store 0 in the same byte if `0x91868` returns zero and the array exists (`0x9B572–0x9B594`) | Generic reject, returns 0 (`0x9B549`) |

For handler 19, the flag at player +0x19A participates in the
[spell cost reduction](lol2-spells.md#cast-tables-and-resource-costs)
at `0xD1068–0xD1096`. A mode-16 result alone does not identify an
item's combat effect.

## Additional admitted modes

**CONFIRMED.** These definitions are indexed from the 91-byte
table at `GLOBAL.MIX+0x5B78E9`.

| Handler and original definition | Request | Native result |
|---|---|---|
| 17, definition 42 at `+0x5B87D7` | 10, 11 | Sets or clears bit 0x04 of player byte `[0x2270E]`, respectively, and returns 1. Other modes return zero (`0x97277–0x972AE`). |
| 18, definition 17 at `+0x5B7EF4` | 10, 11 | Sets or clears bit 0x08 in the same byte. Other modes return zero (`0x972AF–0x972E6`). |
| 102, definition 166 at `+0x5BB3EB` | 1 | When the held instance exists, its +5 is zero, `[0x2260F]` is null and `[0x22712]` & 0x800 is clear, write 5 to instance +5, save the pointer in `[0x2260B]` and set bit 0x08 of `[0x22713]` (`0x9B5B5–0x9B5FD`). The success path returns 1; when the guard fails, `0x9B65C` plays the +0x160 sound and returns 0 (also 0 with sound disabled). The two sound paths read the words at `[[0x269CC]+0x156]` and `[[0x269CC]+0x160]` with the global sound-disable bit clear (`0x9B628–0x9B6BA`). The `[0x22712]` & 0x800 test reads the same bit the handler sets in `[0x22713]`, so it is a one-shot guard. |
| 103, definition 167 at `+0x5BB446` | 10, 11, 16 | Sets and clears bit 0x10 at `[0x22711]` for 10 and 11. Mode 11 clears `[0x22614]` as well. Mode 16 returns 3. All other modes return zero (`0x9B6C4–0x9B715`). |
| 106, definition 130 at `+0x5BA71F` | 17 | Requires the target pointer in request +0x15. Can create template 0x5E via `0x102D00`, then sends a hit of mask/flags `0x0080/0x0008`, kind 1, subtype 0xFF and magnitude 10 to the target’s vtable +0x80. If the target returns type 2, stores 15 at target +0xA3 (`0x9B7AC–0x9B8AC`). |

**CONFIRMED.** The later player path at `0xD25F2–0xD25FD`
copies a removed non-null item pointer to `[0x2260B]` only
when instance +5 is nonzero. Another path stores the returned
pointer of `0x95894` in `[0x2260F]` and clears `[0x2260B]`
under the same nonzero-byte test (`0x77A61–0x77A87`).
The object path at `0x94130–0x9413E` clears `[0x2260F]`
when removing the object identified there. The complete gameplay
meaning of instance +5 remains **UNCONFIRMED**. Compare this
handler’s set-to-5 path with the next consumer of `[0x2260B]`
through one held-to-world transition.

## Handler destinations

**CONFIRMED.** Every handler index 0–107 occurs among the 170 definitions
in `GLOBAL.MIX`. Index 0 has 47 definitions and its handler returns
zero. All 108 table targets below were checked against both the on-disk
table word and the object-2 fixup in the corresponding LE logical page.
The slot for index `h` starts at `LOLG.DAT+0x1CD884+4*h`; fixup offsets
are absolute file offsets. Definition `i` starts at
`GLOBAL.MIX+0x5B78E9+91*i`. An owner's byte +0x42 is the index in the
left column.

| Index | Handler VA | Fixup in LOLG.DAT | Definition indexes |
|---:|---|---|---|
| 0 | `0x95874` | `+0x8BFE3` | 47 definitions |
| 1 | `0x95FF0` | `+0x8BFEC` | 8 |
| 2 | `0x96080` | `+0x8BFF5` | 57 |
| 3 | `0x99C60` | `+0x8BFFE` | 70 |
| 4 | `0x96134` | `+0x8C007` | 123 |
| 5 | `0x96368` | `+0x8C010` | 6, 153 |
| 6 | `0x96504` | `+0x8C019` | 68, 127 |
| 7 | `0x965DC` | `+0x8C022` | 7 |
| 8 | `0x966E4` | `+0x8C02B` | 55 |
| 9 | `0x967A8` | `+0x8C034` | 109, 110 |
| 10 | `0x96880` | `+0x8C03D` | 125 |
| 11 | `0x96A44` | `+0x8C046` | 129 |
| 12 | `0x96DB8` | `+0x8C04F` | 149 |
| 13 | `0x970B4` | `+0x8C058` | 65 |
| 14 | `0x970F4` | `+0x8C061` | 19 |
| 15 | `0x97108` | `+0x8C06A` | 62 |
| 16 | `0x971F0` | `+0x8C073` | 96 |
| 17 | `0x9729C` | `+0x8C07C` | 42 |
| 18 | `0x972D4` | `+0x8C085` | 17 |
| 19 | `0x97310` | `+0x8C08E` | 41 |
| 20 | `0x9732C` | `+0x8C097` | 84 |
| 21 | `0x97408` | `+0x8C0A0` | 82 |
| 22 | `0x97558` | `+0x8C0A9` | 63 |
| 23 | `0x97884` | `+0x8C0B2` | 46 |
| 24 | `0x978D4` | `+0x8C0BB` | 88 |
| 25 | `0x9791C` | `+0x8C0C4` | 89 |
| 26 | `0x97930` | `+0x8C0CD` | 33 |
| 27 | `0x979A8` | `+0x8C0D6` | 72 |
| 28 | `0x97A60` | `+0x8C0DF` | 76 |
| 29 | `0x97B18` | `+0x8C0E8` | 79 |
| 30 | `0x97BD0` | `+0x8C0F1` | 80 |
| 31 | `0x96C08` | `+0x8BD04` | 148 |
| 32 | `0x96CC8` | `+0x8BD0D` | 75 |
| 33 | `0x96E7C` | `+0x8BD16` | 151 |
| 34 | `0x96F64` | `+0x8BD1F` | 150 |
| 35 | `0x97C88` | `+0x8BD28` | 34 |
| 36 | `0x97D08` | `+0x8BD31` | 13, 154 |
| 37 | `0x97DA4` | `+0x8BD3A` | 85 |
| 38 | `0x97E88` | `+0x8BD43` | 116 |
| 39 | `0x97F88` | `+0x8BD4C` | 117 |
| 40 | `0x98050` | `+0x8BD55` | 121 |
| 41 | `0x98154` | `+0x8BD5E` | 122 |
| 42 | `0x9822C` | `+0x8BD67` | 113 |
| 43 | `0x983B8` | `+0x8BD70` | 133 |
| 44 | `0x984B8` | `+0x8BD79` | 83 |
| 45 | `0x984CC` | `+0x8BD82` | 60 |
| 46 | `0x987A4` | `+0x8BD8B` | 126 |
| 47 | `0x98894` | `+0x8BD94` | 49 |
| 48 | `0x988B0` | `+0x8BD9D` | 15 |
| 49 | `0x98984` | `+0x8BDA6` | 91 |
| 50 | `0x98998` | `+0x8BDAF` | 30 |
| 51 | `0x98CC8` | `+0x8BDB8` | 52 |
| 52 | `0x98D00` | `+0x8BDC1` | 51 |
| 53 | `0x98D44` | `+0x8BDCA` | 53 |
| 54 | `0x98D60` | `+0x8BDD3` | 28 |
| 55 | `0x98E84` | `+0x8BDDC` | 24 |
| 56 | `0x990C0` | `+0x8BDE5` | 32 |
| 57 | `0x992DC` | `+0x8BDEE` | 21 |
| 58 | `0x993D8` | `+0x8BDF7` | 35 |
| 59 | `0x9944C` | `+0x8BE00` | 16 |
| 60 | `0x994C4` | `+0x8BE09` | 71 |
| 61 | `0x995C8` | `+0x8BE12` | 45 |
| 62 | `0x995DC` | `+0x8BE1B` | 31 |
| 63 | `0x99684` | `+0x8BE24` | 61 |
| 64 | `0x99820` | `+0x8BE2D` | 132 |
| 65 | `0x99920` | `+0x8BE36` | 64 |
| 66 | `0x9995C` | `+0x8BE3F` | 50 |
| 67 | `0x99970` | `+0x8BE48` | 118 |
| 68 | `0x99A4C` | `+0x8BE51` | 27, 155 |
| 69 | `0x99AC8` | `+0x8BE5A` | 114 |
| 70 | `0x99B94` | `+0x8BE63` | 59 |
| 71 | `0x99BEC` | `+0x8BE6C` | 26 |
| 72 | `0x99D3C` | `+0x8BE75` | 137 |
| 73 | `0x99E18` | `+0x8BE7E` | 138 |
| 74 | `0x99EF4` | `+0x8BE87` | 139 |
| 75 | `0x99FD0` | `+0x8BE90` | 140 |
| 76 | `0x9A0AC` | `+0x8BE99` | 141 |
| 77 | `0x9A188` | `+0x8BEA2` | 142 |
| 78 | `0x9A264` | `+0x8BEAB` | 143 |
| 79 | `0x9A340` | `+0x8BEB4` | 144 |
| 80 | `0x9A41C` | `+0x8BEBD` | 145 |
| 81 | `0x9A4F8` | `+0x8BEC6` | 146 |
| 82 | `0x9A5D4` | `+0x8BECF` | 147 |
| 83 | `0x9A6B0` | `+0x8BED8` | 66 |
| 84 | `0x9A794` | `+0x8BEE1` | 18 |
| 85 | `0x9A82C` | `+0x8BEEA` | 14, 156 |
| 86 | `0x9A9B4` | `+0x8BEF3` | 115 |
| 87 | `0x9AA8C` | `+0x8BB05` | 131 |
| 88 | `0x9AC14` | `+0x8BB0E` | 108 |
| 89 | `0x9AC28` | `+0x8BB17` | 134 |
| 90 | `0x9AD70` | `+0x8BB20` | 107 |
| 91 | `0x9AD98` | `+0x8BB29` | 100 |
| 92 | `0x9AE88` | `+0x8BB32` | 101 |
| 93 | `0x9AF08` | `+0x8BB3B` | 99 |
| 94 | `0x9AFB8` | `+0x8BB44` | 124 |
| 95 | `0x9B104` | `+0x8BB4D` | 128 |
| 96 | `0x9B1E4` | `+0x8BB56` | 157, 158, 159, 160, 161, 162, 163, 164, 165, 169 |
| 97 | `0x9B28C` | `+0x8BB5F` | 87 |
| 98 | `0x9B2A0` | `+0x8BB68` | 111, 119 |
| 99 | `0x9B37C` | `+0x8BB71` | 47 |
| 100 | `0x9B398` | `+0x8BB7A` | 9 |
| 101 | `0x9B538` | `+0x8BB83` | 69 |
| 102 | `0x9B5A0` | `+0x8BB8C` | 166 |
| 103 | `0x9B6FC` | `+0x8BB95` | 167 |
| 104 | `0x9B718` | `+0x8BB9E` | 25 |
| 105 | `0x9B774` | `+0x8BBA7` | 135 |
| 106 | `0x9B7AC` | `+0x8BBB0` | 130 |
| 107 | `0x9B8B0` | `+0x8BBB9` | 12 |

## What is still open

**UNCONFIRMED.** The catalog establishes every handler entry and its
definition owners. The direct effects above and in the [grant
reference](lol2-item-effects.md) were checked through their branches and
first called routines where stated. Most other handlers still need
their complete mode and effect semantics. The projectile paths beneath
`0x1050AC` and `0xFC0D8` need their target writebacks traced.
Handler 102 provides one native instance +5 producer. Start from
the handler entry for a selected definition and compare calls and
stores for the admitted request values. A before/after view of live
instance +4 and +5, the definition pointer and any changed target
fields would settle cases where the return depends on a runtime lookup.
