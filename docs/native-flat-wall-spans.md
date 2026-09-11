# Native flat wall span check

The bounded replay now runs the original routine at analysis address 0x114AA4
through its return for flat ordinary middle-span classes 4 and 12. Neighboring
floor/ceiling intervals are intersected; absent neighbors use the region's own
floor-to-ceiling range. Corner coordinates and the active flag are compared with
an independent interval calculation. Slopes, subdivisions, special connectors,
and upper/lower classes 0/8 are deferred, not synthesized.

Results on the pinned cave: 1,064 records checked, 1,045 active spans, zero
mismatches. Forty synthetic cases cover every edge and both supported classes,
with absent neighbors, intersecting heights and disjoint ranges. The local shell
comparison finds 1,044 exact boundary corner-set matches and one active span
across a neighbor opening. This supports those boundary coordinates but does not
justify turning the opening span into a solid wall. Winding, visibility, texture
UVs, native collision and loader-to-global provenance remain outside this result.

```sh
python3 tools/draracle/lol2_verify_flat_wall_spans.py --game-root /path/to/lol2 --out /path/to/flat-wall-evidence
```

The geometry pipeline runs this check too. Outputs contain per-record fixed-point
corners, active flags and original code excerpts, generated from local files.
This is host interpretation of a call-free subset of the original routine, not
live gameplay execution. The 1,988 deferred records still need their own checks.
The existing Godot map is unchanged by this evidence update.
