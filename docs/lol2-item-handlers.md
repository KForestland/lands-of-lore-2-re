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

### Replacement definitions

**CONFIRMED.** `[0x96904]` is the label object built at startup
(`0x95544–0x955C1`): its +0 points at the 74 pairs of (label
pointer, value) at data `0xC610`. `0x623D4` hashes each label with
the case-sensitive rotate-and-add routine `0x154880`, and for every
91-byte definition whose identity (+0x18, returned by the callback
`0x62694`) equals a label hash it stores the definition's index in
that pair's value (`0x625D3–0x625EA`). So `[[0x96904]] + 8k + 4` is
the definition index named by label k. In the retail files all 74
labels join a definition. The handlers read four of them:

| Handler (`definitions using it`) | Read | Pair | Replacement definition |
|---|---|---:|---|
| 2 (definition 57) | `[[0x96904]]+0x8C` at `0x960EA–0x96111` | 17 | 58 (`GLOBAL.MIX+0x5B8D87`) |
| 8 (definition 55) | `[[0x96904]]+0x7C` at `0x96761–0x96787` | 15 | 56 (`GLOBAL.MIX+0x5B8CD1`) |
| 83 (definition 66) | `[[0x96904]]+0xB4` at `0x9A749–0x9A781` | 22 | 67 (`GLOBAL.MIX+0x5B90BA`) |
| 91, 92, 93 (definitions 100, 101, 99) | `[[0x96904]]+0x12C` at `0x9ADAA` | 37 | 98 (`GLOBAL.MIX+0x5B9BBF`) |

Each item is replaced by its neighbouring definition: the program's
own labels for pairs 15, 17 and 22 end in "brnt" and pair 37's in
"E Globe", the used-up forms. `tools/lol2_item_labels.py --check`
re-runs the join.

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

## Remaining modes and effects

