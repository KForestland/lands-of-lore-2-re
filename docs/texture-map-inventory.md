# LoL2 Texture And Map Inventory

Date: 2026-03-23

## Purpose

This note goes one level deeper than the first generic inventory layer.

It does not claim full texture closure. It records what the current workspace already has in a structured, public-facing way for texture and map work.

## Main Machine-Readable Source

- `data/texture-map-catalog.json`

That file is the current machine-readable catalog for the public LoL2 texture/map surface.

## Current Texture/Map Surface

### Wall Map Outputs

Current cataloged wall-map PNGs:

- `14` files

These include:

- `L1_DC_wall_map.png`
- `L9_DR_wall_map.png`
- `L10_DC_wall_map.png`
- `L20_BB_wall_map.png`

Practical read:

- there is already a meaningful cross-level wall-map output surface
- it is strong enough to inventory publicly even though the final renderer lane is not closed

### Cave / Geometry JSON Surface

Current cataloged cave/geometry JSON files:

- `28` files

This includes:

- `draracle_cave_155x77.json`
- `draracle_geometry.json`
- `lol2_cave_geometry_v17.json`
- `l1dc_geometry.json`

Practical read:

- the map/geometry side is not just images
- it also has structured intermediate outputs worth cataloging

### Selected Visual Output Directories

Current curated visual-output directories:

- `26` directories

Examples:

- `textures`
- `real_textures`
- `correct_textures`
- `sprites`
- `frames`
- `global_assets`
- `wad_textures`

Practical read:

- the workspace has a large visual experiment surface
- the public repo catalogs the surface without pretending every output is equally final

### `lol2_map` PNG Surface

Current cataloged `lol2_map` PNGs:

- `29` files

This includes:

- room tilemaps
- room 1bpc / 2bpc renders
- render-attempt map outputs under `lol2_map/renders/`

## What This Inventory Does And Does Not Mean

What it does mean:

- LoL2 already has a real public texture/map inventory surface
- the repo can now point to concrete outputs, not only to runtime notes

What it does not mean:

- full renderer closure
- final per-texture semantic naming
- publication of every generated PNG in the wider workspace

## Best Current Read

LoL2 now has:

- strong runtime closure docs
- a first public inventory layer
- and a deeper texture/map catalog that shows the project already has substantial visual and geometry output material

That is still below LoL1’s finished inventory standard, but it is no longer “docs only.”
