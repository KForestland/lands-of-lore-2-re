# Options interface shapes in LOCAL.MIX

**CONFIRMED.** `LOCAL.MIX` entry 1 has key `0x8248262E`
(directory row at `+0x12`) and begins at `+0x193112F`. The original
Westwood name hash of `options.shp` is `0x8248262E`. `LOLG.DAT`
contains that name at file offsets `+0x1C1614`, `+0x1C1620` and
`+0x1C2455`. The options code loads it with `0x118AC8` at
`0x6FDD8–0x6FDF6` and `0xB93D9–0xB93EB`. The pointer from
`[0x9679C]` or `[0xB7EEC]` goes to the interface draw helper
`0xC9D94` (`0x70919–0x7095B`, `0xB9A63–0xB9A9E`). That helper
looks up shape 0 at `0xC9DA6` and draws it at `0xC9DFB`.

## Directory and payload

**CONFIRMED.** The `u16` entry count at +0 is 39 and the directory
starts at entry +2. For index `i`, `0x15A22D–0x15A256` adds the
u32 at `entry + 2 + 4*i` to `entry + 2`. Each cited header field
below is relative to that sum.

| Header offset | Type | Meaning and evidence |
|---|---|---|
| +0 | u16 | Flags. Mask 2 selects stored data; the tests are at `0x15A5ED` (draw path) and `0x151FA3` (copy path), after the header read at `0x15A457–0x15A475`. |
| +2 | u8 | Height (`0x15A263–0x15A26C`, draw setup `0xC9DB5–0xC9DE3`). |
| +3 | u16 | Width (`0x15A258–0x15A262`). |
| +5 | u8 | The saved height, copied back to +2 by `0x15A281–0x15A295`. |
| +6 | u16 | Total span including the header. All 39 entries exactly match the next header or end of entry. |
| +8 | u16 | Expanded byte count passed to `0x158D58` on compressed shapes (`0x15A46E–0x15A472`, `0x15A5F6–0x15A604`). |
| +10 | bytes | Start of the payload for both flag values in this file (`0x15A475–0x15A4C3`, `0x151F99–0x151FD1`). |

The payload is thus **+12 from the address previously treated as the
header**. The first two bytes of that previous header read fall
before the true shape. Counting each span from the true header
restores the two bytes missing from the end of the old slice.
The final shape ends exactly at the end of the entry.

| Shape | True header, in LOCAL.MIX | True payload, in LOCAL.MIX | Dimensions (width × height) | Payload bytes |
|---|---|---|---|---:|
| 0 (stored) | `+0x19311D1` | `+0x19311DB` | 128 × 128 | 16,384 |
| 15 (stored) | `+0x1935AF2` | `+0x1935AFC` | 147 × 155 | 11,960 |

**CONFIRMED.** The 37 shapes with flags 0 use the [mode-byte
LZ77 decoder](compression.md#westwood-lz77-with-a-mode-byte)
at `0x158D58`. The 2 shapes with flags 2 feed the stored payload
straight to the shape consumer. A nonzero byte yields one colour
index. A zero followed by `n` draws `n` transparent pixels
(`0x151FC4–0x151FE1`). All 39 streams reach their exact pixel
counts. In particular, the 11,960 bytes of shape 15 cover all
22,785 pixel positions.

Run `python3 tools/lol2_decompress_sphere.py --data /path/to/DAT --check`
to check the key, directory, stored lengths, compressed streams and
pixel counts on your own files. The historical tool name is retained.
