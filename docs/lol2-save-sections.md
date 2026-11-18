# LoL2 native save section descriptors

The tables below use the 1.30 DOS [address convention](lol2-executable-tables.md).
See [native save slots](lol2-save-format.md) for the enclosing directories.

## Reading the descriptors

**CONFIRMED.** The global selector `0xE867C` dispatches through
`LOLG.DAT+0x11F64C`. The level selector `0xE8914` dispatches through
`LOLG.DAT+0x11F800`. The bounds checks are `cmp 0xB / ja` at
`0xE868F–0xE8694` (global) and `cmp 0x44 / ja` at `0xE8928–0xE892D` (level), so
the tables hold 12 and 69 entries; the last entry of each points to the return
that writes nothing (`0xE8647` / `0xE8646`). Each row below was read from the corresponding
switch arm after resolving its LE code fixup. A bracketed expression denotes a
runtime dereference. A bare address denotes an object-5 offset. Counts, lengths,
strides and flags are byte-oriented unless stated otherwise.

For a pool cell `P`, let `H = [P]`. `elements(P)` is `[H+0]`, its byte
length is `[H+8] × [H+0xC]`, and its stride is `[H+0xC]`. `bitmap(P)`
is `[H+4]`, its byte length is `[H+8] >> 3`, and its stride is 1.
`0x5F7C8–0x5F814` checks the bitmap and sets bit `i & 7` in byte `i >> 3`
when allocating element `i`.

**CONFIRMED.** Flag `0x2` selects a baseline XOR before saving, followed
by section-specific pointer conversion (`0xE8192–0xE8283`). The level
baseline `.IMG` is the concatenation of these sections in ascending index
order, written without a directory by `0xE5F9A–0xE5FDE`. On the load
path the XOR is reversed at `0xE7512–0xE755E`, and the loader adjusts
pointers at `0xE7598`. Flag `0x4` selects the section compression at
`0xE8293–0xE82AE` or `0xE8300–0xE8316`. When the level writer's
third argument is zero, flag `0x8` selects which sections it writes
(`0xE815D–0xE8176`). Only level sections 0–2 have `0x8` set.
Flag `0x1` admits the section to the reader at `0xE742E–0xE7436`.
See [save field witnesses](lol2-save-field-witnesses.md) for the other
read-path flags and the two saved world-list heads.

## Global sections

**CONFIRMED.** These are the descriptors for sections 0–10. Section 5 returns
address, length and stride zero if `[0x22CE0]` is null (`0xE8743–0xE876E`).

| Section | Buffer | Byte length | Stride | Flags | Arm | Identified role |
|---:|---|---|---|---:|---|---|
| 0 | `0x22574` | 0x22E | 0x22E | 0x7 | `0xE86A3` | Player object |
| 1 | `[0x26E58]` | [0x26E60] | 0x1 | 0x7 | `0xE86BD` | Shared script bytes |
| 2 | `elements(0x96918)` | pool length | pool stride | 0x7 | `0xE86DC` | Player item instances |
| 3 | `bitmap(0x96918)` | pool length | 1 | 0x7 | `0xE8700` | Player item occupancy |
| 4 | `0x23348` | 0x91F | 0x91F | 0x7 | `0xE8723` | — |
| 5 | `[0x22CE0]+0x10` | 0x2D | 0x2D | 0x1 | `0xE873D` | — |
| 6 | `0x22CE4` | 0xC | 0xC | 0x1 | `0xE876F` | — |
| 7 | `0xDB4CC` | 0x34 | 0x4 | 0x1 | `0xE878D` | — |
| 8 | `0x22518` | 0x5B | 0x5B | 0x1 | `0xE87A9` | — |
| 9 | `[0x96908]` | [0x9690C] | 0x1 | 0x1 | `0xE87C3` | — |
| 10 | `0x22C95` | 0x30 | 0x30 | 0x3 | `0xE87E2` | — |

## Level sections

