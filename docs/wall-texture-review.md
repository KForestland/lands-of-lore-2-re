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
