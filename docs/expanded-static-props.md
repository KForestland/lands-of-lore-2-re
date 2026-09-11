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

Rock formations expanded (2026-09-11): resources297/298/299/300/301 added
through the existing28E decoder. Nine total sprite resources pass44 mip
images/3142 row checks. Thirteen additional static templates supply366
placements; total1010. All644 previous placement records remain identical.
Original positions, state dimensions and trim/flip fields retained.
Headless1010-prop smoke passed; GPU252 hanging rock and273 floor rock
visually inspected.45 tests pass. Both local Godot trees updated.
Source artifacts: lol2_out/draracle_rock_previews_2026-09-11/ and
lol2_out/draracle_rock_props_2026-09-11/. Alpha, billboarding and shading
remain provisional; no prop collision or creature placement changes.

Additional pillars (2026-09-11): resources295/296 decoded with the28E
row parser;11 total sprite resources now54 mips/4058 rows checked.
Templates56/57/60/61/62/64 add86 placements, total1096; previous1010
records unchanged. Template60 has no placements. Height replay expanded
with explicit --templates selection and source flag checks:174 source
cases plus72 synthetic,zero mismatches. GPU169/363 inspected both styles;
1096-prop smoke and45 tests pass. Both Godot trees updated. Source artifacts
lol2_out/draracle_pillar_{previews,heights,props}_2026-09-11/.
Alpha, billboarding and lighting remain provisional; no prop collision
or enemy placement added.
