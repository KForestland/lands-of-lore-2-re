# LoL2 Runtime-To-Renderer Bridge

Date: 2026-03-23

## Scope

This note reconnects the stronger compact-path runtime model to the older renderer/texture question. It is not a full renderer solution. It states what the compact-path work now changes about that problem.

## What The Renderer Lane Already Proved

The older renderer lane remains real:

- the loader has a proven `.tex` / `.odf` branch in disassembly
- shipped runtime map load is MIX-heavy in practice
- `DAT\\L1_DC.MIX` and `DAT\\L9_DR.MIX` expose fixed-stride descriptor families
- `0070:0E6C` is a stable parser/consumer site for `135`-byte descriptor bodies
- the parser stages a normalized runtime block before later game-code consumers take over

Practical read:

- the renderer/texture problem was never just "which file contains the pixels?"
- it was always a runtime assembly problem involving:
  - descriptor families
  - staged runtime state
  - later object/control consumers

## What The Compact-Path Work Added

The compact-path work moved the question forward in three important ways:

### 1. Runtime Object Handoff Is Now Concrete

For the tested compact witness:

- the staged/parsed record does not stop at parse-time bookkeeping
- it reaches a live compact control path:
  - `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

This matters because it proves, for the tested compact witness, that the descriptor path is not abstract metadata only. It feeds live object-side state.

### 2. `+80` Is A Real Live Object/Base Lane

The compact-path work proved:

- `+80` is the strongest live object/base lane on the compact path
- `A00F` commits external writes relative to that live object/base lane
- one of the important external targets is `[+80] + 0xB4`

This matters because it gives the renderer question a stronger runtime anchor:

- not just parser-side fields
- but the live object lane those fields eventually affect

### 3. The Object-Side State Word Is Now Structurally Understood

At `[+80] + 0xB4`:

- pre-`A00F`: `00018000`
- post-`A00F`: `04018000`

Promoted read:

- this is a bit-field register with independently controlled bits
- byte `0` is the strongest known branch-steering field
- byte `0` does not gate `A0C3` reachability
- byte `0` does steer fast `A396` versus alternate `E854 / E861 -> A40A / A44B`

This matters because it proves the runtime path includes object-side branch/state semantics before any final renderer claim would be safe.

## What This Changes About The Renderer Problem

The renderer problem should now be framed as:

- descriptor family selection
- staged runtime normalization
- compact/rich path split
- object/control handoff
- branch-steered loading-phase state
- only then later payload/texture assembly

Not as:

- a flat direct file-to-pixels question

That reframing matters because earlier attempts risked treating `.tex`, `.odf`, `GLOBAL.MIX`, `CDCACHE.MIX`, and `L*_DC.MIX` as if one of them alone had to be "the" answer.

The stronger safe statement is:

- `L*_DC.MIX` descriptor families and the compact control path define runtime object/control state that later renderer-facing work must respect
- the object/control semantics are not downstream noise; they are part of the assembly chain

## The Renderer Consumer Family (Update 2)

Post-A00F read-monitoring captured a **separate consumer family in the 0x6xxx code range** (`6A50`, `6AB5`, `6AC9`, `6B68`, `6CDA`) reading directly from the same `[+80]` object. These readers access:

- `+0xA8` (entity class/type, value 0x06)
- `+0x28` (object-chain pointer)
- `+0x88` (dimension value, 100)
- `+0xB0` (sprite/animation reference, value 5000)
- `+0xB2` (sprite state/frame, value 0)

This is the **runtime-to-renderer bridge**: the same live object that the loading-phase cascade populates is directly read by the renderer/display subsystem. The renderer does not need a separate handoff — it reads from the same `[+80]` object.

## What Is Still Open

The compact-path work did not finish these renderer-side questions:

- exact semantic role of `.tex` versus `.odf` in the shipped path
- exact payload path from descriptor family into final decoded wall/scene texture content
- exact meaning of the deferred scalar target at `[+80] + 0x6C` (confirmed deferred to gameplay phase — not read during loading)
- exact field-by-field mapping for the remaining descriptor payload bytes
- what the 6xxx consumers do with the fields they read (renderer initialization? sprite setup? draw-list building?)

## Best Current Bridge Statement

The LoL2 renderer/texture lane is no longer best treated as a pure asset-location problem. The current compact-path results show that descriptor parsing in `L*_DC.MIX` feeds a live object/control lane, and that object-side loading-phase branch semantics affect downstream runtime behavior before any final renderer claim is safe. Post-A00F consumer tracing has now identified the renderer subsystem (`02E0:6A50`–`6CDA`) as a direct reader of the same `[+80]` object, confirming that the runtime-to-renderer handoff is not a separate pipeline but a shared-object model. The remaining renderer work should therefore be grounded in the now-proven parser -> staged block -> compact/rich path -> live object/state -> renderer-read chain.
