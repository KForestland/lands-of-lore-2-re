# LoL2 Current Status

Date: 2026-03-24

## Status

- RE closure: effectively complete
- Proof levels vary by subsystem: entity pipeline PROVEN by disassembly; wall texture format PROVEN by disassembly; texture atlas source identification based on 1 extracted texture (not runtime-traced); audio decoder verified on 1 track + 1 clip (tool exists for bulk); entity descriptor fields range from PROVEN (f12-f13) to INFERRED (f0-f9, f19-f23)
- Remaining work is minor: mipmap sub-texture format=0x80, HMI-MIDI converter, sound effects container

## Strongest Current Results

- `DAT\\L1_DC.MIX` and `DAT\\L9_DR.MIX` records are proven live runtime inputs.
- `0070:0E6C` is the first observed parser/consumer site for the staged record prefix.
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

- The bit-field register at `[+80] + 0xB4` is prebuilt before `A00F`:
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

- `+0xB4` is a bit-field register with independently controlled bits (2, 6, 7), not a one-byte magic activation gate.
- `A0C3` is reached under all tested `+0xB4` suppression states.
- `A0C3` is **not** a branch-steering site. Disassembly proves it is a cleanup epilogue: `ANDB $0xBF, 0xB4(%eax)` clears bit 6 at `[+80]+0xB4` and returns. The read-monitoring captured a read-modify-write, not a branch decision.
- Baseline and alternate families share some early setup but do not fully converge within the observed loading-phase window.
- Safest current model:
  - partial convergence
  - different completion depth
  - not full convergence

## Post-A00F Consumer Map (Proven)

Direct read-monitoring on the `[+80]` object captured 36 distinct consumer CS:IP sites reading 25 offsets. Two main consumer families:

- **0x6xxx range** (`6A50`, `6AB5`, `6AC9`, `6B68`, `6CDA`): reads `+0xA8` (entity class), `+0x88` (dimension), `+0xB0` (sprite/animation ref), `+0x28` (vtable pointer). This is the renderer/display subsystem (confirmed by disassembly of 6A50: type check, render-skip flag, vtable dispatch).
- **0xAxxx range** (`A0C3`, `A044`, `A156`, `A2F4`, `A32F`, `A365`, `A396`, `A3BA`, etc.): the loading-phase cascade itself.
- **0x18xx–0x21xx range** (`1848`, `1883`, `18BB`, `20BE`, `2165`, `21C2`): early object-field readers.

Key structural result:

- `+0x28` is the hottest field (5 readers) — a vtable pointer (confirmed by disassembly: `call *0x8c(%eax)`) used by both the loading cascade and the 6xxx renderer subsystem.
- `+0x6C` (the deferred scalar, value 0x1E = 30) was **not read** in 256 consumer events — it is consumed in the gameplay phase, not the loading phase.
- `+0xA8` (value 0x06) is read by both the 6xxx and Axxx families as an entity class/type indicator.

## Disassembly Results (Update 3)

Native disassembly from live DOSBox memory fully decoded the entity pipeline:

- **A00F**: bit-field stamp (sets bit 2 at +0xB4) + global timer snapshot to +0x6C + sprite frame setup call
- **0x100B0F08**: sprite frame interpolation — pure arithmetic, NOT a branch point
- **A044**: stores frame result, computes delta, tests +0xA3 flag → jumps to A0C3 if zero
- **A0C3**: cleanup epilogue — clears bit 6 at +0xB4 and returns (NOT a branch-steering site)
- **A396**: animation/rendering update loop — vtable dispatch through +0x28, calls renderer 6A50
- **A40A**: animation speed calculator — computes +0x65 from frame data
- **6A50**: entity render function — type check, render-skip via +0xB5 bit 0, vtable dispatch

Key architectural finding: **+0x28 is a C++ vtable pointer**, enabling polymorphic entity dispatch.

The fast/alternate branch split is **distributed across multiple bit tests** in the rendering and animation pipeline, not localized to a single branch instruction.

See `lol2-entity-object-map.md` for the complete proven field layout.

## Remaining Open Items (Minor)

- Wall texture pixel format: **PROVEN 8bpp palette-indexed** by renderer disassembly. Texture source: **LOCAL.MIX Entry 1** (raw atlas, not in L*_DC.MIX Entry 2). See [`runtime-to-renderer bridge`](lol2-runtime-to-renderer-bridge.md#texture-atlas-pipeline-candidate--not-runtime-confirmed).
- 39 compressed sub-textures (mipmaps) use format=0x80 — not yet decoded
- HMI-MIDI to standard MIDI converter not written
- Sound effects container location not confirmed
