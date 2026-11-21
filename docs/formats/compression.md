# Compression schemes

**What:** the ways LoL2 stores data in compressed form. Three general schemes are known; audio and movies use their own codecs ([sound](sound.md), [VQA](vqa.md)).

| Scheme | Where it is used | Tool | State |
|---|---|---|---|
| LZO1X in blocks | the level texture containers `<LEVEL>.TE_` in every level archive | `lol2_texture_container.py` | CONFIRMED on the data |
| Westwood LZ77 with a leading mode byte | `options.shp` shapes, VQA buffers and the `LOCAL.MIX` WSA animation deltas; decoder at VA `0x158D58` | `lol2_decompress_westwood.py` | decoder and caller buffers CONFIRMED ([Q1](../OPEN_QUESTIONS.md)) |

## LZO1X blocks

```
uint32 total decoded size
repeat until the total is reached:
    uint32 compressed size of this block
    LZO1X-compressed bytes (each block decodes to 1 MiB, the last to the remainder)
uint32 0
```

**CONFIRMED** on all 15 level archives (`lol2_level_report.py --check` finds each texture container by the hash of its name; `lol2_texture_container.py` decodes them with the system `liblzo2`).

**Worked example.** `L1_DC.MIX` entry 2 starts with `14 fb c6 00 d7 22 06 00`:
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

**CONFIRMED.** The byte at data `0x223D6` selects which names that
open uses. `0x9E2D7` reads it. Nonzero loads `c:\leved\-global.tex`
(cell `0xC2E`), `c:\leved\-global.odf` (`0xC43`) and
`c:\leved\-spell.odf` (`0xC58`). Zero loads `global\global.tex`
(`0xC6C`), `global\global.odf` (`0xC7E`) and `global\spell.odf`
(`0xC90`). `0x9E310` then pushes the selected texture name and calls
`0x118730`. The zero arm is `0x9E2FB–0x9E30D`; the open at
`0x9E310–0x9E32D` is shared by both arms. The two `.odf` names are
opened through `0x118730` at `0x9E75C` and `0x9E851`. The byte lies
past the stored data (file offset `0x1E33FA`, file size `0x1E2AAF`),
so it starts at zero and the global arm is the default. No writer was
found: the relocation table holds exactly 66 fixups to `0x223D6`, and
all 66 instructions are reads (`cmp byte` or `mov reg8`). No fixup
targets `0x223D1–0x223D3`, `0x223D4` is never written, `0x223D5` has
byte writes only (`0xA0EF8`, `0x14EFF7`) and the dword writes to
`0x223D0` end at `0x223D3`. The code object (file `0x90024` through
`0x1C1024`) also contains none of the direct absolute byte stores
(the `A2`, `C6 05` and `88 /r` disp32 forms). Those 66 embeddings
are 38 compares with immediate 0 and 28 byte loads, so none of them
writes the byte or loads its address. Every relocated reference to
`0x223C0–0x223E0` (219 fixups) is a memory operand; none is an
address load by `mov reg, imm32`, `lea` or `push imm32`. The writes
already named on `0x223D5`, and the dword writes that end at
`0x223D3`, do not cover this byte, and no word or dword access starts
at `0x223D3–0x223D5`. Not ruled out: a store through a register
pointer, or an indexed store from a lower relocated base (the nearest
is the dword table at `0x221DC`, indexed below 108 at `0xC80E3`).
`lol2_media_check.py --check` matches the instruction bytes, the six
names and that store scan. The same byte selects the sounds file
([sound cues](../lol2-sound-cues.md)).

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
and the first span `+0x1909C31..+0x190A0CB` (inclusive, 1,179 bytes)
expands to 1,351 bytes within the advertised 1,730-byte capacity. The
native output bound is `u16(+0x0A) + 6 − 0x2B`, 37 bytes below that
capacity (`0x15BC7E–0x15BC85`); every member's largest delta fits it. All 640 delta spans in
the 21 entries end at the next offset and decode to 670,607 bytes
in total. `lol2_media_check.py --check` re-decodes all 640 spans and
checks the loader's call targets and the name tables at `0xC488–0xC4F0`;
the table operands at `0x7938F`, `0x7ADF3`, `0x7B252` and the literal
push at `0x72E32` are cited here but not pinned by the check.

**UNCONFIRMED.** Whether these 21 names are every file that reaches
`0x15BEE1` and `0x15C50D`. The frame reader `0x15C3F4` is also called
at `0x15C273` and `0x15C29B` inside the frame player `0x15C116` (30
callers, e.g. `0x72E59`), and the table indexes (`[ebx+0x414]` from
`[ebp+0x18]` at `0x7935C`, and `[ebx+0x415]`) are not bounded in the
code; an index of 8 or more in the `0xC4D8` table would read past it.
To settle it, show that every object reaching `0x15C116` comes from
`0x15BB9C` and bound the index arguments at their producers.

