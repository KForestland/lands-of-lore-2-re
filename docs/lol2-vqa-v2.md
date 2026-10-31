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
- LoL2 movies are version 2 with 4x4 blocks. Each `VQFR` holds `CPL0` (768-byte 6-bit palette), optionally
  `CBFZ` (full codebook, LCW-compressed), `VPTZ` (LCW-compressed vector pointers) and optionally `CBPZ`
  (one part of the next codebook).
- `VPTZ` decodes to two planes of `blocks` bytes: low bytes, then high bytes. High byte 0xFF means a solid
  4x4 block of colour `low`; otherwise the vector index is `high * 256 + low`.
- Palette expansion is `(v << 2) | (v >> 4)`.
- Some movies are stored rotated (the Godot port rotates them clockwise) with a cyan key colour; the decoder
  writes frames as stored.

### Partial codebooks

When `VQHD` byte 13 is N > 0, the next codebook arrives as N `CBPZ` parts, one per frame. The parts are
concatenated and LCW-decoded after the frame that carries the N-th part, and the new codebook is used from
the following frame on. The original loader counts the parts against VQHD byte 13 before publishing the
buffer (cited in the source at LOLG.DAT 0x171168). Movies without partial parts are classified as "not
partial" and left to another decoder.

## The FFmpeg problem this explains

Some LoL2 movies also carry top-level `VQFL` chunks. These are seek snapshots: a full `CBFZ` plus the
`CBPZ` parts of the group in progress, used to jump to loop or segment starts. The original loader only
reads them when load flag 0x20 is set (cited at LOLG 0x16E2B9), so normal linear playback skips them.

FFmpeg (checked against n6.1.1) instead appends each `VQFL` payload to the next `VQFR` packet, and its
decoder keeps only the last `CBPZ` per packet. The snapshot's last part then replaces that frame's own part,
and the next codebook group is assembled from the wrong data. The result is block corruption in the frames
after each snapshot.

Evidence from the Godot rebuild (2026-10, local media, not redistributed): removing only the `VQFL` chunks
from an affected movie and decoding it with stock FFmpeg gave frames identical to this decoder on the
untouched file (2,021 of 2,021 frames). Decoding from every `VQFL` snapshot reproduced the linear state at
58 seek points in 12 clips. A model of FFmpeg's behaviour reproduced FFmpeg's damaged frames apart from 11
pixels in two frames. This decoder is a reimplementation, not an execution of the original player.

## Difference from `tools/lol2_vqa_decode.py`

`lol2_vqa_decode.py` is a chunk inspector: it lists `VQHD` fields and the chunk types (codebook, pointer,
palette and audio chunks) of every VQA entry in a MIX, and does not produce pixels. `lol2_vqa_v2_decode.py`
decodes pixels, but only for version 2, 4x4, partial-codebook movies, and is strict: malformed data or
untested variants (`CBF0`, `CBP0`, `VPT0`, `CPLZ`, `VPTR`, `VPRZ`, other versions or block sizes) raise
`VQAError`. It does not decode audio: top-level chunks other than `VQHD`/`VQFR` are skipped, and any
sub-chunk inside a frame other than `CPL0`/`CBFZ`/`CBPZ`/`VPTZ` raises `VQAError`.

## Checked

Run on retail files (2026-10-31): the listing mode found 126 partial-codebook movies in `L4_HJI.MIX`, 11 in
`L3_DHI.MIX` and none in `MAGIC.MIX` or `VILLAGE.MIX` (the `CHUT.MIX` movies checked were not partial). One
65-frame movie from `L3_DHI.MIX` decoded to frames that look correct on inspection. The FFmpeg comparison
above was not re-run for this note.
