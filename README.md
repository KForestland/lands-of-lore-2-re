# Lands of Lore II RE

Recent update: [Executioner combat evidence and portable native verifier](docs/executioner-combat-evidence.md).

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

1. [`draracle-restoration.md`](docs/draracle-restoration.md) — current cave findings and reproducible geometry pipeline
2. [`closure-summary.md`](docs/closure-summary.md) — plain-English summary of what is closed and what is open
3. [`final-closure-memo.md`](docs/final-closure-memo.md) — short final handoff-style memo for the current public LoL2 state
4. [`lol2-current-status.md`](docs/lol2-current-status.md) — what is currently proven, what is still open, and where the LoL2 lane stands now
5. [`lol2-compact-path-branch-steering.md`](docs/lol2-compact-path-branch-steering.md) — the main near-final LoL2 result: the compact `L1` control path and the loading-phase fast-vs-alternate branch split
6. [`lol2-object-state-word.md`](docs/lol2-object-state-word.md) — the clean breakdown of the bit-field register at `[+80] + 0xB4` and what each bit does
7. [`lol2-entity-object-map.md`](docs/lol2-entity-object-map.md) — complete proven field layout of the `[+80]` entity object (25+ fields with semantic roles)
8. [`lol2-runtime-to-renderer-bridge.md`](docs/lol2-runtime-to-renderer-bridge.md) — explains why this runtime work matters for the old texture/renderer question and how the two lanes connect
9. [`inventory-overview.md`](docs/inventory-overview.md) — explains what LoL2 currently has inventory for, and what is still missing compared to LoL1
10. [`lol2-witness-map.md`](evidence/lol2-witness-map.md) — short map of the main witnesses and trace variants, so the docs above are easier to follow
11. [`audio-inventory.md`](docs/audio-inventory.md) — what audio/music assets exist, their formats, and extraction status
12. [`texture-map-inventory.md`](docs/texture-map-inventory.md) — the first deeper public catalog for LoL2 texture and map outputs

## Quick Start

```bash
git clone https://github.com/KForestland/Lands-of-lore-2-re.git
cd Lands-of-lore-2-re
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Typical first commands:

```bash
python3 tools/lol2_mix_parser.py --help
python3 tools/lol2_wall_texture_extract.py --help
python3 tools/lol2_geometry_cracker.py --help
```

Then read:

1. [`docs/closure-summary.md`](docs/closure-summary.md)
2. [`docs/lol2-current-status.md`](docs/lol2-current-status.md)
3. [`evidence/lol2-witness-map.md`](evidence/lol2-witness-map.md)

## Status

Active RE and restoration; not complete. The original cave layout is extracted
and available in an experimental full-map Godot view. Native slope, connector
and wall-record checks are reproducible with the packaged geometry pipeline.
Wall UVs/span semantics, special openings, interactive objects and native gameplay
remain open. Older closure memos describe scoped historical runtime results.

Start with [Draracle restoration findings](docs/draracle-restoration.md) for
current evidence, commands and supported game-file hashes. The
[Godot project](https://github.com/KForestland/lands-of-lore-unified-godot) hosts
the experimental view; extracted game assets are not included.

## Build the experimental cave

[Asset generation instructions](docs/build-cave-assets.md) cover the new configurable
texture-to-Godot pipeline. It requires matching original files and a populated
cache; arbitrary retail-installation cache generation remains open.

## Repository Layout

- [`docs/`](docs) — promoted writeups and closure notes
- [`evidence/`](evidence) — trace references, witness maps, and evidence indexes
- [`data/`](data) — machine-readable inventory summaries
- [`examples/`](examples) — public-safe screenshots and output examples
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
