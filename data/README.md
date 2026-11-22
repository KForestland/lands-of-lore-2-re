# Data

This folder is for machine-readable LoL2 summaries and check inputs.

`page_facts.json` and `page_facts_coverage.json` are current inputs to `tools/page_facts.py --check`.

> History: the four inventory summaries below record an earlier research snapshot. See the current [status](../docs/STATUS.md) for supported results.

- `workspace-inventory-summary.json`
  - top-level counts for scripts, wrappers, output directories, and file types
- `asset-family-status.json`
  - status of the major LoL2 asset families at the time
- `script-catalog.json`
  - grouped catalog of the scripts and helpers in that snapshot
- `texture-map-catalog.json`
  - curated texture/map output catalog

Working rule:

- keep structured summaries here
- prefer curated inventories over copying thousands of generated files into the repo
