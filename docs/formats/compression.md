# Compression schemes

**What:** the ways LoL2 stores data in compressed form. Three general schemes are known; audio and movies use their own codecs ([sound](sound.md), [VQA](vqa.md)).

| Scheme | Where it is used | Tool | State |
|---|---|---|---|
| LZO1X in blocks | the level texture containers `<LEVEL>.TE_` in every level archive | `lol2_texture_container.py` | CONFIRMED on the data |
| LCW variant ("format 80") | the 37 compressed room sections in `LOCAL.MIX` entry 1 | `lol2_decompress_sphere.py` | CONFIRMED on the data |
| Westwood LZ77 with a leading mode byte | no data found that uses it | `lol2_decompress_westwood.py` | UNCONFIRMED ([Q1](../OPEN_QUESTIONS.md)) |

## LZO1X blocks

```
uint32 total decoded size
repeat until the total is reached:
    uint32 compressed size of this block
    LZO1X-compressed bytes (each block decodes to 1 MiB, the last to the remainder)
uint32 0
```

**CONFIRMED** on all 15 level archives (`lol2_level_report.py --check` finds each texture container by the hash of its name; `lol2_texture_container.py` decodes them with the system `liblzo2`).

**Worked example** (re-run 2026-11-18). `L1_DC.MIX` entry 2 starts with `14 fb c6 00 d7 22 06 00`:
- The total decoded size is 13,040,404 bytes.
- The first block is 402,135 bytes compressed.
- 13 blocks follow: 12 decode to 1 MiB each, and the last decodes to 457,492 bytes.
- The zero trailer ends exactly at the entry's last byte.

The result is byte-identical to the copy found in one game-written `CDCACHE.MIX` at file offset 5,070 ([texture container](texture-container.md)); that cache is written by the game when it runs, not shipped ([Q20](../OPEN_QUESTIONS.md)).

## LCW variant

The room sections use these command bytes (`lol2_decompress_sphere.py` lines 81–92):

| Command byte | Meaning |
|---|---|
| 0x80–0xBF | copy `cmd & 0x3F` literal bytes; `0x80` means 64 |
| 0x00–0x7F | copy `(cmd >> 4) + 3` bytes from `((cmd & 0xF) << 8) \| next byte` back in the output |
| 0xC0–0xFF | copy `(cmd & 0x3F) + 3` bytes from the absolute output offset in the next 2 bytes |

Decoding stops when the stated decoded size is reached. Sections in one group of rotations are decoded into a buffer that already holds the previous section's output.

How it differs from Westwood's classic LCW, which Lands of Lore 1 uses as "Frame4": classic LCW ends on `0x80`, and uses `0xFE` (fill) and `0xFF` (long copy) as separate commands.

**CONFIRMED:** 37 of 37 compressed sections decode to exactly their stated size (`lol2_decompress_sphere.py --check`). The two stored sections, 0 and 15, are 2 bytes short of their stated size ([Q2](../OPEN_QUESTIONS.md)). Details: [room sections](room-sections.md).

The routine in `LOLG.DAT` that decodes these sections has not been located (UNCONFIRMED).

## Westwood LZ77 with a mode byte

`tools/lol2_decompress_westwood.py` implements a scheme with these properties:
- a leading mode byte selects absolute or relative back-references;
- `0x80` ends the stream;
- `0xFE` is a fill and `0xFF` is a long copy.

Its docstring says the scheme came from the executable, but no address is cited, so the scheme is UNCONFIRMED. The decoder passes its self-test. Its data scan, however, finds 8 MIX entries whose first u32 is larger than the entry, and none of them decodes to that size with this decoder (`--check`). Which data uses this scheme, if any, is open ([Q1](../OPEN_QUESTIONS.md)).

`tools/lol2_lcw.py` holds a fourth, LCW-like function. It was kept only because `lol2_verify_wall_atlas_candidate.py` recorded its result. It is not classic LCW, and nothing in the game data is known to use it.
