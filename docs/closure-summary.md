# LoL2 Closure Summary

Date: 2026-03-24

## Status

LoL2 is effectively complete. See `final-closure-memo.md` for the latest state including disassembly results, wall texture format proof, and the current texture-source candidate.

Wall texture format is proven 8bpp palette-indexed by renderer disassembly. LOCAL.MIX Entry 1 is the strongest current texture-source candidate (raw 8bpp atlas; 1 of 39 textures extracted and visually confirmed, but not runtime-traced). Audio decode is sample-verified: 1 music track and 1 dialogue clip were decoded successfully, and a bulk extraction tool exists but has not been run and verified end-to-end. All 24 entity descriptor fields are classified by cross-level statistical analysis, with proof levels varying per field (see `lol2-entity-object-map.md`). Only minor items remain (mipmap format=0x80, HMI-MIDI converter, sound effects container).

## Main Result

The strongest current LoL2 result is the compact `L1` control path:

- `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

That path is now stable enough to support safe statements about:

- the live object/base lane at `+80`
- the bit-field register at `[+80] + 0xB4`
- the loading-phase fast-versus-alternate branch split

## What Changed During This Closure Pass

Earlier LoL2 framing was still too loose in one important way: it treated `[+80] + 0xB4` too much like a one-byte activation gate.

The current promoted result is tighter:

- `[+80] + 0xB4` is a bit-field register (bits 2, 6, 7 independently controlled)
- byte `0` does not gate `A0C3` reachability
- byte `0` is the strongest known loading-phase branch-steering field
- byte `2 = 0x80` is not sufficient to recover the fast path by itself

## Fast Path Versus Alternate Path

Under the tested compact witness:

- fast family:
  - `A0C3`
  - `A2D5`
  - `A6BA`
  - heavy `A396`
  - `6CC4`

- alternate family:
  - `A0C3`
  - `A2D5`
  - `A6BA`
  - `6CC4`
  - `E854 / E861`
  - `A40A / A44B`

This matters because it proves the object-side runtime lane contains real branch/state semantics before any final renderer claim is safe.

## What Is Proven

- `L*_DC.MIX` descriptor families are live runtime inputs
- `0070:0E6C` is a stable parser/consumer site
- the parser stages normalized runtime state
- the compact path reaches a live object/control lane
- the bit-field register at `[+80] + 0xB4` is prebuilt before `A00F`
- the compact fast/alternate branch split is real in the tested loading-phase witness

## What Is Not Yet Claimed

- final semantic names for every byte/field
- final gameplay-phase meaning of the alternate branch family
- 39 compressed sub-textures (mipmaps) with format=0x80
- HMI-MIDI to standard MIDI converter
- sound effects container location

## Best Read Of The Lane Now

LoL2 is no longer blocked on any major question. The texture pipeline has a strong current model (LOCAL.MIX Entry 1 candidate atlas -> column renderer -> distance shading -> VGA blit; texture-source identification is based on 1 extracted texture, not runtime trace of the renderer source pointer). Audio decode is sample-verified on 1 music track and 1 dialogue clip. Entity fields are classified by statistical analysis with mixed proof levels. The remaining work is minor tooling (mipmap decoder, MIDI converter) and confirmation (sound effects container).

## Read Next

1. `lol2-current-status.md`
2. `lol2-compact-path-branch-steering.md`
3. `lol2-object-state-word.md`
4. `lol2-runtime-to-renderer-bridge.md`
