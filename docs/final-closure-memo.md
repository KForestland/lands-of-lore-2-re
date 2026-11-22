# LoL2 March 2026 Research Memo

> **History (March 2026).** The overall estimate of about 99% was withdrawn on 18 November 2026. See [current status](STATUS.md#where-this-stands).

The [Draracle restoration findings](draracle-restoration.md) cover later work on the cave. The October 2026 results for the sound bank, level textures, wall materials, scripts and items are in the [October update](lol2-current-status.md#october-2026-update).

Date: 2026-03-24

## Status

**Status (March 2026):** The overall estimate of about 99% was withdrawn on 18 November 2026. See [current status](STATUS.md#where-this-stands).

The March work traced a compact path from entity creation to rendering and showed that the wall texture format is 8 bits per pixel with a palette. At the time, LOCAL.MIX Entry 1 was a candidate for the wall texture source based on one visual match. Later work established the [source for one drawn wall span](lol2-wall-material-provenance.md). The March audio check covered one music track and one dialogue clip. The March classification of the 24 entity descriptor fields included direct traces of f12 and f13 and statistical inferences for other fields.

## March Runtime Trace

The March trace followed this compact `L1` control path:

- `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

That path is now stable enough to support safe public statements about:

- the live object/base path at `+80`
- the bit-field register at `[+80] + 0xB4` (bits 2, 6, 7 independently controlled)
- the fast/alternate loading-phase branch split (distributed across multiple bit tests in the rendering pipeline)

## What the March Trace Showed

- `L*_DC.MIX` descriptor families are live runtime inputs
- `0070:0E6C` is the first observed parser/consumer site
- parser-side work stages normalized runtime state
- the compact path reaches a live object/control path
- `[+80] + 0xB4` is a bit-field register prebuilt before `A00F`
- A00F sets bit 2 (activation), A0C3 clears bit 6 (loading-complete), 91E4 sets bit 7 (allocated)
- the fast-versus-alternate loading-phase branch split is real in the tested compact witness
- the branch split is distributed across multiple bit tests, not localized to a single instruction

## What Was Added In Update 2

- post-A00F consumer map: 36 consumer sites, 25 offsets, proven by direct read-monitoring
- A0C3 initially inferred as branch-steering site from read-monitoring (later corrected — see Update 3/4)
- 6xxx renderer/display consumer family identified (shared-object model, not separate pipeline)
- `+0x6C` not read during loading phase (confirmed deferred)
- complete first [+80] object field map

## What Was Added In Update 3/4 (Disassembly)

- full native disassembly of A00F, A044, A0C3, 0F08, A396, A40A, 6A50 from live DOSBox memory
- **A0C3 correction**: NOT a branch-steering site — cleanup epilogue that clears bit 6 at `+0xB4` and returns. The Update 2 inference was wrong; the read-monitoring captured a read-modify-write (`ANDB $0xBF`), not a branch decision.
- **+0xB4 reclassified**: bit-field register, not state word (bit 2 = activated, bit 6 = loading, bit 7 = allocated)
- **+0x6C resolved**: global timer snapshot from `0x101D0CB6`, not per-entity computed
- **+0x28 = C++ vtable pointer**: polymorphic entity dispatch with virtual calls at +0x8C and +0x9C
- **6A50 decoded**: entity render function with type check, render-skip flag (+0xB5 bit 0), vtable dispatch
- **0F08 decoded**: sprite frame interpolation — pure arithmetic, not a branch point
- added `lol2-entity-object-map.md`: complete 25+ field layout with proven semantic roles
- fast/alternate branch split is distributed across multiple bit tests, not localized to one instruction
- EIP truncation bug found and fixed in DOSBox trace output

## What Was Added In Update 6 (Wall Texture Format)

- **wall texture format PROVEN: 8bpp palette-indexed** by renderer disassembly
- software renderer at EIP `0x10172C08` uses `REP MOVSD` direct blit from pre-decoded surface buffers
- renderer code at segment base `0x10170000` (separate from entity code at `0x100B0000`)
- all 130+ exotic format attempts (NCC, 7bpp, 16bpp) confirmed wrong

## What Remains Open

- exact wall source/palette/runtime provenance closure
- 39 compressed sub-textures (mipmaps) use format=0x80 — not yet decoded
- HMI-MIDI to standard MIDI converter not written
- Sound effects container location not confirmed
- Full dialogue index table parsing (structure is known, bulk extraction is straightforward)

## March Findings and Limits

These are the findings and limits recorded in March 2026. See [current status](STATUS.md#where-this-stands) for later results:

- compact descriptor parsing feeds a live object/control path with C++ polymorphic dispatch
- object-side bit-field semantics are real and disassembly-confirmed
- wall textures are proven 8bpp palette-indexed with a standard blit renderer
- texture source provenance is narrowed but not fully closed: LOCAL.MIX Entry 1 remains one strong candidate model, but runtime source-pointer confirmation is still missing
- audio decode sample-verified: 1 music track and 1 dialogue clip verified; a bulk extraction tool exists for 33 tracks + 1008 clips, but bulk extraction is not yet fully verified
- all 24 entity descriptor fields classified by cross-level statistical analysis (f12-f13 proven; f14 strongly inferred; f0-f9 and f19-f23 inferred)
