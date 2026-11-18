# LoL2 native save slots

This page describes the 1.30 DOS writer, using [executable analysis addresses](lol2-executable-tables.md).
File offsets in a save are independent of those addresses. Integers are
little-endian. The fixed header, directory bounds and compressed preview were
checked on 27 slots written by the original program, including the autosave
(a player's own saves in the game's `SAVEGAME` folder, not shipped game data;
another player's saves reproduce the layout, not these exact counts),
with SHA-256 prefix `e2393dbe4d2b`. These are file and
code observations.

Run [`lol2_save_header.py`](../tools/lol2_save_header.py) on a slot file to list preview, global and level offsets and lengths. It reads the header and writes its report to standard output.

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
| `0x038–0x043` | 3 u32 | Global data, spell data and sound data version stamps. The writer copies cells `0xD938C`, `0xD9390`, `0xD9394` at `0xE7738–0xE7758`, and the reader compares them at `0xEB857–0xEB87A`. |
| `0x044–0x093` | 20 u32 | Per-level version stamp table from `0xD9398`, copied at `0xE775E–0xE7783`. The initializer appends `.ver` (`LOLG.DAT+0x1C414A`) to the level name and reads four bytes per file (`0xE5B7D–0xE5C34`). The level path is the prefix at object-5 `0x23230`, then the level name, then `.ver`. A missing `.VER` file stores 0xFFFFFFFF (`0xE5AC2`, `0xE5B09`, `0xE5B50`, `0xE5B66`). |
| `0x094` | u32 | Zeroed by the writer at `0xE777D`. Further interpretation is **UNCONFIRMED**. |
| `0x098–0x0A7` | 4 u32 | Preview descriptor, filled from the writer's argument at `0xE789B–0xE78E3`: `0x098` = 1 (meaning **UNCONFIRMED**); `0x09C`/`0x0A0` = preview width and height (320×200); `0x0A4` = preview data offset (0x25A). |
| `0x0A8–0x177` | 26 u32 bases, 26 u32 lengths | Address-range map used for pointer conversion, populated by `0xE5C48`, passed to the save adjustment routine at `0xE7A15`. |
| `0x178–0x17B` | u32 | Address-map adjustment status at map +0xD0 (`0xE7A15–0xE7A1C`, `0xE9207`, `0xEB30D`). |
| `0x17C` | s32 | Active level ID from byte `[0x23331]` at `0xE7887–0xE7895`. |
| `0x180`, `0x184`, `0x188` | s32 each | Player position dwords re-applied by the writer at `0xE7D3F–0xE7D4F`. |
| `0x18C` | u16 | Region index, or 0xFFFF for a null region. The writer computes a 44-byte row pointer at `0xE7D04–0xE7D3A`. |
| `0x18E–0x1B9` | 11 u32 | Absolute offsets for global sections 0–10, written at `0xE794F`. |
| `0x1BA–0x209` | 20 u32 | Absolute offsets for levels 1–20, written at `0xE7B92`. |

**CONFIRMED.** The initializer reads the three global stamps from file
offset zero of `GLOBAL\\GLOBAL.VER`, `GLOBAL\\SPELL.VER` and
`GLOBAL\\SOUNDS.VER` (`0xE5A85–0xE5B50`). The path strings are at
`LOLG.DAT+0x1CF8F0`, `+0x1CF904` and `+0x1CF918`. In `GLOBAL.MIX`
the entries at `0x588E57`, `0x588E5B` and `0x588E5F` contain 0, 0 and
0x3232 respectively, matching slots +0x38, +0x3C and +0x40 in all 27 files.

**CONFIRMED.** Global section 0 takes 0x22E bytes from the player object
at `0x22574` (`0xE86A3`). Section 1 takes the shared script byte array
from `[0x26E58]`, length `[0x26E60]` (`0xE86BD`). Section 2 takes
elements from the pool whose header pointer is `[0x96918]`, writing
count×stride (`0xE86DC–0xE86F6`). The writer can XOR global sections
against a base file (`0xE795E–0xE79FA`), normalize pointer fields
(`0xE7A1C`), and compress sections with flag 4 (`0xE7A3E`).
The global dispatch table is at `LOLG.DAT+0x11F64C`.
See [save section descriptors](lol2-save-sections.md) for all 11 global
and 68 level selector arms.

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
| `0x0D4–0x0D7` | u32 | Address-map adjustment status at map +0xD0 when the pointer helper runs (`0xE827E–0xE8283`, `0xE9719`, `0xEB30D`). The origin of `0xFF00FFFF` in short blocks is **UNCONFIRMED**. |
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
| 25 | Placed item objects, 0x3C bytes, pool-cell `0x968F8` | 7 | `0xE8CCD`, stride at `0x9D30D` |
| 31, 32 | Non-player item instances and allocation bitmap, pool-cell `0x9691C` | 7 | `0xE8D93`, `0xE8DB8`, stride at `0x9D2D9` |
| 61, 63 | 12-byte timer list header and parallel object list header | 3 | `0xE9142`, `0xE9180` |
| 62, 64 | Timer list pointer arrays, lengths `[0xB7DA8]*4` and `[0xB7DB4]*4` | 1 | `0xE915D`, `0xE919B` |
| 67 | 0x51 bytes starting at `0x22C40`, includes both elapsed cells | 3 | `0xE9123` |

**CONFIRMED.** The pointer helper `0xEB2C8` copies the field directly if
the source map is absent and writes zero for a null pointer. For other
pointers `p`, it scans the source map for `old_base <= p < old_base + length`.
A match stores `p + new_base - old_base`. An unmapped pointer sets
destination map +0xD0 to 1 and returns zero (`0xEB2D8–0xEB33C`). The
global and level adjusters clear the status at entry and test it before
returning (`0xE9207`, `0xE93F7`, `0xE9719`, `0xE97AC`).

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

The [save section descriptors](lol2-save-sections.md#items-and-occupancy)
trace item pickup through the placed-object row and the recipient's saved
item pool. A [controlled original save pair](lol2-save-sections.md#controlled-pickup-in-l20_bb)
identifies the changed placement row and player occupancy bit.
