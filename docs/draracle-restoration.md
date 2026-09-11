# Draracle cave restoration findings

Updated 2026-09-11. The project is active; RE and full-game restoration are not
complete. Original instruction replay, runtime evidence and Godot experiments
are different proof levels and must remain distinguishable.

## Reproducible geometry and wall records

The pinned `DAT/L1_DC.MIX` contains 2,695 original vertices and 1,954 region
records. Role-aware extraction separates 1,939 primary regions from 15 floor
subdivision records; the subdivision parent floor is replaced by its children,
yielding 1,953 floor polygons for the review. Child continuation values must not
be interpreted as ceiling heights.

The packaged pipeline reproduces 2,284 slope-corner values across 571 native
floor/ceiling cases, and 224 connector coordinate values across 56 directed
connector cases, with zero mismatches. Four connector pairs are offset rather
than collinear and are preserved rather than snapped. The 86 exceptional links
split into 56 connector directions and 30 subdivision/owner directions.

3,052 eight-byte wall records partition exactly across 1,471 nonempty region
slices. Native address calculations, surface-code extraction and ordinary
object-byte setup agree for every applicable record. The source table pointer
is supplied in the host replay; its loader-to-global provenance is still open.
These are bounded interpretations of original executable instructions, not live
captures or proof of native walkability.

A [native flat-wall check](native-flat-wall-spans.md) now verifies 1,064 wall
records and 40 synthetic cases. Of its active spans, 1,044 exactly match the
existing local Godot boundary corners; other span classes remain open.

## Material findings from the local research workspace

Named cache identity identifies `sphere1\l1_dc\l1_dc.tex`. The extracted set
includes 26 A9 materials / 127 mip images plus 80 bound variant/mip images.
These 207 images are not 207 distinct textures. Twenty static floor preset
references resolve to source descriptors; 1,860 floor polygons have candidate
texture assignments. Lava and other unresolved surfaces remain marked in pink.

The static wall consumer at analysis address 0x11491E reads the first signed
word of each wall record; 0x114951..0x11495E maps nonnegative values into the
12-byte compact descriptor table. Local host replay passes 3,052 records mapping
to 30 descriptor ordinals. This consumer check does not close the supplied
wall-table pointer provenance, class-specific geometry, UVs or live color parity.
The floor cache/material extraction chain is now packaged in
[build_cave_assets.py](build-cave-assets.md), separately from the smaller geometry
pipeline below. The wall consumer binding check remains a reported local result.

## Godot integration

[The Godot repository](https://github.com/KForestland/lands-of-lore-unified-godot)
contains a full recovered static cave walk view: 1,953 floors, 1,939 ceilings,
1,338 boundary quads and 955 provisional interior spans. The local full-world
79-waypoint tour and 119 checkpoint routes pass. Capsule dimensions, movement,
lighting, floor UVs and wall spans remain experimental. Fly mode is inspection
assistance, not original gameplay. Original game assets are excluded from Git.

## Run the packaged pipeline

Use Python 3.10+ and install the repository requirements. From the repository:

```sh
python3 tools/draracle/run_geometry_pipeline.py --game-root /path/to/your/lol2 --out /path/to/local-output
python3 -m unittest discover -s tools/draracle -p 'test_*.py'
```

The game root must contain `DAT/L1_DC.MIX` and `LOLG.DAT`. Paths are configurable;
no Bob-specific path or precomputed evidence directory is required. Supported
files are pinned to these SHA-256 hashes; other editions fail explicitly:

- L1_DC.MIX: `6384ec4d4d78f1aadfc1f154d924e1e20636af037cf5af68fe35af8478854345`
- LOLG.DAT: `b27a35341c6e877e40b1540b6482748e7a750c605fefe6452431b18a5d766775`

Outputs include corrected geometry JSON/OBJ, connector and slope checks, lossless
wall records, and original code excerpts. Generate them locally; do not commit
asset dumps. This command covers geometry/wall records. Use the separate
[asset builder](build-cave-assets.md) to generate diagnostic full-cave Godot assets
from the matching populated cache.

## Next work

1. Close wall table loading, native span classes and wall UV/material integration.
2. Extend the packaged asset builder beyond the matching populated cache: recover
   cache construction from retail archives and support additional editions.
3. Restore special openings, moving objects, action dispatch and hazards.
4. Validate a faithful playable cave before claiming full-game restoration or
   native patch compatibility. Audio remains a later task.
