# Compression schemes

**What:** the ways LoL2 stores data in compressed form. Three general schemes are known; audio and movies use their own codecs ([sound](sound.md), [VQA](vqa.md)).

| Scheme | Where it is used | Tool | State |
|---|---|---|---|
| LZO1X in blocks | the level texture containers `<LEVEL>.TE_` in every level archive | `lol2_texture_container.py` | CONFIRMED on the data |
| Westwood LZ77 with a leading mode byte | `options.shp` shapes and VQA buffers; decoder at VA `0x158D58` | `lol2_decompress_westwood.py` | decoder and caller buffers CONFIRMED ([Q1](../OPEN_QUESTIONS.md)) |

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

## Westwood LZ77 with a mode byte

**CONFIRMED.** VA `0x158D58` (`enter 0x14, 0`, then the saved registers) is the decoder. Its arguments are source, destination and output size. VA `0x158D6C` reads the first source byte:

- `0` selects relative long back-references and is consumed.
- Any other value is the first command. Long back-references are then distances from the start of the output.

In both paths a short command (`0x00`–`0x7F`) copies `(cmd >> 4) + 3` bytes from `((cmd & 0xF) << 8) | next` back in the output. A distance of 0 is `mov esi, edi` then `rep movsb` (VA `0x158DAE`, and the same sequence at `0x158E62`): the source is the destination, so those bytes stay as they are. It does not repeat the previous byte. `0x80` ends the stream. `0x81`–`0xBF` copy `cmd & 0x3F` literal bytes. `0xC0`–`0xFD` are a long back-reference of `(cmd & 0x3F) + 3` from a u16 distance. `0xFE` fills `u16` bytes with the next byte. `0xFF` is a long back-reference whose length and distance are both u16.

The 37 compressed [options interface shapes](room-sections.md) in
`LOCAL.MIX` use this decoder. The shape payload and its expanded size
come from the native shape header.

### Direct calls and their buffers

**CONFIRMED.** The DOS 1.30 code object has eleven direct `call rel32`
instructions whose target is `0x158D58`. The table follows the three
arguments back to their producers. `row` and `node` refer to the
structures accessed by the indicated caller.

| Call | Source and destination | Capacity and evidence |
|---|---|---|
| `0x67052` | Read from a generic resource handle after seeking to row +4. The stream is staged at `allocation + expanded_size − packed_size` and expanded to the allocation base. | Expanded size dword row +8; packed size word row +0xC must be nonzero (`0x67013–0x67052`). The EFX loader supplies zero at `0xE3715 → 0x66E8C`. |
| `0x15204F` | Shape data after the ten-byte header and, if flag bit 0 is set, a 16-byte remap. Destination is the matching payload position in scratch `[0x16774]`. The continuation reads the temporary shape into `[0x1552C]`. | Shape u16 +8 (`0x151F55–0x151F5E`, `0x15A202–0x15A20C`, `0x15201D–0x152063`). |
| `0x15A604` | Shape payload selected after the header and optional remap at `0x15A457–0x15A4C3`. The draw path uses scratch `[0x16774]` for the expanded source. | Shape u16 +8, copied to local −0x40. Enters the decoder when flag bit 1 is clear (`0x15A46E`, `0x15A5ED–0x15A616`). |
| `0x15BEE1` | Stream read at `0x15BEAC` to an address near the end of the destination allocation. The file path seeks to the resource position plus `0xE` and an auxiliary byte count. Destination is local −0x2C; source is that pointer plus expanded length minus packed length. | Resource u16 +0xC (`0x15BE6A–0x15BEE6`). |
| `0x15C50D` | Same resource capacity field, with compressed input read from the handle at `0x15C4F2` to local −0x14 after adjustment by the expanded-minus-packed size. Destination is the pointer stored in dword resource +0xE. | Resource u16 +0xC (`0x15C4D3–0x15C512`). |
| `0x15CAD4` | In-memory record of type byte 4. Source is `record + 8 + u16(record+6)`; destination is the helper's second argument. Its file-fed caller reads the packed bytes after copying the eight-byte header (`0x15CA74–0x15CAA7`). | Record dword +2 (`0x15CACE–0x15CAFD`). |
| `0x17140F` | Packed VQA node input from `node[+8] + node[+0x24]` to `node[+8]`; the result is copied into the pending packet at packet +0x24; node +0x14 bit 3 is cleared after decoding (`0x171420`). | Movie context +0x75A. Decoded length goes to node +0x28 (`0x1713EE–0x171445`). |
| `0x172335` | Same VQA node stream and output, in the other packet-building path. | Movie context +0x75A; clears node +0x14 bit 3 after decoding (`0x172317–0x172352`). |
| `0x1727C6` | Packed stream at `aux_node[+0] + aux_node[+0xC]`, where `aux_node = node[+4]`. Destination is the pointer stored at `aux_node[+0]` or movie context +0x6EE. | Movie context +0x75E; result length at auxiliary node +0x10 (`0x172787–0x1727D6`). |
| `0x1727F1` | Same VQA node +0x24 stream and +8 destination, this time from the frame-preparation path. | Movie context +0x75A; result length at node +0x28 (`0x1727D9–0x172802`). |
| `0x172838` | Compressed VQA pointer payload at `node[+0] + node[+0x20]`. Destination is node +0's pointer or the separate buffer at movie context +0x6E6. | Movie context +0x762. The [original intro trace](vqa.md#native-short-copy-runtime-control) reached this call (`0x172805–0x172845`). |

