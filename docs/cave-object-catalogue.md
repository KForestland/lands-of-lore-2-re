# Cave object catalogue

Run `python3 tools/draracle/catalogue_cave_objects.py --game-root GAME
--walk GODOT/assets/lol2/generated/original_floors/full_walk.json --out OUT`
(on one line). Output includes grouped Markdown, placement CSV and JSON.

The pinned cave has 1,559 spatial placements using 94 template IDs. Positions,
template, selector, state and flags follow the existing native constructor
evidence. The tool applies the walking-map translation derived from its
floor anchor. Nearby checkpoints are geometric hints, not proof of visibility.

Template24 has141 placements across85 regions; template28 has88 across80.
Their repeated use makes them useful identification targets, not proven plants.
Next inspect source template loading and sprite references, then verify an
identity at multiple placements before adding its class to the demo.
No spawn behavior or enemy identity is inferred from template frequency.

## Template/state links

`extract_cave_object_templates.py --game-root GAME --out OUT` reads the
second non-texture entry (key2971019266): header8 points to 103 templates
at offset1482, each55 bytes; header40 supplies the count. Native loader
F1A14 then calls F2B94, which reads count-prefixed16-byte states followed
by count-prefixed12-byte frames. Template bytes2E+2F partition states;
signed state byte0D partitions frames (negative means one record).

All172 states and172 frame records are consumed exactly; all1559 placements
reference valid templates and selectors. This is source parsing backed by
disassembly, not a full loader replay. Templates23/24 share positive resource
reference278;16 uses302,28 uses306,21 uses417. These candidate cache
descriptors use28E encoding and cannot use the raw wall pixel exporter.
Next verify resource routing and decode sprite transparency before assigning
plant/prop names or adding instances. No visible props added in this pass.

## Decoded prop previews

`extract_prop_sprite_previews.py --game-root GAME --out OUT` decodes candidate
resources278/302/306/417 as28E row spans. Header gives width/height and
payload size. Each row has a control word, count and indexed pixels; lower
14 control bits give horizontal start. In all1,158 checked rows, bit4000
exactly matches presence of index0. All19 mip extents/dimensions/ends pass.

Previews use provisional alpha for index0 and omitted pixels. Visual
inspection suggests hanging vegetation278, stalagmite302, column306 and
boulder417. These labels are visual interpretations, not source names.
Native alpha, sprite scale, anchoring and orientation remain to verify.
No props are spawned in the cave yet. Next recover template size/anchor
consumers before integrating repeated instances.

`export_cave_prop_preview.py` exports354 static instances from templates
16/21/23/24, requiring resource flags0 and single states/frames. Includes
source positions, state14/15 dimensions and frame5..8 trims supported by
F1DC9/F1E09 and renderer129300..129377 disassembly. Callback1292C0 resolves
from LE table5D18 slot34. Full renderer replay remains open. Column28 uses
region-height flag2 and is excluded. Godot uses provisional alpha and
fixed-Y billboards; frame flags remain stored but unimplemented.
