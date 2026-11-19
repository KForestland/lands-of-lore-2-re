# LoL2 VQA v2 movies with partial codebooks

Date: 2026-10-31

Tool: [`tools/lol2_vqa_v2_decode.py`](../tools/lol2_vqa_v2_decode.py). Python 3.10+ and **NumPy** are
required; Pillow is needed only to write PNG frames. It reads the user's own MIX archives or `.VQA` files.

```bash
python3 tools/lol2_vqa_v2_decode.py ./lol2_game/DAT/L3_DHI.MIX                    # list movies
python3 tools/lol2_vqa_v2_decode.py ./lol2_game/DAT/L3_DHI.MIX --entry 0 --out frames/
```

## Format notes

- A movie is an IFF `FORM` of type `WVQA` (big-endian chunk sizes, even padding). Top-level chunks seen:
  `VQHD`, `FINF`, `CLIP`, `PINF`, one `VQFR` per frame, and sometimes `VQFL`.
- `VQHD` is 42 bytes: version (u16 +0), frame count (u16 +4), width (+6), height (+8), block width and
  height (bytes +10, +11), frame rate (+12), and the number of partial-codebook parts (byte +13).
- LoL2 movies are version 2. The block size is 4×4 or 4×2. A vector is `block width × block height` bytes.
  The colour count (`VQHD` offset 14) is 256 in every movie under `DAT/`.
- Each `VQFR` holds `CPL0` (768-byte 6-bit palette) and one pointer chunk. The codebook chunks are `CBFZ`
  or `CBF0` (a full book, LCW or raw) and `CBPZ` or `CBP0` (one part of the next book). The pointer table
  is `VPTZ` (LCW) or `VPT0` (raw). `VPRZ` and `VPTR` are a different stream; see below.
- A pointer table is two planes of `blocks` bytes: low, then high. High byte 0xFF is a solid block of
  colour `low` for both block sizes. Any other index is `high × 256 + low`.
- Palette expansion is `(v << 2) | (v >> 4)`.
- Some movies are stored rotated (they display correctly when turned clockwise) with a cyan key colour; the
  decoder writes frames as stored.

### Partial codebooks

When `VQHD` byte 13 is N > 0, the next codebook arrives as N parts, one per frame (`CBPZ` compressed, or
`CBP0` raw, as in `POOL.MIX` entry 4). The parts are joined after the frame that carries the N-th part.
Joined `CBPZ` bytes are one LCW stream; joined `CBP0` bytes are the raw book. The new book is used from
the following frame on. The original loader counts the parts against VQHD byte 13 before publishing the
buffer (cited in the source at LOLG.DAT 0x171168).

When byte 13 is 0, the same join is scheduled by the top-level `CINF` chunk. Its nested `CIND` is a list
of 6-byte entries: a little-endian frame number, then a little-endian size. A non-zero size on frame F is
the length of the `CBPZ` bytes staged by earlier frames. Those bytes are one LCW stream and replace the
codebook before frame F is drawn. The size on frame 0 is the compressed length of that frame's `CBFZ`.
`L20_BBI.MIX` entry 403 and the intro (`MOVIES.MIX` entry 2) are the worked cases on the
[format page](formats/vqa.md).

### Pointer streams

**CONFIRMED.** `VPRZ` and `VPTR` select node +0x14 bit 5 at
`0x16E5F6–0x16E661` and `0x16E4A8–0x16E50C`. `VPRZ` also sets
bit 4 for the mode-byte LCW decoder (`0x172808–0x172845`). The
frame builder tests bit 5 at `0x1728E4` and calls context +0x772
at `0x17291C`. Indexed 4×4 callbacks include `0x17D3D4`
(assignment `0x172068`, after applying the object-2 relocation).
Its input is a stream of little-endian u16 commands, in row order.

| Command | Indexed 4×4 effect | VA |
|---|---|---|
| `0000–7FFF` | One opaque codebook vector. The full word indexes 16-byte vectors. | `0x17D412–0x17D438`, `0x17D7F4–0x17D810` |
| `Axxx` | Repeat the following u16 block selector `xxx` times, with `xxx` the low 12 bits of the command. A selector below `0x8000` is a full vector index. A selector in `0x8000–0xBFFF` fills with its low byte, and `0xC000–0xFFFF` indexes a transparent vector by its low 12 bits. | `0x17D5D3–0x17D627`, `0x17D690–0x17D72A` |
| `Bxcc` | Fill `x` blocks with colour `cc`, leaving them unchanged when `cc = 0`. | `0x17D56D–0x17D5CE` |
| `Cxxx` | Emit `xxx` solid colours from the following bytes in u16 pairs, with the high byte of each pair emitted first. Colour zero leaves the block unchanged. | `0x17D4C8–0x17D568` |
| `Exxx` | One vector selected by low 12 bits. Zero-valued pixels leave the destination unchanged. | `0x17D47B–0x17D4C6`, `0x17D7A4–0x17D7C4` |
| `F0cc` | One solid block of colour `cc`. Colour zero leaves the block unchanged. The arm selects `Fxxx` by its high nibble. | `0x17D43D–0x17D476`, `0x17D7CA–0x17D7D6` |

