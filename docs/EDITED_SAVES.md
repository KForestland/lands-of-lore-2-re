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

All three runs below belong to probes that are still open. None of them
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
