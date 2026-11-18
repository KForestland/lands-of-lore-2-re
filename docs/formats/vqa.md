# VQA movies

**What:** Westwood VQA version 2 movies, stored as IFF `FORM`/`WVQA` entries in the room and level archives (`<LEVEL>I.MIX`, the room archives, `MOVIES.MIX`, `SETUP.MIX`). Full codec notes: [lol2-vqa-v2.md](../lol2-vqa-v2.md). How scripts pick a movie: opcode 21 in the [opcode reference](../lol2-script-opcodes.md#opcode-table). Tool: `tools/lol2_vqa_v2_decode.py`; it needs NumPy, plus Pillow to write frames.

## Layout

- **Container:** an IFF `FORM` of type `WVQA`, with big-endian chunk sizes padded to even length.
- **Top-level chunks:** `VQHD`, then information chunks (`CLIP` or `CINF`, `PINF`, `FINF`, sound chunks), then one `VQFR` per frame.
- **`VQHD`:** 42 bytes, little-endian.

| `VQHD` offset | Type | Meaning |
|---|---|---|
| 0 | u16 | version (2 in every LoL2 movie) |
| 4 | u16 | frame count (equals the number of `VQFR` chunks) |
| 6 / 8 | u16 | width / height |
| 10 / 11 | u8 | block width / height |
| 12 | u8 | frames per second |
| 13 | u8 | number of parts a partial codebook is split into |

A `VQFR` holds some of:
- `CPL0`: a 768-byte palette;
- `CBFZ` or `CBF0`: a full codebook, LCW-compressed or raw;
- `CBPZ` or `CBP0`: one part of the next codebook, LCW-compressed or raw;
- `VPTZ` or `VPT0`: vector pointers, LCW-compressed or raw;
- `VPRZ` or `VPTR`: a different pointer stream, LCW-compressed or raw.

Details are in [lol2-vqa-v2.md](../lol2-vqa-v2.md#format-notes).

## Confirmed on the data

`lol2_vqa_v2_decode.py --check --data <DAT>` re-ran on 2026-11-18. CONFIRMED:
- **All movies valid:** `DAT/` holds 1,948 `WVQA` movies. Every header is valid, every frame count matches, all are version 2, and the colour count at `VQHD` offset 14 is 256 in every one.
- **Pointer tables:** 1,109 movies. The tool checks every frame: the codebook is a whole number of vectors, and every index that is not a solid block lands inside it.
  - 974 are 4×4 with `VQHD` byte 13 greater than 0. One of them, `POOL.MIX` entry 4, uses the raw chunks `CBF0`, `CBP0` and `VPT0` instead of the LCW forms.
  - 5 are 4×2. A high byte of `0xFF` is still a solid block. `L10_DCI.MIX` entry 40 (129 frames) is checked in full.
  - 130 have byte 13 equal to 0. `CINF`/`CIND` says which frame the staged parts become the codebook.
- **Pointer streams:** 837 movies carry `VPRZ` and/or `VPTR`. The codebook still decompresses to whole vectors, and each `VPRZ` is LCW. The tool does not turn that stream into pixels.
- **Two frames stay open:** `L20_BBI.MIX` entry 25 frame 115, and `SPKSTON2.MIX` entry 4 frame 492. Each `VPTZ` stops inside absolute LCW. Every other pointer table in those two movies finishes.
- **Game folder:** the folder next to `DAT/` holds 11 more movies (in `SETUP.MIX` and others), all version 2. This check does not re-read them.

## Worked example

`L4_HJI.MIX` entry 67 (key 0x63CF4BD8, 50,468 bytes). Its `VQHD` begins:

```
02 00  00 00  09 00  e8 00  bc 00  04  04  0f  08
```

| Bytes | Meaning |
|---|---|
| `02 00` | version 2 |
| `09 00` | 9 frames |
| `e8 00`, `bc 00` | 232 × 188 pixels |
| `04 04` | 4×4 blocks |
| `0f` | 15 frames per second |
| `08` | each codebook arrives in 8 parts |

Each frame carries one `CBPZ` part of 1,371 bytes (8 parts in all, one per frame):
- Frame 0 also holds `CBFZ` (18,481 bytes), `CPL0` (768 bytes) and `VPTZ` (2,229 bytes).
- Frame 1 holds `CBPZ` and `VPTZ` (2,467 bytes).
- Frame 2 holds `CBPZ` and `VPTZ` (2,535 bytes).

The intro movie, `MOVIES.MIX` entry 2 (`outtakes\lolg.vqa`, key 0xB3593D3C), has the header `02 00 01 00 f8 0d 80 02 90 01 04 04 0f 00`:
- 3,576 frames of 640×400 at 15 frames per second;
- 4×4 blocks;
- byte 13 is 0, so its codebooks are scheduled by `CIND` rather than split into a fixed number of parts.

`L20_BBI.MIX` entry 403 is the short scheduled example the check walks in full (312 frames). Its `CIND` entries are frame 0, size 29,591, and frame 160, size 22,860. 29,591 is the `CBFZ` on frame 0. 22,860 is the sum of the 160 `CBPZ` parts on frames 0 through 159, and those bytes are one LCW stream of 46,336 bytes (2,896 vectors of 16). On the intro, the `CIND` entry for frame 96 has size 26,274, the single `CBPZ` carried on frame 95. That part decompresses to 31,728 bytes. Frame 96's indexes fit the new book. On frame 496, 1,489 indexes fall outside the previous book, so the new book is in force on the scheduled frame and not on the frame that carried the part.

## Open

- The `VPRZ`/`VPTR` pointer stream. `CAN.MIX` entry 22 is 80×68 (340 blocks of 4×4). Its first `VPRZ` decompresses to 492 bytes, not the 680 a full pointer table would be, and begins `00 b6 00 e0 01 e0 02 e0`. Reading each little-endian word by the top 3 bits, the way a published HiColor note describes `VPTR`, takes the first word as a run of length 0 and the next as a skip of 480. That covers the frame and leaves 487 of the 492 bytes unread, so it does not describe this stream. What would settle it is the routine that expands the accepted buffer.
- The two `VPTZ` frames named above. On `L20_BBI.MIX` entry 25 frame 115 the copy offset is 0 with 30,400 bytes already written (a full table is 32,000). Treating that one command as "repeat the last byte", or as a command that writes nothing, finishes the stream at 32,010 or 32,007 bytes.
- How a script names a movie is a separate page: [movie scenes](../lol2-movie-scenes.md).
