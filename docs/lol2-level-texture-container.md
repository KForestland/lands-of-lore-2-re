# LoL2 Level Texture Container (.TE_)

Date: 2026-10-31. Flag census re-measured 2026-11-18 on all 15 level containers
(38,361 descriptors).

## Scope

This note describes the texture container stored in each level MIX
(`DAT/L1_DC.MIX`, `DAT/L20_BB.MIX`, ...) and which descriptor flags share a
decoded layout. It is a file-format note. It does not claim which image edge
is up, or how a surface picks a material.

Tool: `tools/lol2_texture_container.py` (standard library + system `liblzo2`).

## Entry name and key (PROVEN)

Each level MIX holds one texture entry named
`SPHERE<n>\<LEVEL>\<LEVEL>.TE_`. Its MIX key is the TD/RA Westwood filename
hash of that name (`ww_hash_v1` in `tools/lol2_westwood_hash.py`). Checked by
running the tool on a GOG install:

| MIX | Entry name | Key | Descriptors |
|-----|------------|-----|-------------|
| `L1_DC.MIX` | `SPHERE1\L1_DC\L1_DC.TE_` | `2972657927` | 1962 |
| `L3_DH.MIX` | `SPHERE1\L3_DH\L3_DH.TE_` | `3107535131` | 1660 |
| `L4_HJ.MIX` | `SPHERE1\L4_HJ\L4_HJ.TE_` | `3711781155` | 3649 |
| `L5_HC.MIX` | `SPHERE1\L5_HC\L5_HC.TE_` | `3777974535` | 1834 |
| `L9_DR.MIX` | `SPHERE2\L9_DR\L9_DR.TE_` | `3512559939` | 4360 |
| `L20_BB.MIX` | `SPHERE3\L20_BB\L20_BB.TE_` | `3263632273` | 4654 |

## LZO1X block layout (PROVEN)

```
u32 total_decoded_size
repeat until total reached:
    u32 compressed_size
    LZO1X block (decodes to 1 MiB, the last block to the remainder)
u32 0                      (trailer)
```

Decoding uses `lzo1x_decompress_safe` from the system `liblzo2` through
ctypes, so no `python-lzo` package is needed. The reader refuses
out-of-bounds sizes, short blocks and a non-zero trailer.

A run can store that decode in `CDCACHE.MIX`. Which levels are present, and
at which file offset, depends on the run ([MIX](formats/mix.md)). The L20
decode is 28,451,111 bytes. The L1 decode is 13,040,404 bytes.

## Blob header and sections

| Offset | Type | Meaning | Status |
|--------|------|---------|--------|
| `+0` | u32 | Section count (18 in L1_DC and L20_BB) | PROVEN |
| `+4` | u32 | Palette offset (`0x6A2`, 768-byte 6-bit DAC palette) | PROVEN for L20_BB; LIKELY elsewhere |
| `+8` | u32 x count | Section offsets (0 = absent) | PROVEN |

Sections used here:

| Section | Content | Status |
|---------|---------|--------|
| 2 | Material descriptors, 56 bytes each; count = (sec3 - sec2) / 56 | PROVEN |
| 3 | Material payload records, addressed by descriptor offsets | PROVEN |
| 4 | Shade rows, 256 bytes each, up to section 5 (66 rows in L1_DC and L20_BB) | PROVEN |

Other sections are not interpreted in this note.

## Material descriptor (`'<6H11I'`, 56 bytes)

| Offset | Field | Meaning | Status |
|--------|-------|---------|--------|
| `+0x00` | u16 | Numeric identifier | PROVEN (read) |
| `+0x02` | u16 | Width | PROVEN |
| `+0x04` | u16 | Height | PROVEN |
| `+0x06` | u16 | Encoding flags | PROVEN (selects format) |
| `+0x08` | u16 | `1` on nine flags (see below); `255` on movie-name records; many other values elsewhere | OPEN as a meaning |
| `+0x0A` | u16 | Low byte = number of present mips on every raw-layout descriptor. High byte is 3, or 4 on movie-name records | low byte PROVEN on the raw flags; not traced in the program |
| `+0x0C` | u32 | Name/hash candidate | OPEN |
| `+0x10` | 5 x u32 | Mip record offsets, relative to section 3 | PROVEN |
| `+0x24` | 5 x u32 | Mip record lengths | PROVEN |

The mip chain has five levels, each half the previous size. Some materials
use fewer levels; unused slots are zero.

## Raw 8-bit pixels (PROVEN)

Ten flag values use one record layout. `0xA9` is the one the notes below
were first written for. `0x80A9` is the same layout with bit `0x8000` set.
The same is true of `0x008B`, `0x00C3`, `0x00E1`, and of those low bytes
with bit `0x2000` (`0x20C3`, `0x20E1`) or bit `0x8000` (`0x808B`, `0x80C3`,
`0x80E1`). Those two bits do not change the record size. What they change
in the renderer was not found: the executable has no 16-bit or 32-bit
compare of the immediate values `0x00A9` or `0x80A9`.

