# LoL2 Runtime-To-Renderer Bridge

Date: 2026-03-24

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
- `+0x28` (vtable pointer)
- `+0x88` (dimension value, 100)
- `+0xB0` (sprite/animation reference, value 5000)
- `+0xB2` (sprite state/frame, value 0)

This is the **runtime-to-renderer bridge**: the same live object that the loading-phase cascade populates is directly read by the renderer/display subsystem. The renderer does not need a separate handoff — it reads from the same `[+80]` object.

## What Is Still Open

Minor remaining items (none blocking):

- exact semantic role of `.tex` versus `.odf` in the shipped path
- 39 compressed sub-textures (mipmaps) use format=0x80 — not yet decoded
- what the 6xxx consumers do with the fields they read (renderer initialization? sprite setup? draw-list building?)

Note: +0x6C was resolved by disassembly as a global timer snapshot from `0x101D0CB6` (see `lol2-entity-object-map.md`).

## Texture Atlas Pipeline (Candidate — Not Runtime-Confirmed)

The "blob-to-surface decode" question has a strong candidate answer. Wall textures appear to be in `LOCAL.MIX` Entry 1, stored as a raw texture atlas, rather than encoded within `L*_DC.MIX` Entry 2. Entry 2 appears to contain level geometry and art metadata, not pixel data. This reclassification is based on static analysis and 1 extracted texture, not runtime tracing.

Based on the extraction of 1 texture that visually matches in-game appearance, the working hypothesis is that wall textures are stored as raw pixels in LOCAL.MIX rather than encoded within the L*_DC.MIX blob. This has not been confirmed by runtime tracing of the renderer's texture source pointer.

### Texture Atlas Format (LOCAL.MIX Entry 1)

Note: LOCAL.MIX Entry 1 was identified as the texture source by extracting a 128x128 texture that visually matches the Draracle Caverns cave wall. This identification has not been confirmed by runtime tracing of the column renderer's texture source pointer.

The atlas is a straightforward raw container:

1. `u16 count` — number of textures in the atlas (39 for L1)
2. `u16 header_size` — size of the header block
3. `u32[count]` — offset table pointing to each texture
4. Per texture: 10-byte sub-header + raw pixels (128x128 8bpp palette-indexed)

Each texture is 128x128 raw 8bpp palette-indexed. The column renderer reads texture columns from the atlas and composites them into the back buffer; the `REP MOVSD` blit then copies the composed back buffer to VGA.

### Column Renderer and Distance Shading

The software renderer reads texture columns from these atlas surfaces and applies a distance shade table during wall rendering. Shade table indices 77-93 map to attenuation levels 1-5, creating the depth-fog effect visible in gameplay.

The final blit to VGA Mode X framebuffer occurs at `0x1017B710` via planar writes.

### Why This Was Misidentified

Earlier work assumed textures were encoded within the `L*_DC.MIX` Entry 2 compressed blob because Entry 2 was the largest data block per level. In reality, Entry 2 is geometry/art metadata (8-byte mapping records, mipmap chain pointers), and the actual pixel data lives separately in the shared `LOCAL.MIX` atlas.

## Best Current Bridge Statement

The current best model of the LoL2 texture pipeline: `LOCAL.MIX` Entry 1 likely provides raw 8bpp texture atlases (1 texture extracted and visually confirmed, not runtime-traced), `L*_DC.MIX` Entry 2 provides geometry/art metadata, and the column renderer applies distance shading before writing to VGA Mode X framebuffer. The entity pipeline (`L*_DC.MIX` descriptor parsing → `[+80]` live object → 6xxx renderer consumers) handles sprite/entity rendering through a shared-object model with C++ polymorphic dispatch (proven by disassembly). The wall texture source identification remains a strong candidate pending runtime confirmation of the renderer's texture source pointer.
