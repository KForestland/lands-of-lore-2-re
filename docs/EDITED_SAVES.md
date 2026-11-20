# Runs on edited saves

Some probes on [NEEDS_A_RUNNING_GAME](NEEDS_A_RUNNING_GAME.md) need a
place or an item that no game-written save had. For those, a copy of a
save the game wrote was changed by hand and loaded in the original DOS
1.30 game.

An edited save shows what the original program does with that state. It
does not show that ordinary play reaches the same state. A native save
(one the game wrote during normal play) is still needed for that. The
rules an edit must keep (position fields, saved pointer ranges, repacked
chunk lengths and directory starts, no extra checksum) are in
[editing a copy of an original slot](lol2-save-format.md#editing-a-copy-of-an-original-slot).

All the runs below belong to probes that are still open. None of them
answers a probe on its own; the [rating](../README.md#rating) counts how
many answered probes rest on edited saves only.

## Q12. Movie `ss-4e`, `SPKSTON2.MIX` frame 492

- **Question:** which history do two exceptional movie frames read?
  ([probe](NEEDS_A_RUNNING_GAME.md#q12-which-history-do-two-exceptional-vqa-frames-read))
- **Edited:** a level-20 slot with item 139 added to the pack, in free
  player item row 47
  ([byte table](formats/vqa.md#scene-probes-from-edited-copies)).
- **Showed:** using the item played `ss-4e`. The original decoder
  reached the exceptional short copy at `0x158DB2` and copied five zero
  bytes from 110 bytes before the destination base.
- **A native save would add:** the same playback reached in ordinary
  play, with item 139 from one of its
  [original sources](formats/vqa.md#original-trigger-routes-for-the-two-frames).
  The live codebook and the final picture stay open either way.

## Q12. Movie `bb_brth`, `L20_BBI.MIX` frame 115 (blocked)

- **Question:** the same probe, for the other frame.
- **Edited:** the same source slot, with the party moved beside prop 87
  ([byte table](formats/vqa.md#scene-probes-from-edited-copies)).
- **Showed:** the copy loaded at the new place, but prop 87 was already
  in state 14. The scene had already played in that slot, so frame 115
  was not reached.
- **A native save would add:** a slot from before timer slot 12
  expires, so the scene can still play. An earlier game-written level-20
  slot has that prop state at zero.
- **Recipe:** source `e2393dbe4d2b` (1,612,845 bytes); the fourteen
  bytes at slot `+0x180` (X, Y, the third header dword and the
  following word) become `00 00 6A FA 00 00 A4 10 00 00 EC FF 23 01`, giving
  `5a34d0c63a97`. Re-applied by a reviewer to a fresh copy: identical,
  no other byte changed.
- **Second run, with a live edit (2026-11-20):** the same copy, and in
  memory prop 87 +0x25 set from 14 to 13. No movie started while
  standing, stepping and clicking beside the prop, so frame 115 was not
  reached. The byte alone does not send the value-20 event that starts
  the scene ([details](formats/vqa.md#scene-probes-from-edited-copies)).

## Q9. Lesson with an absent ID (live edit, not a save edit)

- **Question:** what starts the timed message 0x26?
  ([probe](NEEDS_A_RUNNING_GAME.md#q9-what-starts-the-timed-message-0x26))
- **Edited:** nothing in the save (`e2393dbe4d2b` as written by the
  game). After loading, the learned count at data `0x2375D` +0x9C was
  set in memory from 5 to 0.
- **Showed:** using the lesson item reached the message-0x23 push at
  `0x86229`. Player +0x185 stayed zero in its low byte and 0x26 was not
  sent in a few seconds, which leaves the question open
  ([details](lol2-spell-dispatch.md#absent-id-lesson-branch-live-edit)).
- **A native save would add:** a character who has not yet learned the
  lesson's ID, so no memory edit is needed.

## Q17. Level-8 controls 69 and 114

- **Question:** what on-screen action reaches these records?
  ([probe](NEEDS_A_RUNNING_GAME.md#q17-what-on-screen-action-reaches-these-records))
- **Edited:** only the position group, in two copies of one game-written
  L8_SJ slot, one beside each control
  ([byte table](lol2-l8-controls.md#empty-hand-clicks-from-edited-placements)).
- **Showed:** empty-hand clicks reached both controls. Control 69 moved
  the player to height 100 and the view changed. Control 114 asked to
  unlink itself and link control 116; a later click picked control 116.
  The player was already in form 2 in that copy.
- **A native save would add:** the same clicks from a place reached in
  ordinary play, the first visible change, and a click with an item in
  hand for comparison.

## See the fields in an offline page

Run from the tools repository with Python 3.10 or newer. Use a fresh HTML
file outside the game and save folders.

```sh
python3 tools/lol.py save page '/path/to/your/original save' --out "../my save fields.html"
```

Open the page in your browser. It displays the current values and the evidence
status for each editable field. Choose your terminal and a new save path outside the repository and save folder.
For a field you want to change, enter the value and copy its command. Run the
command from the tools repository. It writes one edited copy. For a second edit
to the same save, generate a page from the first copy and choose another output
filename. Keep the page private because it contains your save name and path.

**CONFIRMED.** The page reads the slot name from `+0x00` and the current
level and player position group from `+0x17C` onward. See
[the documented save layout](lol2-save-format.md).