| Flag | Descriptors |
|------|-------------|
| `0x008B` | 74 |
| `0x00A9` | 863 |
| `0x00C3` | 359 |
| `0x00E1` | 570 |
| `0x20C3` | 36 |
| `0x20E1` | 19 |
| `0x808B` | 14 |
| `0x80A9` | 47 |
| `0x80C3` | 19 |
| `0x80E1` | 38 |

2,039 descriptors. Every present mip matches the rules in the next section.
`tools/lol2_texture_container.py --check` re-checks the counts and the bytes.

### Flag `0xA9`, and the nine flags that share it

Each mip record is an 8-byte header and then `width * height` index bytes:

```
u16 flags (= descriptor flags)
u16 width
u16 height
u16 (width * height) & 0xFFFF   (0 for 256x256; not "empty")
u8  pixels[width * height]
```

Record length is always `8 + width * height`. Example, L20_BB descriptor
556 (id `2682`, 256 x 256): mip records at blob `0x113E883`, `0x114E88B`,
`0x1152893`, `0x115389B`, `0x1153CA3`, lengths `0x10008` to `0x108`.

Pixel order: the bytes are stored by column, `index = x * height + y`.
On rectangular images the mean absolute difference between consecutive bytes
matches the difference at stride `height` (a horizontal neighbour) and is
clearly smaller than the difference at stride `width` (not a neighbour).
That is what column storage predicts. The check requires it of the per-flag
average over all rectangular images whose sides are at least 8 (individual
images do not all show it), for `0x008B`, `0x00A9`,
`0x00C3`, `0x00E1`, `0x20C3`, `0x808B`, `0x80A9` and `0x80C3`. The table is a
sample of at most 40 images per flag, stepping so each image contributes about 2,500
pairs, measured:

| Flag | Images | Consecutive | Stride = width | Stride = height |
|------|--------|-------------|----------------|-----------------|
| `0x008B` | 13 | 19.99 | 35.98 | 16.95 |
| `0x00A9` | 40 | 27.38 | 42.84 | 28.63 |
| `0x00C3` | 40 | 13.49 | 21.12 | 13.94 |
| `0x00E1` | 40 | 14.03 | 44.78 | 15.88 |
| `0x20C3` | 13 | 10.95 | 20.58 | 10.65 |
| `0x808B` | 2 | 10.82 | 30.77 | 11.83 |
| `0x80A9` | 31 | 26.87 | 41.55 | 27.34 |
| `0x80C3` | 19 | 25.86 | 56.10 | 23.86 |

`0x20E1` is 19 images, all 256×256, so the two strides are the same test and
do not separate the orders. `0x80E1` has four rectangular images and they do
not separate either (consecutive 41.23, stride-width 41.23, stride-height
30.54); their record size is still the raw one. Which image edge is up is
still open.

Colour: index -> shade row byte -> palette. The runtime witness for
descriptor 556 used shade row `0x2D`; see
[lol2-wall-material-provenance.md](lol2-wall-material-provenance.md).
Row 64 (`section 4 + 64 * 256`) gives plausible colours as a remap row; the
row the game selects at run time is not traced.

Worked example, `L10_DC.MIX` descriptor 317 (id 1519, flag `0x80A9`, 64×64).
The mip-0 header is `a9 80 40 00 40 00 00 10`: flags `0x80A9`, width 64,
height 64, pixel count `0x1000` = 4,096. The five record lengths are 4,104,
1,032, 264, 72 and 24, which are `8 + side²` for sides 64, 32, 16, 8 and 4.
Descriptor `+0x08` is 1 and `+0x0A` is `0x0305` (high byte 3, low byte 5, the
mip count). Mip-0 pixel SHA-256 is
`466f6fcfa90516c3f67e3b94e4f879db4a4e8380fcba99a28decba313c014cdf`.

## Movie-name records (PROVEN)

Flags `0x0143` (23), `0x0161` (1) and `0x0342` (857) are not pixels. All 881
records are 22 bytes. The 8-byte header repeats the descriptor flag, width
and height, and its fourth word is 22, the whole record length. The other
14 bytes are a NUL-padded ASCII name ending in `.vqa`. Descriptor `+0x08` is
255 and the high byte of `+0x0A` is 4.

`L10_DC.MIX` descriptor 71 (flag `0x0143`, 320×200) is
`43 01 40 01 c8 00 16 00` followed by `ud05.vqa` and six NUL bytes.
`L12_CM.MIX` descriptor 93 (flag `0x0161`) names `melt.vqa`. The Westwood
filename hash of the bare name is not a key in any `DAT/` archive, and the
game folder has no loose file of that name. How the name is resolved is open.

## Other flags: header only

Every remaining descriptor has the same first six header bytes (flag, width,
height) equal to the descriptor, except one record noted below. The fourth
header word is not a pixel count.

