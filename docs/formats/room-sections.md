# Room sections in LOCAL.MIX entry 1

**What:** `LOCAL.MIX` (next to `DAT/`) entry 1 holds 39 sections: small tile grids for corridors, corners, chambers and rooms, many as four rotations of one shape. Tool: `tools/lol2_decompress_sphere.py`.

## Layout

The entry starts with a uint16 section count and a table of uint32 section offsets. Each section has a 12-byte header:

| Offset | Type | Meaning |
|---|---|---|
| 0 | uint16 | flags |
| 2 | uint16 | 0 |
| 4 | uint8 | width |
| 5 | uint8 | height |
| 6 | uint8 | 0 |
| 7 | uint8 | width again |
| 8 | uint16 | section size |
| 10 | uint16 | decoded size |

Sections other than 0 and 15 are compressed with a variant of Westwood's LCW ("format 80"; Lands of Lore 1's Frame4 is the classic form). Commands, as `tools/lol2_decompress_sphere.py` decodes them (lines 81-92 and its docstring):

| Command byte | Meaning |
|---|---|
| 0x80-0xBF | copy `cmd & 0x3F` literal bytes; `0x80` means 64 bytes (classic LCW ends on `0x80` instead) |
| 0x00-0x7F | copy `(cmd >> 4) + 3` bytes from `((cmd & 0xF) << 8) | next byte` back in the output |
| 0xC0-0xFF | copy `(cmd & 0x3F) + 3` bytes from the absolute output offset in the next 2 bytes |

Decoding stops when the stated decoded size is reached. Within a group of rotations each section is decoded into a buffer that already holds the previous section's output (chained). The decoded bytes are a grid: a nonzero byte is a tile number, `00 n` skips n empty cells.

## Confirmed

All 37 compressed sections decode to exactly their stated size (`lol2_decompress_sphere.py --check`). The stored sections 0 (128 x 128) and 15 (155 x 147) hold 2 bytes fewer than their headers state ([Q2](../OPEN_QUESTIONS.md)).

## Worked example

Section 11 is a 29 x 29 chamber; `lol2_decompress_sphere.py 11 --png room11.png` draws its tile numbers ([picture](../images/local_mix_room11_tiles.png)). How the game uses these sections (which levels, which rooms) is not traced (UNCONFIRMED). The tool's name "Sphere" comes from the game's `SPHERE<n>` folder names.
