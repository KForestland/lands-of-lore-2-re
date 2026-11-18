# Music selection

Opcode 210 byte 4 picks one of twelve arms. Arms 0 and 1 store byte 5 into the two bytes the filename builder uses as stem indexes. The builder writes `MUSIC\stem.AUD` when the high byte of the dword at data `0x2238E` is 2, and `MUSIC\stem.HMI` otherwise. All 32 real stems have an `.AUD` entry in `DMUSIC.MIX` and an `.HMI` entry in `LOCAL.MIX`. One `DMUSIC.MIX` entry has no stem.

`tools/lol2_media_check.py --check` re-reads the stem table, the 32 hashes, the headers and the worked-example command. It writes nothing. It does not decode samples. Header and chunk facts for the codec are in [the music note](lol2-music-2026-11.md).

## The stem table

CONFIRMED. File `0x1C2268` is `MUSIC\%s.AUD`. File `0x1C2275` is `MUSIC\%s.HMI`. The pointer table is 35 dwords at file `0x1CE10C` (data `0xD0E8`). Slot 0 points at the NUL before the first name, so its string is empty. Slots 3 and 13 are the literal name `badfile`. Both hashes of `MUSIC\badfile.AUD` miss `DMUSIC.MIX`.

| Index | Stem | Index | Stem |
| --- | --- | --- | --- |
| 0 | (empty) | 18 | HUJUNG1 |
| 1 | ARENBAT1 | 19 | HUNT1 |
| 2 | BELBATL1 | 20 | HUVILAG1 |
| 3 | badfile | 21 | MONPOST1 |
| 4 | BELWAND1 | 22 | MONWAND1 |
| 5 | CEMWNDR1 | 23 | RUBAT1 |
| 6 | CHAMWDR1 | 24 | RUPOST1 |
| 7 | CITYWAN1 | 25 | RUWANDR1 |
| 8 | CITYWAN2 | 26 | SKELBAT1 |
| 9 | CLAWBAT1 | 27 | SSARBAT1 |
| 10 | CLAWWAN1 | 28 | SSARCAV1 |
| 11 | DHALLP1 | 29 | SSARPIT1 |
| 12 | DRAHALL1 | 30 | TEMPLE1 |
| 13 | badfile | 31 | VICBATL1 |
| 14 | GLADWAN1 | 32 | WILDBAT1 |
| 15 | HIVEBAT1 | 33 | ANMAGIC |
| 16 | HIVECAV1 | 34 | SAVAGE |
| 17 | CHAMBAT1 |  |  |

## Opcode 210

CONFIRMED. The handler is VA `0x65954`. It reads command byte 4. A value above 11 jumps to VA `0x65BA7`, which returns 1 and stores nothing. Otherwise it jumps through `cs:[arm*4 + 0xC900]`. Those twelve dwords are at file `0x9C924`. Each dword plus `0x59024` is the arm. The same adjustment is the one in [the movie note](lol2-movie-scenes.md). Bytes 2 and 3 are not read by any arm. Every arm reads byte 5.

The stores land on four 6-byte records. Each record is a byte and two words.

| Record | Byte | Words | Arms that write them |
| --- | --- | --- | --- |
| data `0x26D14` | stem | `0x26D16`, `0x26D18` | 0 writes the byte, 4 writes both words |
| data `0x26D1A` | stem | `0x26D1C`, `0x26D1E` | 1 writes the byte, 5 writes both words |
| data `0x26D20` | byte | `0x26D22`, `0x26D24` | 2 writes the byte, 6 writes both words |
| data `0x26D26` | byte | `0x26D28`, `0x26D2A` | 3 writes the byte, 7 writes both words |

Arms 4, 5, 6 and 7 scale byte 5 with `((n << 15) - n) >> 8` and store that word twice. Byte 200 stores 25599. Arms 8 and 9 use the same scale. If the dword at `0x26D2C` already equals `0x26D14` (arm 8) or `0x26D1A` (arm 9), they store only the first word of that record. Otherwise they jump into arm 4 or arm 5 and store both words.

