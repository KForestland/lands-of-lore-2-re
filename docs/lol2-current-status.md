# LoL2 Current Status

Date: 2026-03-23

## Status

- RE closure: near-final
- Confidence: `98-99%`
- Main remaining work:
  - final naming/closure quality on the compact loading-phase branch semantics
  - reconnecting the stronger compact runtime model back into the remaining texture/renderer questions

## Strongest Current Results

- `DAT\\L1_DC.MIX` and `DAT\\L9_DR.MIX` records are proven live runtime inputs.
- `0070:0E6C` stages a parsed/staged record prefix.
- `02E0:0D53` is the first proven downstream consumer and reads field `23` first.
- Rich families and compact control families are structurally distinct at runtime.
- Stable compact `L1` `B_HUMAN 0001` controls are proven.
- The compact `L1` control-frame path is now proven through:
  - `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

## Compact-Path Read

- `5570` stamps a fixed compact header/frame.
- `9BFC` fills the variable/linkage tail.
- `9C76` is the first proven downstream consumer of the compact control frame.
- `+80` is the strongest proven live object/base lane on this compact path.
- `-60` is a staged-record-linked lineage lane rather than a simple object-identity slot.

## Loading-Phase Branch Result

- The external object word at `[+80] + 0xB4` is prebuilt before `A00F`:
  - pre-`A00F`: `00018000`
  - post-`A00F`: `04018000`
- Observed ownership on that word:
  - allocator / zeroing path establishes the baseline
  - `122A` sets byte `+1 = 0x01`
  - `91E4` sets byte `+2 = 0x80`
  - `8F91` enforces byte `+3 = 0x00`
  - `A00F` contributes byte `0`

## What Is Now Proven About Byte 0

- Byte `0` at `[+80] + 0xB4` does not gate `A0C3` reachability.
- Byte `0` is the strongest known loading-phase branch-steering field.
- Under the tested compact-path witness, byte `0` strongly covaries with whether the followed cascade takes:
  - the fast `A396` path
  - or the alternate `E854 / E861 -> A40A / A44B` path
- Byte `2 = 0x80` is not sufficient to recover the fast path by itself.

## Safe Current Interpretation

- `+0xB4` is a multi-byte state word, not a one-byte magic activation gate.
- `A0C3` is reached under all tested `+0xB4` suppression states.
- The branch boundary is now tightened to inside `A0C3` or immediately after it, not at `A2D5` / `A6BA`.
- Baseline and alternate families share some early setup but do not fully converge within the observed loading-phase window.
- Safest current model:
  - partial convergence
  - different completion depth
  - not full convergence

## Remaining Open Items

- Exact safe naming of:
  - byte `0` at `[+80] + 0xB4`
  - the external `+0x6C` target
  - the final lifecycle difference between the fast and alternate loading-phase families
- Reconnection of the stronger compact runtime model to the remaining renderer/texture questions
