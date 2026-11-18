# Native texture cache initialization

Addresses use the [DOS 1.30 convention](lol2-executable-tables.md).
File positions are absolute in the named file.

## Seeds and reset

**CONFIRMED.** On the list-reset branch, the initializer passes
`cdcache.ls_` and `cdcache.lst` to `0x61BA0`
(`0x11996E–0x119983`). That helper opens the source for reading and the
destination for writing, then copies the source in chunks of up to
0xFFFF bytes (`0x61CB0–0x61D7C`). The shipped list is 4,008 bytes.
The game reads 21 eight-byte index slots from offset zero, seeks to the
first dword of the selected slot and reads a 256-byte record
(`0x119A37–0x119A88`). Those slots name 15 distinct records in the seed.
For example, `CDCACHE.LS_+0xA8` is the L1_DC row. It names the `.tex`
resource at record +8 and holds state -1 at +0xD8.
See [MIX layout and files](formats/mix.md).

**CONFIRMED.** When resetting the archive at
`0x119AF5–0x119B36`, the game queries the length of `cachebak.mix`,
reads that many bytes and sends them to the writable cache handle.
The shipped 131 bytes start with a 66-byte ordinary MIX header and
directory. The game can extend the target in 64,000-byte writes from
`0x119BB8–0x119BF0`. It reopens the archive, seeks to the opened MIX
object's data position and reads a marker. On a mismatch it seeks
back and writes dword `0xF1E2D3C4`
(`0x119C38–0x119CFC`).

## The allocator directory starts after the marker

**CONFIRMED.** The post-marker cursor becomes the allocator's index
position (`0x119D08–0x119D35 → 0x116C94`,
`0x116D16–0x116D2F`). It reads or writes 0x1388 bytes there
(`0x116D45–0x116D55`, `0x116DF9–0x116E12`), and the
operations walk this memory in 25-byte strides (`0x116FFD–0x117005`).
That is 200 rows. Reset places the first free span
at the index position plus 0x1388 (`0x116D83–0x116DB2`).
When the ordinary MIX data position is 66, the marker is at
66, the first row at 70, and the initial span at 5,070.

| Row offset | Meaning and source |
|---|---|
| +0x00 u32 | Absolute payload position, compared at `0x116FB8` and returned at `0x1170A1` |
| +0x04 u32 | Span size, tested and split at `0x1170CD–0x1170E3` |
| +0x08 u16 | Occupancy, tested at `0x116FC0`, set to 1 at `0x1170F8` |
| +0x0A u16 | Generation selector, copied from `[0xE3538]` at `0x117102–0x11710B`. A value of 1 bypasses the stamp comparison at `0x116FDA–0x116FF3` |
| +0x0C u32 | Resource key, written at `0x1170DB` and compared at `0x116FCA–0x116FD6` |
| +0x10 u32 | Timestamp from the counter call `0x15F800` at `0x117112–0x11711E`; compared at `0x117303–0x117316` |
| +0x14 u8 | Eviction exclusion, tested at `0x1172F5` and set by the position lookup at `0x116F82–0x116F91` |
| +0x15 u32 | Stamp from `[0xD9394 + 4*selector]` at `0x117126–0x117137`, compared at `0x116FED` |

**OBSERVED (one run's written copy).** In one game-written `CDCACHE.MIX` (90,037,470 bytes,
SHA-256 of bytes 0–5069 starts `0e5ecda400324d0a`), the first
row at +0x46 is position 5,070, size 13,040,404, state 1,
selector 1, key `0xB60E90A4`. The second row at +0x5F is
position 13,045,474, size 28,451,111, state 1, selector 20,
key `0x8AD422E2`. The same positions and lengths are in
that run's `CDCACHE.LST+0xA8` and `+0xEA8`, at their
record offsets +0xE8 and +0xDC respectively. They correspond to
L1_DC and L20_BB. The free span starts at 41,496,585
(row at +0x78, occupancy zero). Another run can allocate
the banks in a different order.

**CONFIRMED (shipped file).** The shipped `CDCACHE.LS_` `l1_dc` record holds position 5,066 at +0xE8: 66 + 0x1388, without the 4-byte marker the code now adds (5,070). The shipped list carries older values.

## From a texture request to the cache

**CONFIRMED.** For a requested bank, the cache opens the packed input,
reads its first dword and stores that size at list record +0xDC and
+0xE0. It allocates a span by calling `0x11706C`, saves the returned
position at +0xE8 and seeks there before decoding the blocks
(`0x1192F8–0x119358`, `0x1193C4–0x119405`).
The input has the [level texture wrapper](lol2-level-texture-container.md#lzo1x-block-layout-proven).

**CONFIRMED.** At shutdown, `0x119D95` passes the current
slot to `0x119E08`. That routine opens `cdcache.lst` and
`temp.cd`, preserves the other populated 256-byte records, writes
the live one at the selected slot through `0x119F62`, and
writes the rebuilt 0xA8-byte index at `0x119F84`. It then
copies `temp.cd` over `cdcache.lst` at `0x119FA8 → 0x61BA0`.
The filenames are the strings in `LOLG.DAT+0x1C499C`,
`+0x1C49A4`, `+0x1C49B0` and `+0x1C49BC`.

**UNCONFIRMED.** The shipped list includes older lengths and
positions, for example the L20_BB size 27,801,780 at
`CDCACHE.LS_+0xF84`. A corresponding original cache from the
shipped build would settle those older values.
