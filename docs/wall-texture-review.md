# Original wall texture review

Run from the repository root:

```sh
python3 tools/draracle/extract_wall_texture_review.py --game-root /path/to/lol2 --out /path/to/wall-review
```

Requires the pinned populated cache used by the cave asset pipeline. Open
`review.html` in the output folder. `wall_textures.json` records source offsets,
pixel hashes, descriptor references and every associated wall record. Original
indexed pixels and file-palette PNGs are written locally, never bundled here.

The pinned cave yields 29 raw-indexed materials, 333 variant/mip images, and
3051 associated wall records. Descriptor284 (one wall record) has a non-raw
payload size and is explicitly deferred. Counts refer to images and references,
not distinct visible surfaces. First variants appear in the gallery.

Every extracted mip has validated dimensions, payload bounds, variant boundary
and original header. This does not establish native UV placement, transparency,
playback order/timing, shading or runtime pointer provenance. The eight geometry
exceptions remain exceptions even where their texture payloads are available.

`verify_wall_mip_ids.py --game-root /path/to/lol2 --textures
/path/to/wall-review/wall_textures.json --out /path/to/mip-check` checks the
original 1326FA..13270B resource-index arithmetic. All 142 mip cases for the
29 extracted materials pass: identifier + mip * variant_count. This is the
base resource ID, not playback or UV selection. The caller at 11495E..11496D
loads renderer global E890 and invokes callback +28 with wall object, compact
descriptor and 15. Active callback identification remains open.

`inspect_wall_dispatch.py --game-root /path/to/lol2 --out /path/to/dispatch`
recovers the two stored callback slots using the existing embedded-MZ/LE page
mapping. Tables 5D18 and 5DA4 have +28 stored values CDC08 and DFC88 at file
offsets 1863012 and 1863152. These are not resolved runtime code addresses.
LE fixup resolution and live renderer selection remain necessary before UV work.

Relocation follow-up: the inspector now parses the relevant fixup page, rejecting
unsupported formats. Both slots have internal 32-bit offset fixups targeting
object2. Its page map resolves them to file15DC2C and file16FCAC, or analysis
addresses126C2C and138CAC under the project's file-minus-37000 convention.
These analysis addresses are not live guest addresses. Fixup records are at
file518087 and518339 respectively. Both targets begin with the expected four
register pushes; runtime renderer selection is still not captured.

In the first target, 127561 dispatches on C000 scale bits; 12759C..1275B3
reads wall bytes30/31 and shifts each left16. This identifies original UV-offset
consumption but does not yet establish full scale/orientation/projection rules.

`verify_wall_uv_inputs.py --game-root /path/to/lol2 --out /path/to/uv-inputs`
replays integer offset conversion12759C..1275B3 for all3052 serialized offset
pairs and512 synthetic pairs; zero mismatches. Each unsigned byte becomes
byte<<16. This verifies input arithmetic even for records whose geometry or
runtime dispatch remains unresolved, not their renderability.

Original initialized double constants at403C/4034/402C are2,.5,.25. The four
scale branches therefore divide the horizontal direction by length times
2,1,.5,.25; their stored vertical coefficients are respectively±.5,±1,±2,±4.
The tool checks constants and immediate coefficients, not x87 normalization.
Orientation flags, constructor-adjusted offsets and final projection remain open.

Projection block12766A..1277A4: `verify_wall_projection.py` checks256 synthetic
cases, seven output coefficients each, against independent formulas. Let X/Y/Z
be incoming locals440/444/448, U/V/W be4F0/4EC/4E4, sx=FE480/65536 and
sy=FE484/65536. Outputs relative to the renderer stack are:

| Offset | Formula |
|---|---|
| 3CC | -W X sx sy |
| 3D0 | U Y sx sy |
| 3D4 | -U W sx sy |
| 3D8 | W Z sy |
| 3DC | -V Y sy |
| 3E0 | V W sy |
| 3F0 | sx (V X - U Z) |

The original floating-point instruction order is interpreted with host doubles
and float32 stores; integer setup is supplied. Binary-exact inputs avoid rounding
ambiguity. This verifies algebra, not guest x87 precision/control-state parity,
orientation setup, camera semantics or downstream rasterization.

Orientation setup: `verify_wall_orientation.py --game-root /path/to/lol2
--geometry-evidence /path/to/geometry-pipeline-output --out /path/to/orientation`
checks four branches per verified wall:12176 cases over3044 records, zero
mismatches. Vertex order follows the wall record geometry:0/1 upper endpoints,
2/3 lower endpoints. Orientation modes0,1,2,3 select anchor/other pairs(0,1),
(1,0),(3,2),(2,3). Modes0/1 use minimum upper Y;2/3 use maximum lower Y.
Horizontal direction is anchor minus other endpoint. Results export the five
intermediate values X,Y,Z,U,V for the source-selected orientation.

This interprets original instruction order with host doubles and float32 stores.
World vertices are supplied as synthetic transformed inputs; it does not replay
camera transformation or clipping. Constructor flag transfer and final Godot UV
parity are not established by this test. The export is an intermediate basis,
not ready-to-use normalized texture coordinates.

