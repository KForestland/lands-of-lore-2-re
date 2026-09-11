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

## Horizontal screen rejection

`verify_wall_screen_bounds.py --game-root GAME --out OUT` checks 5,292
bounded synthetic post-clip cases against 133A49..133BBD, with three supplied
projection/window settings. All three exits are exercised: 486 initial
shared-outcode rejections, 674 window rejections and 4,132 acceptances.
Boundary fixtures include depth 0, 1, 65535, 65536 and 65537.

The first outcodes compare horizontal position against plus/minus depth.
A shared bit rejects; opposite-side outcodes accept immediately. Endpoints
inside this initial wedge are projected with a depth-65536 guard, then
compared with FE424/FE428 using scale FE480. Near endpoints can take a
conservative early acceptance. The replay preserves sequential scratch
updates, including use of the already-projected first horizontal value when
the second endpoint needs depth clipping. No mathematical cleanup is applied.

This verifies a bounded portion of the original helper, not whole-helper or
live visibility. Optional facing shortcut and runtime camera/window setup
remain open. The portable build includes this check.

## Joined visibility helper

`verify_wall_visibility_helper.py --game-root GAME --out OUT` runs continuously
from 1338B7 (after stack allocation) to all four return decisions. No stage
outputs are substituted. 9,442 bounded synthetic cases match the composed
Python model, exercising 1,707 initial-outcode rejections, 710 window
rejections, 2,196 behind-camera rejections and 4,829 acceptances.

The optional fifth argument enables an early acceptance: the signed
high-product facing score of the transformed endpoints against the origin
is nonpositive. This changes 1,599 paired fixture results. It is an acceptance
shortcut, not a generic backface rejection. Fixtures include both values of
this argument, six rotation pairs, three windows and varied unused vertical
scratch words. The caller's region comparison supplies this flag by disassembly;
its live state has not been captured.

This joins the previously separate transform, clipping and screen-boundary
checks. It remains a host instruction replay with synthetic coordinates, not
guest execution. Prologue/epilogue, runtime camera/window setup, edge-mask
neighbor propagation and final draw submission remain outside this proof.
The portable build runs this joined check alongside the narrower checks.

## Reciprocal edge-mask propagation

`verify_wall_neighbor_mask.py --game-root GAME --out OUT` checks 16,128
cases against original F5EAF..F5EEF. Fixtures cover all 256 existing masks,
null neighbors, each reciprocal slot, missing reciprocal links and duplicate
links, with zero/nonzero helper results and negative/zero/positive scores.

A null neighbor causes no write. Otherwise the search compares slots 0, 1
and 2, choosing the first match. If none matches it uses slot 3 without
checking that slot. This fallback is recorded as original behavior, not
asserted to occur in the cave's live topology. The chosen edge always gets
its checked bit. It gets its rejection bit when the helper returned zero
or the signed facing score is nonpositive; all existing bits are preserved.
For a successful helper and zero score, the current side remains eligible
while the neighbor side gets rejected. This is not a blanket copy of the
current edge mask. The helper-zero path does not depend on the scratch
score even though the original reads it before checking the helper result.

The portable build includes this check. Actual runtime neighbor construction,
traversal scheduling, camera/window setup and live rendering remain outside
this synthetic replay.

## Runtime neighbor constructor

`verify_wall_neighbor_constructor.py --game-root GAME --out OUT` checks
F59D4..F5AAE against all 1,954 cave region records in both supplied object
flag-40 modes (3,908 cases). The ordinary mode retains a neighbor only when
the two region words at offset 18 match (5,926 directed links in this fixture).
Mode 40 instead requires the neighbor's region flag 80 (28 links). These
counts describe separate hypothetical mode assignments, not the live graph.

FFFF source neighbors become null pointers and set the corresponding bit
in object byte 9D. Filtered neighbors become null without setting that bit.
The constructor also clears traversal bit 4 in object byte 9F. Non-null
pointers follow allocation_base + (neighbor_id-base_region_id)*160.
The replay supplies a contiguous allocation covering all regions with base
index zero; actual allocation range and selection of object flag 40 remain
open. Full raw neighbor records must not be treated as runtime links without
these filters. The portable build now includes this check.

## Source-selected neighbor mode

`verify_wall_neighbor_mode.py --game-root GAME --out OUT` verifies
F58D9..F58FF in 2,466 cases. Region flag 80 sets object flag 40; other object
bits are preserved. Fifteen cave regions select this mode. The constructor
replay now also uses source-selected modes: 5,862 cases total, with 5,894
retained directed links in the source-selected fixture. Every retained link
has a reciprocal link in this fixture; missing-link fallback is not needed.

Allocation setup disassembly F5853..F589A takes the first region from a
word at descriptor offset 0 and object count from byte 17, requesting
count*160 bytes from A1958. Descriptor provenance and allocator execution
remain open. The constructor fixture still supplies a single contiguous
allocation for all cave regions, so its graph is not yet a live allocation
validation. Mode selection itself is no longer hypothetical.

## Allocation request and descriptor caller

`verify_wall_allocation_request.py --game-root GAME --out OUT` verifies
F5853..F5889 for 1,536 synthetic descriptors, covering every byte-sized
count and six start indices. The starting region address is base+first*44;
the requested object allocation is count*160 bytes. Zero count is passed
through by this block, which contains no range validation.

Caller disassembly E18BE..E18D9 computes descriptor index relative to global
22D10 with stride 42. E1962/E1963 passes that descriptor to F584C. This
connects allocation setup to the runtime descriptor table, but the file
loader for this table remains unresolved. No actual cave allocation range
is inferred from synthetic request fixtures. Included in the portable build.

## Source allocation ranges

`audit_wall_allocation_ranges.py --game-root GAME --out OUT` audits the
pinned cave table at header A4 (offset 265757), with count AC (173). Its
26-byte descriptors use the first word and byte 17 for allocation ranges.
They cover all 1,954 regions exactly once, requesting 312,640 object bytes
in total, excluding allocator overhead. No overlap or uncovered region.

Loader E24D4 allocates count*42, reads 26 bytes per record, clears byte 10,
masks byte 19 to its low nibble and zeroes the 16-byte tail (disassembly).
9D076 calls it and 9D083 stores the result at world+38. Handoff from that
field to global22D10 remains to be closed; actual allocations are not captured.
The new range audit is source evidence, not a full loader instruction replay.

## Neighbor replay within recovered allocations

The neighbor constructor now adds a fourth fixture using each of the 173
source allocation ranges independently. Object addresses remain synthetic,
but each replay uses its actual first-region index and source-selected mode.
All 1,954 region cases pass, raising constructor coverage to 7,816 cases.
The 5,894 retained directed links all stay within their owning allocation;
no retained pointer crosses a recovered allocation boundary. Results agree
with the earlier whole-table fixture.

The portable build also runs the exact-partition allocation audit. This
closes the earlier assumption of base-region index zero for every object.
The world+38 to global22D10 handoff and live allocator/camera state are still
unverified; these checks do not change the playable scene.
