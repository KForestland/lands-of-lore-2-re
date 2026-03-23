# Lands of Lore II RE

Reverse-engineering and closure documentation for the DOS version of *Lands of Lore II*.

This repository is the clean public-facing LoL2 lane of the broader project. It focuses on:

- promoted reverse-engineering notes
- compact runtime-path closure
- evidence indexing and witness mapping
- future patch planning kept separate from canon

It does not aim to redistribute raw game data.

## Start Here

If you are new to this repo, read these in order:

1. `docs/closure-summary.md`
   Plain-English summary of what is actually closed and what is still open.
2. `docs/final-closure-memo.md`
   Short final handoff-style memo for the current public LoL2 state.
3. `docs/lol2-current-status.md`
   What is currently proven, what is still open, and where the LoL2 lane stands now.
4. `docs/lol2-compact-path-branch-steering.md`
   The main near-final LoL2 result: the compact `L1` control path and the loading-phase fast-vs-alternate branch split.
5. `docs/lol2-object-state-word.md`
   The clean breakdown of the bit-field register at `[+80] + 0xB4` and what each bit does.
5b. `docs/lol2-entity-object-map.md`
   Complete proven field layout of the `[+80]` entity object (25+ fields with semantic roles).
6. `docs/lol2-runtime-to-renderer-bridge.md`
   Explains why this runtime work matters for the old texture/renderer question and how the two lanes connect.
7. `docs/inventory-overview.md`
   Explains what LoL2 currently has inventory for, and what is still missing compared to LoL1.
8. `evidence/lol2-witness-map.md`
   Short map of the main witnesses and trace variants, so the docs above are easier to follow.
9. `docs/audio-inventory.md`
   What audio/music assets exist, their formats, and extraction status.
10. `docs/texture-map-inventory.md`
   The first deeper public catalog for LoL2 texture and map outputs.

## Status

- RE closure: approximately 99%
- Entity instantiation-to-rendering pipeline fully decoded via native disassembly (7 functions)
- Wall texture format proven 8bpp palette-indexed by renderer disassembly
- `[+80]` entity object mapped: 25+ fields with proven semantic roles
- Remaining: blob-to-surface decode step, audio/dialogue extraction

## Repo Layout

- `docs/`
  - promoted writeups and closure notes for humans to read first
- `evidence/`
  - trace references, witness maps, and evidence indexes that back the docs
- `data/`
  - machine-readable inventory summaries
- `tools/`
  - tool notes, workflow summaries, and later cleaned helpers
- `future-patches/`
  - future patch planning only, kept separate from RE canon

## Detailed File Map

- `docs/closure-summary.md`
  - plain-English entry point
- `docs/final-closure-memo.md`
  - final short handoff note for the current repo state
- `docs/lol2-current-status.md`
  - current state of the LoL2 lane
- `docs/lol2-compact-path-branch-steering.md`
  - main compact-path closure note
- `docs/lol2-object-state-word.md`
  - focused note on `[+80] + 0xB4`
- `docs/lol2-runtime-to-renderer-bridge.md`
  - bridge back to the renderer/texture lane
- `docs/repo-scope.md`
  - what this repo includes and excludes
- `docs/provenance.md`
  - where the current claims came from and how advisory output was handled
- `docs/tooling-catalog.md`
  - what tools/workflows were used in practice
- `docs/inventory-overview.md`
  - what LoL2 currently has and does not yet have inventory for
- `docs/texture-map-inventory.md`
  - deeper texture/map inventory surface
- `evidence/lol2-evidence-index.md`
  - where the supporting local artifacts live
- `evidence/lol2-witness-map.md`
  - which witness proved which result
- `data/workspace-inventory-summary.json`
  - top-level counts for the current LoL2 workspace
- `data/asset-family-status.json`
  - current status of textures, maps, traces, audio, scripts, and tools
- `data/script-catalog.json`
  - grouped catalog of the current LoL2 scripts
- `data/output-catalog.json`
  - grouped catalog of the current `lol2_out/` output surface
- `data/texture-map-catalog.json`
  - curated texture/map output catalog

## Asset Policy

This repo intentionally avoids shipping full copyrighted asset dumps.

Included:

- documentation
- evidence maps
- workflow/tooling notes
- structured inventory summaries

Not included in the initial repo:

- raw retail game files
- full extracted media dumps
- raw private working ledgers

## Scope Rules

- Keep promoted facts separate from hypotheses.
- Keep LoL2 RE canon separate from future patch planning.
- Do not mix advisory AI output into canon without local confirmation.

