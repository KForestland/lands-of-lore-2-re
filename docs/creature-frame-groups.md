# Creature frame group review

## Original shipped texture banks

**CONFIRMED.** The `0x1246` descriptors in the 15 original `.TE_` entries
partition into 1,844 consecutive groups with 27,889 frames. `+0x08`
gives the group size, and `+0x09` runs from zero to size minus one within
each group. The table is section 2 of the expanded bank, located by the
u32 at bank `+0x10`, with 56 bytes per descriptor. `0x1326FA–0x13270B`
uses the low byte at `+0x08` as the multiplier for the resource selector
and adds the base ID word at `+0x00`. The high-byte ordering is measured
from the stored rows. Its use as a native input is **UNCONFIRMED**.
`python3 tools/lol2_texture_container.py --check --data DAT` checks the
partition and the associated vector records using the shipped archives.

## Earlier cave cache measurements

All1324 cave1246 descriptors partition exactly into93 groups. Descriptor
byte8 is the group count; byte9 is the ordinal. Subtracting the ordinal
from the descriptor index gives the group start. Each group has every
ordinal from0 through count-1, contiguous resource IDs, matching dimensions
and a shared candidate name hash. These are source invariants; they do not
identify state names, viewing directions or timing.

```sh
python3 tools/history/draracle/build_creature_group_review.py --game-root /path/to/lol2 --frames /path/to/decoded-block-sprites
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

The builder also writes gallery.html:93 cards with first/middle/last poses.
Each pose links to groups.html#group=BASE&frame=INDEX. The playback page
provides a link to its current pose; invalid fragments fall back safely.
All gallery image paths and group/frame links were checked, along with
JavaScript syntax. Browser interaction remains manually reviewable.

Resources314–407 look like a guard in a cook's outfit (visual identification):
94 frames in6 complete groups. The builder labels those exact frames
and the other guard groups from that visual identification. Insect-like
resources733–861 remain separately labelled with identity pending. Labels
and their evidence are included in groups.json. These are user observations,
not recovered filenames or proof of native character/state bindings.
