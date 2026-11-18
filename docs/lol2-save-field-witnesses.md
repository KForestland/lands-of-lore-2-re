# LoL2 save list heads and placed-item inputs

Addresses use the DOS 1.30 [analysis convention](lol2-executable-tables.md).
Slot offsets below refer to the native reference save with SHA-256 prefix
`a97f9c4782d4`. Its level-1 block starts at `0x6EA8`. See the
[section reference](lol2-save-sections.md).

## Saved world-list links

**CONFIRMED.** `0xE8D42` selects level section 28 from object-5 cell
`0xB7D6C`, and `0xE8D5D` selects section 29 from `0xB7D70`. These are two
singly linked object-list heads. The insertion helper `0xB3A9C` puts the
old head in object +0x10, puts the object in the head cell and sets object
+0x17 bit `0x20` for the first list (`0xB3AAC–0xB3ABD`). The removal path
at `0xB3B04` clears that bit and removes the object by updating the head
or its predecessor's +0x10 (`0xB3B15–0xB3B54`). The constructor path for a
placed item inserts it into the list at `0xB7D6C` (`0xAEA0B–0xAEA2E`).
The release path at `0xAEBBA–0xAEBD5` chooses a head cell according to
object +0x14 mask `0x20000000` before removing it.

**CONFIRMED.** The following values come from two raw spans of
the reference slot. Applying each saved base and pool stride identifies a row
within its pointer range. Range slots 18 and 19 come from the control
and actor pools at `0xE5DD6–0xE5E00`. Both section-adjust entries in
object-2 table `0x905B4` target `0xE9D90`, which calls `0xEB2C8` to map a
single pointer. The raw-span load path calls the adjuster at `0xE76A4`.

| Section | Slot offset | Saved pointer | Old range slot and base | Pool row |
|---:|---|---|---|---:|
| 28 | `0x194FA` | `0x11217554` | 19 at block +0x50, base `0x11214C34` | Actor 56, stride 0xBC |
| 29 | `0x194FE` | `0x11214354` | 18 at block +0x4C, base `0x11212014` | Control 141, stride 0x40 |

**CONFIRMED.** Across the 149 nonempty reference blocks, 100 carry
both section heads. At the offsets from each block’s +0xD8 directory,
section 28 pointers fall in range slots 19 (53), 18 (17), 20 (14),
17 (11) and 23 (5). Section 29 pointers fall in slots 17 (59), 18
(24), 19 (16) and 20 (1). Base and extent arrays begin at block +4
and +0x6C. The actor and control rows above describe one save.

**CONFIRMED.** Flag `0x1` at `0xE742E–0xE7436` is the admission gate for
this level-state loader. If the bit is clear, the branch skips reading
that section through this path. Flag `0x4` still selects compressed or
raw input at `0xE7626–0xE765B` for a section without the XOR flag. This
bounds the role of flag `0x1` for the traced reader. Other consumers of
that flag remain **UNCONFIRMED**.

## From placement row to item definition

**CONFIRMED.** The level loader seeks and calls `0x94078` at
`0x9D43A–0x9D450`. `0x94096–0x940BF` reads 37-byte placement rows and
calls the placed-item constructor. In that constructor, `0x93FD8–0x93FE1`
passes placement u32 +0x20 to `0x9EB5C`. The latter is an identity lookup:
it compares against item definition dword +0x18 and advances by 0x5B
(`0x9EB65–0x9EB78`). The return is passed to `0x95824`, together with
u8 placement +0x24 (`0x93FD4–0x93FEE`). A null pointer is replaced
by `[0x22CF4]` at `0x94007–0x9400C`. The base constructor reads s16
placement +0x0A as a region index, or −1 for no region
(`0xAEA30–0xAEA5C`).

**CONFIRMED.** Reading the geometry header's offset +0x20 and count
+0x6C gives 663 rows across the 15 original level archives. In each
archive `offset + 37*count` equals the next table offset read at header
+0x24. All 663 identity words at row +0x20 resolve to the 170 definitions.
There are 643 zero values for row +0x24 and 20 nonzero values, ranging
from 1 to 5. This is the byte copied through to instance +4. Its effect
is item-specific, as shown in [item handlers](lol2-item-handlers.md).

For example, `L1_DC.MIX+0x6FBD7E` is placed-item row 0. Its identity at
`+0x6FBD9E` is `0x082D2562` and its instance input at `+0x6FBDA2` is zero.
The identity is definition row 34 (`GLOBAL.MIX+0x5B78E9+34*91+0x18`).
The [controlled L20_BB pickup](lol2-save-sections.md#controlled-pickup-in-l20_bb)
shows the changed placement row and player occupancy bit in two native saves.

## Short snapshot status

**CONFIRMED.** The 26-pair map builder `0xE5C48` ends its writes at map
+0xCC (`0xE5E75–0xE5E8B`). The level writer passes its stack buffer +4
as the map at `0xE80CD–0xE80D7`, and writes it as part of the complete
0x2F8-byte header at `0xE83D4–0xE83DF`. The only three sections saved
with zero third argument bypass the address-adjuster call at `0xE8283`
because their flags lack `0x2` (`0xE815D–0xE8195`). The normal map-status
zero store in `0xE96EC` therefore does not execute on a short write.

**UNCONFIRMED.** The existing stack value yielding `0xFF00FFFF` in the
49 short native examples lacks a verified producer. The map path and
entire header write were checked. A targeted trace would watch the stack
address passed at `0xE83D9` plus 0xD4, starting before `0xE7F68`.
The controlled pickup resolves a separate question from this
short-header value.
