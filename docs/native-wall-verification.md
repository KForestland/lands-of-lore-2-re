# Expanded native wall verification

The ordinary wall checks now cover 2,903 distinct original records out of 3,052:

- Flat middle classes 4/12: 1,064 source cases and 40 synthetic cases.
- Flat upper/lower classes 0/8: 834 source cases and 320 synthetic cases.
- Sloped middle classes 4/12: 241 source cases, including original slope helper instructions.
- Sloped upper/lower classes 0/8: 764 source cases, 171 active; 597 use neighbor slope heights.

All pass with zero coordinate/active-flag mismatches. The upper/lower test also
checks the lower-wall vertical texture-offset byte correction for clipped tops,
including absent-ceiling selectors, all four scale modes and byte wraparound.
No source record in that selected flat set changes its offset, so the correction
branch is exercised by synthetic cases rather than claimed as an observed cave effect.

The interpreter's approved helper calls are F4504, F4590 and F49FC; unknown calls
or instructions fail explicitly. The new sloped middle cases compare native
helper execution with the earlier independent slope port. Loader/global pointers
are still supplied by the host fixture. These checks are not live runtime captures
and do not prove native rendering, UVs, material visibility or collision semantics.

The remaining 149 records need checks for special/subdivision handling and
other deferred combinations. Geometry checking percentages
must not be described as overall cave readiness percentages.

Run the existing configurable `run_geometry_pipeline.py` to reproduce all four
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
