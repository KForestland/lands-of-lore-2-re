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

## Native field and payload cross-reference

**CONFIRMED.** In the table, G denotes the global directory and L a level
directory. The save writers call the cited selectors at `0xE7931` (G)
and `0xE8125` (L). The global writer compresses at `0xE7A3E` or
writes raw bytes at `0xE7A5B`. The level writer uses `0xE82AE` or
`0xE8316` for compression and `0xE82D0` or `0xE8338` for raw bytes.
The same selectors supply destination addresses to the loader at
`0xE69D1` (G) and `0xE7418` (L). Global XOR restoration writes at
`0xE6B0E/0xE6B46`, global raw restoration calls `0x118820` at
`0xE6CFC`. Level XOR restoration writes at `0xE7521/0xE7559`
and level raw restoration calls `0x118820` at `0xE765B`.
For flags 7 the level delta passes through `0xE749C` first.
Both loaders apply section-specific fixups after the read
(`0xE6B88/0xE6D45` and `0xE7598/0xE76A4`).

| Section | Field or payload | Writer address | Reader address | Meaning |
|---|---|---|---|---|
| Slot +0x094 | u32 | `0xE777D` | Bulk header read at `0xE687E` | **UNCONFIRMED** semantic role. The writer supplies zero. |
| Slot +0x098 | u32 | `0xE78B1` | Bulk header read at `0xE687E` | **UNCONFIRMED** consumer of value 1. |
| Slot +0x20A…+0x259 | 80 bytes after directories | Full header at `0xE7CF1` | Bulk header read at `0xE687E` | **UNCONFIRMED** field meanings. The directory write loop stops after 20 offsets. |
| L block +0xD4 | address-map status | `0xE9719` full path, `0xE83DF` header output | Fixup result at `0xE97AC` | Maps pointer adjustment error state. Source of the short block's residual bytes is **UNCONFIRMED**. |
| G4 | +0 and following bytes | `0xE8723` | UI strike callers of `0x88D2C`, e.g. `0x7DAC0` | UI and combat context. Individual fields beyond those joined in the [item note](lol2-item-format.md) remain **UNCONFIRMED**. |
| G5 | scene movie context +0x10 through +0x3C | `0xE873D` | `0xA02C2`, `0xA03B4–0xA03B7` | Object at `[0x22CE0]`, used by the movie control path. Resume copies its +0x3C byte to +0x4E. Other saved fields **UNCONFIRMED**. |
| G6 | 12 bytes at `0x22CE4` | `0xE876F` | `0xE6CFC` | **UNCONFIRMED** subfields. This is the span after the movie-context pointer. |
| G7 | 13 dwords at `0xDB4CC` | `0xE878D`; set `0xEF347`, clear `0xEF375` | `0xEF39B` | Bitmap indexed by argument / 32 and argument & 31. Game-facing labels of individual bits are **UNCONFIRMED**. |
| G8 | 91 bytes at `0x22518` | `0xE87A9` | Menu callers `0xB94F3`, `0xB95A5` | Input/overlay context used by menu open and close. Individual saved fields **UNCONFIRMED**. |
| G9 | byte per 91-byte definition | `0xE87C3`; set at `0x95697` | `0x9567B–0x956AB` | Bit 0 records that the per-definition branch has already run. The updater computes the row from the definition pointer difference ÷ 91. Other bits are **UNCONFIRMED**. |
| G10 | +0x04 clock, +0x14 accumulated sample, +0x21 frame index | `0xE87E2`; `0xA0239`, `0xE0A67` | `0xA021F–0xA022C`, `0xE0BE9` | Level clock, sample cell and frame index respectively. The index is outside level section 67 and inside this global section. Other subfields **UNCONFIRMED**. |
| L0–2 | Short block payloads | `0xE8940`, `0xE896C`, `0xE898C` | `0xE742E–0xE7436` | **UNCONFIRMED** meanings. The level restore gate admits section 1 (flags 9) and skips 0 and 2 (flags 0xC). |
| L3/4, L5/6 | 0x1C-byte headers and 8-byte arrays | `0x9CC23–0x9CC3B`, `0x9CC78–0x9CC88` | `0x64745`, `0x6474D`, `0xA0523` | Two arrays with allocation, cursor and count fields. Roles of each 8-byte element **UNCONFIRMED**. |
| L7/8, L9/10 | Two event-data and command-stream pairs | `0x9CF06/0x9CF4B`, `0x9CF90/0x9CFD5` | `0xF2D5C`, `0xAD89E–0xAD8AD`, `0xB71BC–0xB71C7` | Region-side data/commands, and object-side data/commands. Section 9 supplies the placed-item event lists. |
| L11, L13, L14 | Vertex, secondary region and wall rows | `0xE8AB4`, `0xE8B09`, `0xE8B3A` | `0x5FD1E`, `0x63207`, `0x1147F8` | The level arrays described in [geometry](formats/geometry.md). |
| L15 | 12-byte rows | `0xE8B5D` | `0xE2AD3–0xE2AE2` | A u16 index selects a row and the initializer installs its address at +4 of an audio-side record. Row semantics **UNCONFIRMED**. |
| L18 | secondary element pool | `0x9D254`, `0xE8BD3` | `0xADEDC`, `0xEA133` entry 18 | Separate pool from L21 actors, with pointer adjustments at `0xE9A1E`. Game-facing role **UNCONFIRMED**. |
| L20/L23 | offset-selected bytes | `0x5B7CD`, `0x63151` | `0x5DA2A`, `0x644A6` | Controls and movables select the byte address by adding their u16 +0x36. Full row formats **UNCONFIRMED**. |
| L26/L27 | 24-byte and 8-byte rows | `0xE8CF2`, `0xE8D1F` | `0xA053E`, `0xA0553` | Frame update takes each table pointer with its count. Detailed fields **UNCONFIRMED**. |
| L30 | 0x30-byte context | `0xE8D78` | `0xD36FE` | Context passed alongside the player object to `0x115D6C`. Subfields **UNCONFIRMED**. |
| L33 | dword at `0x969A4` | `0xA7245` | `0xAA5E9` | Object pointer saved when the comparison at `0xA7234` selects the player. Game-facing role **UNCONFIRMED**. |
| L34 | dword at `0x96A28` | `0xA65D3/0xA65F6` | `0xAAC06–0xAAC59` | Optional pointer to a row in `[0x22D1C]`, chosen by the command's u16 +6 or cleared by 0xFFFF. Consumer uses row position and its +6 reach byte. |
| L35 | 16 eight-byte rows at `0x969A8` | `0xE8E12`, `0xA20D2` | `0xAAED6`, `0xABF02` | **UNCONFIRMED** gameplay identities. |
| L36 | dynamic effect object pool | `0x9CCA8–0x9CCB0` | `0x10A7ED–0x10A7F4`, `0x10BE79–0x10BE80` | Pool receiving the effect instances. Internal object fields vary by vtable. |
| L37–40 | limit, step, animation byte copy, selected pointer | `0x10A587`, `0x10A94A`, `0x10A953`, `0x10A5AC` | `0x10A832`, `0x10A838`, `0x10A9C8`, `0x10A804` | Effect-8 path. Its step counter is compared to the loaded animation limit and advances with effect +0x56. |
| L41–44 | limit, step, animation byte copy, selected pointer | `0x10BBF8`, `0x10BFF9`, `0x10C028`, `0x10BC1D` | `0x10BEBE`, `0x10BEC4`, `0x10C0A0`, `0x10BE90` | Parallel effect path. The update compares the step to the limit and exits when the step reaches it or the target is absent. |
| L45/L48 | effect admission state | `0x10F068`, `0x10F6A4` | `0x10F661`, `0x10F66E` | Inputs to the effect-2 constructor gate. |
| L46/L47 | link and flag dwords | `0x10C2B7`, `0x10D31C` | `0x10C2AC`, `0x10D301` | Subsequent effect branches read a link and test a flag for zero. The full lifecycle is **UNCONFIRMED**. |
| L49 | dword | `0x1060A8/0x106308` | `0xA8FC0`, `0x106300` | Count incremented and decremented by an effect family. |
| L50/L51 | three dwords and enable flag | `0x1071A4–0x1071C1` | `0x106684`, `0x106743–0x10679E` | Saved position inputs. The first two dwords enter distance and direction calculations and the third sets a height difference. |
| L52–55 | counter, phase, repeats, target coordinates | `0x107F3F`, `0x107F62`, `0x107F19`, `0x107F87–0x107F9C` | `0x107F00–0x107F4E`, `0x1080C8–0x1080E4` | Effect-18 update advances a counter, wraps the phase and decrements repeats at the threshold. Coordinates copy from target +0x36. |
| L56 | dword at `0xEB64` | `0xFA165` | `0xFA5C4` | **UNCONFIRMED** gameplay role. |
| L57/L58 | effect counters | `0x102176/0x102295`, `0x100889/0x100947` | `0x10216A`, `0x100747` | Separate counters. The latter participates in a comparison with 10. The complete event conditions are **UNCONFIRMED**. |
| L59 | dword at `0xEB68` | `0xF84BE/0xF8696` | `0x971B8–0x971C9` | Nonzero admits a lookup in the effect pool. Full lifecycle **UNCONFIRMED**. |
| L60 | audio object slice starting at +0x18 | `0xE90BC` | `0xE75FC → 0xE376C` | Contains the sound system's voice state. The post-restore pass re-reads the voice table at object +0x2B38. Other subfields **UNCONFIRMED**. |
| L65 | 0x140 bytes and pointer at +0x18 | `0xE90DB` | `0xA051B`, `0xEA119` | Frame-side context with a pointer rebased on load. Remaining fields **UNCONFIRMED**. |
| L66 | 12-byte rows | `0x665BF–0x665D8` | `0x6660C`, `0x66651`, `0x6668A` | Lookups use +8 and +6 as keys. A separate iterator selects nonzero +9, which starts at zero. Game-facing purpose **UNCONFIRMED**. |

The unresolved cells above were traced through the on-disk selectors and
read branches first. To settle the remaining field names, follow the
cited consumer to its vtable or event dispatch, then compare a pair of
original saves around one instance of that effect. For the unused-looking
header tail, trace writes into the 0x25A-byte buffer before `0xE7CF1`
and reads from its match at `0xE687E`.

Run `python3 tools/lol2_save_native.py --check --data /path/to/DAT`
to re-read the original selector, read, write and timer witness instructions.
