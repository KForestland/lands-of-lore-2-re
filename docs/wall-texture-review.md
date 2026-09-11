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