**CONFIRMED.** These are the descriptors for indices 0–67. Code citations for
regions, controls, actors, movables and timers are in [native save slots](lol2-save-format.md#level-blocks).
The item and list-node evidence is below.

| Section | Buffer | Byte length | Stride | Flags | Arm | Identified role |
|---:|---|---|---|---:|---|---|
| 0 | `[0x26BC0]` | 18 × [0x26BC4] | 0 | 0xc | `0xE8940` | — |
| 1 | `[0x26BD0]` | 0x1FA4 | 0 | 0x9 | `0xE896C` | — |
| 2 | `[0x26BD4]` | 6 × [0x26BD8] | 0 | 0xc | `0xE898C` | — |
| 3 | `0x26E6C` | 0x1C | 0x1C | 0x7 | `0xE89B8` | — |
| 4 | `[0x26E6C]` | 8 × [0x26E84] | 8 | 0x7 | `0xE89D3` | — |
| 5 | `0x26E88` | 0x1C | 0x1C | 0x7 | `0xE89F6` | — |
| 6 | `[0x26E88]` | 8 × [0x26EA0] | 8 | 0x7 | `0xE8A11` | — |
| 7 | `[0xB877C]` | [0xB8B80] | 2 | 0x7 | `0xE8A34` | — |
| 8 | `[0x2B51C]` | [0x2B520] | 4 | 0x7 | `0xE8A54` | — |
| 9 | `[0xB7D74]` | [0xB7D78] | 2 | 0x7 | `0xE8A74` | — |
| 10 | `[0x2B514]` | [0x2B518] | 4 | 0x7 | `0xE8A94` | — |
| 11 | `[0x22D04]` | 8 × [0x22D24] | 8 | 0x7 | `0xE8AB4` | — |
| 12 | `[0x22D0C]` | 44 × [0x22D2C] | 44 | 0x7 | `0xE8AD7` | Regions |
| 13 | `[0x22D10]` | 42 × [0x22D30] | 42 | 0x7 | `0xE8B09` | — |
| 14 | `[0x22D08]` | 8 × [0x22D28] | 8 | 0x7 | `0xE8B3A` | — |
| 15 | `[0x22D18]` | 12 × [0x22D40] | 8 | 0x7 | `0xE8B5D` | — |
| 16 | `elements(0xB7E24)` | pool length | pool stride | 0x5 | `0xE8B8A` | List-node elements |
| 17 | `bitmap(0xB7E24)` | pool length | 1 | 0x5 | `0xE8BAF` | List-node occupancy |
| 18 | `elements(0xDB590)` | pool length | pool stride | 0x7 | `0xE8BD3` | — |
| 19 | `elements(0x273E0)` | pool length | pool stride | 0x7 | `0xE8BF8` | Controls |
| 20 | `[0x273E4]` | 4 × [0x273E8] | 4 | 0x7 | `0xE8C1D` | — |
| 21 | `elements(0x9696C)` | pool length | pool stride | 0x7 | `0xE8C40` | Actors |
| 22 | `elements(0x2B500)` | pool length | pool stride | 0x7 | `0xE8C65` | Movables |
| 23 | `[0x2B504]` | 4 × [0x2B508] | 4 | 0x7 | `0xE8C8A` | — |
| 24 | `[0x26E54]` | [0x26E5C] | 1 | 0x7 | `0xE8CAD` | Local script bytes |
| 25 | `elements(0x968F8)` | pool length | pool stride | 0x7 | `0xE8CCD` | Placed item objects |
| 26 | `[0x22D44]` | 24 × [0x22D64] | 24 | 0x7 | `0xE8CF2` | — |
| 27 | `[0x22D54]` | 8 × [0x22D74] | 8 | 0x7 | `0xE8D1F` | — |
| 28 | `0xB7D6C` | 0x4 | 0x4 | 0x1 | `0xE8D42` | First world-list head |
| 29 | `0xB7D70` | 0x4 | 0x4 | 0x1 | `0xE8D5D` | Second world-list head |
| 30 | `0x26B4C` | 0x30 | 0x30 | 0x7 | `0xE8D78` | — |
| 31 | `elements(0x9691C)` | pool length | pool stride | 0x7 | `0xE8D93` | Non-player item instances |
| 32 | `bitmap(0x9691C)` | pool length | 1 | 0x7 | `0xE8DB8` | Non-player item occupancy |
| 33 | `0x969A4` | 0x4 | 0x4 | 0x1 | `0xE8DDC` | — |
| 34 | `0x96A28` | 0x4 | 0x4 | 0x1 | `0xE8DF7` | — |
| 35 | `0x969A8` | 0x80 | 8 | 0x5 | `0xE8E12` | — |
| 36 | `[[0xDF660]]` | [[0xDF660]+4] | 0 | 0x5 | `0xE8E2F` | — |
| 37 | `0xDF69C` | 0x4 | 0x4 | 0x1 | `0xE8E4F` | — |
| 38 | `0xDF694` | 0x4 | 0x4 | 0x1 | `0xE8E6A` | — |
| 39 | `0xDF698` | 0x4 | 0x4 | 0x1 | `0xE8E85` | — |
| 40 | `0xDF6A0` | 0x4 | 0x4 | 0x1 | `0xE8EA0` | — |
| 41 | `0xDF6AC` | 0x4 | 0x4 | 0x1 | `0xE8EBB` | — |
| 42 | `0xDF6A4` | 0x4 | 0x4 | 0x1 | `0xE8ED6` | — |
| 43 | `0xDF6A8` | 0x4 | 0x4 | 0x1 | `0xE8EF1` | — |
| 44 | `0xDF6B0` | 0x4 | 0x4 | 0x1 | `0xE8F0C` | — |
| 45 | `0xEDD4` | 0x4 | 0x4 | 0x1 | `0xE8F27` | — |
| 46 | `0xDF6B8` | 0x4 | 0x4 | 0x1 | `0xE8F42` | — |
| 47 | `0xEDD8` | 0x4 | 0x4 | 0x1 | `0xE8F5D` | — |
| 48 | `0xDF6B4` | 0x4 | 0x4 | 0x1 | `0xE8F78` | — |
| 49 | `0xDF66C` | 0x4 | 0x4 | 0x1 | `0xE8F93` | — |
| 50 | `0xDF670` | 0xC | 0xC | 0x1 | `0xE8FAE` | — |
| 51 | `0xDF67C` | 0x4 | 0x4 | 0x1 | `0xE8FC9` | — |
| 52 | `0xDF680` | 0x4 | 0x4 | 0x1 | `0xE8FE4` | — |
| 53 | `0xEDCC` | 0x4 | 0x4 | 0x1 | `0xE8FFF` | — |
| 54 | `0xDF684` | 0x4 | 0x4 | 0x1 | `0xE901A` | — |
| 55 | `0xDF688` | 0xC | 0xC | 0x1 | `0xE9035` | — |
| 56 | `0xEB64` | 0x4 | 0x4 | 0x1 | `0xE9050` | — |
| 57 | `0xDF668` | 0x4 | 0x4 | 0x1 | `0xE906B` | — |
| 58 | `0xDF664` | 0x4 | 0x4 | 0x1 | `0xE9086` | — |
| 59 | `0xEB68` | 0x4 | 0x4 | 0x1 | `0xE90A1` | — |
| 60 | `0x23C80` | 0x2D48 | 0x2D48 | 0x5 | `0xE90BC` | — |
| 61 | `0xB7DA4` | 0xC | 0xC | 0x3 | `0xE9142` | Timer list header |
| 62 | `[0xB7DA4]` | 4 × [0xB7DA8] | 4 | 0x1 | `0xE915D` | Timer list pointers |
| 63 | `0xB7DB0` | 0xC | 0xC | 0x3 | `0xE9180` | Parallel object list header |
| 64 | `[0xB7DB0]` | 4 × [0xB7DB4] | 4 | 0x1 | `0xE919B` | Parallel object list pointers |
| 65 | `0x26D14` | 0x140 | 0x140 | 0x1 | `0xE90DB` | — |
| 66 | `[0x2B53C]` | 12 × [0x2B538] | 12 | 0x7 | `0xE90F6` | — |
| 67 | `0x22C40` | 0x51 | 0x51 | 0x3 | `0xE9123` | Includes timer elapsed cells |

## Items and occupancy

**CONFIRMED.** The pickup path calls `0x95A64` at `0xD266A`. That helper
allocates a 12-byte instance from `[0x96918]` for the player object
`0x22574` or `[0x9691C]` for another recipient (`0x95A70–0x95A99`).
It copies the instance embedded at world-object +0x2C (`0x95AA0–0x95AA5`,
`0x9B8DF`, `0x95804–0x95822`). The copy includes the definition pointer and
instance bytes +4 and +5. Slot sections 2/3 save the player's elements and
allocation bitmap. Level sections 31/32 save the corresponding non-player
pool. The adjust arms for global section 2 (`0xE940E–0xE9452`) and level
section 31 (`0xE9DA1`, calls at `0xE9DCD` and `0xE9DE1`) touch the pointer
dwords at +0 and +8, leaving +4/+5 in the byte data.

**CONFIRMED.** The placement loader copies 0x25 bytes per input record,
allocates a 0x3C-byte row from `[0x968F8]`, and calls `0x93FBC`
(`0x94090–0x940C4`). That constructor resolves placement +0x20 as an item identity through
`0x9EB5C` and supplies placement +0x24 as the initial instance byte. See
[the 663 placement witnesses](lol2-save-field-witnesses.md#from-placement-row-to-item-definition).
The constructor installs the vtable at object-5 `0x573C`
(`0x93FD4–0x93FFC`). The world-object method invoked by the transfer at
`0x95AB9` is the vtable +0xF0 entry (dword `LOLG.DAT+0x1C6850`, LE fixup
`LOLG.DAT+0x7F548`, target `0x940F8`). With argument 2, the method calls
`0x5CB8C`, sets object +0x16 mask `0x80` at `0x9412C`, and calls
`0xAEB28`. The latter updates the world lists at `0xAEB91–0xAEBDA`.
A reusable row is selected by the same mask at `0x94195–0x9419B`.
The constructor for initially empty rows uses `0x00800000` in the flag
argument (`0x94044–0x94054`). Thus the flag marks an available placed-item
row. A pickup can set it, and existing empty rows can already have it set.

**CONFIRMED.** Level section 25 serializes the whole placed-item row pool
(`0xE8CCD`, creation stride `0x9D30D`), including +0x16. Its pointer
adjustment touches only dwords +0x0C, +0x10 and +0x2C
(`0xE9D15–0xE9D89`), leaving the flag in the XOR byte data. When the
world-list helper calls `0x5F830` from `0xAEBAD`, it releases a list node
from `[0xB7E24]`, whose elements and bitmap are independently saved in
sections 16/17 (`0xE8B8A`, `0xE8BAF`). This gives two places to look when
following one pickup through a save. Level section 25 contains world rows,
and the recipient's separate pool holds the copied item instance.

## Reference measurements

**CONFIRMED.** The 27-slot reference set yields 135 compressed and 162
raw global spans (`slot+0x18E`). All 135 compressed spans decode as LZO1X.
The 149 nonempty blocks yield 3,316 compressed and 3,449 raw nonempty level spans (10,132 spans in all, 3,367 of them empty).
To reproduce, take adjacent offsets from `block+0xD8`, choose raw or
LZO1X from the selector flags above, and compare each output length with
the directory at `block+0x1E8`. Every nonempty span matches. Of the 149
blocks, 49 contain sections 0–2 only, with `block+0xD4 = 0xFF00FFFF`.
The other 100 have `block+0xD4 = 0`. All 27 slots have `slot+0x178 = 0`.
Both adjustment helpers clear their address-map status before processing
(`0xE9207`, `0xE9719`). The short layout skips that processing in the level
writer because none of sections 0–2 has flag `0x2` (`0xE8192`).

**CONFIRMED.** In the native reference save with SHA-256 prefix
`a97f9c4782d4`, the level-1 block starts at slot `0x6EA8`. The lengths
of its flag-`0x2` sections sum to `0x4AFE3`. The measurements below come from
the decoded save deltas alone. A runtime baseline `L1_DC.IMG` written by the game
(not shipped; SHA-256 prefix `1d2165406adc`, same length) is zero at every byte
these rows use, so it is not needed to reproduce them.

| Section | Slot offset and span | `.IMG` offset and raw length | Measured delta |
|---:|---|---|---|
| 24 | `0x19240`, `0x1E` | `0x4664E`, `0x34` | Local script byte indices 43–48 change. |
| 25 | `0x1925E`, `0x200` | `0x46682`, `0x4380` | 378 byte positions differ in the decoded delta, including pointer data. No row changes bit `0x80` at +0x16 in this pair. |
| 31 | `0x19516`, `0x38` | `0x4AC42`, `0x300` | 38 nonzero decoded bytes. Pointer words are processed separately. |
| 32 | `0x1954E`, `0x14` | `0x4AF42`, `8` | One bitmap byte of the delta, `0x3F`: 6 bits set. |

## Open fields

- **UNCONFIRMED.** Blank roles in the selector tables still need gameplay
  identities. The dispatch tables, pointer cells, counts and strides were
  checked first and matched against the native file directory. For semantic
  names, trace the writes to each buffer behind the selector. For the scalar
  run in level sections 37–59, begin with the writes to the object-5 cells
  in the table and connect those writers to an original level event or object
  update. A controlled save pair can then check each proposed meaning.
- **UNCONFIRMED.** The source of the value `0xFF00FFFF` in the short
  blocks remains open. The reference files locate it at `block+0xD4` and
  the short writer path bypasses `0xE96EC`. Trace preparation of the scratch
  header for the zero-third-argument path before the write at `0xE83DF` to
  determine how those four bytes acquire their value.
- **UNCONFIRMED.** An isolated before/after save pair for taking a specific
  placed item is still missing. The original pickup, release and write paths
  identify the row flag and both saved pools, while the reference level-1 block shows no bit transition in section 25. With a same-level pair around
  one pickup, follow that object's section-25 row and +0x16 bit, the global
  section-3 allocation bit, and the corresponding section-2 definition and
  instance bytes. The row may be reused, so compare immediately after pickup.
- **UNCONFIRMED.** The meanings of unlabelled slot-header bytes remain
  open. All 27 headers were checked against the fixed-size write at
  `0xE7CE1–0xE7CFE`. The 20 level stamps end at +0x93. The dword at
  +0x94 is explicitly zeroed at `0xE777D`. To classify the remaining
  bytes after +0x209, trace the writes to that part of the header buffer
  passed to `0x118864` at `0xE7CF1`, then check a pair of saves differing
  in one known setting.
