# LOCAL.MIX Entry 1 Record 0 Runtime Buffer Check

Date: 2026-04-02

This note records one narrow follow-up to the Entry 1 verdict:

- does the surviving raw witness in `LOCAL.MIX` entry `1`, record `0`,
  appear directly inside the preserved runtime wall buffers?

Tool:

- [lol2_verify_entry1_runtime_witness.py](/home/bob/lands-of-lore-2-re/tools/lol2_verify_entry1_runtime_witness.py)

Targets checked:

- `l1cap_wall_lane.bin` (`128x128`)
- `bigdump_wall_lane.bin` (`128x128`)
- `l1cap_renderer_texture.bin` (`256x256`)
- `bigdump_renderer_src.bin` (`128x64`)

## Result

No direct raw reuse was found in these preserved captures under the
tested straightforward layouts.

Observed:

- no full-buffer equality
- no full `tex0` substring hit in any target
- no exact `8x8` patch reuse
- no exact `16x16` patch reuse
- best row agreement stayed very low:
  - `3 / 128` for the two `128x128` wall-lane captures
  - `16 / 128` for the `256x256` renderer-texture capture
  - `1 / 128` for the `128x64` renderer-source capture
- simple `flip-x`, `flip-y`, and transpose row checks did not improve
  the `128x128` wall-lane result

## Safe Interpretation

This does `not` prove Entry 1 record `0` is unrelated to the runtime
wall path.

It `does` rule against the simplest current story:

- "the preserved runtime wall buffers are just raw copies of Entry 1
  record 0"

So Entry 1 record `0` remains a useful visual witness, but it is still
not runtime-proven as the direct wall-source owner.

## Practical Effect

This pushes the next proof step toward one of these:

1. show a more specific runtime use of Entry 1 bytes than these broad
   buffer captures preserve
2. prove a non-trivial transform from Entry 1 record `0` into the live
   wall-source surface
3. demote Entry 1 further and return to the stronger runtime-proven
   `MOVIES.MIX -> 0x106AF1xx -> 0x10394xxx` producer lane
