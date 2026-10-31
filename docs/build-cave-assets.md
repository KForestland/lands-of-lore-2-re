# Build the diagnostic cave assets

The source pipeline can now generate the full experimental Godot cave assets
without precomputed evidence directories. It still requires the supported game
files and a matching populated cache. It does not build that cache from untouched
retail archives or support arbitrary editions.

## Requirements

- Python 3.10+, repository requirements (Pillow and Capstone 5).
- An x86-64 host with `cc` supporting GNU x87 inline assembly. Validated on Linux;
  other host/compiler combinations are not claimed.
- An existing Godot source checkout if exporting directly into that project.
- A local game root containing `DAT/L1_DC.MIX`, `LOLG.DAT`, `CDCACHE.LST` and
  `CDCACHE.MIX`.

The MIX/executable hashes are listed in [restoration findings](draracle-restoration.md).
The cache loader requires a unique stored-state-2 record for
`sphere1\l1_dc\l1_dc.tex` (canonical cache names supported by the loader).
Its extracted blob must have SHA-256
`102410e0b69037da2bdf451dd4de9c7e30df2c9d1309b1d0a1c0224ab7218c97`.
Missing files, unsupported cache states or changed hashes fail explicitly. Cache
creation/repair is not automated; do not overwrite your installation to make it match.

## Commands

From the RE repository, after installing requirements:

```sh
python3 tools/draracle/build_cave_assets.py --game-root /path/to/lol2 --out /path/to/evidence --godot-project /path/to/lands-of-lore-unified-godot
```

Omit `--godot-project` to export into `out/godot_assets`. The command writes only
its evidence directory and, when requested, the Godot generated-assets directory.
It reads the game installation. Evidence subdirectory names retain their original
checkpoint date for compatibility with the packaged exporter.

Then, from the Godot checkout:

```sh
bash tools/lol2/run_full_cave.sh
```

Use the Godot repository at commit `5a91ca8` or a compatible later version.
The pipeline packages the matching exporter sources in `tools/draracle/godot_export`;
keep them aligned with future Godot schema changes.

## What is generated

Corrected cave geometry; 26 A9 materials / 127 mip images; 80 additional bound
variant/mip images; 21 floor presets; static descriptor bindings; native floor
setup checks; a host x87 reproduction of the recovered rotation initializer;
and diagnostic floor textures, local samples and full-map JSON. The final
`build_manifest.json` records hashes of exported asset files.

Original surfaces and binary evidence are generated locally, never included in
this source update. The full map contains 1,953 floors, 1,860 texture assignments,
1,939 ceilings, 1,338 boundary quads and 955 candidate interior spans. It remains
an experimental static scene: wall textures/native UVs, animated effects, dynamic
objects, special openings and gameplay parity are not completed by this command.
Host x87 reproduction is not a live guest-table capture.

## Validation

A clean build into a path containing spaces produced 21 final asset files, all
byte-identical to the established local cave assets. A second build exported into
the published Godot source checkout, where all 119 full-map sprint checkpoint
routes passed with zero fall resets. All 25 geometry/cache/material unit tests
pass. These are bounded checks, not exhaustive gameplay or platform validation.
