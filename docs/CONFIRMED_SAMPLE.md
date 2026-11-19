# Re-deriving a sample of confirmed statements

Two samples of 30 statements labelled confirmed were taken from the current
pages, each by its own rule, and checked again from the original bytes: the archives in `DAT/`
and beside the game, `LOLG.DAT` disassembled at code address = file offset
minus `0x37000`, and the shipped cache seed. No game, emulator or debugger
was run, so the running-game part of a statement is listed as not repeated.
Each list was fixed before any statement on it was checked.

"Held" means the bytes give the same values as the page. "Part held"
means the checked part held and a broader part of the same statement
was not re-checked. "Wrong" and "Overstated" statements were corrected
on the page.

## First sample (19–20 November 2026)

Pages in the order the rating counts them; every third page from the
third page on, the first paragraph on it that carries a confirmed label
and names an address or offset. Those pages gave 25 statements, so the
list was filled from pages 1, 4, 7, … (pages 1, 4, 7, 28 and 31 were the
first five with such a paragraph). The rule was written into the picking
script and the list was fixed at 22:54 UTC on 19 November; the checking
scripts are from 23:07 on. Four statements are also on the second
sample's list (the cookbook help table, level assembly load order, the
form compare tree and the geometry entry), so 26 are new to it. 30
statements: **25 held, 3 part held and 2 wrong (both corrected).**

| Page | Statement | Result |
| --- | --- | --- |
| [Running game](NEEDS_A_RUNNING_GAME.md) | Player +0x185 clears | Held |
| [Progression](PROGRESSION.md) | Exit matchers run every match | Held |
| [Round trip](ROUND_TRIP.md) | Mode byte and rebuilt streams | Part held: the decoder, its mode byte and the 15 texture streams (all in the absolute mode); the encoder, writer and synthetic tests were not re-run from the bytes |
| [Tour](TOUR.md) | L1_DC map entry | Part held: the entry, the vertex and region tables and the 1,954 regions; the picture was not re-rendered |
| [Compression](formats/compression.md) | Scheme table | Held |
| [Items](formats/items.md) | Table counts and handler indexes | Held |
| [Maps](formats/maps.md) | Automap markers | Held |
| [Sound](formats/sound.md) | Bank layout and cue indices | Held |
| [Walls](formats/walls.md) | Wall table fields | Held |
| [L12_CM notes](levels/notes/L12_CM.md) | Stream and event counts | Held |
| [L16_CA notes](levels/notes/L16_CA.md) | Stream and event counts | Held |
| [L3_DH notes](levels/notes/L3_DH.md) | Stream and event counts | Held |
| [L7_DH notes](levels/notes/L7_DH.md) | Stream and event counts | Held |
| [Level notes](levels/notes/README.md) | Group runner and direct references | Held |
| [Item effects](lol2-item-effects.md) | Definition base and lookup | Held |
| [L8 controls](lol2-l8-controls.md) | Placement 69 control event | Held |
| [Texture container](lol2-level-texture-container.md) | Container header | Held |
| [Music selection](lol2-music-selection.md) | Music name table | Held |
| [Save field witnesses](lol2-save-field-witnesses.md) | Section 28 and 29 object lists | Held |
| [Script engine addendum](lol2-script-engine-facts-2026-10-addendum.md) | Predicate table and evaluator | Held (the six class vtable slots and the opcode 16 write were re-read in the review below) |
| [Script motion](lol2-script-motion.md) | Motion command slot | Held |
| [Sound cues](lol2-sound-cues.md) | Low opcode dispatcher | Held |
| [Spells](lol2-spells.md) | Cast effect index | Held |
| [VQA version 2](lol2-vqa-v2.md) | Pointer-stream node bits | Wrong, corrected: `VPRZ` sets bit 4 at `0x16E635`; the cited `0x172808–0x172845` tests the bit, calls `0x158D58` and clears it |
| [One event](tutorial-one-event.md) | Prop 1050 event chain | Held |
| [Cookbook](COOKBOOK.md) | Help-message location | Held |
| [Level assembly](HOW_A_LEVEL_IS_PUT_TOGETHER.md) | Load order and MAP header check | Wrong, the same correction as in the second sample |
| [Numbers](NUMBERS.md) | Form compare tree | Part held: the compare tree, the arm entries and the duration helper; the census of stored opcode 2 commands was not walked again |
| [Entity records](formats/entity-records.md) | ODF suffix and keys | Held |
| [Level data](formats/level-data.md) | Geometry entry selection | Held |

