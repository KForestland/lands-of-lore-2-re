# LoL2 script opcodes

This reference uses the retail 1.30 `LOLG.DAT` with SHA-256
`b27a35341c6e877e40b1540b6482748e7a750c605fefe6452431b18a5d766775`.
Addresses below are analysis VAs. For instructions in the code object, add
`0x37000` to obtain the file offset. Bracketed addresses name object-5
cells. Multibyte operands are little-endian. Offsets such as `+4` are
relative to the command unless a different record is named.

**CONFIRMED.** The size decoder at `0x645E0` recognizes 37 byte values.
The dispatcher at `0xB6B8D` uses a 24-entry table indexed by opcode minus one.
Its operand fixup is at `LOLG.DAT+0x52404`. Table data begin at
`LOLG.DAT+0xEC89C`, with fixups starting at `LOLG.DAT+0x51C5C`. The table
also has slots for 4 and 10, whose lengths are unspecified by the size decoder.
The group walker at `0x646EC` puts commands below 195 in the queue at
`0x26E6C`, and commands at or above 195 in the queue at `0x26E88`
(`0x64735–0x6475B`). The latter reaches the high dispatcher
`0x64770` through `0x664AD`.

**CONFIRMED.** Command byte +0 is the opcode. Many object commands pass
byte +1 and u16 +2 to the selector at `0x5FBC8`. The remaining bytes depend
on the opcode. For example, kind 0x20 selects pool `0x2B500` at `0x5FCB5`
and kind 0x90 reaches the 44-byte region table at `0x5FCE6`. Raw operands
are preserved in the listing. For selectors below 0x10
`0x5FD50–0x5FD72` branches on the whole byte.

## Opcode table

Sizes and handler destinations are **CONFIRMED** at the dispatchers above.
The count column is the number of commands in both framed streams across the
15 level archives, reproduced by the corpus check below. Each behavior is
**CONFIRMED** through the cited branch or call. An **UNCONFIRMED** qualifier
identifies a continuation whose effect is still open.

