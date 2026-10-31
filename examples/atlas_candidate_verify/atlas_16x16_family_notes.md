# LOCAL.MIX Entry 1: 16x16 Compressed Family Notes

Date: 2026-04-01

This note records the first repo-safe structural pass over the
compressed `16x16` atlas records in `LOCAL.MIX` entry `1`.

Important update:

- the same entry also parses cleanly under the repo's existing
  `lol2_decompress_sphere.py` model
- section count, widths/heights, and per-record total sizes line up
  exactly across all `39` records
- that means the `16x16` range being studied here is not an isolated
  "mipmap sub-texture family" by default; it is also a known room-section
  family in the repo's Sphere model

## Scope

Records inspected:

- `3, 4, 5, 6`
- `24..38`

All of these advertise `16x16` dimensions and `format=0x80`.

## Main Result

The `16x16` compressed family is `not` one uniform "start at byte 0 and
run Format80" payload family.

Observed:

- direct `decompress_f80(payload)` does not yield `256` bytes for any of
  these records
- the later `16x16` family (`24..38`) shows a much more regular prefix
  layout than the early group (`3..6`)
- the first four payload bytes of the later family look header-like:
  two little-endian values in the rough range `103..173`
- bytes `4..15` of the later family show repeated small-value patterns,
  zero separators, and repeated `0x6? / 0x7?` bytes

## Family Split

### Early oddball group: `3..6`

Characteristics:

- payload sizes are much smaller: `37..55`
- prefixes are irregular
- two records start with:
  - `9d 00 81 4f ...`
  - `9d 00 87 4f ...`
- skip/decode probes produce only tiny outputs or unstable results

Working read:

- these may not belong to the same sub-family as the later `16x16`
  records
- they may use a different wrapper or mode

### Later structured group: `24..38`

Characteristics:

- payload sizes are larger: `75..156`
- all begin with:
  - `u16 a`
  - `u16 b`
  - then a structured-looking byte lane

Examples:

- `24`: `a3 00 97 00 04 6e 03 00 01 7c 7a 00 ...`
- `30`: `a1 00 95 00 06 7e 7f 00 02 6c 00 05 ...`
- `37`: `a0 00 9d 00 04 6c 6f 00 01 7f 7f 00 ...`

## Flag-Class Clustering

The later structured family also clusters by `flags`:

- `flag 7`: records `25, 26, 38`
- `flag 8`: records `29, 30, 32, 33, 34`
- `flag 16`: records `27, 28, 35, 36`
- singleton classes:
  - `flag 2`: record `24`
  - `flag 5`: record `31`
  - `flag 59`: record `37`

This is useful because the prefix lanes are not random. They show a
shared skeleton with flag-specific variation.

## Shared Prefix Skeleton (Later Family)

Across `24..38`, the first bytes follow a repeatable pattern:

- byte `1` = `0x00`
- byte `3` = `0x00`
- bytes `0..1` = little-endian value `a`
- bytes `2..3` = little-endian value `b`
- byte `4` is usually a small value in `{4,5,6,7}`

That gives a stable first-pass read:

- `u16 a`
- `u16 b`
- `mode-ish byte`
- then a compact descriptor / encoded lane

This is the strongest evidence so far that these are structured runtime
records rather than raw LCW streams.

## Sphere Cross-Check

`LOCAL.MIX` entry `1` does not only parse as the repo's current atlas
candidate. It also parses cleanly as the repo's existing Sphere
room-section model.

Cross-check result:

- atlas parser record count: `39`
- Sphere parser section count: `39`
- per-record:
  - offsets line up
  - widths/heights line up
  - total sizes line up

Examples:

- atlas `24`: `16x16`, `flags=2`, `total_size=166`
- Sphere `24`: `16x16`, `flags=32770`, `decoded_size=163`,
  `total_size=166`

- atlas `27`: `16x16`, `flags=16`, `total_size=85`
- Sphere `27`: `16x16`, `flags=32784`, `decoded_size=104`,
  `total_size=85`

