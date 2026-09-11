# Cave sprite sequences

`extract_cave_sprite_sequences.py` decodes original 0x2C6 row-span sequences
for resources 145,166,196,260,449,862,872,882,887,897,907,946.
The existing 0x28E row decoder accepts this header only when explicitly requested.
Each variant carries its own payload length; descriptor size describes the
first variant, so multiplying it by the variant count is incorrect.

```sh
python3 tools/draracle/extract_cave_sprite_sequences.py --game-root /path/to/lol2 --out /tmp/cave-sequences
```

Verified against the pinned named cave texture cache:750 images,56732 rows.
All dimensions, row extents, row transparency-hint consistency, first-variant
sizes and mip boundaries pass. Final sequence endpoints coincide with other
descriptor starts; descriptors can alias variants inside a larger sequence.
The output includes PNGs, hashed source offsets in sequences.json, a contact
sheet and review.html with manual variant sliders.34 unit tests pass.

Visual inspection shows environmental effects, including dripping stalactites
(862–897), flame (907), and cloud/water-like forms. These are not verified
enemy resources. Stored sequence order does not establish timing, animation
state or viewing direction. Index-zero alpha and lighting remain provisional.
No new entities or effects were placed in the cave from this extraction.

The next enemy investigation should follow the previously recorded 147-byte
named entity definitions for Roach, ROACH, WORM and guards, separately from
the 55-byte scenery templates. This pass does not verify that entity-to-sprite
binding or any live spawn position.

## Walkthrough stand-in export

`export_dummy_creatures.py` selects original block frames408 (ordinary guard)
and733 (roach-like insect), crops transparent borders and emits indices plus
provisional display metadata. Kevin314–407 is excluded. No original spawn,
scale, animation or AI binding is claimed. The Godot walkthrough places two
of each as static, non-colliding visual dummies; see docs/dummy-creatures.md
in that repository. Reinspection of966 shows a fallen guard-like image,
so any earlier roach speculation for966 should not be used as identification.
