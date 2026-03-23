# LoL2 Closure Summary

Date: 2026-03-23

## Status

LoL2 is near-final (estimated roughly `98-99%` based on the compact-path closure state and known remaining gaps). See `final-closure-memo.md` for the latest state including disassembly results and wall texture format proof.

This repo is not yet claiming full renderer closure. What it does claim is that the core compact runtime lane is now structurally understood well enough to stop treating the renderer question as isolated file archaeology.

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
- full renderer/texture payload closure
- full field-by-field semantic map of all descriptor payload bytes

## Best Read Of The Lane Now

LoL2 is no longer mainly blocked on “where does the data go?” The front line has shifted into closure quality:

- naming the compact-path object/state semantics carefully
- reconnecting those semantics back to the remaining renderer/texture questions
- keeping the final public repo readable instead of memo-heavy

## Read Next

1. `lol2-current-status.md`
2. `lol2-compact-path-branch-steering.md`
3. `lol2-object-state-word.md`
4. `lol2-runtime-to-renderer-bridge.md`