A review re-derived six of these from the bytes again with its own
readers (picked at random, seed 85, from the 26 not on the second list):
the L1_DC map entry, the automap markers, the L16_CA counts, the predicate
table and evaluator, the cast effect index and the ODF suffix and keys.
All six gave the result above. For the predicate statement the review
also read the six class vtable slots (all `0xB71A0`), the opcode 16 write
at `0xB5A3C` and the seven direct references to `0xB7D80` (two stores,
five readers), which the first check had not read correctly.

## Second sample (19–20 November 2026)

Every third page from the second page on, the last statement on it that
names an address or offset; level-note tables give their last row. The
list was fixed at 23:01 UTC on 19 November; the first byte for it was read
at 23:07. The first sample, taken by a different rule, is above. Four statements on this list are
also on the list frozen for the first sample (the cookbook help table,
level assembly load order, the form compare tree and the geometry entry),
so 26 are new to it. 30 statements: **22 held, 6 part held, 1 wrong and
1 overstated (both corrected).**

| Page | Statement | Result |
| --- | --- | --- |
| [Cookbook](COOKBOOK.md) | Help-message location | Held |
| [Level assembly](HOW_A_LEVEL_IS_PUT_TOGETHER.md) | Load order and MAP header check | Wrong, corrected: file `+0xD3CBC` loads the name argument; the `0x244`-byte read is at `0x9CCCE–0x9CCDB` and the tag and region-count tests at `0x9CCE3–0x9CCEE`. The [script format](lol2-level-script-format.md#finding-the-geometry-entry) page cited the same old address and was corrected too |
| [Numbers](NUMBERS.md) | Form compare tree | Held |
| [Entity records](formats/entity-records.md) | L1 ODF table extent | Held |
| [Level data](formats/level-data.md) | Geometry entry selection | Held |
| [L13_RC notes](levels/notes/L13_RC.md) | Kind-19 trailers | Held |
| [L17_HC notes](levels/notes/L17_HC.md) | Kind-19 trailers | Held |
| [L1_DC notes](levels/notes/L1_DC.md) | Kind-19 trailers | Held (351 from the lists; the two pools hold 21 more, on placed items) |
| [L4_HJ notes](levels/notes/L4_HJ.md) | Kind-19 trailers | Held |
| [L8_SJ notes](levels/notes/L8_SJ.md) | Kind-19 trailers | Held |
| [Cache initializer](lol2-cache-initializer.md) | Version and date strings | Part held: the strings, their pointers and readers, and the seed strings; not the folder names in the decoded banks |
| [Creature observation](lol2-creature-observation.md) | Three actor byte reductions | Held |
| [Event producers](lol2-event-producers.md) | Pickup event join | Part held: the file join from the placed row to the kind-4 record; the click not repeated |
| [Item format](lol2-item-format.md) | Difficulty and whole ticks | Held |
| [Level graph](lol2-level-graph.md) | Room-module direct calls | Held |
| [Movie scenes](lol2-movie-scenes.md) | L12 movie command | Held |
| [Save format](lol2-save-format.md) | Edited-save placement | Part held: the copy at `0xD0250`; the edited-save loads not repeated |
| [Script opcodes](lol2-script-opcodes.md) | Timer start | Held |
| [Speech](lol2-speech.md) | Cue-pointer uses and player calls | Part held: the two straight call walks; not the 533 pointer uses |
| [Text tables](lol2-text-tables.md) | Eight stored tables | Held |
| [Open questions](OPEN_QUESTIONS.md) | Q20 cache seed | Part held: seed marker, first row and strings; not the allocator callers or the decoded banks |
| [Geometry](formats/geometry.md) | Portal links | Overstated, corrected: the counts held (52,669 regions, 178,728 links, 177,774 reciprocal, 177,318 sharing the side); the role of the 86 other L1_DC links is not shown by them and is now labelled as open |
| [Loose files](formats/loose.md) | `DAT/SETUP.EXE` layout | Held |
| [Options shapes](formats/room-sections.md) | Shape framing and pixel count | Held |
| [VQA](formats/vqa.md) | Edited-save movie placement | Part held: the copy at `0xD025F–0xD0279`; the run not repeated |
| [L10_DC notes](levels/notes/L10_DC.md) | Kind-19 trailers | Held |
| [L14_HT notes](levels/notes/L14_HT.md) | Kind-19 trailers | Held |
| [L19_BC notes](levels/notes/L19_BC.md) | Kind-19 trailers | Held |
| [L20_BB notes](levels/notes/L20_BB.md) | Kind-19 trailers | Held |
| [L5_HC notes](levels/notes/L5_HC.md) | Kind-19 trailers | Held |

A review re-derived five of these from the bytes again (picked at random,
seed 146): the geometry entry selection, the version and date strings, the
eight stored tables, the edited-save movie placement and the L10_DC
trailers. All five gave the result above; the review also traced the
version and date pointers to their readers.
