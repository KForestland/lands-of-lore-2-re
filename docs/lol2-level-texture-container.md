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
word's high two bits occur across the banks. UNCONFIRMED: the meaning
of those bits, the treatment of uncovered pixels and the native reader
address. The counted spans establish byte framing.

### Vector-coded rows (flag `0x1246`)

**CONFIRMED.** The native selector at `0x125FC4` reads the resource
word and gives priority to bit `0x1000`. Its object-2 pointer `0xCD058`
(LE fixup at `LOLG.DAT+0x6A1C0`) resolves to `0x12607C`.
That reader returns one pixel row. For nonnegative row number `y`,
use the following inputs.

| Mip record input | Native use |
|---|---|
| +0x16 and +0x17, u8 each | First and last active four-pixel band, inclusive, compared with `y/4` at `0x12608F–0x1260BB`. |
| +0x18, table of u16 | A band offset indexed by `y/4 - first`. Nonzero offsets are relative to +0x18. Zero gives an empty row (`0x1260D2–0x1260FD`). |
| u16 +2 | Width in pixels. The decoder starts with `width/4` blocks (`0x12610A–0x126120`). |
| u32 +8 | Companion key. The class-3 material arm adds it to `[0x22D98]` and loads the resource into `[0x22514]` (`0x132808–0x132843`). |

A run starts with a marker and a block count (one byte each).
A zero marker writes `count` zero dwords, and a zero run that reaches
the row end returns without writing (`0x12617B–0x126193`). At the
beginning of the band, the
first zero run instead sets the horizontal offset to four times its
count (`0x126122–0x126144`).
A nonzero marker is followed by that many u16 codebook indices.
The native read is the four consecutive bytes at
`[0x22514] + 16*index + 4*(y&3)`, written into the row buffer
(`0x126148–0x126195`). A 16-byte codebook entry thus supplies a
4×4 block of source bytes.

**CONFIRMED from the file join.** The decoded bank's section 9
contains 12-byte companion rows. At index record +8, the row
gives a u32 bank source offset in section 8, u32 capacity and
a stored length (the generic loader reads it as a u16 at +0xC). The contents read as the original mode-byte
LZ77 format, consistent with the generic resource loader
`0x67022–0x67052`. The corpus check walks 27,889 mip-0
records, 1,135,521 band slots (1,762 empty) and 21,231,709
codebook references into 400 companions. All references fit
the declared capacity. Of these books, 253 finish below capacity,
and six stop at capacity with more than one input byte left.

Example. `L10_DC.MIX` descriptor 699 is at decoded bank
`+0x1149B2E`, 320×200 with a 1,202-byte mip. Bytes +0x16/+0x17
are 3 and 47. The row-3 offset is `0x005A`, with commands
starting at bank `+0x1149BA0`. The first run skips 33 blocks.
The next run references three entries `0x027F`, `0x072D`,
`0x0727`. A final zero run covers 44 blocks. Companion 0 has
its table row at `+0x25E5BB` and compressed bytes at `+0x2009BB`
(stored length 19,474 and capacity 32,000).

**CONFIRMED (count; `--check` asserts the total).** 190 references in
180 row slots of 30 `L20_BB.MIX` descriptors, all in book 3, exceed the
bytes emitted by companion 3. **UNCONFIRMED:** what the native read
returns for them.
Every one stays within its 32,000-byte allocation. For example,
descriptor 4473 at decoded bank `+0x1A7897C` uses index 1972,
but the stream named by section-9 row `+0x52F611` ends after
1,954 entries. Follow the original buffer at `0x67052` and
the first affected lookup at `0x12616C` to verify what bytes it reads.
Every vector mip also leaves `2*(height/4)-2` bytes beyond the
last row-run extent. The row reader stops before those bytes.
The separate purpose or origin of the tail remains open.

### Run-length columns and raw fallback mips

**CONFIRMED.** At `0x13F1F4–0x13F21F` the scaler tests flag
bit `0x04` before calling `0x12621C`. That reader indexes
u16 offsets at mip +8 using the selected column, then adds
a nonzero offset to +8. A zero offset yields an empty column.
For each run, read its u8 length. If the next byte is 0, 1 or 2,
it supplies the repeated value. Otherwise that byte is the beginning
of the literal run itself, and the reader copies `length` bytes.
The output count is the mip height (`0x12622D–0x12625E`,
`0x1262FE–0x126330`).

The exact walk covers 4,366 compressed mips of flags
`0x008F`, `0x00C7`, `0x20C7`, `0x808F` and `0x80C7`,
ending at each record boundary. Another 1,185 mips on these
descriptors clear bit `0x04` in the **mip header** and hold
raw bytes. For example, `L10_DC.MIX` descriptor 85 has its
`0x008F` first mip at `+0x37246F`. The first column at
`+0x3725F7` starts a 128-byte literal run. The same descriptor's
104-byte 12×8 last mip (8-byte header and 96 pixel bytes) has flag `0x008B` at `+0x378FD7`.

**CONFIRMED.** `0x126000` is the separate row-span helper
for the four span flags above. It advances by four plus the
count, returns the two high flag bits and low 14-bit position
separately, and returns the payload pointer at row +4
(`0x126018–0x126076`). The four `0x02AC` mips also frame as
rows. **UNCONFIRMED.** Their live path and the rendering
effect of the two high span bits. The generic selector tests
the record's `0x20` bit first for `0x02AC`, selecting the
contiguous-row helper `0x1261E8`. A caller trace would establish
which record and helper reach the sampler for those four mips.

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
CHECK textures: 15 levels, 38361 descriptors; raw 8-bit 2039; movie-name records 881 (0 bare names are DAT keys); payload-length header 7537 (1 header-height mismatch); flag 0x1246 records 27889; 30593 row spans and 4 ambiguous spans, 4366 compressed columns, 1185 raw fallback mips; 400 vector books, 1135521 row slots, 190 indexes beyond decoded book data; empty 15; rectangular raw samples store columns; bad=none
```

## Open

- Which image edge is up.
- Meaning of descriptor `+0x08`, `+0x0C`, bits `0x8000` and `0x2000` of the flag, and the high byte of `+0x0A`.
- The high span bits, the live `0x02AC` branch and the vector tail and underfilled-book contents.
- How a movie-name record is resolved to a file.
- How the renderer picks a shade row per surface.
- Sections other than 2, 3 and 4.
