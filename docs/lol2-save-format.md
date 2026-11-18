# LoL2 native save slots

This page describes the 1.30 DOS writer, using [executable analysis addresses](lol2-executable-tables.md).
File offsets in a save are independent of those addresses. Integers are
little-endian. The fixed header, directory bounds and compressed preview were
checked on 27 native slots in the reference set, including the autosave
with SHA-256 prefix `e2393dbe4d2b`. These are file and
code observations.

## Slot header and directory

**CONFIRMED.** The writer at `0xE7CE1–0xE7CFE` writes 0x25A bytes at
slot offset zero. The header gives absolute offsets to the compressed
preview, 11 numbered global sections and 20 numbered level blocks.
Each section spans from its directory offset to the following one. Equal
offsets describe empty spans. The final level's end is the file size.

| Slot offset | Type | Meaning and evidence |
|---|---|---|
| `0x000` | NUL-terminated bytes | Slot display name, copied to the head of the buffer at `0xE785C–0xE7873`. Bytes beyond the terminator can vary. |
| `0x02C` | u32 | Total slot size, set by the end query at `0xE7CC3–0xE7CD3`. |
| `0x030`, `0x034` | u32 each | Values 0x12 and 0x66, both checked by `0xEB847–0xEB853`. |
| `0x038–0x043` | 3 u32 | Compatibility comparisons to cells `0xD938C`, `0xD9390`, `0xD9394` at `0xEB857–0xEB87A`. Their external meaning is **UNCONFIRMED**. |
| `0x098–0x0A7` | 4 u32 | Preview descriptor. The observed values are 1, 320, 200 and data offset 0x25A, filled from the writer's argument at `0xE789B–0xE78E3`. |
| `0x0A8–0x177` | 26 u32 bases, 26 u32 lengths | Address-range map used for pointer conversion, populated by `0xE5C48`, passed to the save adjustment routine at `0xE7A15`. |
| `0x178–0x17B` | 4 bytes | **UNCONFIRMED**. |
| `0x17C` | s32 | Active level ID from byte `[0x23331]` at `0xE7887–0xE7895`. |
| `0x180`, `0x184`, `0x188` | s32 each | Player position dwords re-applied by the writer at `0xE7D3F–0xE7D4F`. |
| `0x18C` | u16 | Region index, or 0xFFFF for a null region. The writer computes a 44-byte row pointer at `0xE7D04–0xE7D3A`. |
| `0x18E–0x1B9` | 11 u32 | Absolute offsets for global sections 0–10, written at `0xE794F`. |
| `0x1BA–0x209` | 20 u32 | Absolute offsets for levels 1–20, written at `0xE7B92`. |

**CONFIRMED.** Global section 0 takes 0x22E bytes from the player object
at `0x22574` (`0xE86A3`). Section 1 takes the shared script byte array
from `[0x26E58]`, length `[0x26E60]` (`0xE86BD`). Section 2 takes
elements from the pool whose header pointer is `[0x96918]`, writing
count×stride (`0xE86DC–0xE86F6`). The writer can XOR global sections
against a base file (`0xE795E–0xE79FA`), normalize pointer fields
(`0xE7A1C`), and compress sections with flag 4 (`0xE7A3E`).
The global dispatch table is at `LOLG.DAT+0x11F64C`.

## Level blocks

**CONFIRMED.** The native per-level writer `0xE7F68` appends `.img`
and `.lsv` from object-5 cells `0x3153` and `0x3158`. The slot writer
calls it at `0xE7B0F` and copies existing level save files at
`0xE7C26–0xE7C47`. The suffix at `0x3149` used by that copy is
also `.lsv` (file `0x1C416D`).

All 149 nonempty blocks in the 27-slot reference set have a fixed 0x2F8-byte
prefix, nondecreasing section offsets and size matching their directory
span. The writer reserves it
at `0xE80DC` and fills it at `0xE83DF`.

