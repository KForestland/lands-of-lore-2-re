# Cave block sprite decoder

The native125FC4 routine selects the12607C row callback when the image
flags include0x1000. Its12607C–1261B3 body divides the requested pixel row
by4, checks frame bytes22/23, and reads a16-bit row offset relative to
frame+24. Each row consists of two-byte commands: zero skips blocks,
nonzero copies a run of16-bit codebook indices. Each index addresses16
bytes; the requested row within that4×4 block selects four bytes.

`extract_block_sprite_frames.py` translates this algorithm. Frame dword8
selects one of17 section9 triples, whose offset and packed length locate
an LCW-compressed codebook in section8. That association is supported by
source structure and coherent output, not a replay of the resource loader.
The middle triple value is a storage allocation, not decoded length.

```sh
python3 tools/draracle/extract_block_sprite_frames.py --game-root /path/to/lol2 --out /tmp/block-sprites
```

Results:1324 frames,17 codebooks. Header size follows record length minus22.
All referenced row streams, dimensions, LCW commands and block indices pass
bounds checks. All1324 records have unread tail bytes (maximum198); these
are counted in frames.json and remain unexplained. They are not silently
promoted to padding or decoded pixels.42 unit tests pass, including block
row order, index/run rejection and overlapping LCW copies.

Sampled output visually shows guards and roaches in different poses and
directions. Resource967 is a guard despite being adjacent to roach-like966;
resource adjacency is not a valid creature binding. The generated review.html
provides a manual resource slider. Original palette, provisional index-zero
alpha; no animation timing, native shade, named-state binding, spawn or
Godot creature integration is claimed. No new live capture was performed.