| Flag | Count | Fourth word |
|------|-------|-------------|
| `0x008F` | 225 | payload length, so the record is 8 + that word |
| `0x00C7` | 790 | payload length |
| `0x028E` | 794 | payload length |
| `0x02AC` | 2 | payload length |
| `0x02C6` | 4,785 | payload length |
| `0x20C7` | 25 | payload length |
| `0x808F` | 23 | payload length |
| `0x80C7` | 74 | payload length |
| `0x828E` | 70 | payload length |
| `0x82C6` | 749 | payload length |
| `0x1246` | 27,889 | record length minus 22 |

CONFIRMED. 7,537 mip-0 records use the payload-length word (the ten flags
above `0x1246`). Their payloads are shorter than `width * height`.
The one mip-0 height mismatch is `L9_DR.MIX` descriptor 1321, flag
`0x02C6`. The descriptor says 640×434. The mip header says 640×192,
and the fourth word is 65,369 (record length 65,377 minus 8).

### Four row-framed flags

CONFIRMED from the decoded `.TE_` banks. For flags `0x028E`, `0x02C6`,
`0x828E` and `0x82C6`, start at mip record `+8`. Read two little-endian
u16 words, then advance by the second word in bytes. Do this once per
row of the **mip header** height. The sum of the first word masked by
`0x3FFF` and the second word is at most the mip header width. This walk
ends at the exact declared record boundary for all 30,593 present mips
(3,691, 22,997, 321 and 3,584 respectively), including the 192-row sample.

In `L10_DC.MIX`, descriptor 1 mip 0 (`0x028E`, 320×200) starts at decoded
bank `+0x2762E7` and is 7,659 bytes. The 37 pairs from payload
`+0x2762EF` are `(0x0140, 0)`. The next pair at bank `+0x276383` is
`(0x40A9, 6)` and is followed by six bytes. All four values of the first
word's high two bits occur across the banks. UNCONFIRMED. The significance
of those bits, the treatment of uncovered pixels and the native reader
address. The counted spans establish byte framing.

### Other compressed records

CONFIRMED. Each of the 27,889 `0x1246` records is 22 bytes plus the fourth
word. In `L10_DC.MIX`, descriptor 699 mip 0 at decoded bank
`+0x1149B2E` is 320×200, 1,202 bytes, with fourth word 1,180. It has 13
zero bytes and one `03` between the header and the payload. The payload
at record `+0x16` begins `2F 5A 00 66 00 76 00`. Only mip 0 is populated.

UNCONFIRMED. The `0x1246` payload and the other six payload-length flags
have no verified row decoder. Feeding one sample of each to the movie
LCW and mode-byte LZ77 decoders produced no exact pixel count. A direct
comparison with `0x1246` was absent in the code scan. To settle it, trace
the masked bank flag read into the copy loop for the descriptor 699
payload at record `+0x16`, then compare the same reader with descriptor
1 at record `+8` to locate the high-bit branches.

Fifteen further descriptors have flag 0, size 0×0, and no mip records.
The 15 levels together hold 38,361 descriptors and no other flag value.

On the raw flags `0x008B`, `0x00A9`, `0x808B` and `0x80A9`, and on
`0x008F`, `0x028E`, `0x02AC`, `0x808F` and `0x828E`, descriptor `+0x08` is
always 1. On the other flags it takes many values. The high byte of
`+0x0A` is 3 on every flag except the movie-name flags, where it is 4.

## Usage

```bash
python3 tools/lol2_texture_container.py info     --mix ./lol2_game/DAT/L1_DC.MIX
python3 tools/lol2_texture_container.py material --mix ./lol2_game/DAT/L10_DC.MIX --index 317 --partial-mips
python3 tools/lol2_texture_container.py export   --mix ./lol2_game/DAT/L20_BB.MIX --index 556 --shade-row 45 --out OUT
python3 tools/lol2_texture_container.py blob     --mix ./lol2_game/DAT/L20_BB.MIX --out l20_bb.bin
python3 tools/lol2_texture_container.py --check --data ./lol2_game/DAT
```

`export` writes one RGB PNG per mip from your own files (palette at header
`+4`, optional shade row) for any of the ten raw flags. Outputs are for
local use; do not commit them. `--check` prints one line and writes nothing.
It is not one of the checks in `check_all.py`.

The line from the 2026-11-19 run:

```
CHECK textures: 15 levels, 38361 descriptors; raw 8-bit 2039; movie-name records 881 (0 bare names are DAT keys); payload-length header 7537 (1 header-height mismatch); flag 0x1246 records 27889; 30593 framed row payloads; empty 15; rectangular raw samples store columns; bad=none
```

## Open

- Which image edge is up.
- Meaning of descriptor `+0x08`, `+0x0C`, bits `0x8000` and `0x2000` of the flag, and the high byte of `+0x0A`.
- The native interpretation of the four row-framed flags and the payload layout of the remaining seven compressed flags.
- How a movie-name record is resolved to a file.
- How the renderer picks a shade row per surface.
- Sections other than 2, 3 and 4.
