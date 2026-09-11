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
