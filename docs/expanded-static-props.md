# Expanded static cave props

Expanded static props (2026-09-11): added202 placements using already
decoded resources278/302/417, templates13/14/15/17/18/19/20/22/46.
Total644; all442 previous prop records compare identical. Source single-state,
single-frame, resource flags and dimensions pass existing exporter checks.
Both Godot copies updated. Headless644-prop smoke and45 tests pass.
GPU checkpoint14 inspected. Prop inspectors343/134 were occluded by walls;
fixed110-unit camera offset needs improvement, not treated as visual proof.
No prop collision or creature spawn changes. Creature frame binding remains
open. Source artifact lol2_out/draracle_expanded_props_2026-09-11/.

Reproduce with export_cave_prop_preview.py and the existing prop sprite
previews.55 new hanging-vegetation placements,55 stalagmite placements and
92 boulder placements retain original anchors, state dimensions and trims.
No new sprite encoding or guessed placement is introduced. Alpha, lighting
and billboard parity remain provisional.