The renderer advances to the next block row at the column boundary
and stops at width-in-blocks times height-in-blocks (`0x17D825–0x17D847`).
The original `CAN.MIX` entry 22 first frame has 340 blocks in 20 columns.
Its 492-byte stream begins `00 B6 00 E0 01 E0 02 E0`. The first word
`0xB600` advances six blocks without writing pixels, and the next
three words select transparent vectors 0, 1 and 2.

**CONFIRMED.** The command census consumed 52,187 pointer-stream
frames across the 837 movies. All use 4×4 blocks. All commands
completed within their row and consumed the exact stream length.
The tool's `--check --full` walks the commands and checks vector
indices against the selected codebook. **UNCONFIRMED.** The
starting destination pixels of transparent draws on each seek and
the equivalent behavior under other callback selections. Stream
frames remain outside the tool's RGB export.

The two exceptional `VPTZ` frames use the ordinary pointer-table
path. The absolute mode of `0x158D58` still permits short relative
copies. The [native copy and buffer analysis](formats/vqa.md#native-short-copy-runtime-control)
locates the prior destination data those commands use.

## The FFmpeg problem this explains

Some LoL2 movies also carry top-level `VQFL` chunks. These are seek snapshots: a full `CBFZ` plus the
`CBPZ` parts of the group in progress, used to jump to loop or segment starts. The original loader only
reads them when load flag 0x20 is set (cited at LOLG 0x16E2B9), so normal linear playback skips them.

FFmpeg (checked against n6.1.1) instead appends each `VQFL` payload to the next `VQFR` packet, and its
decoder keeps only the last `CBPZ` per packet. The snapshot's last part then replaces that frame's own part,
and the next codebook group is assembled from the wrong data. The result is block corruption in the frames
after each snapshot.

Evidence (2026-10, local media, not redistributed): removing only the `VQFL` chunks
from an affected movie and decoding it with stock FFmpeg gave frames identical to this decoder on the
untouched file (2,021 of 2,021 frames). Decoding from every `VQFL` snapshot reproduced the linear state at
58 seek points in 12 clips. A model of FFmpeg's behaviour reproduced FFmpeg's damaged frames apart from 11
pixels in two frames. This decoder is a reimplementation, not an execution of the original player.

## Difference from `tools/lol2_vqa_decode.py`

`lol2_vqa_decode.py` is a chunk inspector: it lists `VQHD` fields and the chunk types (codebook, pointer,
palette and audio chunks) of every VQA entry in a MIX, and does not produce pixels. `lol2_vqa_v2_decode.py`
decodes pixels for version 2 pointer-table movies (4×4 and 4×2, partial or scheduled codebooks, and the
raw `CBF0`/`CBP0`/`VPT0` forms). Malformed data raises `VQAError`. A `VPRZ`/`VPTR` movie is checked through the codebook and pointer
commands. Frame export is available for pointer tables. The tool does not decode audio: top-level chunks other
than `VQHD`, `VQFR` and `CINF` are skipped. An unknown sub-chunk inside a frame raises `VQAError`.

## Checked

Run on retail files (2026-10-31): the listing mode found 126 partial-codebook movies in `L4_HJI.MIX`, 11 in
`L3_DHI.MIX` and none in `MAGIC.MIX` or `VILLAGE.MIX` (the `CHUT.MIX` movies checked were not partial). One
65-frame movie from `L3_DHI.MIX` decoded to frames that look correct on inspection. The FFmpeg comparison
above was not re-run for this note.

Re-run on 2026-11-18 over every `WVQA` in `DAT/`. `--check` is the chunk census and one sample of each
layout. `--full` walks every frame: 1,109 pointer-table movies pass, including the 4×2 movies and the
byte-13 value 0 movies, and 837 pointer-stream movies have framed pointer commands. Two pointer-table frames require buffer history for their
relative LCW copies; the count is 1,109 + 837 + 2 = 1,948. Of the 130 movies with byte 13 equal to 0,
10 stage `CBPZ` parts and 120 have a single `CBFZ`. `L4_HJI.MIX` entry 67 still expands to 9 of 9 frames.