The global texture file supplies a named witness for `0x67052`.
`0x9E305–0x9E32D` opens `global\global.tex` from
`LOLG.DAT+0x1C1C90` (data address `0xC6C`). The original file name hashes to `0xEF88C09F`,
`LOCAL.MIX` entry 50 at `+0x4E6`. The loader reads the secondary
base at member +0x298 (`0x9E332–0x9E358`), then seeks to its
section-9 table (`0x9E689–0x9E6A0`). In the original member the
secondary base is `0x18AE18`; the dword at secondary base +0x2A4 gives 15 rows, and the dword at secondary
base +0x2C (`0x1AECA7`) gives the table's offset from that base
(`LOCAL.MIX+0x339FA5`).
The read at `0x9E6BE` uses three dwords per row. The call
`0x9E6ED → 0x66E8C` stores secondary base + row offset (an absolute file position, sought
at `0x67015`), capacity and the packed length (a word) in resource +4,
+8 and +0xC (`0x66EA7–0x66EBC`). For a texture with mask `0x1000`,
the class-2 resource path (`0x13277C`; table `[0x22D88]`, loader
struct `0x22CD8` + 0xB0, index base `[0x22DA0]`) asks for the companion
at `0x1327B1`,
and the resource reader takes the packed arm at `0x67022–0x67052`.

The first row at `LOCAL.MIX+0x339FA5` names the stream at
`+0x2BCFA5`, packed size 11,476 and capacity 32,000. It emits
27,536 bytes. `lol2_media_check.py --check` checks all 15 rows
and reproduces 466,864 bytes in total, in 16-byte groups.

### Named WSA animation deltas

**CONFIRMED.** Calls at `0x72E39`, `0x79397`, `0x7AE1E` and `0x7B27D`
enter the filename-based loader at `0x15BB9C`. The first uses the
literal `P_LUTHER.WSA` (`LOLG.DAT+0x1C1653`), and the other calls
use dword pointer tables at `LOLG.DAT+0x1CD4AC`, `+0x1CD4FC` and
`+0x1CD4DC`, respectively. That loader opens the named file at
`0x15BBB4`, reads the header through `0x15BBC8`, and expands the
first delta at `0x15BEE1`. It also calls the per-frame reader
`0x15C3F4` at `0x15C08A` and `0x15C0B2`; its file-backed arm reads
a later delta at `0x15C4F2` and expands it at `0x15C50D`.

**CONFIRMED.** All 21 distinct nonempty table names join members of
`LOCAL.MIX` by the original filename hash. Their u16 +0 is followed
by dimensions at +6/+8, capacity at +0x0A and flags at +0x0C.
The dwords at +0x0E form a directory of `u16(+0) + 2` offsets.
For `P_LUTHER.WSA`, the member starts at `LOCAL.MIX+0x1909B17`,
and the first span `+0x1909C31..+0x190A0CB` expands to 1,351 bytes
within the advertised 1,730-byte capacity. All 640 delta spans in
the 21 entries end at the next offset and decode to 670,607 bytes
in total. `lol2_media_check.py --check` rechecks the archive and code.

**UNCONFIRMED.** The complete set of filenames reaching `0x67052` and
`0x15CAD4`, and the shape data reaching `0x15204F` and `0x15A604`.
For the first branch, inspect the row builder callers
`0x9DDBB`, `0x9DE84`, `0x9E5D2` and `0x9E66D`
for a nonzero packed length. For the shape and resource loaders, follow the
handle passed to the read at `0x118820` back to its open, then verify the packed span
against that file. The CLI's leading-u32 experiment does not detect
this framing.

`tools/lol2_decompress_westwood.py` follows the decoding rule above. Its self-test passes. Of the MIX entries whose first u32 is larger than the entry and at most 16 times the entry, 8 were tried and none decoded to that size (`--check`, re-run 2026-11-18).

`tools/lol2_lcw.py` holds a fourth, LCW-like function. It was kept only because `lol2_verify_wall_atlas_candidate.py` recorded its result. It is not classic LCW, and nothing in the game data is known to use it.
