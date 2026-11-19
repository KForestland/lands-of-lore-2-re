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

## Shipped lengths compared to shipped banks

**CONFIRMED.** `CACHEBAK.MIX+0x00` declares five members and a
65-byte body. Each member is 13 bytes (directory length dwords at
`+0x0E + 12*i`), and all five are the same short text line. Their spans partition the complete body at +0x42.
The backup has no allocator table or level texture bank. The retail
initializer overwrites this position with the marker and then inserts
the allocator, which explains the four-byte difference between the
first seed position and the native reset position (5,066 = 66 + 0x1388
and 5,070 = 70 + 0x1388 are consistent with that).

**CONFIRMED.** Each shipped list name (record +8, convert the final
`.tex` to `.te_`) identifies one original MIX member through its
archive hash. Its first dword is the size that `0x11931D–0x119349`
uses for allocation. Compare it to `CDCACHE.LS_` record +0xDC.
All 15 matching MIX members in this edition start at absolute offset
`0x2A` (the first data byte of each three-entry level MIX). In the
list, state +0xD8 is −1 throughout. Position +0xE8 is 5,066 on
L1_DC and 0xFFFFFFFF on the other 14 records. Length +0xE0
duplicates +0xDC in those 14 and is zero on L1_DC.

| Level | Seed record offset | Seed size at +0xDC | Shipped bank dword at MIX +0x2A | Bank dword minus seed |
|---|---:|---:|---:|---:|
| L1_DC | `0xA8` | 13,040,404 | 13,040,404 | +0 |
| L3_DH | `0x1A8` | 10,825,806 | 10,799,733 | -26,073 |
| L4_HJ | `0x2A8` | 23,198,828 | 23,232,234 | +33,406 |
| L5_HC | `0x3A8` | 10,680,077 | 11,008,401 | +328,324 |
| L7_DH | `0x4A8` | 8,971,396 | 9,062,941 | +91,545 |
| L8_SJ | `0x5A8` | 21,947,290 | 22,014,842 | +67,552 |
| L9_DR | `0x6A8` | 38,890,424 | 38,890,424 | +0 |
| L10_DC | `0x7A8` | 23,169,487 | 23,192,086 | +22,599 |
| L12_CM | `0x8A8` | 15,818,686 | 15,854,483 | +35,797 |
| L13_RC | `0x9A8` | 14,037,279 | 14,087,322 | +50,043 |
| L14_HT | `0xAA8` | 23,639,037 | 23,639,037 | +0 |
| L16_CA | `0xBA8` | 39,420,101 | 39,420,119 | +18 |
| L17_HC | `0xCA8` | 8,342,669 | 8,507,280 | +164,611 |
| L19_BC | `0xDA8` | 11,211,703 | 11,236,800 | +25,097 |
| L20_BB | `0xEA8` | 27,801,780 | 28,451,111 | +649,331 |

Three lengths match and 12 differ. The native loader replaces the
old values with the bank's first dword (its decoded size) on the unpack path.
The full comparison is repeatable with
`python3 tools/lol2_cache_seed.py --check --data /path/to/DAT` (part of `check_all.py`).

**CONFIRMED.** This executable holds the version and date strings
`DOS 1.30` at `LOLG.DAT+0x1C4714` and `Dec 03 1997` then `17:51:02` at
`LOLG.DAT+0x1C4749`. They are string literals reached through the data
pointers at `0xEE54`, `0xEE5C` and `0xEE60`, not a header field (the LE
header has no time stamp). `0xB9BD0` loads the `DOS 1.30` pointer and
passes it to `0x159EDC`. `0x60AD5` and `0x60B80` copy the date and the
time string into the buffer at `0x21A9C` and read them with the string
helpers at `0x153B96` and `0x153BB9`. The program holds other dates:
`VQA playback 4.2 (Sep 05 1997 13:11:59)` at file `0x1C5AC8` and the
DOS/4G `Apr 03 1996 15:01:07` at file `0x33364`, so `Dec 03 1997` is
not the date of every part of the program. The seed's
only printable runs of four or more bytes are the 15 level names, in
that order, and the seed stores no date. Each of the 15 banks' first
decoded block names `PROJECTS\LOL_2\ART\WALLSETS\` plus an art folder
and `PROJECTS\LOL_2\LEVED\` plus a leved folder. The art folder in
`L3_DH` is `SPHERE1\L2&3` and its leved folder is `sphere1\l3_dh`.
The other fourteen art folders match the bank stem (`SPHERE1\L1_DC`,
`SPHERE2\L8_SJ`, `SPHERE3\L16_CA` and the rest). Drive-letter case and
the case of `LEVED` vary. Those names identify the export tree of the
shipped banks. The twelve seed sizes are not a version field in the
executable. `lol2_cache_seed.py --check` re-reads the version and date strings with their pointers and readers, the
fifteen seed strings and the fifteen folder pairs.

**UNCONFIRMED.** The exact build or original members that produced
the 12 differing values, and what the date strings record (which
build step or source module they date). The version and date strings
and the folder names above identify this executable and the shipped
banks. They do not name the older
sizes. The two supplied seed files and all 15 named shipped banks were
compared. To settle provenance, compare another genuine edition's
`.te_` first dwords and its installer seed rows by the same name hash.
A new writable cache records the current bank sizes.

## Close-out

### Q20

**What was measured.** The first decoded block of the `L3_DH.MIX` texture bank is 1,048,576 bytes and begins `12 00 00 00 A2 06 00 00 F3 50 01 00 F3 50 01 00`. Inside that block the art path starts at offset 153 and the leved path starts at offset 410.

**What was tried.** This decode is the same first block the page already uses for the folder names. The page already records the fifteen seed-to-bank size deltas and the version strings in `LOLG.DAT`.

**What would settle it.** Compare the same named first dwords, and the installer seed rows by the same name hash, in an earlier original edition.
