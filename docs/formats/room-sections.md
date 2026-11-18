# Room sections in LOCAL.MIX entry 1

**What:** `LOCAL.MIX` (next to `DAT/`) entry 1 holds 39 sections: small tile grids for corridors, corners, chambers and rooms, many as four rotations of one shape. Tool: `tools/lol2_decompress_sphere.py`.

## Layout

The entry starts with a uint16 section count and a table of uint32 section offsets. The first bytes of a section are:

| Offset | Type | Meaning |
|---|---|---|
| 0 | uint16 | flags |
| 2 | uint16 | 0 on a compressed section; 2 on the stored sections 0 and 15 |
| 4 | uint8 | width |
| 5 | uint8 | height |
| 6 | uint8 | 0 |
| 7 | uint8 | width again |
| 8 | uint16 | bytes from the start of this section to the next |
| 10 | uint16 | decoded size on a compressed section; on a stored section, bytes counted from offset 10 |

Sections other than 0 and 15 are compressed with a variant of Westwood's LCW ("format 80"; Lands of Lore 1's Frame4 is the classic form). Commands, as `tools/lol2_decompress_sphere.py` decodes them (lines 81-92 and its docstring):

| Command byte | Meaning |
|---|---|
| 0x80-0xBF | copy `cmd & 0x3F` literal bytes; `0x80` means 64 bytes (classic LCW ends on `0x80` instead) |
| 0x00-0x7F | copy `(cmd >> 4) + 3` bytes from `((cmd & 0xF) << 8) | next byte` back in the output |
| 0xC0-0xFF | copy `(cmd & 0x3F) + 3` bytes from the absolute output offset in the next 2 bytes |

Decoding stops when the stated decoded size is reached. Within a group of rotations each section is decoded into a buffer that already holds the previous section's output (chained). The decoded bytes are a grid: a nonzero byte is a tile number, `00 n` skips n empty cells.

## Confirmed

All 37 compressed sections decode to exactly their stated size (`lol2_decompress_sphere.py --check`).

Sections 0 and 15 are the stored ones. Measured on `LOCAL.MIX` entry 1:

| Section | +2 | Width × height | Word at +8 | Word at +10 | Bytes after offset 12 |
|---|---:|---|---:|---:|---:|
| 0 | 2 | 128 × 128 | 16,394 | 16,384 | 16,382 |
| 15 | 2 | 155 × 147 | 11,970 | 11,960 | 11,958 |

The word at +8 equals the bytes from the start of the section to the next section. The word at +10 equals the bytes from offset 10 to the next section. The compressed sections have 0 at +2, and their word at +10 is a decoded size that is not equal to that tail. Those two facts do not say whether the payload starts at offset 10 or at offset 12: the reader in the executable was not traced, so that stays open ([Q2](../OPEN_QUESTIONS.md)). The tool reads the payload at offset 12, which is 2 bytes short of the word at +10. Section 0's tail from offset 10 is exactly 128 × 128. Section 15's tail is 11,960 bytes, and 155 × 147 is 22,785, so that section is not a raw grid of its stated dimensions. The last section, 38, declares 166 bytes and the entry has 168, two trailing bytes.

## Worked example

Section 11 is a 29 x 29 chamber; `lol2_decompress_sphere.py 11 --png room11.png` draws its tile numbers ([picture](../images/local_mix_room11_tiles.png)). How the game uses these sections (which levels, which rooms) is not traced (UNCONFIRMED). The tool's name "Sphere" comes from the game's `SPHERE<n>` folder names.
