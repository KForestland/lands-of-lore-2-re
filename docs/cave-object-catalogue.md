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
