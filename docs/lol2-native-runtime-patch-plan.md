# LoL2 Native Runtime Patch Plan

Date: 2026-04-04

## Purpose

This note records the intended post-RE implementation direction for
Lands of Lore II once the remaining wall/runtime closure work is done.

The goal is not a DOS binary hack that somehow turns the original EXE
into a native Vulkan game. The practical target is a new native runtime
for Windows and Linux that reuses original game assets and reproduces
original gameplay behavior closely enough to support:

- Windows and Linux native builds
- higher rendering resolutions
- quality-of-life improvements
- bug fixes
- optional renderer enhancements such as a better skybox
- modern graphics backend support, including Vulkan

## Current Strategic Read

The LoL2 reverse-engineering work is far enough along that native-runtime
planning is justified, but not far enough that renderer/asset-path
architecture should be frozen immediately.

The remaining wall-side gap is narrow:

- the post-read landing point and consumer path for the later
  `DAT\\MOVIES.MIX` near-variant family

So the recommended sequencing is:

1. finish the remaining LoL2 wall/runtime closure
2. in parallel, define the native runtime architecture
3. begin implementation after the runtime picture is stable enough to
   avoid redesigning the asset/render path

## Why LoL3 Is Deferred

LoL3 is intentionally not the next immediate focus.

Reason:

- LoL3 is likely to present the same broad class of problems:
  - runtime staging
  - renderer provenance gaps
  - asset/control indirection
- splitting attention now would slow closure on LoL2
- the cleaner move is to finish the LoL2 model, then reuse the methods
  and lessons on LoL3 later

So the current project order should remain:

- finish LoL2 closure and establish the native-runtime plan
- defer LoL3 until LoL2 is in a better implementation state

## Recommended Technical Direction

### Core Principle

Build a new native runtime. Do not make the DOS executable the long-term
center of the shipping solution.

The original executable remains useful as:

- reference behavior
- trace target
- disassembly target
- regression oracle

But the shipping patch/runtime should be native.

### Runtime Layers

The native implementation should be split into clear layers:

1. `data layer`
   - reads original game containers and records
   - exposes decoded assets through stable native structures

2. `runtime layer`
   - game state
   - movement/navigation
   - timing
   - object/control logic
   - save/load
   - event/script handling

3. `renderer layer`
   - starts from correctness-first scene reconstruction
   - supports original-style output first
   - later adds enhanced rendering modes

4. `platform layer`
   - windowing
   - input
   - audio
   - file paths
   - config

### Technology Direction

Recommended baseline:

- C++17/20 or Rust
- SDL3 for window/input/audio/bootstrap
- renderer abstraction with Vulkan as the intended primary backend

Important implementation rule:

- keep the renderer backend separate from the gameplay/runtime layer

That allows:

- Vulkan on supported systems
- possible fallback backend during bring-up
- easier testing and debugging

## Feature Priorities

The implementation priority should be:

1. native Windows/Linux runtime
2. correctness of original gameplay/runtime behavior
3. higher 3D rendering resolution
4. UI scaling and presentation cleanup
5. QoL improvements
6. bug fixing
7. optional skybox enhancement
8. Vulkan optimization/polish

Reason:

- correctness comes before enhancement
- high-res only matters if the scene is right
- skybox work is valuable, but it should not drive the engine design

## Higher-Resolution Strategy

Higher resolution should not mean simple framebuffer stretching.

The runtime should support at least three presentation modes:

### 1. Original

- original-style rendering rules
- original aspect/presentation constraints where appropriate

### 2. Enhanced

- higher internal 3D render resolution
- original art and scene rules preserved
- cleaner scaling and filtering choices

### 3. Modern

- widescreen-aware presentation
- optional modern camera/input improvements
- optional enhanced skybox/background treatment
- configurable visual upgrades

UI and 3D resolution should be separable:

- 3D scene resolution
- UI scale
- text scale

## Quality-Of-Life Target Set

Strong early QoL candidates:

- borderless fullscreen
- remappable keyboard/mouse/controller input
- modern mouse support
- quick save / quick load
- autosave on transitions
- configurable UI scale
- text speed / subtitle quality options
- cleaner configuration handling
- accessibility-oriented contrast and readability options

QoL features that risk gameplay drift should be optional and clearly
labeled.

## Bug-Fix Policy

Bug fixes should be categorized into three buckets:

### 1. Accuracy Fixes

- restore intended original behavior

### 2. Compatibility Fixes

- crashes
- timer issues
- save/load problems
- platform-specific breakage

### 3. Enhancement Fixes

- modernized behavior that changes the original experience

Where possible, enhancement-side fixes should be toggleable.

## Renderer and Skybox Plan

Vulkan is a good target, but it should not be the first milestone by
itself.

Recommended order:

1. reproduce scene composition correctly
2. reproduce wall/object/floor rendering correctly
3. establish original-style presentation mode
4. add enhanced render resolutions
5. add optional skybox improvements
6. optimize/polish Vulkan path

The skybox work should preserve tone and atmosphere. The goal is not to
make LoL2 look like a different game.

Best approach:

- keep original/background-compatible mode
- add optional enhanced sky mode
- tie it to original palette/light/scene assumptions as much as possible

## Milestones

### Milestone 1: Native Foundation

Target:

- native launcher
- project structure
- data loading framework
- asset inspection/debug viewers

Expected output:

- Windows/Linux app opens
- original data files mount
- decoded assets can be inspected in native tools

### Milestone 2: Runtime Skeleton

Target:

- camera/navigation shell
- scene loading
- wall/object placement model
- timing/update loop

Expected output:

- walkable/debuggable scene viewer using original data

### Milestone 3: Correctness Pass

Target:

- reproduce runtime object/control behavior
- close major scene/render mismatches
- validate against trace evidence and original behavior

Expected output:

- first trustworthy gameplay-adjacent native build

### Milestone 4: Enhanced Build

Target:

- high-res render modes
- UI scaling
- QoL features
- bug-fix framework

Expected output:

- first broadly usable enhanced native build

### Milestone 5: Renderer Enhancements

Target:

- Vulkan polish
- optional skybox enhancement
- optional graphics improvements

Expected output:

- native enhanced build with modern presentation options

## Estimated Timeline

If the LoL2 closure work continues cleanly:

- start serious native-runtime implementation planning:
  - within days
- start first real native implementation work:
  - roughly `3-7` working days after the remaining LoL2 wall/runtime gap
    is closed enough
- first native asset/runtime viewer:
  - about `1-2` weeks after implementation start
- first walkable/debuggable native build:
  - about `3-6` weeks
- first serious enhanced build:
  - about `2-3` months

These are implementation estimates, not guarantees.

## Immediate Pre-Implementation Requirement

Before locking the render/data architecture, the remaining LoL2
wall-control provenance gap should be narrowed a bit further:

- identify the post-read landing/consumer path of the later
  `DAT\\MOVIES.MIX` near-variant family

That is the main remaining blocker to saying the full wall-side flow is
closed enough for architecture freeze.

## Best Current Project Order

1. finish LoL2 wall/runtime closure
2. keep this native-runtime plan as the implementation guide
3. start the LoL2 native runtime
4. defer LoL3 until LoL2 has a stable implementation base