- atlas `32`: `16x16`, `flags=8`, `total_size=160`
- Sphere `32`: `16x16`, `flags=32776`, `decoded_size=152`,
  `total_size=160`

- atlas `35`: `16x16`, `flags=16`, `total_size=104`
- Sphere `35`: `16x16`, `flags=32784`, `decoded_size=108`,
  `total_size=104`

The flag relation is also simple:

- `sphere_flags = 0x8000 | atlas_flags` for the compressed records

This materially changes the interpretation:

- the older "atlas with 39 mip/sub-textures" read is no longer the best
  first reading for records `1..38`
- those records are at least equally well explained as chained room
  sections under the existing Sphere model
- any texture claim built only from the atlas view must now clear this
  cross-check first

## Why The Earlier Skip Results Were Misleading

The later `16x16` family (`24..38`) is exactly the same range that the
Sphere decoder groups as chained `16x16` room sections.

That explains several otherwise awkward facts from the atlas-only pass:

- direct `decompress_f80` from byte `0` fails
- body-start classes vary by record
- some records look self-seeding while others look dependent
- the troublesome range is exactly a chained family under the Sphere
  decoder

In other words:

- the skip/seed behavior may be telling us about the wrong model
- it may reflect room-section chained decoding rather than texture
  mip/sub-texture decoding

## Flag-Specific Prefix Behavior

### Flag `8` family

Records:

- `29, 30, 32, 33, 34`

Observed tendencies:

- byte `4` is mostly `6` or `7`
- byte `5` is often high (`0x6A`..`0x7E`)
- bytes `8..15` often look like small tuple-like fields rather than
  compressed stream data

Examples:

- `29`: `99 00 8f 00 06 7e 7f 00 01 6f 03 00 05 00 02 7f`
- `30`: `a1 00 95 00 06 7e 7f 00 02 6c 00 05 00 01 7e 7e`
- `32`: `98 00 94 00 06 7d 7c 00 01 6d 35 00 05 00 03 7d`

2-byte tuple view of bytes `4..23`:

- `29`: `06 7e | 7f 00 | 01 6f | 03 00 | 05 00 | 02 7f | 7d 7d | 00 0d | 83 02 | 3f 5f`
- `30`: `06 7e | 7f 00 | 02 6c | 00 05 | 00 01 | 7e 7e | 7c 7d | 7d 7c | 00 02 | 3f 3f`
- `32`: `06 7d | 7c 00 | 01 6d | 35 00 | 05 00 | 03 7d | 7a 75 | 75 00 | 02 3d | 6e 00`
- `33`: `07 7c | 3f 35 | 00 06 | 00 05 | 7e 7b | 79 6a | 6e 00 | 09 87 | 04 7d | 79 7a`
- `34`: `07 6a | 03 00 | 07 00 | 07 68 | 6e 00 | 06 84 | 06 6c | 3d 6d | 10 07 | 83 5d`

Repeated pair motifs in this family:

- `6e00`
- `067e`
- `7f00`
- `0300`
- `0500`
- `0005`

Current best read:

- 2-byte chunking fits this family better than 3/4/5-byte chunking
- the lane looks fielded and pair-organized rather than bytecode-like

### Flag `16` family

Records:

- `27, 28, 35, 36`

Observed tendencies:

- byte `4` is usually `5..7`
- positions `8..15` again look tuple-like, but with a different lane
  than flag `8`
- no simple direct decode or simple skip-to-LCW decode was found

Examples:

- `27`: `68 00 8b 00 07 7c 6f 00 07 00 06 7d 7a 6d 10 07`
- `35`: `6c 00 94 00 06 3e 7d 00 08 00 06 3b 6e 7d 7e 00`

2-byte tuple view of bytes `4..23`:

