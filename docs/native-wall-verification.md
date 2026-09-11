# Expanded native wall verification

The ordinary wall checks now cover 3,044 distinct original records out of 3,052:

- Flat middle classes 4/12: 1,064 source cases and 40 synthetic cases.
- Flat upper/lower classes 0/8: 834 source cases and 320 synthetic cases.
- Sloped middle classes 4/12: 241 source cases, including original slope helper instructions.
- Sloped upper/lower classes 0/8: 764 source cases, 171 active; 597 use neighbor slope heights.

All pass with zero coordinate/active-flag mismatches. The upper/lower test also
checks the lower-wall vertical texture-offset byte correction for clipped tops,
including absent-ceiling selectors, all six scale modes and byte wraparound.
No source record in that selected flat set changes its offset, so the correction
branch is exercised by synthetic cases rather than claimed as an observed cave effect.

The interpreter's approved helper calls are F4504, F4590 and F49FC; unknown calls
or instructions fail explicitly. The new sloped middle cases compare native
helper execution with the earlier independent slope port. Loader/global pointers
are still supplied by the host fixture. These checks are not live runtime captures
and do not prove native rendering, UVs, material visibility or collision semantics.

The remaining eight records need runtime preparation/dispatch checks for
region 1851, whose serialized neighbor IDs are absent. Geometry checking percentages
must not be described as overall cave readiness percentages.

Run the existing configurable `run_geometry_pipeline.py` to reproduce all six
wall groups, or run their individual tools with `--game-root` and `--out`.
The extended pipeline and all 25 existing geometry/cache/material unit tests pass.
No Godot wall replacement is made by this evidence-only update.

For sloped upper/lower walls, the neighbor helper maps the edge start vertex to
neighbor corner k and uses corner (k+3)&3 for the other endpoint. The verifier
requires an unambiguous reciprocal indexed edge before comparing this model.
Neighbor ceiling slopes supply upper-wall bottoms without the flat floor clamp;
neighbor floor slopes supply lower-wall tops without the flat ceiling clamp or
vertical-offset correction. Own slope heights supply the opposite boundary.
Only 171 of these 764 records have a positive height at either endpoint, which
is another reason not to turn every serialized wall record into solid geometry.

Connector middle classes 4/12 add 88 source cases, all active, with zero
coordinate or active-flag mismatches. The interpreter now executes the native
signed division used to recover the owning region index, and passes source
byte6 bit7 as the original routine's third argument. For a connector neighbor,
class 4 joins the own edge start to connector corner k+1; class 12 joins connector
corner k to the own edge end. k is 0 when the connector's first link points back
to the owner, otherwise 2. Heights come from the owner unless source bit7
selects the connector. This checks the routine with serialized inputs; it does
not close constructor call-site provenance or collision behavior.

All 88 source records have bit7 clear. The bit7-set height selection is a
disassembly interpretation, not a branch covered by these source cases.

Special upper/lower classes add 53 source cases (all active), covering flat
connector-associated records and three subdivision-associated records. Coordinates,
active flags and vertical-offset bytes match the independent model. The original
constructor at 11472B..114738 passes source byte6 bit7 to 114AA4, confirming that
argument's source on the ordinary dispatch path.

The eight remaining records are 245..252, all owned by region 1851. Its four
serialized neighbor IDs are FFFF. The upper/lower routine dereferences a neighbor
without an absent-neighbor guard; a zero-filled host allocation cannot establish
the actual result. Runtime preparation/dispatch for this region remains open.
Do not interpret the record coverage as proof that every serialized region is
passed unchanged to this routine during gameplay.

The pipeline now ends with `audit_wall_coverage.py`: it checks disjoint record
IDs across all six groups, exact coverage of the source table, and reproduces
the eight deferred cases reaching the FFFF region dereference. WallReplay
rejects reads from that sentinel-derived region address before reading host
memory. This is an input/provenance diagnostic, not evidence of a live game bug.
The audit emits `coverage/wall_coverage.json`, including incoming links to region
1851, so downstream work can preserve explicit unresolved records.

## Edge-mask update

`verify_wall_edge_mask.py --game-root GAME --out OUT` checks 15,360 synthetic
cases against original F5DFB/F5DFD and F5E82..F5EA9 instructions. The edge's
high-nibble bit is always set; its low-nibble rejection bit is set when helper
1338B0 returns zero or the supplied signed facing score is positive. Other bits
are preserved. F5D93 skips an edge whose high bit is already set. This is a
per-edge computed marker, separate from the low bits used by wall eligibility.

The score-producing arithmetic is deliberately bypassed in this replay. The
original uses signed multiply high halves and 32-bit subtraction; replacing it
with an unrestricted floating-point cross product would require verification.
Helper semantics, edge lookup tables, camera inputs, neighbor propagation and
live visibility are still open. This check does not enable cave wall culling.
The portable wall build runs this check automatically.

## Fixed-point edge-facing score

`verify_wall_facing.py --game-root GAME --out OUT` replays F5E03..F5E7B
for 17,756 synthetic cases, including signed limits and deterministic random
coordinates. Original LE data tables EB24/EB34 select endpoint pairs (1,0),
(2,1), (3,2), (0,3). Each coordinate difference wraps to signed 32 bits.
The score subtracts the independently extracted signed high halves of
`(observer_x-a_x)*(b_y-a_y)` and `(observer_y-a_y)*(b_x-a_x)`,
then wraps the subtraction. A positive score sets the edge rejection bit.

This is not interchangeable with the sign of an unrestricted cross product:
a=(0,0), b=(0,1), observer=(1,0) gives a native score of zero.
The observer inputs originate at offsets 19/1D of the object referenced by
global B8668 (F5C22..F5C4A); equivalence to renderer camera globals remains
open. Helper 1338B0 contains a separate coordinate transform and clipping
path, still to be replayed. This check is included in the portable build,
but does not enable live culling in Godot.

## Horizontal camera transform and camera-plane clipping

`verify_wall_camera_clip.py --game-root GAME --out OUT` checks 3,072
synthetic horizontal transforms and 2,401 zero-depth clipping cases against
the original instructions. Transform inputs include signed wrapping and six
rotation coefficient pairs. The code subtracts camera globals FE470/FE478,
then multiplies by FE4D8/FE4D4 with signed products shifted by 16 bits.
Endpoint results are checked separately; the second depth is observed in ESI
before its final store. Unused vertical scratch inputs are supplied as zero.

The zero-depth stage rejects both-negative depths (441 fixtures), retains
zero-depth endpoints, and clips one-negative-depth edges with signed integer
division truncated toward zero. Clipping fixtures deliberately avoid overflow.
This is the camera plane, not the later depth-65536 projection guard.
Optional facing shortcut, horizontal outcodes, projection/window bounds and
live camera setup remain unresolved. These checks run in the portable build;
the playable cave has not yet adopted this incomplete visibility helper.
