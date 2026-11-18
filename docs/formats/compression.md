# Compression schemes

**What:** the ways LoL2 stores data in compressed form. Three general schemes are known; audio and movies use their own codecs ([sound](sound.md), [VQA](vqa.md)).

| Scheme | Where it is used | Tool | State |
|---|---|---|---|
| LZO1X in blocks | the level texture containers `<LEVEL>.TE_` in every level archive | `lol2_texture_container.py` | CONFIRMED on the data |
| LCW variant ("format 80") | the 37 compressed room sections in `LOCAL.MIX` entry 1 | `lol2_decompress_sphere.py` | CONFIRMED on the data |
| Westwood LZ77 with a leading mode byte | the function at VA `0x158D58`; no MIX entry with a leading size decodes | `lol2_decompress_westwood.py` | code CONFIRMED; the buffers are open ([Q1](../OPEN_QUESTIONS.md)) |

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

A run can keep that decode in `CDCACHE.MIX`. The file is written by the game, and the offset depends on the run ([MIX](mix.md)).

## LCW variant

The room sections use these command bytes (`lol2_decompress_sphere.py` lines 81–92):

| Command byte | Meaning |
|---|---|
| 0x80–0xBF | copy `cmd & 0x3F` literal bytes; `0x80` means 64 |
| 0x00–0x7F | copy `(cmd >> 4) + 3` bytes from `((cmd & 0xF) << 8) \| next byte` back in the output |
| 0xC0–0xFF | copy `(cmd & 0x3F) + 3` bytes from the absolute output offset in the next 2 bytes |

Decoding stops when the stated decoded size is reached. Sections in one group of rotations are decoded into a buffer that already holds the previous section's output.

How it differs from Westwood's classic LCW, which Lands of Lore 1 uses as "Frame4": classic LCW ends on `0x80`, and uses `0xFE` (fill) and `0xFF` (long copy) as separate commands.

**CONFIRMED:** 37 of 37 compressed sections decode to exactly their stated size (`lol2_decompress_sphere.py --check`). Sections 0 and 15 are stored. Their size word counts from offset 10. The tool reads the payload at offset 12, which is 2 bytes short of that word. Whether the game starts at 10 or at 12 is open ([room sections](room-sections.md)).

The routine in `LOLG.DAT` that decodes these sections has not been located (UNCONFIRMED).

## Westwood LZ77 with a mode byte

CONFIRMED in the executable, not yet tied to a file. VA `0x158D58` (`enter 0x14, 0`, then the saved registers) is the decoder. Its arguments are source, destination and output size. VA `0x158D6C` reads the first source byte:

- `0` selects relative long back-references and is consumed.
- Any other value is the first command. Long back-references are then distances from the start of the output.

In both paths a short command (`0x00`–`0x7F`) copies `(cmd >> 4) + 3` bytes from `((cmd & 0xF) << 8) | next` back in the output. A distance of 0 is `mov esi, edi` then `rep movsb` (VA `0x158DAE`, and the same sequence at `0x158E62`): the source is the destination, so those bytes stay as they are. It does not repeat the previous byte. `0x80` ends the stream. `0x81`–`0xBF` copy `cmd & 0x3F` literal bytes. `0xC0`–`0xFD` are a long back-reference of `(cmd & 0x3F) + 3` from a u16 distance. `0xFE` fills `u16` bytes with the next byte. `0xFF` is a long back-reference whose length and distance are both u16.

Eleven direct calls pass the three arguments from registers, structure fields or globals. The call at VA `0x15A604` pushes `[ebp-0x40]`, the global `[0x16774]`, then `[ebp-0x44]` (size, destination, source). The eleven calls are VA `0x67052`, `0x15204F`, `0x15A604`, `0x15BEE1`, `0x15C50D`, `0x15CAD4`, `0x17140F`, `0x172335`, `0x1727C6`, `0x1727F1` and `0x172838`. The address is not stored as a dword. Following one of those calls back to a buffer that came from a file is still open ([Q1](../OPEN_QUESTIONS.md)).

`tools/lol2_decompress_westwood.py` follows that rule. Its self-test passes. Of the MIX entries whose first u32 is larger than the entry and at most 16 times the entry, 8 were tried and none decoded to that size (`--check`, re-run 2026-11-18).

`tools/lol2_lcw.py` holds a fourth, LCW-like function. It was kept only because `lol2_verify_wall_atlas_candidate.py` recorded its result. It is not classic LCW, and nothing in the game data is known to use it.