**CONFIRMED.** The preceding sections and the [item grant reference](lol2-item-effects.md#selected-item-use-handlers)
describe 24 of the 108 indexes. This pass adds a native mode and effect
description for the other 84, in index order. Effects are reported at
the first concrete state change, hit, movie, or constructor input.
The destination table above gives the original definition and fixup
for each row. Unless a row gives another result, its mode column lists
the paths described here.

| Index | Mode | Native effect and evidence |
|---:|---|---|
| 3 | 1, 15 | Runs movie selector 1 and returns 1. Mode 15 returns 1 before opening a resource. See the family below (`0x99C70–0x99D38`). |
| 4 | 1, 8 | Clears the hand. If player flag `[0x2270E]&0x10` is clear, stores the returned `0x9B994` item link, adds 20 to `[0x236E4]`, and sets the bit. Mode 8 updates the timer at `0x23AC1` with frame elapsed and can remove the bonus (`0x96188–0x961DE`, `0x96260–0x96358`). |
| 5 | 6, 7, 13 | Effect creation through `0xF7B94`. Mode 7 checks `[0x2271F]`; 6/13 can detach an item and try the target route. The constructor sets a type-0x5A object and adds a variant for the nonzero option (`0x96368–0x964F6`, `0xF7BA0–0xF7BD9`). |
| 6 | 1, 9 | Requires `[0x23C3F] <= 8`, calls `0x7C5DC` with 1, and removes the held item (`0x9651F–0x965C9`). |
| 7 | 5 | Uses pose and attack-region checks, resolves an effect template and calls `0x107498` with the attacker and target context (`0x965F2–0x966AC`). |
| 9 | 1 | Clears the hand and adds 5 to dword `[0x2271A]` before the feedback request (`0x967F2–0x9686E`). |
| 13 | 10, 11 | Equip sets `[0x2279B]&0x80` and one of `[0x2270E]&1` or `[0x22711]&8`. Removal clears the selected flag and can clear the first bit when neither flag nor `[0x226E5]` remains (`0x9703A–0x970AD`). |
| 14 | 10, 11 | Equip sets `[0x2270E]&2` and `[0x22712]&4`. Removal clears the former bit (`0x970CB–0x970F3`). |
| 15 | 1 | Requires target type 2, then clears the held item and submits the target to `0xF8324` on template lookup success (`0x9711D–0x971DE`). |
| 20 | 1 | Clears the held object, zeroes `[0x22729]` and invokes `0x7C7DC` and feedback `0x7C528(4, 30)` with controller `0x23819` (`0x97376–0x973F3`). |
| 21 | 5, 10, 11 | Mode 5 builds a hit on the current target and calls its +0x80 virtual receiver. Equip sets `[0x2270E]&0x40`. Removal can clear it on a zero `0x91868` result (`0x97426–0x97452`, `0x9746D–0x97534`). |
| 22 | 1, 17 | Mode 1 clears the held object and can launch three `0xF8EA8` effects, one at the player and two displaced by 40 units before restoring XY. Mode 17 calls `0xABB2C` on a type-2 target (`0x97579–0x97795`, `0x97821–0x97847`). |
| 24 | 10, 11 | Sets `[0x2270F]&1` and clears it on removal if the index-0x20 count test returns zero (`0x9789E–0x978E6`). |
| 25 | 10, 11 | Same family with `[0x2270F]&2` and count index 0x21 (`0x978E7–0x9792F`). |
| 26 | 6, 13 | Compares range with 0x800000 and can submit a template to `0x101F74` (`0x9794B–0x97995`). |
| 27–30 | 1 | Remove held instance, OR masks 1, 2, 4 and 8 respectively into `[0x23ABD]`, and request lesson ID 5 (`0x97A36/0x97AEE/0x97BA6/0x97C5E`, with the lesson calls 0x16 bytes later). |
| 34 | 1 | Clears held item and asks for school ID 4. If already available, starts the template-0x6A path through `0x1049A4` (`0x96F7A–0x97028`). |
| 35 | 6, 13 | Range comparison against 0x800000, then optional template effect `0x10275C` (`0x97CA4–0x97CF4`). |
| 37 | 10, 11 | Queries ID 0x103, changes player flags at `0x22710` or saved link at `0x22701` and invokes the recomputation at `0xDA72C` or `0xD6A08` (`0x97DBD–0x97E79`). |
| 38 | 1 | Clears held item and can call player-state helper `0xD6B20` with byte 1 (`0x97EEB–0x97F74`). |
| 39 | 1 | Clears held item and adds 5 to player +0x145, clamped by `0xD6A88` (`0x97FA4–0x9803E`). |
| 40 | 1 | Clears held item and can call `0xD6B20` with byte 2 (`0x9806C–0x98142`). |
| 41 | 1 | Clears held item and adds 20 to dword `[0x2271A]` before feedback (`0x9819D–0x9821A`). |
| 42 | 1 | Clears held item, then the `0x12415C` return determines whether it submits a self-hit with mask 0x80, flag 0x40 or 0x20, and subtype 0x45 or 0x44 (`0x9827F–0x983A0`). |
| 44 | 10, 11 | Sets `[0x2270F]&4`; removal can clear it if the index-0x1D count test returns zero (`0x98480–0x984C8`). |
| 45 | 1 | Clears held item. Can submit one `0xF9920` effect at the player and two at displaced XY, restoring player XY after each (`0x984EE–0x9878E`). |
| 46 | 1 | Clears held item and calls the player update helper `0xDA7BC` (`0x987C0–0x98858`). |
| 47 | 10, 11, 16 | Sets/clears `[0x2270F]&8`. Mode 16 gives category 2 (`0x9886A–0x988AD`). |
| 48 | 5 | Builds a hit on the player from the running attack context and submits it to `0xD03B8` (`0x988C5–0x98940`). |
| 49 | 10, 11 | Sets `[0x2270F]&0x10`; removal can clear it if the index-0x23 count test returns zero (`0x9894F–0x98995`). |
| 50 | 6, 13 | Target and range branches select template 0x5E, 0x6E, 0x6A or 0x72. Downstream options include `0x1028A4`, `0x101F74`, `0x10BB28` and `0xF7030` with variant 2 (`0x989BB–0x98C27`). |
| 51 | 10, 11 | Sets/clears `[0x2270F]&0x20` (`0x98CA3–0x98CD8`). |
| 52 | 10, 11, 16 | Sets/clears `[0x2270F]&0x40`. Mode 16 gives category 1 (`0x98CDB–0x98D16`). |
| 53 | 10, 11, 16 | Sets/clears `[0x2270F]&0x80`. Mode 16 gives category 2 (`0x98D1A–0x98D5D`). |
| 54 | 6, 13 | Range and coating branches select template 0x72 and call `0xF7030` with variants 8, 9 or 10 (`0x98D7F–0x98E70`). |
| 55 | 6, 13 | Uses template 0x72 and submits variant 1 to `0xF7030` (`0x98EA5–0x98FB5`, `0x99073–0x99092`). |
| 56 | 6, 13 | Range and target branches use template 0x72 and submit variant 4 to `0xF7030` (`0x990E1–0x99163`, `0x99222–0x992AF`). |
| 57 | 5 | Reads attack target type, checks pose and target health via virtual calls, then can submit template 0x7A through `0x1000C4` (`0x9932C–0x993A8`). |
| 58 | 6, 13 | Range-checks the request and can send its template into `0xF7030` (`0x993F3–0x9943A`). |
| 59 | 5 | Tests the target's virtual type and current versus upper quantity, then can pass the target to `0x101214` (`0x9945D–0x994B5`). |
| 60 | 5, 10, 11 | Mode 5 selects a template and `0x10B5C0` or `0x1028A4`. Equip and removal toggle `[0x22710]&1` (`0x994EA–0x9958F`). |
| 61 | 10, 11 | Sets/clears `[0x22710]&2` (`0x995A6–0x995DB`). |
| 62 | 6, 13 | Compares range with 0x800000, resolves template 0x6E and calls `0x102874` (`0x995F7–0x99670`). |
| 63 | 6, 7, 13 | Variant branches find a target and can launch template 0x6A through `0x10BB28`, setting `[0x22712]&0x80`. A mode-7 branch temporarily sets `[0x23C46]&1` for its target search (`0x996A3–0x9976F`). |
| 64 | 1 | Clears held item and requests message 0x25 directly (`0x99835–0x998A7`). |
| 65 | 10, 11 | Sets `[0x22710]&4`, calls school substitution with 6, and calls substitution with 1 on removal. That path can clear the equip bit after count test 0x14 (`0x998CD–0x99912`). |
| 66 | 10, 11 | Calls `0xDB4B0` or `0xDB4EC`. The former sets player +0x19C bit 3, and can set +0x228 bit 6. The latter tests player +0x1D2 and +0x1AB before requesting a replacement state (`0x99933–0x9996F`, `0xDB4B0–0xDB524`). |
| 67 | 1 | Clears held item and writes `0x02B20000` to player +0x1D6 through `0xDAEA0` (`0x999BE–0x99A3A`, `0xDAEA0–0xDAEB5`). |
| 69 | 1 | Clears held item and adds 0xE10 to word `[0x22750]` (`0x99B12–0x99B88`). |
| 70 | 14, 16, 18 | Mode 14 clears shared-array entry `[u8(0x2333F)]` when present and returns zero. Mode 18 stores 1 there and returns 1. Mode 16 returns category 2 (`0x99B94–0x99BEA`). |
| 71 | 6, 13 | Range check and optional template effect via `0xF7030` (`0x99C07–0x99C4E`). |
| 72–82 | 1, 15 | Movie selectors 2 through 12, one per slot. Each has the mode-15 short return. See the family below (`0x99D3C + 0xDC*(h-72)`). |
| 83 | 1 | Finds a target; type selects between two template-0x5E effects. Afterward it replaces the held definition using the loaded index at `[[0x96904]]+0xB4` (`0x9A6C4–0x9A741`, `0x9A749–0x9A781`). |
| 84 | 5 | On its draw and template-0x62 lookup path, calls `0xFF964` (`0x9A7AA–0x9A7F1`). |
| 85 | 6, 7, 13 | Shares the `0xF7B94` projectile constructor with index 5. Mode 7 checks `[0x2271F]`; 6/13 can clear a held item before the target-side request (`0x9A82C–0x9A993`). |
| 86 | 1 | Clears held item and extends player word +0x1F8 by 0xE10. If +0x1F6 was zero, the helper also sets `[0x23AB6]&0x10`, increments `[0x22798]` and clears `[0x23BD9]` (`0x9AA67`, `0xDB818–0xDB859`). |
| 87 | 1 | Clears held item, sets `[0x23AB7]&0x20`, calls `0xD6B20` with byte 1 and adds 0x780 to word `[0x22768]` (`0x9AAD6–0x9ABBE`). |
| 88 | 10, 11 | Sets `[0x22710]&0x10` and calls `0xDB85C`. Removal may clear the bit if the index-0x26 count test returns zero (`0x9ABCF–0x9AC26`). |
| 89 | 1 | Plays the admitted sounds, draws a value, clears held item and requests feedback through `0x7C528` (`0x9AC3D–0x9ACEE`). |
| 90 | 10, 11 | Sets or clears one of two equip flags at 0x22710/11. Adds 5 on equip and subtracts 5 on removal, to both player +0x141 and +0x145, with the native clamps (`0x9AD00–0x9AD94`, `0xDA780–0xDA7A5`, `0xD6A93–0xD6ABD`). |
| 91–93 | 1 | Replace the held definition via the loaded index at `[[0x96904]]+0x12C`. With successful template-0x6A lookup, 91 calls `0x104C4C`, 92 calls `0x107C44` and sets `[0x22712]&2`, and 93 calls `0x10BB28` and updates `[0x22712]` (`0x9ADAA–0x9AE76`, `0x9AE97–0x9AEF9`, `0x9AF17–0x9AFAE`). |
| 94 | 1 | Selects between sound paths, clears the hand and requests feedback through `0x7C528` (`0x9AFD3–0x9B0EF`). |
| 95 | 1 | Clears the held item and updates `[0x2279D]`. Writes `0x02760000` to player +0x1D6 through `0xDAEA0` (`0x9B14E–0x9B1CF`). |
| 96 | 1, 15 | Mode 1 can play definition word +0x37 from the held item and returns 1. Mode 15 returns 2 immediately (`0x9B1FF–0x9B256`). |
| 98 | 1 | Plays the admitted sound, clears the held item and releases the returned allocation (`0x9B2B5–0x9B347`). |
| 99 | 10, 11, 16 | Sets/clears `[0x22711]&4`. Mode 16 returns 1 (`0x9B358–0x9B395`). |
| 100 | 6, 7, 13 | Uses template 0x72 through `0xF7030` with variant 12. Mode 7 tests `[0x2271F]`; 6/13 can move the held item into the world and compare distance with 0x800000 (`0x9B3B4–0x9B516`). |
| 104 | 17 | Requires a type-2 target, resolves template 0x7A and calls `0x10E2F8` (`0x9B72B–0x9B761`). |
| 105 | 17 | Requires a type-2 target and passes it to `0xABC08` (`0x9B783–0x9B79D`). |

### The twelve movie items

**CONFIRMED.** Handler 3 and handlers 72–82 follow the same
two-format path. The string formats are `SPKSTON%d.MIX` and
`ss-%de.vqa` at file `LOLG.DAT+0x1C1BD4` and `+0x1C1BE2`.
The first filename's selector comes from object-5 +0xCA11
through +0xCA1C (file +0x1CDA35), yielding
`1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4` in that handler order.
The second filename's selector is 1 through 12. Handler 3's
witness is `0x99C88–0x99CF5`, handler 72's is
`0x99D64–0x99DD1` and handler 82's is `0x9A5FC–0x9A669`.
With the original gate at `[0xB860]` set, it opens the optional
MIX and saves the returned handle in `[0x96914]`. It runs the
VQA path through `0xCF3C0`, then closes that handle and
clears the cell. Mode 15 takes the return-1 arm without
running those paths (`0x99C76–0x99C78` → `0x99D2C–0x99D38`;
the run path is `0x99CC8–0x99D38`).

### Projectile variants at `0xF7030`

**CONFIRMED.** `0xF7030` builds a template object (`0xFB838`),
installs class vtable `0x980C` at +0x28, stores the variant byte at
+0x66 and, by variant, the sequence +0x58 and lifetime +0x5E
(`0xF704C–0xF70C6`, switch `0x9DFD0`). The class's slot +0x40
(`0xF7774`) is the contact handler. When the projectile is still
alive (+0x5E nonzero) and the contact is not its owner (+0x3E), it
fills a 0x36-byte hit packet: target +4, owner +8, projectile +0x10,
kind 5 at +0x14, byte 0x5B at +0x15, magnitude dword +0x16, first
word +0 (default 8) and second word +2 (default 4), and sends it to
the target's vtable +0x80 (`0xF7A46–0xF7AEB`):

| Variant | Packet sent to the target's +0x80 | Native lines |
|---:|---|---|
| 0, 6, 7 | word 0 `0x108`, magnitude 10 | `0xF798A–0xF79AE` |
| 1 | magnitude 10; when `0x12415C(1000)` exceeds 750 an extra packet first (word 0 `0x100`, word 2 4, magnitude 10) and a sound on the target | `0xF7802–0xF78B0` |
| 2 | an extra packet (word 0 `0x100`, magnitude 10) and sound, then word 0 `0x108`, magnitude 10 | `0xF78B5–0xF7948` |
| 3, 12 | defaults: word 0 8, word 2 4, magnitude 5 | `0xF77E1–0xF77F0` |
| 4 | magnitude 5 | `0xF794F–0xF7959` |
| 5 | a player or creature target is attached instead (+0x6E = 1, +0x6A = target, no packet); other targets take magnitude 50 | `0xF79B5–0xF79E7` |
| 8, 9, 10 | word 0 `0x108`, magnitude 5 | `0xF795E–0xF7983` |
| 11 | magnitude 5; the target is also kept at +0x6A | `0xF79EC–0xF79FB` |
| 13 | word 0 `0x108`, magnitude 40 | `0xF79FE–0xF7A17` |
| 14 | word 0 `0x108`, magnitude 20 | `0xF7A1E–0xF7A37` |

Variants 6 and 9 also set word 0 bit `0x80` and word 2 bit `0x20`;
variants 7 and 10 set word 0 bit `0x80` and word 2 bit `0x40`
(`0xF7A72–0xF7AE0`). For an attached variant-5 projectile the update
slot +0x38 reads the target's +0x98 and +0x88 values, each capped at
25, and passes them with template 0x7A to `0x1000C4`
(`0xF740C–0xF7473`). On the ground, variant 4 spawns templates 0x5E and
0xC2 and variant 11 can spawn near the player (`0xF748D–0xF753E`).
The receivers are the class +0x80 handlers described in
[combat](lol2-combat-ai.md).

**UNCONFIRMED.** Runtime names of several native flags, and what
the packet word bits mean on screen. To name a bit, follow the packet
at `0xF7774` into the selected +0x80 receiver and compare an original
contact that sets that bit with one where it is clear.

## Close-out

### Q8

**What was measured.** The code in `LOLG.DAT` contains 20 byte stores (`C6 /0`) whose 8-bit displacement is 5. One, at `0x9B5E9`, is `C6 40 05 05`, and nine store immediate 0, including `C6 40 05 00` at `0x95830`. The handler-2 instructions from `0x960EA` to `0x96111` contain no memory displacement 5; their first twelve bytes are `A1 04 69 09 00 8B 00 05 88 00 00 00`.

**What was tried.** This scan counted those displacement-5 byte stores. The page already records the constructor clear of instance +5, handler 102's store of 5, and the replacement read in that handler-2 window.

**What would settle it.** The running-game test is not yet run ([probes not yet run](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run)). Watch the held instance +5 across one use of handler 2 and compare it with the value written at `0x960EA–0x96111`. For the packet bits, follow the receiver called at `0xF7774` before and after that contact.
