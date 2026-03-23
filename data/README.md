# Data

This folder is for machine-readable LoL2 inventory summaries.

Read these first:

- `workspace-inventory-summary.json`
  - top-level counts for scripts, wrappers, output directories, and file types
- `asset-family-status.json`
  - honest status of the major LoL2 asset families
- `script-catalog.json`
  - grouped catalog of the current LoL2 scripts and helpers
- `output-catalog.json`
  - grouped catalog of the current `lol2_out/` output surface
- `texture-map-catalog.json`
  - curated texture/map output catalog

Working rule:

- this folder is for structured summaries, not raw dumps
- prefer curated inventories over copying thousands of generated files into the repo
