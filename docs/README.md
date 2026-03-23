# Docs

This folder is for promoted LoL2 reverse-engineering writeups only.

Read order:

- `closure-summary.md`
  - Plain-English summary of the current closure state.
- `lol2-current-status.md`
  - Start here. Short state of the lane, strongest proven results, and remaining open items.
- `lol2-compact-path-branch-steering.md`
  - Main closure note for the compact `L1` control path and the fast-vs-alternate loading-phase branch split.
- `lol2-object-state-word.md`
  - Focused explanation of the object-side state word at `[+80] + 0xB4`.
- `lol2-runtime-to-renderer-bridge.md`
  - Explains how the runtime-object results change the renderer/texture problem.
- `inventory-overview.md`
  - Explains what the LoL2 repo does and does not yet inventory cleanly.
- `texture-map-inventory.md`
  - The first deeper public inventory for texture/map outputs.
- `repo-scope.md`
  - Explains what this repo includes and excludes.
- `tooling-catalog.md`
  - Explains what tools and workflows were actually used.

Working rule:

- only move material here after it has been locally verified and cleaned
- no raw advisory dumps