- `27`: `07 7c | 6f 00 | 07 00 | 06 7d | 7a 6d | 10 07 | 82 7f | 6d 20 | 07 82 | 6e 7d`
- `28`: `07 6e | 6d 6d | 00 06 | 00 04 | 03 7c | 7e 03 | 3f 3f | 10 0a | 86 34 | 7e 7f`
- `35`: `06 3e | 7d 00 | 08 00 | 06 3b | 6e 7d | 7e 00 | 06 00 | 06 3d | 6c 34 | 34 00`
- `36`: `05 3f | 5f 7f | 03 00 | 07 00 | 05 3c | 6d 00 | 01 7c | 6e 7e | 7e 00 | 04 00`

Repeated pair motifs in this family:

- `0700`
- `6e7d`
- `7e00`

Current best read:

- this family also fits a short-pair lane better than larger tuple sizes
- pair slots appear more stable than any 3/4/5-byte framing

### Flag `7` family

Records:

- `25, 26, 38`

Observed tendencies:

- byte `5` is strikingly stable in this family (`0x6D`)
- the rest of the lane still varies enough that these are not trivially
  the same record with small deltas

Examples:

- `25`: `93 00 9e 00 05 6d 00 01 7e 7e 00 07 00 05 3e 3f`
- `26`: `6a 00 8e 00 06 6d 7d 00 08 00 06 3d 34 7b 7e 00`
- `38`: `a7 00 a1 00 04 6d 6f 00 01 7d 7b 00 07 00 04 68`

2-byte tuple view of bytes `4..23`:

- `25`: `05 6d | 00 01 | 7e 7e | 00 07 | 00 05 | 3e 3f | 00 01 | 78 79 | 7a 7b | 00 04`
- `26`: `06 6d | 7d 00 | 08 00 | 06 3d | 34 7b | 7e 00 | 06 00 | 08 83 | 6a 7a | 7b 00`
- `38`: `04 6d | 6f 00 | 01 7d | 7b 00 | 07 00 | 04 68 | 6d 00 | 02 76 | 7c 7c | 7c 7e`

Repeated pair motifs in this family:

- `0001`
- `7b00`

Current best read:

- byte `5 = 0x6d` stays strikingly stable
- the lane again looks more like a pair-coded descriptor surface than a
  direct LCW stream

## What The Prefix Probably Is Not

Based on the first pass, the first two `u16` values are probably not
simple direct statements of:

- payload size
- output size
- `256 - something` with one clean invariant

The values are correlated with payload size, but not equal to it in a
simple way.

Additional negative result:

- the first two `u16` values do `not` behave like plain payload length
  fields
- they do `not` match:
  - payload size
  - pixel count
  - `payload_size - const`
  - `pixel_count - const`
  with one stable invariant across the later family

So the current best read is:

- they are likely selectors / offsets / wrapped-size fields
- not simple "compressed bytes" and "decompressed bytes"

## Skip-Probe Result

Using the repo's current `decompress_f80` helper:

- no `16x16` record produced an exact `256`-byte decode under direct
  start-at-zero decoding
- no `16x16` record produced an exact `256`-byte decode under the simple
  `skip 0..15` probe either

This matters because it means the later family is not solved by
"skip a tiny header and run the current LCW helper unchanged".

## Current Best Structural Read

The later `16x16` family most likely has:

1. a short fixed header beginning with two little-endian fields
2. one or more mode / flag / tuple lanes after that
3. an encoded body that is not currently being entered correctly by the
   repo's direct `decompress_f80` helper

That is consistent with:

- serialized engine-native records
- per-record wrapper metadata
- small sub-texture / mip-like runtime surfaces

and inconsistent with:

- a plain standalone image codec beginning at byte `0`

## Tuple Boundary Result

Bytes `4..23` were compared under:

- 2-byte chunking
- 3-byte chunking
- 4-byte chunking
- 5-byte chunking

Current best fit:

- `2-byte chunking`

Reason:

- repeated pair motifs recur within flag families
- zero-separated pair slots appear stable
- 3/4/5-byte chunking looks substantially less regular

This does not prove the lane is literally an array of `u16` fields, but
it strongly suggests the structure is organized around short field slots
rather than free-form compressed bytes.