### Level texture filename

**CONFIRMED.** The table at data `0xCA20` (file `LOLG.DAT+0x1CDA44`)
has one eight-byte row per level number 0–20. The first dword is
the stem pointer. Slot 0 holds `.\`, and slots 2, 6, 11, 15 and 18
hold empty strings. All 15 other rows hold
`sphere<n>\<level>\<level>`. At `0x9C040` the level loader starts the
name with the context string at +0x558. The initializer copies an empty
string there from data `0xBCC` (`0x9BC32–0x9BC6A`).
The loader appends the indexed stem at `0x9C06E–0x9C094` and
passes that buffer as argument 2 to `0x9C0E4` (`0x9C0C6–0x9C0CF`).
The latter reads the same argument at `0x9C35E`, appends `.tex`
from data `0xBFF`, and passes the result to `0x9D894` at `0x9C3E8`.

For example, slot 20's stem is `sphere3\l20_bb\l20_bb`. The
file opener at `0x9D8E4` receives that stem with `.tex` appended.
The cache lookup at `0x119268–0x119279` substitutes an underscore
for the final character when looking up the compressed member.
Hashing the resulting `sphere3\l20_bb\l20_bb.te_` gives
`0xC2871391`. The member begins at `L20_BB.MIX+0x2A`.
`lol2_media_check.py --check` pins the filename instructions and
checks this join on all 15 levels. The open at `0x9D8E4` uses that name before
the test of `0x223D6` at `0x9D907`, and that test does not write the
byte. The row at `0x9DE84` takes its packed length from the third
dword of the 12-byte record read at `0x9DE42`, so this arm can still
reach `0x67052`. The other four direct callers of the row builder
push a packed length of zero and skip the decoder: `0x9DDBB`
(`push 0` at `0x9DD8F`), `0x9E5D2` (`xor esi, esi` at `0x9E5B1`,
then `push esi`), `0x9E66D` (`push 0` at `0x9E633`) and `0xE3715`
(`push 0` at `0xE3705`). The directory arm at `0x9E6ED` pushes the
packed length from its 12-byte row. With the selector byte at its
starting zero, that name is `global\global.tex`. The type-4 reader
at `0x15C9DA` opens its first argument at `0x15C9F1` and reads the
packed body at `0x15CA8F`. It has no direct call and no filename
immediate. The call at `0x15204F` sits in the function entered at
`0x151F0A`. Its one direct caller, `0x144701`, pushes four registers
and no filename. The call at `0x15A604` sits in the function entered
at `0x15A2A0`. The code object holds 317 `E8` encodings that call
it; the first, at `0x72EA3`, passes the stack buffer at
`[esp+0x1D5C]`, and the others were not traced. A store of `0x223D6`
through a register pointer was not ruled out. The CLI's
leading-u32 experiment does not detect this framing.

`tools/lol2_decompress_westwood.py` follows the decoding rule above. Its self-test passes. Of the MIX entries whose first u32 is larger than the entry and at most 16 times the entry, 8 were tried and none decoded to that size (`--check`).

`tools/history/lol2_lcw.py` holds a fourth, LCW-like function. It was kept only because `lol2_verify_wall_atlas_candidate.py` recorded its result. It is not classic LCW, and nothing in the game data is known to use it.

## Close-out

### Q1

**What was measured.** The code in `LOLG.DAT` contains the address bytes `D6 23 02 00` 66 times. Thirty-eight are the seven-byte compare `80 3D D6 23 02 00 00`, every one with immediate 0, and the other 28 are `8A` loads of that byte (`8A 25` eleven times, `8A 35` nine, `8A 15` two, `8A 3D` two, `8A 2D` two, `8A 1D` once and `8A 0D` once).

**What was tried.** This scan counted those embedded address bytes in the code object, matched them to the 66 LE fixups whose target is `0x223D6`, classified the 219 fixups to `0x223C0–0x223E0`, and disassembled the six direct callers of the row builder at `0x66E8C`. Stores through a register were not searched. The page already records the 66 relocation reads and that the direct absolute store forms are absent.

**What would settle it.** The level stem is resolved by the [15 archive joins](#level-texture-filename). The remaining tests are to identify the first argument of `0x15C9DA` and follow the buffers passed to `0x151F0A` and `0x15A2A0` to their file-open calls.
