# VQA movies

**What:** Westwood VQA version 2 movies, stored as IFF `FORM`/`WVQA` entries in the room and level archives (`<LEVEL>I.MIX`, the room archives, `MOVIES.MIX`, `SETUP.MIX`). Full codec notes: [lol2-vqa-v2.md](../lol2-vqa-v2.md). How scripts pick a movie: opcode 21 in the [opcode reference](../lol2-script-opcodes.md#opcode-table). Tool: `tools/lol2_vqa_v2_decode.py`; it needs NumPy, plus Pillow to write frames.

## Layout

- **Container:** an IFF `FORM` of type `WVQA`, with big-endian chunk sizes padded to even length.
- **Top-level chunks:** `VQHD`, then information chunks (`CLIP` or `CINF`, `PINF`, `FINF`, sound chunks), then one `VQFR` per frame.
- **`VQHD`:** 42 bytes, little-endian.

| `VQHD` offset | Type | Meaning |
|---|---|---|
| 0 | u16 | version (2 in every LoL2 movie) |
| 4 | u16 | frame count (equals the number of `VQFR` chunks) |
| 6 / 8 | u16 | width / height |
| 10 / 11 | u8 | block width / height |
| 12 | u8 | frames per second |
| 13 | u8 | number of parts a partial codebook is split into |

A `VQFR` holds some of:
- `CPL0`: a 768-byte palette;
- `CBFZ` or `CBF0`: a full codebook, LCW-compressed or raw;
- `CBPZ` or `CBP0`: one part of the next codebook, LCW-compressed or raw;
- `VPTZ` or `VPT0`: vector pointers, LCW-compressed or raw;
- `VPRZ` or `VPTR`: a different pointer stream, LCW-compressed or raw.

Details are in [lol2-vqa-v2.md](../lol2-vqa-v2.md#format-notes).

## Confirmed on the data

`lol2_vqa_v2_decode.py --check --data <DAT>` is a chunk census plus one sample of each layout. `--full` decodes every movie. Re-ran on 2026-11-18. CONFIRMED:
- **All movies valid:** `DAT/` holds 1,948 `WVQA` movies. Every header is valid, every frame count matches, all are version 2, and the colour count at `VQHD` offset 14 is 256 in every one.
- **The count:** 1,109 pointer-table movies pass every frame, 837 are pointer streams, and 2 pointer-table movies fail on one frame. 1,109 + 837 + 2 = 1,948. An earlier "948 decoded" figure was a classification, not a frame-by-frame pass: that class is 948 movies with a `CBPZ` or `CBP0` chunk, 4×4 blocks and byte 13 greater than 0, and it includes one `VPRZ` movie (`L4_HJI.MIX` entry 103) and the 2 open movies. The 1,109 holds 945 of that class and 164 outside it: 29 4×4 movies with byte 13 greater than 0 and no `CBPZ`/`CBP0` chunk, the 5 4×2 movies and the 130 byte-13 = 0 movies.
- **Pointer tables:** 1,111 movies have a pointer table in the header.
  - 976 are 4×4 with `VQHD` byte 13 greater than 0. 974 of them pass every frame. One of the passing movies, `POOL.MIX` entry 4, uses the raw chunks `CBF0`, `CBP0` and `VPT0` instead of the LCW forms.
  - 5 are 4×2. A high byte of `0xFF` is still a solid block. `L10_DCI.MIX` entry 40 (129 frames) is checked in full.
  - 130 have byte 13 equal to 0. 10 of them stage `CBPZ` parts, and `CINF`/`CIND` says which frame those parts become the codebook. The other 120 have a single `CBFZ` and no `CBPZ`.
- **Pointer streams:** 837 movies carry `VPRZ` and/or `VPTR`. The codebook still decompresses to whole vectors, and each `VPRZ` is LCW. The tool does not turn that stream into pixels.
- **Two frames stay open:** `L20_BBI.MIX` entry 25 frame 115, and `SPKSTON2.MIX` entry 4 frame 492. Both are relative copies inside an absolute-mode LCW stream (long back-references are distances from the start of the output; these commands are the short form). On frame 115 the command bytes are `00 00` at input 23,847: distance 0, with 30,400 bytes already written. On frame 492 the command bytes are `22 a2`: distance 674, with 564 bytes already written. Every other pointer table in those two movies finishes.
- **Game folder:** the folder next to `DAT/` holds 11 more movies (in `SETUP.MIX` and others), all version 2. This check does not re-read them.

## Worked example

`L4_HJI.MIX` entry 67 (key 0x63CF4BD8, 50,468 bytes). Its `VQHD` begins:

```
02 00  00 00  09 00  e8 00  bc 00  04  04  0f  08
```

| Bytes | Meaning |
|---|---|
| `02 00` | version 2 |
| `09 00` | 9 frames |
| `e8 00`, `bc 00` | 232 × 188 pixels |
| `04 04` | 4×4 blocks |
| `0f` | 15 frames per second |
| `08` | each codebook arrives in 8 parts |

Each frame carries one `CBPZ` part of 1,371 bytes (8 parts in all, one per frame):
- Frame 0 also holds `CBFZ` (18,481 bytes), `CPL0` (768 bytes) and `VPTZ` (2,229 bytes).
- Frame 1 holds `CBPZ` and `VPTZ` (2,467 bytes).
- Frame 2 holds `CBPZ` and `VPTZ` (2,535 bytes).

The intro movie, `MOVIES.MIX` entry 2 (`outtakes\lolg.vqa`, key 0xB3593D3C), has the header `02 00 01 00 f8 0d 80 02 90 01 04 04 0f 00`:
- 3,576 frames of 640×400 at 15 frames per second;
- 4×4 blocks;
- byte 13 is 0, so its codebooks are scheduled by `CIND` rather than split into a fixed number of parts.

`L20_BBI.MIX` entry 403 is the short scheduled example the check walks in full (312 frames). Its `CIND` entries are frame 0, size 29,591, and frame 160, size 22,860. 29,591 is the `CBFZ` on frame 0. 22,860 is the sum of the 160 `CBPZ` parts on frames 0 through 159, and those bytes are one LCW stream of 46,336 bytes (2,896 vectors of 16). On the intro, the `CIND` entry for frame 96 has size 26,274, the single `CBPZ` carried on frame 95. That part decompresses to 31,728 bytes. Frame 96's indexes fit the new book. On frame 496, 1,489 indexes fall outside the previous book, so the new book is in force on the scheduled frame and not on the frame that carried the part.

## Native short-copy runtime control

**CONFIRMED.** On the original DOS 1.30 intro, the bounded DOSBox
trace reached the pointer LCW call at `0x172838`. The first logged
call passed guest source `0x10394CB6`, destination `0x1038834C`, and
capacity `0x7D04` in that run. The call enters `0x158D58`. In the
absolute-mode path, a short copy uses length `(command >> 4) + 3`
limited by the remaining capacity and reads from `EDI − distance`
(`0x158D81–0x158DB2`). `EDI` is the next output byte and the
distance is `((command & 0x0F) << 8) | next_byte` at `0x158D94–0x158DB0`.

| Original case | VPTZ payload start in MIX | Static prediction at `0x158DB2` (not observed) |
|---|---|---|
| `L20_BBI.MIX`, key `0xD3C844E7`, entry 25 frame 115 | `+0x35202D6` | `ESI` equals `EDI` at destination base +30,400. Up to 3 bytes advance through a self-copy. |
| `SPKSTON2.MIX`, key `0x4119C826`, entry 4 frame 492 | `+0x17695E8` | `EDI` is destination base +564 and `ESI` is destination base −110. Up to 5 bytes come from that preceding range. |

**CONFIRMED.** The pointer decode at `0x17280D–0x172826` chooses
node +0's allocation or the shared pointer buffer `[context+0x6E6]`
(when `[context+0x152] & 0x02` is set), and `0x172828–0x172838` calls
`0x158D58`. Initialization allocates the shared buffer through the
context callback (op 2) and passes it to op 4 with length +0x762 at
`0x16CD31–0x16CD94`.

**CONFIRMED.** The movie openers at `0xCA798`, `0xCF5B5`, `0x112B68`
and `0x113A1B` install the same memory callback at `0x113550` through
the settings copy at `0x15DE49–0x15DE76`. Its op-2 arm at `0x11356B`
passes allocation flags zero to `0x14FBE0`. The allocator fills the
payload with zero only if those flags have mask `0x02` (`0x14FD66–0x14FD70`).
Op 4 selects `0x113588` (the fourth dword of the table at file
`LOLG.DAT+0x14A538`). This arm returns the passed pointer, first
calling `0x14FB00` when `[0x223D5]` is nonzero. The built-in fallback
installed at `0x15DE76` has an op-4 arm at `0x16D814` that also calls
`0x14FB00`. That helper passes DPMI function `0x0600`, with the pointer
and length, to interrupt `0x31` (`0x14FB22–0x14FB62`). It locks the
memory range. The callback and the decode call leave the shared buffer's existing
bytes in place.
`lol2_media_check.py --check` re-reads the callback slots and call sites.

In the shared case, frame 115 copies at distance 0, so it reads three bytes
that were already in the buffer at those positions. In the node case it
reads the contents left there when that node was last written or
reused. Frame 492 reads five bytes at offsets −110 through −106 from the
selected base. The clamp at `0x158DA3–0x158DA8` limits copy length by output
capacity, while `0x158DAE–0x158DB2` uses the computed source.

**UNCONFIRMED.** The source bytes and the active codebook in the two
specific frames are still open. The Extras menu exposed the intro and
other replays. Loading L20_BB from the copied autosave (a player save written by the game, not shipped) read the directory
of `L20_BBI.MIX` at offsets 0, 4 and 6, leaving the target payload unvisited.
The `SPKSTON2.MIX` key matches `OUTTAKES\ss-4e.vqa` by the original
[name hash](mix.md#keys). The matching item-use path starts at
`0x99EF4`. That handler's item was absent from the sampled player pool
in the loaded slot.
At the native LCW call, first match the archive read and the VPTZ
payload above. Then log `ESI`, `EDI` and `ECX` at `0x158DB2`
and the new `EDI` at `0x158DB4`. Compare the destination contents
with the resulting tile references before the colour conversion.

### Original trigger routes for the two frames

**CONFIRMED.** Scene 65 points to `bb_brth` in the original
`LOLG.DAT+0x1CF690` table slot. The hash of
`SPHERE3\L20_BB\bb_brth.vqa` is `0xD3C844E7`, the key of
`L20_BBI.MIX` entry 25. Stream 1 group 770 in
`L20_BB.MIX+0xEC61EB` plays 65 at command `+0xEC6217`.
Prop 87's kind-6 record at `+0xECD705` matches value 20.
Predicate 219 at `+0xEE1701` requires the bound object's +0x25
byte to equal 13 (`0xADDE0`, `0x66B3B`, `0x66C43`). A native
property-21 path sends value 20 at `0xB5448`.

**CONFIRMED.** Scene 42 is `ss-4e` (`LOLG.DAT+0x1CF634`).
`L9_DR.MIX+0x16265B6` plays it from stream 1 group 5448.
Prop 967's kind-6 record at `+0x162A7BE` matches value 20. Its
predicate 19 at `+0x166EA91` requires level byte 13 to equal 4
(`0x66B15`, `0x66C43`). The `ss-` movie path calls `0x95E4C`
and opens the formatted clip at `0x95ECA`. Regular handler 74
also formats clip 4 and opens it through `0xCF3C0` at `0x99F89`.
Its one original definition is row 139, identity `0x5AA2B9B5`
at `GLOBAL.MIX+0x5BAA6A`.

| Original way to get definition 139 | Witness |
|---|---|
| L5_HC floor placement 9 | `L5_HC.MIX+0x5ABD3F` (region 325, field +0x24 = 0). The 37-byte placement reader resolves its identity at `0x93FD8–0x93FE1`. |
| L9_DR item-use consumer | `L9_DR.MIX+0x162BEB6` (identity at `+0x162BEBC`): a mode-3 kind-4 record (group 14860, predicate 30) that tests for this identity. |
| L9_DR script grant | `L9_DR.MIX+0x1628C06`, stream 1 group 15238. Control 119 has the kind-4 record at `+0x162BF5E` with mode 0 and predicate 19. The command before the grant resets level byte 13 at `+0x1628C00`. The [native player grant path](../lol2-item-handlers.md) resolves the same identity. |

The 663 original placements and 876 stored opcode-3 selector-1
commands across the 15 levels have these two matches.
**UNCONFIRMED.** The exact on-screen interactions that deliver
the value-20 events and the contents of the native output history
on either target frame. Use the named groups and acquired item
as breakpoint targets for the next runtime trial; the `SPKSTON` open also needs `[0xB860]` nonzero (`0x95E60`), and the L9 route needs level byte 13 = 4 (predicate 19).

## Open

- The indexed `VPRZ`/`VPTR` command grammar is [traced here](../lol2-vqa-v2.md#pointer-streams). The remaining question is the initial destination for each transparent draw and seek.
- The two `VPTZ` frames above use the native short-copy instruction. Their prior destination contents remain open.
- How a script names a movie is a separate page: [movie scenes](../lol2-movie-scenes.md).

### Scene probes from edited copies

**CONFIRMED, edited-save run, ss-4e.** The DOS 1.30 source
`e2393dbe4d2b` supplied a level-20 slot. The edit added one
pack reference and reused free player item row 47. These are
the complete decoded byte changes within the three LZO chunks.

| Selector (source slot offset) | Decoded offsets and old → new |
|---|---|
| Global 2 (`0x8595`) | `+0x234 F8→35`, `+0x235 55→6F`, `+0x238 01→00` |
| Global 3 (`0x8854`) | `+0x05 7F→FF` |
| Global 4 (`0x8875`) | `+0x290..+0x293 00 00 00 00→20 57 2F 10` |

The original definition-table range base at slot `+0xB4`
plus `139 × 91` yields `0x10956F35`. The old pool base at
slot `+0xC8` plus `47 × 12` yields the pack reference
`0x102F5720` (map writer `0xE5C9C–0xE5D0B`).
The corresponding base-image bytes are zero. Each changed section
was one LZO chunk. Repacking changed stored spans from
703/33/590 to 751/44/634 bytes. The recipe changes the packed-length
word of each chunk, adds the running size delta to the following
global and level start offsets (`+0x18E/+0x1BA` directories),
and increases the total length at `+0x2C` by 103.
The resulting 1,612,948-byte copy has prefix `d8b54a66a8ad`.
The source version/stamp bytes and all per-level payloads stayed
byte-identical.

On restore, pack entry 4 referenced row 47, whose definition
identity was `0x5AA2B9B5` and handler byte 74. The occupied bit
was set. The original startup already made `[0xB860]` nonzero.
It is a command-line gate set at `0x14E5E0` after checks for
`-NOMIX` and `-PATH` (literals at `LOLG.DAT+0x1C5278/+0x1C527F`).
The save edit left that cell to startup. Taking the new pack
item and pressing W hit `0x99EF4`, and `0x99F64` returned
a nonnull handle after opening `SPKSTON2.MIX`. Selector 4 supplies the clip filename used by the playback
call at `0x99F89`.

The original archive read began at `SPKSTON2.MIX+0x17695E8`,
the frame-492 VPTZ payload. At `0x158DB2` the watched source
base was `0x1130E8B0` and the input pointer had advanced by
`0x225`, matching token `22 A2` at payload +0x223. Destination
base was `0x112E603C`, capacity 32,004, destination
`0x112E6270` (+564) and source `0x112E5FCE` (−110).
`ECX=5` and the source bytes were `00 00 00 00 00`.
This resolves the short-copy input in this run. The live codebook
and the final pixels for this frame remain **UNCONFIRMED**.
Capture both after `0x158DB4` in a repeated playback to tie
the five output bytes to the visible tile references.

**CONFIRMED, edited-save run, bb_brth setup.** The same source
was relocated beside prop 87. The fourteen contiguous bytes at
slot `+0x180` changed from
`26 A2 36 F2 22 1A 5C 12 16 FD 00 00 27 03` to
`00 00 6A FA 00 00 A4 10 00 00 EC FF 23 01`
(copy `5a34d0c63a97`). The original restored X −1430,
Y 4260 and heading 0 via `0xE6F17–0xE6F2A` and
`0xD025F–0xD0279`. The third header dword supplies the
heading's low word, and the observed height of −20 came from
the loaded geometry.

The loaded prop 87 at (−1496, 4268, −20), corresponding to
`L20_BB.MIX+0xED0972`, already had +0x25 = 14. Group
`0x0302` sets state 14 at `+0xEC61FF`. An earlier native
level-20 slot, `25ab2119ec3d`, has zero at the same decoded
prop state offset (level selector 18, row 87 +0x25).
**UNCONFIRMED.** Frame 115. Start from a native slot before
timer slot 12 expires, watch group `0x02E8`
(`L20_BB.MIX+0xEC61D1`), and follow its state-13 write and
value-20 dispatch to group `0x0302`. The position edit alone
left the post-scene state in place.