| Block offset | Layout | Native evidence |
|---|---|---|
| `0x000` | u32 block size | End query and header rewind at `0xE83BB–0xE83DF`. |
| `0x004` | 26 u32 source bases, then 26 u32 lengths | Map filled at `0xE80D2` via `0xE5C48`. |
| `0x0D4–0x0D7` | 4 bytes | **UNCONFIRMED**. |
| `0x0D8` | 68 u32 block-relative section offsets | `0xE8148`, increment and loop guard `0xE837E–0xE8393`. |
| `0x1E8` | 68 u32 section lengths before compression | `0xE8184`. |
| `0x2F8` | First section data | Frame starts after the fixed prefix at `0xE80E4`. |

Use the section index with `0xE8914` to get the native pointer, byte count,
stride and flags. For flag 2 the writer XORs live bytes with the corresponding
base `.img` bytes (`0xE820E`, `0xE8247`) and passes the result through
section-specific pointer handling at `0xE8283`. Flag 4 writes compressed
chunks via `0xEB6A0`. Otherwise the selected bytes are written at
`0xE82D0` or `0xE8338`. Untouched bytes XOR to zero before pointer
handling. In region section 12 the pointer helper is called on the first
dword of each 44-byte row (`0xE9923–0xE9972`), beyond which the floor
word at +0x12 remains in the XOR data.

| Section | Buffer and stride | Flags | Native selector |
|---:|---|---:|---|
| 12 | Region records, 44 bytes, pointer `[0x22D0C]`, count `[0x22D2C]` | 7 | `0xE8AD7` |
| 19 | Control elements, 0x40 bytes, pool-cell `0x273E0`, includes +0x26 durability | 7 | `0xE8BF8`, stride at `0x9D278` |
| 21 | Actor elements, 0xBC bytes, pool-cell `0x9696C`, includes +0x88 health and +0xA8 state | 7 | `0xE8C40`, stride at `0x9D2A7` |
| 22 | Movable elements, 0x58 bytes, pool-cell `0x2B500`, includes position/state at +0x48/+0x55 | 7 | `0xE8C65`, stride at `0x9D33C` |
| 24 | Local script byte array `[0x26E54]`, length `[0x26E5C]` | 7 | `0xE8CAD` |
| 61, 63 | 12-byte timer list header and parallel object list header | 3 | `0xE9142`, `0xE9180` |
| 62, 64 | Timer list pointer arrays, lengths `[0xB7DA8]*4` and `[0xB7DB4]*4` | 1 | `0xE915D`, `0xE919B` |
| 67 | 0x51 bytes starting at `0x22C40`, includes both elapsed cells | 3 | `0xE9123` |

## Compression and worked example

**CONFIRMED.** The native chunk writer `0xEB6A0` writes repeated
`u32 raw_size, u32 packed_size, packed_bytes[packed_size]` until the
section's input length is consumed. The raw limit is 0x2000 per chunk
(`0xEB6CC`), the accepted packed limit is 0x2090 (`0xEB716`), and the
compression call is at `0xEB70A`. LZO1X decoding succeeds on all 27
preview streams, each consuming exactly its directory span and producing
64,000 bytes. The first two autosave global sections also decode with LZO1X.

**CONFIRMED.** In the autosave with SHA-256 prefix `e2393dbe4d2b`,
u32 +0x2C is `0x189C2D`. The first preview chunk at +0x25A starts with
`00 20 00 00 60 0E 00 00`, so decode 0xE60 packed bytes to 0x2000 raw
bytes. The next chunk begins at `0x25A + 8 + 0xE60 = 0x10C2`. Eight
chunks consume the preview through +0x846E, which is the first global
section's offset. Directory entries for levels 2 and 3 both hold
`0x101F1`, giving level 2 an empty span. The level-1 block at +0x8C65 has
size 0x758C, ending at that same offset.

**UNCONFIRMED.** Several header fields, the remaining global and level
section identities, and the byte that records taking a placed item need
additional field tracing. To locate the latter, compare the decompressed
spans of saves from immediately before and after taking one item in the
same level, then match the changed offsets to the native section and
pool writer.
