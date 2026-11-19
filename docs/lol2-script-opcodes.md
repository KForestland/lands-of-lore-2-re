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
| 11 (0B) | 8 | 0 | `0xB5C6E` | Calls `0xA1A74` with u16 +4. The callee checks the index against `[0x96954]` and passes `[0x96958][index]` in a request to `0x156BD0`, storing the result at `0xD0A4` (`0xA1A7E–0xA1ADC`). **UNCONFIRMED** a caller in a stored script. Find a retail stream with opcode 11, then trace the resource ID returned through `0x156BD0`. |
| 12 (0C) | 6 | 174 | `0xB5AA2` | Calls `0xED6D0` with u8 +4. It checks bit 25 of `[0x2279A]`, forwards +4 to `0xED470` and takes a further resource and audio path for indices below 46 (`0xED6DB–0xED78B`). **CONFIRMED** all 174 requests map to the 46-name table at `LOLG.DAT+0x1CFA90`. See the [level-to-room census](lol2-level-graph.md#room-archives). |
| 13 (0D) | 8 | 1452 | `0xB5937` | Calls vtable +0xAC as opcode 1 does. For props, `0xF22B4` returns immediately for opcode 13. **UNCONFIRMED** remaining class effects. Resolve slot +0xAC from each object constructor and trace the opcode check. |
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
| 24 (18) | 10 | 58 | `0xB5BDC → 0xB5C2E` | Calls `0xE3D2C(0x23C68, 0, object, command+6, u16(+4))`. The callee substitutes resource 0x3103 for the zero second argument at `0xE3D4C`. The early path sends the fifth argument to the kind-8 matcher at `0xE3FED`. The fifth argument is also stored at sound object +0x2BB4 (`0xE3E76`). Its full use is **UNCONFIRMED**. |
| 196 (C4) | 12 | 3018 | `0x6484A → 0x64DDC` | Modifies a 44-byte region row selected by u16 +2 from `[0x22D0C]`. Updates floor or ceiling. Signed +4 provides the height operand and +0xA holds the remaining movement. See [rate, callbacks and the eight post-call stores](lol2-script-motion.md#opcode-196). |
| 197 (C5) | 6 | 536 | `0x6485A → 0x64CD4` | Selects a 44-byte region via u16 +2 and switches on +4 at `0x64D0A`. Arms change region flags at +0x1C/+0x1D or use the associated 42-byte row from `[0x22D10]`. |
| 198 (C6) | 6 | 2011 | `0x64887` | Sets level-local byte u8 +4 to u8 +5 in `[0x26E54]`. |
| 199 (C7) | 6 | 132 | `0x648F6 → 0x64A8C` | Sets shared byte u8 +4 to u8 +5 in `[0x26E58]`, with special ceilings below. |
| 200 (C8) | 6 | 0 | `0x64999 → 0x64BB4` | At shared index u8 +4, stores `R(0, 32*(u8(+5)+1)-1) >> 5`, subject to special ceilings. |
| 201 (C9) | 6 | 4 | `0x64906` | Same range as 200, stored to level-local index u8 +4. The range and shift are also visible in the helper at `0x64C48`. |
| 204 (CC) | 8 | 1348 | `0x647B3` | s16 +4 = −1 calls `0xF44CC(region, u16(+6))`, which writes region bytes +0x20/+0x27. −2 writes u8 +6 to region byte +0x22. Other values select an 8-byte row in `[0x22D08]`, store u16 +6 to row +0 and set row byte +5 bit 0x40. |
| 205 (CD) | 8 | 0 | `0x6497D` | High dispatch rejects it and returns zero. **UNCONFIRMED** whether any other caller handles it. Search entry points bypassing `0x6497D` and check the original generated command at dispatch. |
| 206 (CE) | 6 | 115 | `0x6489F → 0x64B1C` | Adds s8 +5 to shared index u8 +4, saturating at zero and the applicable ceiling. |
| 207 (CF) | 6 | 242 | `0x648AF` | Adds s8 +5 to level-local index u8 +4, saturating at 0–255. |
| 208 (D0) | 8 | 129 | `0x6493B → 0x65518` | Arm +4 = 0 computes a duration from u8 +6 times 60 in 16.16 units and uses +5 to update or clear cells `0x26B4E/0x26B52`. Arm 1 uses the region at u16 +2 and cache `[0x2B524]`. **UNCONFIRMED** presentation and the full arm-1 effect. |
| 209 (D1) | 10 | 2 | `0x6494B → 0x6583C` | Resolves a 42-byte region group. For resident objects with flag 0x100, adds s16 +4/+6/+8 to X/Y/Z in 16.16 units and calls vtable +0x18. Kind 0x90 obtains the group from the 44-byte region's +0x18. |
| 210 (D2) | 6 | 108 | `0x6495B → 0x65954` | +4 selects one of 12 settings at the jump `0x6596D`. Includes bit updates in `0x26D40` and a signed +5 store in `0x26D14`. **UNCONFIRMED** meanings of all settings. |
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

**UNCONFIRMED.** Virtual implementations of +0xAC, the complete +4 switches
of opcodes 2, 6, 9 and 15, and downstream effects in helpers such as
`0xED6D0` are open. The bytecode framing and the handler destinations establish
where to start. The next static check is to match observed command selectors to
constructor vtables and follow their concrete calls. A branch witness with
initial and final objects would settle effects involving queued or indirect writes.

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