| Opcode dec (hex) | Bytes | Count | Handler VA | Behavior and evidence |
|---|---:|---:|---|---|
| 0 (00) | 4 | 0 | `0xB6B6E` guard | Fails the low switch range after subtracting one. The size is defined at `0x645E0`. |
| 1 (01) | 6 | 1166 | `0xB5937` | Passes object and command to vtable slot +0xAC. Result controls whether the node is consumed. |
| 2 (02) | 6 | 2252 | `0xB5BAC` | +4 selects an action. Arms 5 and 6 resolve a target at `0xB5AE4` and `0xB5B14`. Arm 5 calls `0xDD5DC` with the player, target and u8 +5. Other arms go to `0xD7890`. With +5 zero, arm 4 requests form 0 if enabled at `0xD7F58–0xD7F97`. Arm 0x13 chooses a different form index at `0xD7FB7–0xD801F`. Arm 0x1C splits u8 +5 into a low five-bit level and high three-bit arrival index (`0xD8797–0xD87C5`). |
| 3 (03) | 12 | 1086 | `0xB5937` | Calls vtable +0xAC as opcode 1 does. The player target resolves the definition identity and creates an instance. See [script grants](lol2-item-effects.md#script-grants). |
| 4 (04) | — | 0 | `0xB5947` | Common low-table epilogue. No framed command length at `0x645E0`. |
| 5 (05) | 6 | 3752 | `0xB5970` | Calls vtable +0xB0 with u8 +4 and u8 +5. |
| 6 (06) | 6 | 963 | `0xB598B → 0xB3EC8` | Object-action switch on +4. For an admitted object with a region, arm 1 calls `0x9F584` at `0xB3F5D` and passes the current region’s u16 +0x18 twice to `0xB4130` at `0xB3FB1`. Other arms depend on object flags and class. |
| 7 (07) | 6 | 2451 | `0xB5997` | Calls vtable +0xB4 with s8 +4 and u8 +5. Prop vtable 0xA848 points to `0xF21A4`; prop arm 0 sets +0x36 bits 0x05 at `0xF21C6`. |
| 8 (08) | 8 | 2390 | `0xB5A1B` | Calls vtable +0xAC. A zero result exits immediately at `0xB5A33`. |
| 9 (09) | 6 | 6586 | `0xB59B3 → 0xB50C0` | Switches on +4. See the property arms below. |
| 10 (0A) | — | 0 | `0xB5947` | Common low-table epilogue. No framed command length at `0x645E0`. |
| 11 (0B) | 8 | 0 | `0xB5C6E` | Calls `0xA1A74` with u16 +4. The callee checks the index against `[0x96954]` and passes `[0x96958][index]` in a request to `0x156BD0`, storing the result at `0xD0A4` (`0xA1A7E–0xA1ADC`). **CONFIRMED.** The handler is only jump-table slot 11 (file `LOLG.DAT+0xEC8C4`; the other stored pointer is that slot's fixup record at `LOLG.DAT+0x51CBB`). The walker queues each stored command through `0x662C4` (only caller `0x64752`); the dispatcher `0xB58FC` takes commands only from queue `0x26E6C` (`0x66550`), and the opcode 1–24 table at `LOLG.DAT+0xEC89C` is indexed by opcode−1 at `0xB6B8D`. No call targets it. All 21 direct callers of the group walker `0x646EC` pass a stored command: stream base `0x2B514` or `0x2B51C` plus a u16 from the event record (`0xB8D04` returns `0x2B514`). The 15 archives contain no opcode 11 command, so none of those callers passes one. |
| 12 (0C) | 6 | 174 | `0xB5AA2` | Calls `0xED6D0` with u8 +4. At `0xED6DB–0xED6E8`, bit 25 of `[0x2279A]` selects a jump to `0xEDA7F` when set. If clear, the ordinary path forwards +4 to `0xED470` at `0xED72A` and takes a further resource and audio path for indices below 46 (`0xED72A–0xED78B`). **CONFIRMED** all 174 requests map to the 46-name table at `LOLG.DAT+0x1CFA90`. See the [level-to-room census](lol2-level-graph.md#room-archives). |
| 13 (0D) | 8 | 1452 | `0xB5937` | Calls vtable +0xAC as opcode 1 does. Slot +0xAC by vtable: `0x5484` → `0x5D904`, `0x573C` → `0x95328`, `0x58D0` → `0xA62F4`, `0x59C8` and `0x5AD8` → `0x1502EB`, `0xA848` (props) → `0xF22B4`. **CONFIRMED.** For controls, placed items and props, opcode 13 returns 1 at `0x5D913`, `0x9533C` and `0xF22C3` after the respective byte check for opcode 8, 9 and 8. The two shared slots are the pure-virtual stub: it prints `pure virtual function called!` once (`0x150305`, string at `LOLG.DAT+0x1C56D8`, gated by `0x197B0`). Of these slots, only the creature slot, its 23-entry table and the prop slot are pinned by `lol2_level_notes.py --check`. Creature slots use the [23-entry action switch](lol2-creature-transitions.md#explicit-changes-and-animation-completion). Stored streams aim opcode 13 at actors (1,439 sites, selector 2) and props (13 sites, selector 3). |
| 14 (0E) | 8 | 3026 | `0xB59BF → 0xB47B4` | +4 is the timer action, +5 its argument, +6 the zero-based timer selector. See [timer actions](lol2-script-events.md#object-timers). |
| 15 (0F) | 8 | 761 | `0xB5C82` | Resolves a secondary object from u8 +5 and u16 +6 through `0x5FBC8`. Copies its three coordinate dwords into locals and adds the unsigned low byte of vtable +0xEC's return to Z in 16.16 units. +4 indexes the switch at `0xB5CF1`. |
| 16 (10) | 6 | 4873 | `0xB5A3C` | Stores u8 +4 in object byte +0x25. |
| 17 (11) | 6 | 66 | `0xB5A76` | Adds s8 +4 to object byte +0x25 and clamps to 0–255. |
| 18 (12) | 18 | 634 | `0xB59CE` | Occupies the sequence slot `[0xB7D5E]` if vacant. If u16 +0xA has bit 0x20 set, it resets its progress, clears the slot and sends kind-6 value 6. Otherwise the object update advances the sequence at `0x65BB0`. See [sequence motion](lol2-script-motion.md#opcode-18). |
| 19 (13) | 10 | 156 | `0xB6B5F → 0x66130` | Builds and delivers a hit through vtable +0x80. Mask and flags are u16 +4 and u16 +6. +8 carries magnitude, and +9 selects a literal or percentage. See [scripted hits](lol2-combat-ai.md#scripted-hits-and-thresholds) for the native calculations. |
| 20 (14) | 10 | 2444 | `0xB5BDC → 0xB5C0D` | Calls sound request `0xE3924` with u16 +4, the object, a pointer to +6 and constant 1. |
| 21 (15) | 6 | 577 | `0xB5AB5 → 0xCF2B4` | Passes u8 +4 and +5. The callee bounds +4 against `[0xE740]` and resolves dword slot `[0xE568+4*index]` at `0xCF2E2`. There is also a high-dispatch arm at `0x6486A`. |
| 22 (16) | 18 | 54 | `0xB5C3B` | Sends the block at +4 to `0x61190`, then calls `0xE3D2C` with the result, object, pointer to +0xE and sentinel 0xFFFE. |
| 23 (17) | 6 | 28 | `0xB5A4C` | Draws through `0x12415C`, shifts the result right five and stores its low byte at object +0x25. |
| 24 (18) | 10 | 58 | `0xB5BDC → 0xB5C2E` | Calls `0xE3D2C(0x23C68, 0, object, command+6, u16(+4))`. The callee substitutes resource 0x3103 for the zero second argument at `0xE3D4C`. The early path sends the fifth argument to the kind-8 matcher at `0xE3FED`. The fifth argument is also stored at sound object +0x2BB4 (`0xE3E76`). The later use of +0x2BB4 is **UNCONFIRMED**. The explicit disp32 occurs once in the code object, in that store. Track computed reads of sound-object +0x2BB4 after `0xE3E76`, and compare any value used at kind-8 matcher `0xAE510`. |
| 196 (C4) | 12 | 3018 | `0x6484A → 0x64DDC` | Modifies a 44-byte region row selected by u16 +2 from `[0x22D0C]`. Updates floor or ceiling. Signed +4 provides the height operand and +0xA holds the remaining movement. See [rate, callbacks and the eight post-call stores](lol2-script-motion.md#opcode-196). |
| 197 (C5) | 6 | 536 | `0x6485A → 0x64CD4` | Selects a 44-byte region via u16 +2 and switches on +4 at `0x64D0A`. Arms change region flags at +0x1C/+0x1D or use the associated 42-byte row from `[0x22D10]`. |
| 198 (C6) | 6 | 2011 | `0x64887` | Sets level-local byte u8 +4 to u8 +5 in `[0x26E54]`. |
| 199 (C7) | 6 | 132 | `0x648F6 → 0x64A8C` | Sets shared byte u8 +4 to u8 +5 in `[0x26E58]`, with special ceilings below. |
| 200 (C8) | 6 | 0 | `0x64999 → 0x64BB4` | At shared index u8 +4, stores `R(0, 32*(u8(+5)+1)-1) >> 5`, subject to special ceilings. |
| 201 (C9) | 6 | 4 | `0x64906` | Same range as 200, stored to level-local index u8 +4. The range and shift are also visible in the helper at `0x64C48`. |
| 204 (CC) | 8 | 1348 | `0x647B3` | s16 +4 = −1 calls `0xF44CC(region, u16(+6))`, which writes region bytes +0x20/+0x27. −2 writes u8 +6 to region byte +0x22. Other values select an 8-byte row in `[0x22D08]`, store u16 +6 to row +0 and set row byte +5 bit 0x40. |
| 205 (CD) | 8 | 0 | `0x6497D` | **CONFIRMED.** `0x6477B` zeros edx. Opcode 0xCD misses both compares at `0x6496B` (against `0xCC` and `0xCE`) and falls into `0x6497D`, which returns that zero. The only compare of the byte 0xCD in the code object is the length decoder at `0x64642`, which returns 8. No call targets `0x6497D`. The 15 archives contain no such command. |
| 206 (CE) | 6 | 115 | `0x6489F → 0x64B1C` | Adds s8 +5 to shared index u8 +4, saturating at zero and the applicable ceiling. |
| 207 (CF) | 6 | 242 | `0x648AF` | Adds s8 +5 to level-local index u8 +4, saturating at 0–255. |
| 208 (D0) | 8 | 129 | `0x6493B → 0x65518` | Arm +4 = 0 computes a duration from u8 +6 times 60 in 16.16 units and uses +5 to update or clear cells `0x26B4E/0x26B52`. Arm 1 uses the region at u16 +2 and cache `[0x2B524]`. **UNCONFIRMED** presentation and the full arm-1 effect. Follow one selected region from `0x65518` through the cache lookup and track the returned value to an object update or draw. |
| 209 (D1) | 10 | 2 | `0x6494B → 0x6583C` | Resolves a 42-byte region group. For resident objects with flag 0x100, adds s16 +4/+6/+8 to X/Y/Z in 16.16 units and calls vtable +0x18. Kind 0x90 obtains the group from the 44-byte region's +0x18. |
| 210 (D2) | 6 | 108 | `0x6495B → 0x65954` | +4 selects one of 12 settings at the jump `0x6596D`. Includes bit updates in `0x26D40` and a signed +5 store in `0x26D14`. Other setting names are **UNCONFIRMED**. For each arm at `0x6596D`, follow its first stored value to the matching reader of `0x26D40` or the context at `0x26D14`. |
| 240 (F0) | 6 | 9678 headers | `0x646EC` | +4 gives the number of following commands. The walker advances each child by its decoded length. These headers are counted separately. |

**CONFIRMED.** The shared-array caps are 10 at index `[0x23342]`, 2 at
`[0x23343]`, and 2 at `[0x23344]`. Other indexes cap at 255
(`0x64A8C–0x64C46`). In the table, `R(lo, hi)` calls `0x12415C` on seed
`0x221D8` and draws from the inclusive interval.

### Property command 9

**CONFIRMED.** The embedded +4 table has 35 entries at analysis `0xB5034`
(file `0xEC034`), indexed at `0xB50DE`. These arms have direct,
independently readable effects.

| +4 | Arm VA | Effect |
|---:|---|---|
| 2 | `0xB50E6` | Calls object unlink path. |
| 3 | `0xB5117` | Calls object link path. |
| 16 | `0xB5401` | Stops the object's sound through the audio helper. |
| 17 / 18 | `0xB50FB` / `0xB5109` | Sets or clears object flags bit 0x4000. |
| 10 | `0xB5393` | Clears bit 1 of object byte +0x16. |
| 19 | `0xB5420` | Stores u8 +5 in object byte +0x26. |
| 21 | `0xB5448` | Obtains the object list via vtable +0xB8 and sends kind-6 event value 20 through `0xADDE0`. |

### Region command 197

**CONFIRMED.** These direct actions use the switch at `0x64D0A` and
table at object-2 offset `0xBC84`. The secondary row is 42 bytes,
indexed by region u16 +0x18 from `[0x22D10]`.

| Command +4 | Arm VA | Effect |
|---:|---|---|
| 0 / 1 | `0x64D28` / `0x64D33` | Clear bits 0 / 1 of region byte +0x1C, respectively. |
| 2 / 3 | `0x64D3E` / `0x64D49` | Set bits 0 / 1 of region byte +0x1C, respectively. |
| 4 / 5 | `0x64D5F` / `0x64D54` | Set / clear both low bits of region byte +0x1C. |
| 6 / 7 | `0x64D6A` / `0x64D90` | Clear / set bit 0x04 in secondary row byte +0x19. |
| 8 / 9 | `0x64D1D` / `0x64D12` | Set / clear bit 0x01 of region byte +0x1D. |
| 10 | `0x64DB7` | Look up u16 +2 through `0x66664`. If found, set returned row +9 to 1. |
| 11 or greater | `0x64C7E` | Return 1 without a write. |

**UNCONFIRMED.** The on-screen result of an arm that only calls onward, the remaining effects inside `0xED6D0`, and which geometry case obstructs each class. Each selector's handler is in the table below. A running-game watch of one call-only arm would name its result.

## Subcommand handlers

<!-- script-arms:begin -->
**CONFIRMED.** `tools/lol2_instance_field.py --check` lists every selector handler. Opcode 2 at `0xB5BAC` takes selector 5 at `0xB5ACE` and selector 6 at `0xB5B05`; both call `0x5FBC8`, and selector 5 then calls `0xDD5DC`. Every other selector calls `0xD7890`, whose search on byte +4 is the opcode 2 row below. That search lands at `0xD89F6` for values 5 and 6, which this dispatcher does not pass in, and a value above 66 lands at `0xD8527`. Opcode 6 (`0xB4126`, table at `0xB3E94`, indexes 0 through 12), opcode 9 (`0xB50DE`, table at `0xB5034`, indexes 0 through 34) and opcode 15 (`0xB5CF1`, table at `0xB56D8`, indexes 0 through 112) follow. A selector past the last index lands at `0xB3F50`, `0xB56BE` or `0xB5947`. The tables hold 13, 31 and 69 different targets. In opcode 9, 4 indexes go to the past-the-end landing `0xB56BE`; in opcode 15, 42 go to `0xB5947`, the common low-table epilogue that every out-of-range selector also reaches. On opcodes 1 and 3, controls, the placed-item vtable and props return 1. The player returns 0 for opcode 1. For opcode 3 it returns 0 when `[0x223D4]` is nonzero; otherwise it calls `0x95B68`, returns 0 when that returns 0, and else returns 1, calling `0x95600` first when player byte +0x228 bit 0x80 is clear and +0x227 bit 0x40 is set. A creature returns 1 for opcode 1 and calls `0x95B68` for opcode 3. Both pure-virtual cells enter `0x1502EB` and do not read the opcode.

| Switch | Selector | Handler | First instruction |
|---|---:|---|---|
| opcode 2 | 0 | `0xD89EE` | `test ah, ah` |
| opcode 2 | 1 | `0xD79F9` | `mov al, byte ptr [ebx + 0x227]` |
| opcode 2 | 2 | `0xD89AE` | `mov edi, 1` |
| opcode 2 | 3 | `0xD7EFB` | `mov edi, 1` |
| opcode 2 | 4 | `0xD7F58` | `mov edi, 1` |
| opcode 2 | 5 | `0xB5ACE` | `mov al, byte ptr [esi + 5]` |
| opcode 2 | 6 | `0xB5B05` | `xor eax, esi` |
| opcode 2 | 7 | `0xD8988` | `xor eax, eax` |
| opcode 2 | 8 | `0xD7B8E` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 9 | `0xD7BB6` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 10 | `0xD7BE7` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 11 | `0xD8936` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 12 | `0xD7C18` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 13 | `0xD7C4F` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 14 | `0xD7C9D` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 15 | `0xD7CEE` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 16 | `0xD88CD` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 17 | `0xD7DFC` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 18 | `0xD7EA4` | `or byte ptr [ebx + 0x22a], 4` |
| opcode 2 | 19 | `0xD7FB7` | `mov edi, 1` |
| opcode 2 | 20 | `0xD8826` | `mov edi, 1` |
| opcode 2 | 21 | `0xD803F` | `mov edi, 1` |
| opcode 2 | 22 | `0xD808F` | `mov edi, 1` |
| opcode 2 | 23 | `0xD80DF` | `mov edi, 1` |
| opcode 2 | 24 | `0xD87EB` | `mov eax, 0x23348` |
| opcode 2 | 25 | `0xD812E` | `mov eax, 0x23819` |
| opcode 2 | 26 | `0xD8150` | `mov eax, 0x23819` |
| opcode 2 | 27 | `0xD8172` | `mov eax, 0x23819` |
| opcode 2 | 28 | `0xD8797` | `cmp byte ptr [0x223d6], 0` |
| opcode 2 | 29 | `0xD7D48` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 30 | `0xD7D74` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 31 | `0xD8194` | `mov eax, 0x23348` |
| opcode 2 | 32 | `0xD81AE` | `mov eax, 0x23348` |
| opcode 2 | 33 | `0xD876E` | `mov eax, 0x2375d` |
| opcode 2 | 34 | `0xD81C8` | `mov eax, 0x2375d` |
| opcode 2 | 35 | `0xD81E2` | `xor eax, eax` |
| opcode 2 | 36 | `0xD823A` | `mov dl, byte ptr [ebx + 0x228]` |
| opcode 2 | 37 | `0xD8708` | `mov al, byte ptr [ebx + 0x228]` |
| opcode 2 | 38 | `0xD7A9B` | `mov dh, byte ptr [ebx + 0x228]` |
| opcode 2 | 39 | `0xD7B21` | `and byte ptr [ebx + 0x228], 0x7f` |
| opcode 2 | 40 | `0xD8260` | `xor eax, eax` |
| opcode 2 | 41 | `0xD86B6` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 42 | `0xD828A` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 43 | `0xD82CD` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 44 | `0xD8310` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 45 | `0xD8659` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 46 | `0xD8352` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 47 | `0xD7DA2` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 48 | `0xD7DCE` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 49 | `0xD83D7` | `cmp dword ptr [ebx + 0x81], 0` |
| opcode 2 | 50 | `0xD8607` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 51 | `0xD8395` | `mov ax, word ptr [ebx + 0x20c]` |
| opcode 2 | 52 | `0xD8419` | `mov eax, 0x23819` |
| opcode 2 | 53 | `0xD8433` | `mov eax, 0x23819` |
| opcode 2 | 54 | `0xD8575` | `xor eax, eax` |
| opcode 2 | 55 | `0xD844D` | `xor eax, eax` |
| opcode 2 | 56 | `0xD84AB` | `push ebx` |
| opcode 2 | 57 | `0xD7E54` | `cmp byte ptr [0x223d4], 0` |
| opcode 2 | 58 | `0xD89B3` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 59 | `0xD7F00` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 60 | `0xD7F5D` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 61 | `0xD7FBC` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 62 | `0xD882B` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 63 | `0xD8044` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 64 | `0xD8094` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 65 | `0xD80E4` | `test byte ptr [ebx + 0x228], 0x10` |
| opcode 2 | 66 | `0xD84C0` | `push 1` |
| opcode 2 | 67-255 | `0xD8527` | `mov eax, 1` |
| opcode 6 | 0 | `0xB3F00` | `mov eax, ebx` |
| opcode 6 | 1 | `0xB3F5C` | `push ebx` |
| opcode 6 | 2 | `0xB3FC5` | `push ebx` |
| opcode 6 | 3 | `0xB4006` | `mov eax, dword ptr [esi + 2]` |
| opcode 6 | 4 | `0xB401B` | `mov eax, dword ptr [esi + 2]` |
| opcode 6 | 5 | `0xB4030` | `mov al, byte ptr [esi + 5]` |
| opcode 6 | 6 | `0xB4042` | `xor eax, eax` |
| opcode 6 | 7 | `0xB4057` | `xor ah, ah` |
| opcode 6 | 8 | `0xB4075` | `xor ah, ah` |
| opcode 6 | 9 | `0xB4098` | `mov ch, byte ptr [ebx + 2]` |
| opcode 6 | 10 | `0xB40B3` | `mov cl, byte ptr [ebx + 2]` |
| opcode 6 | 11 | `0xB40E9` | `mov dh, byte ptr [ebx + 2]` |
| opcode 6 | 12 | `0xB40CE` | `mov dl, byte ptr [ebx + 2]` |
| opcode 9 | 0 | `0xB53D9` | `xor eax, eax` |
| opcode 9 | 1 | `0xB53D9` | `xor eax, eax` |
| opcode 9 | 2 | `0xB50E6` | `push 0` |
| opcode 9 | 3 | `0xB5117` | `push 1` |
| opcode 9 | 4 | `0xB512C` | `mov eax, dword ptr [ebx + 0x14]` |
| opcode 9 | 5 | `0xB520D` | `mov eax, dword ptr [ebx + 0x14]` |
| opcode 9 | 6 | `0xB52EE` | `mov eax, dword ptr [ebx + 0x14]` |
| opcode 9 | 7 | `0xB5369` | `or byte ptr [ebx + 0x14], 0x80` |
| opcode 9 | 8 | `0xB5377` | `and byte ptr [ebx + 0x14], 0x7f` |
| opcode 9 | 9 | `0xB5385` | `or byte ptr [ebx + 0x16], 2` |
| opcode 9 | 10 | `0xB5393` | `and byte ptr [ebx + 0x16], 0xfd` |
| opcode 9 | 11 | `0xB53A1` | `or byte ptr [ebx + 0x15], 0x20` |
| opcode 9 | 12 | `0xB53AF` | `and byte ptr [ebx + 0x15], 0xdf` |
| opcode 9 | 13 | `0xB53BD` | `and byte ptr [ebx + 0x15], 0x7f` |
| opcode 9 | 14 | `0xB53CB` | `or byte ptr [ebx + 0x15], 0x80` |
| opcode 9 | 15 | `0xB53E0` | `mov esi, dword ptr [0xb7d5e]` |
| opcode 9 | 16 | `0xB5401` | `mov eax, 1` |
| opcode 9 | 17 | `0xB50FB` | `or byte ptr [ebx + 0x15], 0x40` |
| opcode 9 | 18 | `0xB5109` | `and byte ptr [ebx + 0x15], 0xbf` |
| opcode 9 | 19 | `0xB5420` | `mov al, byte ptr [eax + 5]` |
| opcode 9 | 20 | `0xB5430` | `test byte ptr [ebx + 0x15], 0x80` |
| opcode 9 | 21 | `0xB5448` | `push 0x14` |
| opcode 9 | 22 | `0xB546A` | `cmp dword ptr [0x225f5], 0` |
| opcode 9 | 23 | `0xB54A1` | `mov edi, dword ptr [ebx + 0x14]` |
| opcode 9 | 24 | `0xB5516` | `or byte ptr [ebx + 0x16], 1` |
| opcode 9 | 25 | `0xB5592` | `mov edx, dword ptr [ebx + 0x28]` |
| opcode 9 | 26 | `0xB56BE` | `push eax` |
| opcode 9 | 27 | `0xB56BE` | `push eax` |
| opcode 9 | 28 | `0xB56BE` | `push eax` |
| opcode 9 | 29 | `0xB56BE` | `push eax` |
| opcode 9 | 30 | `0xB5628` | `mov al, byte ptr [eax + 5]` |
| opcode 9 | 31 | `0xB5666` | `mov al, byte ptr [eax + 5]` |
| opcode 9 | 32 | `0xB569E` | `mov edx, dword ptr [ebx + 0x28]` |
| opcode 9 | 33 | `0xB55EA` | `mov al, byte ptr [eax + 5]` |
| opcode 9 | 34 | `0xB55B2` | `mov al, byte ptr [eax + 5]` |
| opcode 15 | 0 | `0xB6346` | `mov eax, dword ptr [ebp - 0x28]` |
| opcode 15 | 1 | `0xB6346` | `mov eax, dword ptr [ebp - 0x28]` |
| opcode 15 | 2 | `0xB5947` | `test edi, edi` |
| opcode 15 | 3 | `0xB6346` | `mov eax, dword ptr [ebp - 0x28]` |
| opcode 15 | 4 | `0xB6346` | `mov eax, dword ptr [ebp - 0x28]` |
| opcode 15 | 5 | `0xB5DE0` | `mov eax, 0x5e` |
| opcode 15 | 6 | `0xB5E10` | `mov eax, 0x5e` |
| opcode 15 | 7 | `0xB5E3F` | `mov eax, 0xc2` |
| opcode 15 | 8 | `0xB5947` | `test edi, edi` |
| opcode 15 | 9 | `0xB5E6F` | `mov eax, 0x7e` |
| opcode 15 | 10 | `0xB5947` | `test edi, edi` |
| opcode 15 | 11 | `0xB5947` | `test edi, edi` |
| opcode 15 | 12 | `0xB5947` | `test edi, edi` |
| opcode 15 | 13 | `0xB5947` | `test edi, edi` |
| opcode 15 | 14 | `0xB5947` | `test edi, edi` |
| opcode 15 | 15 | `0xB5EFF` | `mov eax, 0x5e` |
| opcode 15 | 16 | `0xB5947` | `test edi, edi` |
| opcode 15 | 17 | `0xB5F34` | `mov eax, 0x66` |
| opcode 15 | 18 | `0xB5947` | `test edi, edi` |
| opcode 15 | 19 | `0xB5F60` | `or byte ptr [0x22712], 8` |
| opcode 15 | 20 | `0xB5F74` | `mov eax, 0x6a` |
| opcode 15 | 21 | `0xB5FA4` | `mov eax, 0x6a` |
| opcode 15 | 22 | `0xB5FD4` | `mov eax, 0x6a` |
| opcode 15 | 23 | `0xB6003` | `mov eax, 0x6a` |
| opcode 15 | 24 | `0xB5947` | `test edi, edi` |
| opcode 15 | 25 | `0xB5947` | `test edi, edi` |
| opcode 15 | 26 | `0xB5947` | `test edi, edi` |
| opcode 15 | 27 | `0xB5947` | `test edi, edi` |
| opcode 15 | 28 | `0xB5947` | `test edi, edi` |
| opcode 15 | 29 | `0xB5947` | `test edi, edi` |
| opcode 15 | 30 | `0xB5CF9` | `mov eax, 0x5e` |
| opcode 15 | 31 | `0xB5D2A` | `mov eax, 0x5e` |
| opcode 15 | 32 | `0xB5D5B` | `mov eax, 0x6e` |
| opcode 15 | 33 | `0xB5D91` | `mov eax, 0x6e` |
| opcode 15 | 34 | `0xB5DC8` | `mov eax, 0x14` |
| opcode 15 | 35 | `0xB67EF` | `mov eax, 0x66` |
| opcode 15 | 36 | `0xB5947` | `test edi, edi` |
| opcode 15 | 37 | `0xB6829` | `mov eax, 0x66` |
| opcode 15 | 38 | `0xB685D` | `xor eax, eax` |
| opcode 15 | 39 | `0xB5947` | `test edi, edi` |
| opcode 15 | 40 | `0xB5947` | `test edi, edi` |
| opcode 15 | 41 | `0xB5947` | `test edi, edi` |
| opcode 15 | 42 | `0xB5947` | `test edi, edi` |
| opcode 15 | 43 | `0xB5947` | `test edi, edi` |
| opcode 15 | 44 | `0xB5947` | `test edi, edi` |
| opcode 15 | 45 | `0xB6443` | `mov eax, 0x6a` |
| opcode 15 | 46 | `0xB6479` | `mov eax, 0x66` |
| opcode 15 | 47 | `0xB64AE` | `mov eax, 0x14` |
| opcode 15 | 48 | `0xB64C6` | `mov eax, 0x6e` |
| opcode 15 | 49 | `0xB5947` | `test edi, edi` |
| opcode 15 | 50 | `0xB5947` | `test edi, edi` |
| opcode 15 | 51 | `0xB5947` | `test edi, edi` |
| opcode 15 | 52 | `0xB6562` | `mov eax, 0x7a` |
| opcode 15 | 53 | `0xB65CE` | `mov eax, 0x72` |
| opcode 15 | 54 | `0xB6617` | `mov eax, 0x7a` |
| opcode 15 | 55 | `0xB6683` | `mov eax, 0x72` |
| opcode 15 | 56 | `0xB5947` | `test edi, edi` |
| opcode 15 | 57 | `0xB66CC` | `test esi, esi` |
| opcode 15 | 58 | `0xB6360` | `mov eax, 0x6e` |
| opcode 15 | 59 | `0xB63C5` | `mov eax, 0x66` |
| opcode 15 | 60 | `0xB6392` | `mov eax, 0x6e` |
| opcode 15 | 61 | `0xB5947` | `test edi, edi` |
| opcode 15 | 62 | `0xB63F4` | `xor eax, eax` |
| opcode 15 | 63 | `0xB6406` | `mov eax, dword ptr [0xdf66c]` |
| opcode 15 | 64 | `0xB6033` | `mov eax, 0x5e` |
| opcode 15 | 65 | `0xB6071` | `mov eax, 0x5e` |
| opcode 15 | 66 | `0xB60B0` | `mov eax, 0x5e` |
| opcode 15 | 67 | `0xB6760` | `mov eax, 0x6e` |
| opcode 15 | 68 | `0xB5ECE` | `mov eax, 0x62` |
| opcode 15 | 69 | `0xB5E9C` | `mov eax, 0x62` |
| opcode 15 | 70 | `0xB5947` | `test edi, edi` |
| opcode 15 | 71 | `0xB64F5` | `mov eax, 0x6e` |
| opcode 15 | 72 | `0xB678F` | `mov eax, 0x66` |
| opcode 15 | 73 | `0xB6533` | `mov eax, 0x62` |
| opcode 15 | 74 | `0xB5947` | `test edi, edi` |
| opcode 15 | 75 | `0xB5947` | `test edi, edi` |
| opcode 15 | 76 | `0xB5947` | `test edi, edi` |
| opcode 15 | 77 | `0xB5947` | `test edi, edi` |
| opcode 15 | 78 | `0xB5947` | `test edi, edi` |
| opcode 15 | 79 | `0xB5947` | `test edi, edi` |
| opcode 15 | 80 | `0xB5947` | `test edi, edi` |
| opcode 15 | 81 | `0xB67BE` | `mov eax, 0x6e` |
| opcode 15 | 82 | `0xB6AC7` | `mov eax, 0x6a` |
| opcode 15 | 83 | `0xB5947` | `test edi, edi` |
| opcode 15 | 84 | `0xB5947` | `test edi, edi` |
| opcode 15 | 85 | `0xB5947` | `test edi, edi` |
| opcode 15 | 86 | `0xB686F` | `mov eax, 0x66` |
| opcode 15 | 87 | `0xB689F` | `mov eax, 0x5e` |
| opcode 15 | 88 | `0xB68D4` | `mov eax, 0x66` |
| opcode 15 | 89 | `0xB6905` | `mov eax, 0x5e` |
| opcode 15 | 90 | `0xB5947` | `test edi, edi` |
| opcode 15 | 91 | `0xB61D3` | `mov eax, 0x72` |
| opcode 15 | 92 | `0xB626E` | `mov eax, 0x72` |
| opcode 15 | 93 | `0xB62A4` | `mov eax, 0x72` |
| opcode 15 | 94 | `0xB6209` | `mov eax, 0x72` |
| opcode 15 | 95 | `0xB62DA` | `mov eax, 0x72` |
| opcode 15 | 96 | `0xB6310` | `mov eax, 0x72` |
| opcode 15 | 97 | `0xB623E` | `push 0x6e` |
| opcode 15 | 98 | `0xB60EF` | `push 0x62` |
| opcode 15 | 99 | `0xB611C` | `push 0x62` |
| opcode 15 | 100 | `0xB614A` | `push 0x62` |
| opcode 15 | 101 | `0xB6178` | `push 0x62` |
| opcode 15 | 102 | `0xB61A6` | `push 0x62` |
| opcode 15 | 103 | `0xB5947` | `test edi, edi` |
| opcode 15 | 104 | `0xB69B5` | `mov ecx, dword ptr [ebp - 0x24]` |
| opcode 15 | 105 | `0xB69A3` | `mov eax, dword ptr [ebp - 0x20]` |
| opcode 15 | 106 | `0xB6991` | `mov ecx, dword ptr [ebp - 0x20]` |
| opcode 15 | 107 | `0xB6939` | `test byte ptr [0x269c4], 1` |
| opcode 15 | 108 | `0xB6AB5` | `push 0x22574` |
| opcode 15 | 109 | `0xB5947` | `test edi, edi` |
| opcode 15 | 110 | `0xB5947` | `test edi, edi` |
| opcode 15 | 111 | `0xB6B31` | `push 0x72` |
| opcode 15 | 112 | `0xB6B03` | `push 0x72` |

| Slot | Cell | Handler | Opcode 1 | Opcode 3 |
|---|---|---|---|---|
| controls | `0x5484` | `0x5D904` | returns 1 | returns 1 |
| placed item | `0x573C` | `0x95328` | returns 1 | returns 1 |
| creature | `0x58D0` | `0xA62F4` | returns 1 | calls `0x95B68`, then returns 1 |
| pure virtual | `0x59C8` | `0x1502EB` | does not read the opcode | does not read the opcode |
| pure virtual | `0x5AD8` | `0x1502EB` | does not read the opcode | does not read the opcode |
| props | `0xA848` | `0xF22B4` | returns 1 | returns 1 |
| player | `0x5C20` | `0xD7890` | returns 0 | 0 when `[0x223D4]` is nonzero or `0x95B68` returns 0, else 1 |
<!-- script-arms:end -->

## Worked disassembly and corpus check

```bash
python3 tools/lol2_disassemble_scripts.py --data /path/to/DAT L1_DC
python3 tools/lol2_disassemble_scripts.py --data /path/to/DAT --check
```

**CONFIRMED.** `L1_DC.MIX+0x6FD211` contains `0E 03 14 06 03 00 00 00`.
The listing prints opcode 0x0E, selector kind 3, index 0x0614, action 3,
argument zero and timer index zero. Native arm `0xB485C` clears the timer's
disabled bit and keeps its current countdown when the argument is zero.
The corpus check frames both streams, resolves the linked event groups and
verifies the listing prints all 42,594 commands. See
[the stream layout](lol2-level-script-format.md) for geometry header offsets.

## Close-out

### Q4

**What was measured.** At `0xB6E8F` the three bytes are `FF 50 08`, a call through vtable slot +8. The compare at `0xB6E98` is `39 C7`, and the next instruction is `0F 8F 12 01 00 00`, a jump to `0xB6FB2` when the first operand is greater.

**What was tried.** This slice is the obstruction compare next to the opcode-196 gate. The opcode page already records the handler `0x64DDC` and the framed corpus of 42,594 commands.

**What would settle it.** The running-game test is not yet run ([probes not yet run](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run)). Match the opcode-196 handler at `0x64DDC` and record the first geometry rejection before the candidate transform is written.
