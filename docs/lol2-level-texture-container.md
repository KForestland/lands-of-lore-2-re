# LoL2 Level Texture Container (.TE_)

Date: 2026-10-31

## Scope

This note describes the texture container stored in each level MIX
(`DAT/L1_DC.MIX`, `DAT/L20_BB.MIX`, ...) and the one material encoding that
is decoded today (flag `0xA9`). It is a file-format note. It does not claim
native UV orientation, scene-to-material binding, or decoding of the other
flag families.

Tool: `tools/lol2_texture_container.py` (standard library + system `liblzo2`).

## Entry name and key (PROVEN)

Each level MIX holds one texture entry named
`SPHERE<n>\<LEVEL>\<LEVEL>.TE_`. Its MIX key is the TD/RA Westwood filename
hash of that name (`ww_hash_v1` in `tools/lol2_westwood_hash.py`). Checked by
running the tool on a GOG install:

| MIX | Entry name | Key | Descriptors |
|-----|------------|-----|-------------|
| `L1_DC.MIX` | `SPHERE1\L1_DC\L1_DC.TE_` | `2972657927` | 1962 |
| `L3_DH.MIX` | `SPHERE1\L3_DH\L3_DH.TE_` | `3107535131` | 1660 |
| `L4_HJ.MIX` | `SPHERE1\L4_HJ\L4_HJ.TE_` | `3711781155` | 3649 |
| `L5_HC.MIX` | `SPHERE1\L5_HC\L5_HC.TE_` | `3777974535` | 1834 |
| `L9_DR.MIX` | `SPHERE2\L9_DR\L9_DR.TE_` | `3512559939` | 4360 |
| `L20_BB.MIX` | `SPHERE3\L20_BB\L20_BB.TE_` | `3263632273` | 4654 |

The four `SPHERE1` keys are the same keys the Godot port's level-texture
producer pins for those areas.

## LZO1X block layout (PROVEN)

```
u32 total_decoded_size
repeat until total reached:
    u32 compressed_size
    LZO1X block (decodes to 1 MiB, the last block to the remainder)
u32 0                      (trailer)
```

Decoding uses `lzo1x_decompress_safe` from the system `liblzo2` through
ctypes, so no `python-lzo` package is needed. The reader refuses
out-of-bounds sizes, short blocks and a non-zero trailer.

The decoded blob is byte-identical to the blob the game caches in
`CDCACHE.MIX`. For L20, the LZO decode of `L20_BB.MIX` gives `28,451,111`
bytes with SHA-256
`adf44e535d7b890f0f47e28266e480559fa0417094e0b5495f0775e06c41ef21`, the same
hash recorded for the named cache blob `sphere3\l20_bb\l20_bb.te_` in the
2026-09-11 cache-identity checkpoint. The L1 decode has the same length as
the cached L1 blob (`13,040,404` bytes).

## Blob header and sections

| Offset | Type | Meaning | Status |
|--------|------|---------|--------|
| `+0` | u32 | Section count (18 in L1_DC and L20_BB) | PROVEN |
| `+4` | u32 | Palette offset (`0x6A2`, 768-byte 6-bit DAC palette) | PROVEN for L20_BB; LIKELY elsewhere |
| `+8` | u32 x count | Section offsets (0 = absent) | PROVEN |

Sections used here:

| Section | Content | Status |
|---------|---------|--------|
| 2 | Material descriptors, 56 bytes each; count = (sec3 - sec2) / 56 | PROVEN |
| 3 | Material payload records, addressed by descriptor offsets | PROVEN |
| 4 | Shade rows, 256 bytes each, up to section 5 (66 rows in L1_DC and L20_BB) | PROVEN |

Other sections are not interpreted in this note.

## Material descriptor (`'<6H11I'`, 56 bytes)

| Offset | Field | Meaning | Status |
|--------|-------|---------|--------|
| `+0x00` | u16 | Numeric identifier | PROVEN (read) |
| `+0x02` | u16 | Width | PROVEN |
| `+0x04` | u16 | Height | PROVEN |
| `+0x06` | u16 | Encoding flags | PROVEN (selects format) |
| `+0x08` | u16 | Unknown (`1` in descriptor 556) | OPEN |
| `+0x0A` | u16 | Low byte = active mip count when fewer than five | LIKELY (asserted by the port's producer) |
| `+0x0C` | u32 | Name/hash candidate | OPEN |
| `+0x10` | 5 x u32 | Mip record offsets, relative to section 3 | PROVEN |
| `+0x24` | 5 x u32 | Mip record lengths | PROVEN |

The mip chain has five levels, each half the previous size. Some materials
use fewer levels; unused slots are zero.

## Flag `0xA9`: raw 8-bit pixels (PROVEN)

Each mip record is an 8-byte header and then `width * height` index bytes:

```
u16 flags (= descriptor flags, 0xA9)
u16 width
u16 height
u16 (width * height) & 0xFFFF   (0 for 256x256; not "empty")
u8  pixels[width * height]
```

Record length is always `8 + width * height`. Example, L20_BB descriptor
556 (id `2682`, 256 x 256): mip records at blob `0x113E883`, `0x114E88B`,
`0x1152893`, `0x115389B`, `0x1153CA3`, lengths `0x10008` to `0x108`.

Pixel order: the port's tools convert the bytes as column-major
(`index = x * height + y`) and that matches the reviewed cave-wall images.
That is a presentation convention; native world-space orientation is OPEN.

Colour: index -> shade row byte -> palette. The runtime witness for
descriptor 556 used shade row `0x2D`; see
[lol2-wall-material-provenance.md](lol2-wall-material-provenance.md).
The port uses row 64 (`section 4 + 64 * 256`) as its initial remap row; that
choice is a producer convention, not a traced runtime selection.

## Other flags (not decoded here)

`0xA9` is a small share of all descriptors (26 of 1962 in L1_DC, 31 of 4654
in L20_BB). Flag values seen in those two levels:

`0x0`, `0x8B`, `0x8F`, `0xA9`, `0xC3`, `0xC7`, `0xE1`, `0x143`, `0x28E`,
`0x2C6`, `0x342`, `0x1246`, `0x808B`, `0x808F`, `0x80A9`, `0x80E1`,
`0x828E`, `0x82C6`.

The tool refuses all of them except `0xA9`, including `0x80A9` (bit `0x8000`
set on the same low byte). Their payload layouts are OPEN in this repo.
The port has separate readers for some (row-span sprites, column wall
payloads), but those are not part of this note.

## Usage

```bash
python3 tools/lol2_texture_container.py info     --mix ./lol2_game/DAT/L1_DC.MIX
python3 tools/lol2_texture_container.py material --mix ./lol2_game/DAT/L20_BB.MIX --index 556
python3 tools/lol2_texture_container.py export   --mix ./lol2_game/DAT/L20_BB.MIX --index 556 --shade-row 45 --out OUT
python3 tools/lol2_texture_container.py blob     --mix ./lol2_game/DAT/L20_BB.MIX --out l20_bb.bin
```

`export` writes one RGB PNG per mip from your own files (palette at header
`+4`, optional shade row). Outputs are for local use; do not commit them.

## Open

- Native UV orientation of `0xA9` pixels.
- Meaning of descriptor `+0x08`, `+0x0C`, and the high byte of `+0x0A`.
- All non-`0xA9` encodings, including `0x80A9`.
- How the renderer picks a shade row per surface.
- Sections other than 2, 3 and 4.
