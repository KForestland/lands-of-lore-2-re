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

837 movies use `VPRZ` (LCW) or `VPTR` (raw) instead of a pointer table. They still have a 256-colour
palette and a codebook of 8-bit vectors, so they are not 15-bit frames. `CAN.MIX` entry 22 shows the
mismatch: 340 blocks would need a 680-byte table, and the `VPRZ` decompresses to 492 bytes. The tool
checks the codebook and that the `VPRZ` is LCW. It does not expand the stream. Two further `VPTZ` frames
do not finish as absolute LCW; they are named in the check line.

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
raw `CBF0`/`CBP0`/`VPT0` forms). Malformed data raises `VQAError`. A `VPRZ`/`VPTR` movie is checked as far
as the codebook and is not written out as frames. The tool does not decode audio: top-level chunks other
than `VQHD`, `VQFR` and `CINF` are skipped. An unknown sub-chunk inside a frame raises `VQAError`.

## Checked

Run on retail files (2026-10-31): the listing mode found 126 partial-codebook movies in `L4_HJI.MIX`, 11 in
`L3_DHI.MIX` and none in `MAGIC.MIX` or `VILLAGE.MIX` (the `CHUT.MIX` movies checked were not partial). One
65-frame movie from `L3_DHI.MIX` decoded to frames that look correct on inspection. The FFmpeg comparison
above was not re-run for this note.

Re-run on 2026-11-18 over every `WVQA` in `DAT/`: 1,109 pointer-table movies pass the index check, including
the 4×2 movies and the byte-13 value 0 movies, and 837 pointer-stream movies pass the codebook check. The
check line names the two `VPTZ` frames that do not finish. `L4_HJI.MIX` entry 67 still expands to 9 of 9 frames.
