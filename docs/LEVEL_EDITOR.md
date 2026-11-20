# Move a placement on a level plan

Open a plan from your own game files. The editor moves existing items and prop
placements. Use Python 3.10 or newer and run the commands from this repository.

```sh
python3 tools/lol.py level --data "/path/to/game" --level L1_DC --out "/path/to/level plans"
```

Open `L1_DC.html` in the new folder. Click **Move a placement**, then pick
an item or prop in the list. You can also select its marker. The plan outlines
its stored region. Enter the new X and Y, or click **Pick on the plan** and
click inside the outline. Click **Stage move** to preview the new position.
**Download changes** writes a JSON file with the moves. **Clear moves** resets
the preview.

Give the downloaded file and your original game to the writer. Use a new
output folder whose parent exists. The writer prints the file and number of
verified moves. Add `--patch` to create `level-patch.json` and a private
`undo.json` beside the copied `DAT/` folder. The undo can restore the
original archive through the [patch apply command](formats/patch.md#make-apply-and-undo).

```sh
python3 tools/level_edit.py "/path/to/downloaded moves.json" --data "/path/to/game" --out "/path/to/edited level" --patch
python3 tools/level_edit.py "/path/to/downloaded moves.json" --data "/path/to/game" --out "/path/to/edited level" --verify
```

Verification compares every archive byte. An empty move file produces an
identical archive. To try an edited level, put the verified archive in place of
the matching archive under `DAT/` in a separate copy of the game.

The available rows have coordinates within their stored region. Moves stay
inside that same region and keep height, heading, type, events, and all other
stored fields. Adding or removing placements and moving them to other
areas require their own tools. **UNCONFIRMED.** Changed copies have been
verified by the reader. Their in-game behavior has yet to be observed.

**CONFIRMED.** Prop and item rows use the geometry header's `+0x14/+0x60` and
`+0x20/+0x6C` pairs. Both tables have 37-byte rows. The placement constructor
reads signed X/Y words at `+0/+2` and the region word at `+0x0A`
(`LOLG.DAT` VAs `0xAE99A–0xAE9CB`, `0xAEA30–0xAEA5C`). The editor writes
the two coordinates. [Level layout](formats/level-data.md) ·
[Prop constructor and event example](tutorial-one-event.md)

**CONFIRMED.** Named items join the placement identity at `+0x20` to
the executable's item labels at `LOLG.DAT+0x1CD634`. Other items use
their definition number. Props use the stored template number read at
VA `0xF207F`. A source display name for these prop templates remains
**UNCONFIRMED**. [Item identity join](lol2-item-format.md#record-fields) ·
[Prop templates](cave-object-catalogue.md#templatestate-links)