The bit8 rasterizer branch12D54F..12D584 clamps each signed coordinate to zero,
adds its 16.16 offset, logically shifts for the mip level, then wraps by that
mip's width/height in16.16 units. `verify_wall_uv_wrap.py` checks870 cases across
58 extracted mip layouts, including negative coordinates, boundaries and offsets.
Use `--game-root`, `--textures` pointing to wall_textures.json, and `--out`.
No-overflow test inputs are used; arbitrary32-bit overflow is not modeled by the
independent formula. Other flag branches and final Godot UV parity remain open.

Addressing follow-up: the verifier now starts at12D4D1 and covers all three
branches, including flags8+16 together (bit8 wins).3480 cases across58 mip
layouts pass against the independent `wall_uv_addressing.address_uv` port.
Without either bit, both coordinates shift arithmetically and clamp; offsets
are ignored. Bit16 alone repeats U with its offset but clamps V without its
offset. Bit8 repeats both with offsets. Clamp upper limits are dimension<<16
minus1. The portable function rejects unverified overflow inputs.

This reusable function accepts pre-addressing renderer16.16 coordinates. It is
not yet a world-space-to-Godot UV converter; projection integration, filtering,
transparency and live visual comparisons remain outstanding.

`export_wall_uv_fixture.py` accepts `--game-root`, `--geometry-evidence`,
`--textures` (wall_textures.json), and `--out`. It selects a verified active flat
wall with material134 and repeating addressing, exporting wall_fixture.json and
wall_preview.png. The pinned selection is record2168, region6:222.800359 by228
original units, one texel/unit, zero offsets.15 synthetic camera samples agree
with the recovered projection coefficient ratios. This is a geometric UV
inference, not live renderer parity. The512x256 preview is a rescaled sampling
panel, not an aspect-correct in-game screenshot. No scene replacement occurs.

`export_flat_wall_uvs.py` uses the same four arguments as the single fixture.
The pinned export contains946 rectangular repeating static-material walls,
Godot-coordinate vertices and unwrapped normalized UVs. Do not wrap vertex UVs:
that loses repeats during interpolation. A16-panel local gallery accompanies
flat_wall_uvs.json. Among3044 checked records, exclusions are664 inactive,
1304 other addressing modes,50 unsupported/multi-variant materials and80
nonrectangular spans; eight additional geometry records remain unresolved.

These are diagnostic inferred UVs. Pixel previews are file-palette samples,
not validated lighting/transparency. Texture dimensions are original. Camera
parity, source material semantics and scene integration remain outstanding.

User-reported preview correction: walls0,131,1933,1961 exposed an incorrect
row-major assumption. A9/80A9 PNG previews now reorder source pixels from
index=x*height+y into PNG rows. Original .indices bytes and source hashes remain
unchanged. Rectangular and square ordering tests added. This corrects the wall
review extractor only; other extraction lanes and non-A9 layouts need auditing.
Descriptor3 resolves visually to a dog/photo test image; wall0 is labelled as
unresolved cave use, not silently replaced with rock. Header/extent checks alone
did not establish image layout. The correction is visually supported, not a
new claim of complete native sampling parity.

Layout audit follow-up: column_major_to_rows now lives in lol2_pixel_layout.py
and is shared by the wall review, cave A9 exporter (PNG and shaded canvas), and
80A9 floor variant preview. Non-A9 variant layouts remain explicitly unverified.
127 A9 mip previews and five80A9 variant/mip previews are corrected. All207
original indexed payload files across the cave/variant exports remain byte-identical.
The complete portable asset build passes into a separate output directory;
existing playable demo assets are not replaced by this audit.

Demo refresh audit: the remaining floor E1 descriptors156/161/285 are square,
so row/column candidates are simple transposes and both look coherent. Visual
inspection cannot settle their orientation; they remain unchanged/unverified.
The corrected A9/80A9 pipeline was exported to the working demo with a prior
asset backup. Exactly nine PNGs changed; geometry/traversal files are unchanged.
Godot's full-map sprint checkpoint smoke passed119 routes with zero resets.
This tests loading/traversal, not live-game texture-orientation parity.

Expanded rectangular export:2035 walls/22 static textures, including clamped
and horizontal-repeat modes. For rectangular spans, clamped axes use descriptor
size divided by span extent; repeating axes use recovered world scale. Offsets
apply only to repeating axes. Existing946 repeat-both entries retain their UVs.
The diagnostic Godot review uses per-axis clamp/repeat fragment sampling. Native
mip rounding, transparency and camera parity remain unverified. Exclusions now:
664 inactive,50 unsupported/multi-variant,295 nonrectangular, eight unresolved.

Wall2702 palette audit: record2702, region493, descriptor600, A9, one variant.
All16384 RGB pixels match original column-major indices and the file palette;
the preview exporter adds no blue tint. This does not establish live shade-bank,
transparency or material semantics. Reproduce with audit_wall_palette.py using
--game-root, --textures (wall review directory), --record2702 (as separate
argument/value: --record 2702), and --out.

Sloped diagnostic extension:2327 exported walls, including292 additional
nonrectangular spans. World-space UV anchoring uses maximum upper height for
top modes and minimum lower height for bottom modes, matching the inverted-height
renderer frame.1168 original orientation-block checks pass for these292 spans
across four modes. All2035 previous rectangular UV sets are unchanged. Three
crossing-boundary spans remain deferred;50 materials and664 inactive records
remain excluded, plus eight unresolved geometry records. Godot review loads2327
meshes/23 textures. Native camera/clipping and material visibility parity remain open.
