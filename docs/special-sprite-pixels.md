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
The separate Godot indexed compositor matches all 256000 pixels of its
640×400 CPU reference. The playable cave still has 1183 static props;
its RGB buffer does not retain exact palette indices.

## Initial table binding recovered

`verify_special_pixel_table_binding.py` checks seven LE fixups and the
hash-pinned native loader instructions. Renderer immediates at 12B441 and
12B75E relocate to **object4 + 0x4000**; ordinary shade bases relocate to
object4 + 0. Object4 has virtual size 0x14200 and no file-backed pages.
Inspecting initialized object5 at offset4000 was therefore the wrong
object and explained the unrelated strings found there.

Loader 9D894 reads the 0x6A2-byte cache header onto its stack. At 9D9B3 it
assigns object4 + 0 to the pointer in object5 + 0x223E0. At 9DBAF it seeks
to header dword +0x18 (section4; the preceding push accounts for the
stack operand +0x1C), then reads 0x4200 bytes into that pointer at 9DBCC.
The named cavern cache section has exactly that length: 66 rows of 256.
Thus the **initial** special-pixel table is section4 row64, file offset
18850. This is static loader provenance, not a live memory capture or
proof that later code never modifies the table.

Run the verifier with --game-root /path/to/lol2 --out /path/to/output.
It writes binding.json and the local-only initial_remap.bin. The fixture
builder now requires this verification and embeds the evidence in
fixture.json. The table bytes and reference image are unchanged from the
previous candidate fixture. 50 unit tests pass, including malformed and
unsupported relocation rejection. Original assets remain outside Git.

Next: preserve palette indices through the cave render path, or explicitly
scope an approximate RGB fallback. Ordinary source shading and later
runtime table changes remain separate research questions.

## In-cave overlap diagnostic

`export_special_sprite_indices.py` exports resource474 and the verified initial
remap for the Godot special_cave_review scene. It checks the pinned inputs and
records650 special pixels in the138×83 source. Two diagnostic copies composite
in sequence over the cave with verified intermediate index/RGB results and
controlled depth blockers. These are not original placements or native draw
order evidence. See Godot docs/special-cave-review.md for validation and scope.
