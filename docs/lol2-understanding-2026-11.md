# LoL2 understanding — November 2026

Updated 2026-11-06. **Almost fully understood.** The whole game can now be followed from the first cave to the final
scene in terms of its own data: every level, every story step, the script opcodes behind them, and the engine rules that
make the world look and behave the way it does. A short list of things is still open (end of this page); those are
covered by small, documented adapters in the Godot rebuild instead of guesses.

This page summarizes what the Godot rebuild ([lands-of-lore-unified-godot](https://github.com/KForestland/lands-of-lore-unified-godot))
learned since the [October update](lol2-current-status.md). The rebuild is where the reverse engineering is tested: a
fact counts as understood when the rebuilt game plays that part from the original data and a test proves it.

## Proof levels used here

- **Native**: read from the original files or the original code (Ghidra), reproduced byte-for-byte or behaviour-for-behaviour.
- **Observed**: matches the original game in a full longplay (5 h 10 min, frame index every 5 s for Act 1, every 30 s after).
- **Adapter**: the original mechanism is not decoded yet; the rebuild does the same visible thing in a modern way, and
  the gap is logged. Adapters are named as adapters everywhere; they are never presented as decoded.

## What is understood

### The whole story, A to Z
- **Act 1** (Draracle's cave, the Museum, the Huline Jungle, the village, the Hive, the monastery, Dark Halls): every step
  hosted from native scripts and walked by an earned test from a real save. Certified as one campaign chain.
- **Act 2** (the darker jungle and the Huline village, Claw Mountains, the Dracoid ruins and cemetery, Ruloi citadel, the
  Huline Temple): every main step mapped to its native records, items and movies; hosted and walked.
- **Act 3** (the city, its towers and greenhouse, the caverns, the sewers, Belial's domain, the final fight and the last
  scene): every story step from the Chamber of Voices to the final scene (book steps 66-93) mapped to native ids, props,
  movies and the opcodes on the path, with one save chain from the greenhouse to the finale.
- **Good/evil branches**: the soul-value branches (Baccata at the power field and at the Belial statue, the village
  guild path, and the rest) mapped with both outcomes and their conditions.

### Script opcodes (November additions)
- **Opcode 9**: arm 3 is the host link (with byte +0x15 bit 0x10: store 0 at +0x0C, clear the bit, set +0x16 bit 1 and
  +0x17 bit 0x20); arm 2 is the player release. Arm 6 is still open.
- **Opcode 18**: direct relocation (flags 0x0804) with a destination point, heading and region floor; also the path a
  moving object follows (the greenhouse fireball). The drift speed is not decoded.
- **Opcode 20**: a sound cue (for example sound 452 "jugcrash", sound 780 "creaky2" on ladders and the tree bridge).
- **Opcode 2**: arm 0x11 sets the link bit and calls the three link helpers; arm 0x1C is a level arrival (for example
  level 16 arrival 1); arm 0x0C as part of the greenhouse group.
- **Opcode 196**: writes region floor/ceiling heights at a speed (for example region 1614 floor 100 / ceiling 200 at
  speed 10). Partly decoded; the remaining stores are open.
- **Kind-10 record groups** run when a moving object arrives (the greenhouse fireball opens the FireWall doors 92-94).

### Engine rules
- **What is drawn**: the original engine draws only the regions it reaches through region edges (portals) inside the
  view; rooms that overlap or lie beyond solid walls are never drawn. Treating every shared polygon edge as a portal,
  including low walls, parapets, drops and windows, matches the longplay. The rebuild's earlier "draw everything"
  approach is what made stacked levels (the Huline Temple, the Hive) look like a tangle.
- **Water**: regions without their own bank level take the most common bank level of the connected bed; with that,
  every water region has a surface. Drowning takes about 15 s under water (measured in the original with DOSBox).
- **Collision**: native solid boxes (placement flag 0x80 plus a box template), region blockers (region bit 0) and
  movables with presence flags (0x1000 = starts absent) explain the walkable world, including the L8 tree bridge
  (assembly 114 standing tree, 116 fallen log).
- **Storeys**: each level splits into floors by height and by the connectivity of its creature navigation regions;
  this is what a readable automap needs.

### Maps
Every map point in the Brady and Prima guides, across 14 areas, was checked against the native records and the longplay
frames. Each one is either an existing record (sometimes under a different name than the guide uses), part of a story
step above, or not in the original at all (guide wording). No point the original game shows is missing from the
understanding.

## Still open
- Opcode 14 arm 5 (part of the city gate groups 672/698/3004), opcode 9 arm 6, opcode 18 drift speed, the rest of
  opcode 196.
- The L8 control records for the cache ladder (control 69) and the tree bridge (control 114) are read from the original
  but not yet decoded into the public tools.
- HMI-MIDI music conversion; texture flags other than 0xA9 (including 0x80A9); full VQA codebooks for every movie.
- The Huline Temple's interior: its rooms are reached through doors that act as portals into separate spaces; the
  geometry is understood well enough to draw, but not yet well enough to look right everywhere.

## What this means
Lands of Lore II is close to fully understood as a game: its content, its story order, its scripts and its engine rules.
What remains is a handful of opcode arms and media formats, each already covered in the rebuild by a logged adapter.