## Positional Slot Read (Bytes 4..23)

Treating bytes `4..23` as ten 2-byte slots gives a useful first-pass
 field-role view.

### Strongest positional candidates

#### Slot 0 (`bytes 4..5`)

This is the strongest mode/class candidate.

Why:

- present and non-zero in all later-family records
- low byte is small and usually in `4..7`
- high byte is often in a constrained higher range (`0x3e`, `0x6a`,
  `0x6d`, `0x7c`, `0x7e`, etc.)
- the pattern varies by flag family but stays structurally similar

Best read:

- a packed pair such as `(mode, class/index)` or `(variant, family)`

#### Slot 1 (`bytes 6..7`)

This is the strongest optional/selector candidate.

Why:

- high byte is zero in `11 / 15` later-family records
- values are often forms like:
  - `7f00`
  - `7d00`
  - `6f00`
  - `0300`
- but a few records hold non-zero-high-byte forms such as `3f35`,
  `5f7f`, `6d6d`

Best read:

- likely a selector or small value with frequent zero-extension
- not raw stream data

#### Slots 2-4 (`bytes 8..13`)

These look like the densest control/descriptor lane.

Why:

- they contain the highest concentration of low-value pairs and
  zero-separated forms
- examples:
  - `0006`
  - `0005`
  - `0500`
  - `0700`
  - `0800`
  - `0001`
  - `0002`

Best read:

- small counters / indices / flags / table selectors

### Weaker positional candidates

#### Slots 5-9 (`bytes 14..23`)

These look more mixed.

Why:

- fewer zero-extended forms
- more medium/high-value pairs
- more likely transition into encoded-body or body-adjacent descriptor
  data

Examples:

- `7e7e`, `7d7d`, `7c7d`
- `3f5f`, `3f3f`
- `6e7d`, `6e7e`
- `835d`, `8634`, `827f`

Best read:

- either late descriptor tuples or the beginning of the wrapped body

## Zero-Byte Heuristic

Across the later family:

- slot `1` has a zero high-byte in `11 / 15` records
- slots `3`, `4`, `6`, and `9` also show frequent zero high-bytes
- slot `0` never has a zero high-byte or low-byte

This reinforces:

- slot `0` is likely header-class metadata
- slots `1..4` are the most promising compact-field area
- later slots are progressively less "header-like"

## Best Current Field Hypothesis

For the later `16x16` family:

- bytes `0..3`: wrapper/header fields (`u16 a`, `u16 b`)
- slot `0`: packed mode/class field
- slots `1..4`: short descriptor/control fields
- slots `5..9`: late descriptor or early body-transition lane

This is still a hypothesis, but it is much tighter than:

- "unknown compressed bytes from byte 4 onward"

## Bridge To The Tiny Exact-Hit Records

Three smaller compressed records outside the `16x16` family produced
exact output-size matches after skipping a short prefix:

- record `2` (`32x5`): exact at `skip=2`
- record `16` (`8x8`): exact at `skip=10`
- record `18` (`8x6`): exact at `skip=8`

These do not all behave the same, but they still support the same
high-level model:

- descriptor/wrapper bytes first
- body starts later
- current repo `decompress_f80` only works when entered near the true
  body start

### Record `2` (`32x5`, flag `0`)

Payload:

- `a0 00 85 4f 4f 39 4f 58 ff 9b 00 00`

Exact decode:

- start at byte `2`
- decoded size = `160`

But the decoded output is mostly zeros:

- `155 / 160` bytes are zero
- only `5` non-zero bytes

Read:

- exact output size alone is not proof of a meaningful image

### Record `16` (`8x8`, flag `0`, fmt byte `0x4f`)

Payload begins:

- `42 00 83 00 02 4f 20 01 84 00 01 4f 39 20 01 83 ...`

Exact decode:

- start at byte `10`
- decoded size = `64`

Decoded result:

- all `64` bytes are zero

Read:

- strong evidence of wrapper/prefix bytes
- but again, exact size is not enough to claim visual success

