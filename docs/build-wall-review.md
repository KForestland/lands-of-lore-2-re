# Rebuild the diagnostic wall review

From the RE repository:

```sh
python3 tools/draracle/build_wall_review.py \
  --game-root /path/to/lol2 \
  --out /path/to/wall-review-build \
  --godot-project /path/to/lands-of-lore-unified-godot
```

Requires Python3, Capstone, Pillow and the matching populated CDCACHE used by
the existing cave extraction. The Godot checkout must include the wall review
scene. Original game files are read only. Omit --godot-project to build assets
without updating a checkout. Only generated wall-review files are copied; no
scene code or existing files are deleted.

The command runs geometry and coverage verification, corrected texture extraction,
mip/offset/orientation/projection/addressing checks, and the diagnostic UV export.
It writes a SHA256 build_manifest.json and godot_assets directory. The pinned
build produces2373 walls,27 materials and60 files (59 stored-variant PNGs plus
walls.json). A fresh build in a path containing spaces matches all60 working
review assets byte-for-byte.

Launch the Godot checkout's tools/lol2/run_wall_review.sh. N/P browse walls;
V cycles stored variants. Orientation concerns, transparency, variant layouts,
playback timing and live rendering parity remain unresolved. The six crossing
spans, unsupported material and eight geometry exceptions remain explicit.
