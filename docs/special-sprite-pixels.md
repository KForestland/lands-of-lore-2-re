# Special sprite pixels

Row flag8000 correlates with source palette index1. The renderer's row
jumptable selects12B41B for flags4/6 and12B738 for68/70 (horizontal mirror).
At12B454 and12B771 it compares the source with1. Zero skips the write.
For1,12B62B/12B948 read the destination and remap it through a table whose
base is4000. Other source indices use the ordinary source shade lookup.
These are static analysis addresses, not guest addresses.

`verify_sprite_special_pixels.py` replays the original first-pixel
instructions for256 source ×256 background indices ×2 directions:
131072 cases, zero mismatches. Distinct synthetic lookup tables verify
which value indexes which table; their colours do not establish the
original runtime remap contents. Full clipping/scaling is outside scope.

`extract_special_sprite_masks.py` exports193/194/474/475/476 using an
explicit opt-in to the existing row parser. Both4000/index0 and8000/index1
hint consistency are checked.23 mips contain5119 index1 pixels. Colour
PNGs omit indices0/1; mask PNGs mark index1 white. review.html displays
both layers, not a final composite.47 unit tests pass, including opt-in
and hint rejection. Original game assets remain outside Git.

Run either tool with --game-root /path/to/lol2 --out /path/to/output.
Next recover native table4000 and implement destination remapping in Godot.
No new scene props were added in this pass.
