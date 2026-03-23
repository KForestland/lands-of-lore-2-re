# LoL2 Final Closure Memo

Date: 2026-03-23

## Status

The LoL2 lane is at approximately `99%` — the entity instantiation-to-rendering pipeline is fully decoded via native disassembly, the wall texture format is proven 8bpp palette-indexed, and the remaining open items are the blob-to-surface decode step and inventory gaps (audio, dialogue).

This repo does not claim that every LoL2 asset family is solved to the same depth as LoL1. It does claim that the compact runtime lane is now strong enough to serve as the public closure backbone for the current state of the project.

## Final Practical Result

The central LoL2 closure result is the compact `L1` control path:

- `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

That path is now stable enough to support safe public statements about:

- the live object/base lane at `+80`
- the bit-field register at `[+80] + 0xB4` (bits 2, 6, 7 independently controlled)
- the fast/alternate loading-phase branch split (distributed across multiple bit tests in the rendering pipeline)

## What Is Safely Closed

- `L*_DC.MIX` descriptor families are live runtime inputs
- `0070:0E6C` is the first observed parser/consumer site
- parser-side work stages normalized runtime state
- the compact path reaches a live object/control lane
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

- **blob-to-surface decode**: the decompressed Entry 2 blob has a second encoding layer that produces 8bpp surface buffers during level loading — the decode function has not been traced yet
- LoL1-grade inventory coverage for LoL2 audio/music and script/dialogue/text

## Safe Bottom Line

LoL2 is no longer mainly blocked on "where does the data go?" or "what format are the textures?" The current public repo captures near-final truth:

- compact descriptor parsing feeds a live object/control lane with C++ polymorphic dispatch
- object-side bit-field semantics are real and disassembly-confirmed
- wall textures are proven 8bpp palette-indexed with a standard blit renderer
- the remaining work is the blob-to-surface decode step and asset inventory coverage
