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

A `VQFR` holds:
- `CPL0`: a 768-byte palette;
- `CBFZ`: optional, a full codebook, LCW-compressed;
- `CBPZ`: optional, one part of the next codebook;
- `VPTZ`: the LCW-compressed vector pointers.

Details are in [lol2-vqa-v2.md](../lol2-vqa-v2.md#format-notes).

## Confirmed on the data

`lol2_vqa_v2_decode.py --check --data <DAT>` re-ran on 2026-11-18. CONFIRMED:
- **All movies valid:** `DAT/` holds 1,948 `WVQA` movies; every header is valid, every frame count matches, and all are version 2.
- **Decoded by this tool:** 948 movies use partial codebooks in the layout the tool decodes. As a sample, the shortest of them (`L4_HJI.MIX` entry 67, 9 frames) decodes fully, giving 9 of 9 frames.
- **Partial codebooks the tool does not decode:** 14 movies.
  - 4 use 4×2 blocks with 8 parts, for example `L10_DCI.MIX` entry 25 (248×256 pixels, 160 frames).
  - 10 declare 0 parts in `VQHD`, among them the intro movie.
- **Game folder:** the folder next to `DAT/` holds 11 more movies (in `SETUP.MIX` and others), all version 2.

The remaining movies carry full codebooks only.

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
- 0 parts, which places it among the 10 movies this tool does not decode.

## Open

- Decoding the 4×2-block movies, and the movies with partial codebooks but 0 parts.
- The scene-to-movie control table ([Q12](../OPEN_QUESTIONS.md)).
