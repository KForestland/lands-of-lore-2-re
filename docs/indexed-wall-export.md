# Indexed wall texture export

`tools/draracle/export_wall_index_textures.py` exports variant0 palette
indices from the hash-pinned named cavern cache for the existing walls.json.
Arguments: --game-root, --wall-assets (current wall_review directory), --out.
It writes27 grayscale data textures, a palette and a manifest for2373 spans.
Each indexed texture resolves exactly to its current RGB preview. A9 uses
column-major conversion; other raw formats preserve current row-major
preview assumptions, not newly verified native orientation. Original
textures and palette remain local generated assets, excluded from Git.

The Godot indexed_cave_wall_review scene consumes these assets. Three
perspective checkpoints pass a combined1555200-pixel GPU/CPU palette
resolve comparison. Floors, roof and props are outside this diagnostic;
see the Godot repository's docs/indexed-cave-walls.md for scope and commands.
