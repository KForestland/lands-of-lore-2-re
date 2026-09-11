# Prop frame mirroring

The original F1D1E path forwards frame byte +2 to draw-input +0x12.
Native setup at analysis address 129AC8 masks 0xC0 and selects the
left/right and top/bottom destination corner. Bit 0x40 reverses horizontal
drawing; bit 0x80 starts at the bottom with negative row pitch.
Addresses are static analysis addresses, not DOSBox guest addresses.

Run from the repository root:

```sh
python3 tools/draracle/verify_prop_flip_setup.py --game-root /path/to/lol2 --out /tmp/prop-flip
```

The hash-pinned bounded instruction replay checks all 256 flag values on
two unclipped screen rectangles: 512 cases, zero mismatches. Its scope is
destination start and row pitch; full clipping, sampling, shading and
framebuffer rendering are not replayed. No new live capture is claimed.

Godot applies these flags with material UV scale/offset, caching by both
descriptor and flags so shared sprites can have different orientations.
Current cave preview: 142 horizontal flips among 442 original placements,
zero vertical flips. Rendered stalagmite record365 and headless loading
passed. Alpha and fixed-Y billboarding remain provisional.
