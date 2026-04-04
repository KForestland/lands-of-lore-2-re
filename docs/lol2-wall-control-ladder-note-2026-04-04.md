# LoL2 Wall Control Ladder Note

Date: 2026-04-04

## Scope

This note captures the current wall-control runtime picture from the
April 2026 trace pass. It is narrower and more runtime-grounded than the
older atlas/source guesses. It does not claim full wall-source closure.

## Proven Ladder

The strongest repeated ladder now is:

- `0x103937A3 -> 0x10393A2D`
- `0x10393A2D -> 0x10393C3D`
- `0x10393C3D -> 0x10393EC5`
- `0x10393EC5 -> 0x10394ACD`
- `0x10394ACD -> 0x10394FC4`

Captured producer endpoints:

- `7D87` on `0x10393A2D -> 0x10393C3D`
- `7DF2` on `0x10393C3D -> 0x10393EC5`
- `7DF2` on `0x10393EC5 -> 0x10394ACD`
- `7DF2` on `0x10394ACD -> 0x10394FC4`

The decoder frame at `0x10167D3F` is generic producer grammar, not
bespoke wall-tail code.

## Stable External Builder Stream

Across multiple traces, the producer calls share the same external
builder-side source stream:

- `arg_dword0 = 0x106AB520`

The captured `builder_source_dump` bytes for `0x106AB520` are stable
across repeated wall-control traces and match `DAT\\MOVIES.MIX @ 77622`
byte-for-byte over the captured `512`-byte window.

This has been verified in multiple traces, including:

- `stage2_producer_input`
- `wall_control_source_continuous`
- `wall_control_source2_continuous`
- `wall_lane_continuous`
- `stage2_tail_no_stage_rearm`

So the strongest current source-side statement is:

- the stable external builder stream used by captured wall-control
  producer calls comes from `DAT\\MOVIES.MIX @ 77622`

## Internal Node Images Are Separate

The internal producer source images are not the same as the external
builder stream.

Examples:

- `0x10393A2D` source for `7D87` is a sparse compact control image
- `0x10393EC5` source for `7DF2` is a different sparse compact control image
- `0x10394ACD` source for final tail `7DF2` is another later sparse control image

So the producer call is combining:

- a stable external builder stream from `0x106AB520`
- a separate internal node image at `ESI`

## What The Later MOVIES.MIX Near-Variant Family Is Not

A repeated later `DAT\\MOVIES.MIX` family is loaded in the same runtime
bursts:

- `99632`
- `121638`
- `143564`
- `165530`
- `187526`
- `209590`
- `231654`

These blocks are near-variants of the `77622` stream, but current
evidence says they are not direct matches for the pinned wall-control
source images.

They do not match:

- the stable `0x106AB520` builder stream
- the separate `0x10394CB6` stream/palette-side builder lane
- the captured internal sparse node images used at `ESI`

Current safest read:

- they are real runtime inputs
- they are often loaded immediately before wall-control producer calls
- but in the current witness set they are only seen as raw file reads,
  not as any pinned downstream byte image

## Tail-Window Result

In the final tail trace, the later-family burst runs directly into the
final `7DF2` cluster:

- last later-family reads:
  - `231654`
  - `239846`
  - `248038`
- then immediately:
  - watched `7DF2` write
  - `builder_info`
  - `builder_source_dump`
  - `stage2_producer_info`
  - `stage2_producer_src_dump`

There are no other traced non-read/non-seek events in that tiny window.
So the later-family bytes disappear inside an uninstrumented handoff
immediately before the final producer call.

## Read-State Split Inside The Later Family

The later burst is not one flat caller state.

In the final tail trace:

- `77622`, `99632`, `121638` share one caller-frame shape
- `143564`, `165530`, `187526` share a second
- `209590`, `231654` share a third

So the near-variant family is being advanced through at least staged
caller-state phases before the uninstrumented handoff.

## Best Current Picture

The current high-confidence wall-control picture is:

1. runtime loads a wider `MOVIES.MIX` burst
2. the stable `77622` block becomes the external builder stream at
   `0x106AB520`
3. generic producer calls consume that builder stream together with
   evolving internal node images
4. the node ladder advances into the final tail-producing
   `0x10394ACD -> 0x10394FC4` `7DF2` hop
5. a later near-variant `MOVIES.MIX` family is also loaded in the same
   burst context, but its exact post-read landing point is still open

## Remaining Open Item

The main remaining wall-side gap is now narrow:

- where the later `99632 .. 231654` `MOVIES.MIX` near-variant family
  lands after read-time, and what consumes it before the final producer
  cluster