Arm 0, before it stores, calls VA `0x156030` when the high byte of `[0x2238E]` is 2, and VA `0x156F12` otherwise. The call happens only when byte 5 differs from the stored stem and `[0x26D2C]` already equals `0x26D14`. Arm 1 does the same for `0x26D1A`. The calls pass the dword at `0x26D30` and 0. What they change was not followed.

Arm 10 adds a nonzero byte 5 to the dword at `0x26D34`. A zero byte stores 0 there. Arm 11 stores the scaled word, masked to 16 bits, in the dword at `0x26D3C`. What those dwords change in playback was not followed. The same is true of the scaled words.

## The filename

CONFIRMED. When the byte at data `0xB868` is not zero, VA `0xA0516` calls VA `0xACFD0` with `0x26D14`. That function keeps the pointer in `ebx`. It calls the builder at VA `0xAD3C8` twice: once with the byte at `[ebx + 6]` (the stem at `0x26D1A`) and once with the byte at `[ebx]` (the stem at `0x26D14`). What writes `0xB868` was not re-read.

The builder leaves immediately when that byte is 0, which is the empty slot. Otherwise the byte indexes the stem table. The high byte of `[0x2238E]` selects the format: 2 uses `MUSIC\%s.AUD`, any other value uses `MUSIC\%s.HMI`. It builds the name through VA `0x150158` and probes it with VA `0x118934`. A zero probe sets a bit on the caller's flag byte and returns. What stores the high byte of `0x2238E` was not re-read. Both spellings of each name hash to the same id, because the hash uppercases.

## Where the files are

CONFIRMED. `DMUSIC.MIX` has 33 entries. For every stem except the empty slot and `badfile`, both hash functions of `MUSIC\stem.AUD` agree, and that id is one entry. That is 32 hits. The `.HMI` ids are not in `DMUSIC.MIX`. All 32 are in `LOCAL.MIX`.

The entry with no stem is index 16, id `0x22F7A4EB`, size 2,784,067. Its header is rate 22050, flags 2, codec 99, and the first chunk id is `0xDEAF`. The compressed-size field plus 12 equals the entry size. No name was invented for it.

Every one of the 33 headers has flags 2, codec 99, first chunk id `0xDEAF`, and compressed size plus 12 equal to the entry size. Thirty-two are 22050 Hz. Entry 10 is `SSARPIT1` (stem 29), id `0xD76E26ED`, rate 44100, size 3,394,572. This pass did not decode the samples.

## Worked example

CONFIRMED. `DAT/L12_CM.MIX` command stream 1, file offset 9823696:

```
d2 00 00 00 00 0a
```

Opcode 210, bytes 2–3 are 0, arm 0, byte 5 is 10. Stem 10 is `CLAWWAN1`. Both hashes of `MUSIC\CLAWWAN1.AUD` are `0x7F0A3AE3`, which is `DMUSIC.MIX` entry 30.

The next command, file offset 9823702, is `d2 00 00 00 01 09`: arm 1, stem 9 `CLAWBAT1`, id `0x7EB63AEF`, entry 29. File offset 9823708 is `d2 00 00 00 04 c8`: arm 4, byte 5 is 200, so both words at `0x26D16` and `0x26D18` become 25599. File offset 9823714 is `d2 00 00 00 05 c8`: arm 5, the same scale into `0x26D1C` and `0x26D1E`.

Which extension those two stems use depends on the high byte of `[0x2238E]` at the moment the builder runs. The `.AUD` bytes are the `DMUSIC.MIX` entries above. The `.HMI` bytes are the `LOCAL.MIX` entries with the other hash.

## What is still open

- What writes the high byte of data `0x2238E`, and what writes the gate byte at `0xB868`.
- What the calls at VA `0x156030` and VA `0x156F12` do, and what the scaled words and the arm 10 and arm 11 dwords change.
- A name for `DMUSIC.MIX` entry 16. The 34 stems do not hash to it.
