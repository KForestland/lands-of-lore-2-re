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
