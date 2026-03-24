# LoL2 Inventory Overview

Date: 2026-03-23

## Purpose

This note answers a simple repo question:

- what do we currently have a real LoL2 inventory for
- what do we not yet have

It is intentionally honest. LoL2 is not yet at the same inventory maturity as LoL1.

## Current Inventory Surface

The repo now has a first machine-readable inventory layer in `data/`.

Most useful files:

- `data/workspace-inventory-summary.json`
  - top-level counts for the current local LoL2 workspace
- `data/asset-family-status.json`
  - which LoL2 asset families are strong, partial, or still gaps
- `data/script-catalog.json`
  - grouped inventory of the current Python scripts and helper wrappers
- `data/output-catalog.json`
  - grouped inventory of the `lol2_out/` output surface

## What We Clearly Have

### 1. Texture And Visual Output Surface

This is the strongest non-trace *local* inventory surface after the compact runtime docs.

Current evidence:

- large local texture/visual script surface
- many visual outputs under `lol2_out/`
- many texture-related directories already grouped in the new output catalog

Safe read:

- textures and visual extraction experiments are well represented locally
- the public repo now has a foundation inventory for them
- deeper per-asset indexing is still future work

### 2. Map And Geometry Surface

This is also strong.

Current evidence:

- many cave / geometry / map scripts
- geometry JSON outputs in the wider workspace
- wall-map and cave-map image outputs already present

Safe read:

- map/geometry work exists in meaningful volume
- the public repo now has a foundation inventory for it
- a curated public map/geometry index is still future work

### 3. Runtime Trace And Witness Surface

This is currently the strongest LoL2 inventory family overall.

Current evidence:

- many `dosbox_guest_trace_*` directories
- witness map already in the repo
- evidence index already in the repo

Safe read:

- this family is already well represented publicly
- it is the strongest current backbone of the LoL2 repo

## What We Do Not Yet Have Cleanly

### 1. Audio / Music Inventory

Current read:

- **RESOLVED**: audio inventory now published in `audio-inventory.md`
- 1 music track decoded and verified from DMUSIC.MIX (195.5s); tool exists for all 33 tracks (~116 min est.)
- 1008 dialogue clips identified in LOCALLNG.MIX (first clip decoded, bulk extraction straightforward)
- Remaining gap: sound effects container location, HMI-MIDI converter

### 2. Script / Dialogue / Text Asset Inventory

Current read:

- dialogue audio is decoded (see above), but script/text asset inventory is still a gap compared to LoL1

### 3. Curated Public Tool Set

Current read:

- **RESOLVED**: 18 curated tools published in `tools/` covering MIX parsing, LZ77 decompression, LE analysis, entity tracing, audio decode, sprite/geometry/mesh extraction, and semantic analysis
- the local workspace still contains ~335 scripts; the published 18 are the cleaned, verified subset

## Counts Worth Knowing

From the first inventory pass:

- `335` local `lol2_*.py` scripts
- `2` `run_lol2_*.sh` wrappers
- `2` native `fd_trace` helper files
- `153` top-level directories under `lol2_out/`
- `57` trace-run directories under `lol2_out/`

Practical read:

- LoL2 does not lack material
- it lacks curation

## Best Current Comparison To LoL1

LoL1 has:

- stronger public `data/`
- cleaner public `tools/`
- more fully solved asset-family inventories

LoL2 now has:

- a clean closure-document layer
- a first public inventory layer
- a visible list of what is still missing

That is progress in the right order.
