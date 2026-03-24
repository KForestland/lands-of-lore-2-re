# Lands of Lore II RE

Reverse-engineering and documentation for the DOS version of *Lands of Lore: Guardians of Destiny*.

This repository contains:

- promoted reverse-engineering writeups
- runtime entity pipeline documentation
- evidence indexes and witness maps
- structured inventory summaries
- curated analysis and extraction tools

It does not aim to redistribute raw game data.

## Start Here

If you are new to this repo, read these in order:

1. [`closure-summary.md`](docs/closure-summary.md) — plain-English summary of what is closed and what is open
2. [`final-closure-memo.md`](docs/final-closure-memo.md) — short final handoff-style memo for the current public LoL2 state
3. [`lol2-current-status.md`](docs/lol2-current-status.md) — what is currently proven, what is still open, and where the LoL2 lane stands now
4. [`lol2-compact-path-branch-steering.md`](docs/lol2-compact-path-branch-steering.md) — the main near-final LoL2 result: the compact `L1` control path and the loading-phase fast-vs-alternate branch split
5. [`lol2-object-state-word.md`](docs/lol2-object-state-word.md) — the clean breakdown of the bit-field register at `[+80] + 0xB4` and what each bit does
6. [`lol2-entity-object-map.md`](docs/lol2-entity-object-map.md) — complete proven field layout of the `[+80]` entity object (25+ fields with semantic roles)
7. [`lol2-runtime-to-renderer-bridge.md`](docs/lol2-runtime-to-renderer-bridge.md) — explains why this runtime work matters for the old texture/renderer question and how the two lanes connect
8. [`inventory-overview.md`](docs/inventory-overview.md) — explains what LoL2 currently has inventory for, and what is still missing compared to LoL1
9. [`lol2-witness-map.md`](evidence/lol2-witness-map.md) — short map of the main witnesses and trace variants, so the docs above are easier to follow
10. [`audio-inventory.md`](docs/audio-inventory.md) — what audio/music assets exist, their formats, and extraction status
11. [`texture-map-inventory.md`](docs/texture-map-inventory.md) — the first deeper public catalog for LoL2 texture and map outputs

## Status

RE closure: ~99%

- Entity instantiation-to-rendering pipeline fully decoded via native disassembly (7 functions)
- Wall texture format proven 8bpp palette-indexed by renderer disassembly
- `[+80]` entity object mapped: 25+ fields with proven semantic roles
- Open: blob-to-surface decode step ([details](docs/lol2-runtime-to-renderer-bridge.md#blob-to-surface-decode-open)), audio/dialogue extraction ([details](docs/audio-inventory.md))

## Repository Layout

- [`docs/`](docs) — promoted writeups and closure notes
- [`evidence/`](evidence) — trace references, witness maps, and evidence indexes
- [`data/`](data) — machine-readable inventory summaries
- [`tools/`](tools) — curated analysis and extraction tools
- [`future-patches/`](future-patches) — future patch planning (separate from RE canon)

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