### Record `18` (`8x6`, flag `1`)

Payload begins:

- `30 00 81 4f 20 01 8f 39 15 16 17 3b 39 19 18 33 ...`

Exact decode:

- start at byte `8`
- decoded size = `48`

Decoded result:

- sparse but non-trivial:
  - `37 / 48` bytes zero
  - `8` unique byte values

Read:

- this is the best tiny witness that "skip into body" can produce
  plausible structured output, not just size matches

## Why This Matters

The tiny exact-hit records do not prove the `16x16` family decode path.

They do support one important general conclusion:

- exact body start is record-dependent
- there is a real wrapper/prefix before the compressed body in at least
  some compressed atlas records

That is consistent with the later `16x16` slot model and inconsistent
with the idea that the compressed atlas records are plain LCW streams
starting at byte `0`.

## Decode-Behavior Buckets (Later `16x16` Family)

Testing candidate body starts at even offsets:

- `0`
- `2`
- `4`
- `6`
- `8`
- `10`
- `12`

does not yield one universal rule, but it does produce stable
subfamilies.

### Bucket A: `best skip = 0`

Records:

- `24` (flag `2`)
- `29` (flag `8`)
- `30` (flag `8`)
- `31` (flag `5`)
- `37` (flag `59`)

Common tendency:

- decode size is largest at start `0`
- decode size generally shrinks as skip increases

Strongest shared prefix tendency:

- slot `0` often `067e` or `04xx`
- slot `1` often `7f00` or another zero-high-byte pair

Working read:

- for this bucket, the body may begin very early, possibly immediately
  after the first wrapper fields

### Bucket B: `best skip = 2`

Records:

- `25` only

This looks like a singleton micro-class for now.

### Bucket C: `best skip = 4`

Records:

- `26` (flag `7`)
- `27` (flag `16`)
- `32` (flag `8`)
- `34` (flag `8`)
- `35` (flag `16`)
- `36` (flag `16`)
- `38` (flag `7`)

Common tendency:

- decode size jumps sharply at `skip 4`
- after `skip 4`, decode size usually declines gradually as skip
  increases further

This is the strongest current body-start bucket.

Working read:

- these records likely have a 4-byte wrapper after the outer
  texture-record payload start
- the wrapped body or its next descriptor stage probably begins at
  offset `4`

### Skip-4 Class Signature

Records in this class:

- `26` (flag `7`)
- `27` (flag `16`)
- `32` (flag `8`)
- `34` (flag `8`)
- `35` (flag `16`)
- `36` (flag `16`)
- `38` (flag `7`)

Shared surface properties:

- payload bytes `0..3` are always:
  - `u16 a`
  - `u16 b`
- bytes `1` and `3` are always `0x00`
- bytes `4..` can be fed directly to the repo `decompress_f80` helper
  and give the best decode length for this class

Observed decode lengths from `skip 4`:

- `26`: `171`
- `27`: `120`
- `32`: `102`
- `34`: `84`
- `35`: `100`
- `36`: `130`
- `38`: `105`

This does not prove these are final correct image outputs, but it does
show that "body begins at offset 4" is a real structural class, not a
random coincidence.

### Skip-4 Class Slot Tendencies

For the `skip 4` class:

- slot `0` (`bytes 4..5`) is always a non-zero pair with low byte in
  `{4,5,6,7}`
- slot `1` (`bytes 6..7`) usually has high byte `0x00` or the pair
  belongs to a small constrained set:
  - `7d00`
  - `6f00`
  - `7c00`
  - `0300`
  - `5f7f`
- slot `2` (`bytes 8..9`) is strongly low-valued:
  - `0800`
  - `0700`
  - `016d`
  - `0300`
  - `017d`

Best read:

- the first 4 bytes are wrapper
- the body starts at byte `4`
- but the body itself still begins with a compact internal control lane,
  not immediately obvious final-pixel commands

### Skip-4 Decoded-Surface Check

The `skip 4` class was then tested by taking the decoded outputs as raw
surfaces.

Current result:

- some records decode to sparse but non-trivial data
- several records decode to all-zero surfaces

Examples:

- record `27` (`flag 16`) at `skip 4`:
  - decoded length `120`
  - `17` unique byte values
  - not all zero
  - rendered examples saved as:
    - `idx27_w10x12.png`
    - `idx27_w8x15.png`

- record `35` (`flag 16`) at `skip 4`:
  - decoded length `100`
  - all bytes zero

- record `36` (`flag 16`) at `skip 4`:
  - decoded length `130`
  - all bytes zero

Implication:

- `skip 4` is a real structural body-start class
- but "best decode length at skip 4" still does not mean
  "final meaningful pixel data"
- at least some records in this class require one more layer of
  interpretation even after entering at the right structural offset

## Zero-Fill Versus Sparse Skip-4 Outputs

Comparing the `flag 16` skip-4 records sharpened the picture:

- record `27` (`flag 16`) gives sparse non-zero output
- records `35` and `36` (`flag 16`) decode to all-zero output

### Record `27`

- decoded length: `120`
- first non-zero output byte appears at offset `32`
- decoded stream contains repeated sparse motifs like:
  - `7f 6d`
  - `6e 7d`
  - `7d 7f`
  - `5e 69`
  - `5f 3f`

This looks like structured low-density data, not random garbage.

### Records `35` and `36`

- decoded lengths: `100`, `130`
- all output bytes are zero

This matters because it suggests that:

- the repo helper is reaching a structurally valid body for these
  records
- but the body is not yet the final pixel plane
- some additional mode/table/context is still missing for at least part
  of the skip-4 class

## First Non-Zero Offset Check

Across the skip-4 class:

- `26`: first non-zero output at decoded offset `105`
- `27`: first non-zero output at decoded offset `32`
- `34`: first non-zero output at decoded offset `37`
- `32`, `35`, `36`, `38`: no non-zero output at all

Best read:

- even inside the skip-4 class, there are at least two subcases:
  - sparse-data decodes
  - pure zero-fill decodes

This strengthens the case that one more interpretation layer exists
after the current `decompress_f80` stage.

### Bucket D: `best skip = 12`

Records:

- `28` (flag `16`)
- `33` (flag `8`)

Common tendency:

- almost everything before `12` decodes poorly
- decode size jumps only at `12`

Working read:

- these are likely the strongest evidence for an extended descriptor lane
  before the actual compressed body

## What This Changes

The later `16x16` family should not be treated as one decode family.

Current better model:

- one shared wrapper vocabulary
- multiple body-start classes
- likely selected by some combination of:
  - flag class
  - slot `0`
  - slot `1`
  - early slot pattern

## Best Current Body-Start Read

Safe current statement:

- body-start is `record-class-specific`
- `skip 4` is the strongest recurring candidate for a real body-start
  class
- `skip 0` and `skip 12` are also real classes inside the later family
- there is no support for one universal skip rule across all compressed
  atlas records

## Tail Observations

The record tails also show repeated byte motifs in some flag classes.

Examples:

- flag `8` family often ends with forms like:
  - `... 0d 84 07 03 00`
  - `... 84 07 7e 00`
- flag `16` family includes endings like:
  - `... 84 07 03 00`
  - `... 81 7e 10 06 81`

These are not yet decoded, but they reinforce the same read:

- the body is likely a wrapped command/tuple stream
- not a plain byte-aligned LCW payload beginning immediately after the
  first few bytes

## Leading `u16` Correlation Check

For the later family, the first two fields (`a`, `b`) were compared
against payload length:

- `a - payload_size` ranges roughly from `2` to `29`
- `b - payload_size` ranges roughly from `-58` to `58`
- `b - a` changes sign across the family

That rules out a simple universal interpretation like:

- `a = compressed_size`
- `b = decompressed_size`

at least for the raw payload slice currently being tested.

## What Looks Real

The later family is still clearly structured:

- byte `1` is always `0x00` in the later family
- byte `3` is always `0x00` in the later family
- byte `4` is often a small mode-like value (`4`, `5`, `6`, `7`)
- later bytes contain repeated palette-looking low values and zero
  delimiters

That strongly suggests:

- `prefix/header fields`
- followed by a compact encoded body

rather than random compressed noise.

## Best Current Read

For the repo-first atlas candidate:

- texture `0` is a strong reproducible raw witness
- some tiny compressed records (`32x5`, `8x8`, `8x6`) can hit exact
  output sizes after skipping a short prefix
- the important `16x16` family still needs wrapper/header
  interpretation before any decode claim is safe

## Skip-4 Seeded Decode Check

The strongest recurring body-start class in the later `16x16` family is
still `skip 4`.

Records in that class:

- self-seeding / sparse-output: `26`, `27`, `34`
- dependent / zero-fill under current helper: `32`, `35`, `36`, `38`

Direct `skip 4` decode using the repo's current `decompress_f80` helper
produces:

- `26`: `172` bytes, sparse non-zero output
- `27`: `121` bytes, sparse non-zero output
- `34`: `84` bytes, sparse non-zero output
- `32`: `102` bytes, all zero
- `35`: `100` bytes, all zero
- `36`: `130` bytes, all zero
- `38`: `105` bytes, all zero

### Seeded Result

The zero-fill records are not dead streams. They wake up if the output
buffer is pre-seeded with a non-zero dictionary byte before decode.

Minimal witness:

- a one-byte seed `b"\\x01"` at dictionary position `0` turns every
  dependent record non-zero
- a one-byte seed `b"\\xff"` does the same
- a tiny ramp seed produces repeated ramp values in the decoded output
- previously decoded `skip 4` outputs from `26`, `27`, or `34` do
  **not** wake the dependent records

This is the cleanest evidence so far that the zero-fill records are
`dictionary/state dependent`, not merely "wrong skip" failures.

Important caveat:

- this wake-up behavior happens under the repo's current helper because
  its short-backref path clamps negative source positions to output
  index `0`
- when the same streams are traced without that clamp, they do not
  naturally reference a small pre-seeded `0..15` dictionary window

So the seeded result should be read carefully:

- it proves the current helper is missing some condition needed by the
  dependent records
- but it does **not** yet prove that the real engine uses a literal
  one-byte seed or a tiny fixed dictionary

### Command-Mix Split

Tracing the `skip 4` bodies shows a clean split:

- `26`: `28` short backrefs, `11` literal commands
- `27`: `18` short backrefs, `10` literal commands
- `34`: `16` short backrefs, `6` literal commands, then `end0`
- `32`: `16` short backrefs, then `end0`
- `35`: `17` short backrefs, then `end0`
- `36`: `22` short backrefs, then `end0`
- `38`: `16` short backrefs, then `end0`

First literal emergence:

- `27`: step `7`
- `34`: step `10`
- `26`: step `19`
- `32`, `35`, `36`, `38`: no literal before termination

That means the self-seeding records bootstrap themselves with literal
bytes, while the dependent records never do. Under the current helper,
they only copy from already-decoded output state.

### Why The Seed Test Matters

The early backrefs in the dependent records all point before the current
output start, so the current helper collapses them toward dictionary
position `0`.

That makes the best current repo-safe read:

- `skip 4` is a real body-start class
- some records in that class are standalone enough to self-seed
- others require either:
  - preinitialized decode state
  - another pre-stage before the current helper applies
  - or a correction to the current helper's handling of early backrefs

This fits the broader "serialized engine-native runtime record" model
better than a plain standalone-image model.

## Best Next Step

Focus on the later structured `16x16` family (`24..38`) only.

Recommended next pass:

1. stay on the `skip 4` class only
2. compare self-seeding records (`26`, `27`, `34`) against dependent
   records (`32`, `35`, `36`, `38`)
3. test whether the dependent records expect a fixed dictionary seed,
   previous surface state, or a palette/background prefill
4. only after that, broaden back out to `skip 0` / `skip 12` classes
