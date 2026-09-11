# Creature frame group review

All1324 cave1246 descriptors partition exactly into93 groups. Descriptor
byte8 is the group count; byte9 is the ordinal. Subtracting the ordinal
from the descriptor index gives the group start. Each group has every
ordinal from0 through count-1, contiguous resource IDs, matching dimensions
and a shared candidate name hash. These are source invariants; they do not
identify state names, viewing directions or timing.

```sh
python3 tools/draracle/build_creature_group_review.py --game-root /path/to/lol2 --frames /path/to/decoded-block-sprites
```

Run after extract_block_sprite_frames.py. The generated groups.html offers
a group selector, previous/next buttons, frame slider and adjustable preview
playback. groups.json records every descriptor membership. PNG existence
is checked;45 unit tests pass, including missing variants and mixed hashes.
Viewer JavaScript syntax was checked; no automated browser interaction test.

The named entity constructor A1C94 calls5A268, which creates name-specific
objects through59C0C. LE initialized-data strings at4,11,1A,24,30,3D reveal
`global\ai\%s`, stat.csv, goals.csv, actions.csv, effector.csv and spells.csv.
This path loads AI configuration; it is not evidence of a named sprite link.
A1CA8..A1CCA does confirm the entity table-offset relocation using96964.
These are static disassembly findings, not live captures.

Next trace the actual frame-selector consumer and world placement link.
No original animation rate or creature placement is assigned by this viewer.
