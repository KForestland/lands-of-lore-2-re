# Re-deriving a sample of confirmed statements

The two 19–20 November samples of 30 statements labelled confirmed were taken from the current
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
scripts are from 23:07 on. Four statements were also on the second
sample's initial list (the cookbook help table, level assembly load
order, the form compare tree and the geometry entry); the second sample
replaced them, so the two samples count 60 different statements. 30
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
at 23:07. The first sample, taken by a different rule, is above. Four
statements on this list were also on the list frozen for the first sample
(the cookbook help table, level assembly load order, the form compare
tree and the geometry entry). They are counted in the first sample only,
and their results here are kept below the table. The next four pages by
the same rule replace them (rows 27–30). That list was fixed at 23:39 UTC;
the earliest record of a check on it is from 23:58. Line numbers are
those of the pages when the first list was fixed (commit `f3cc436`). 30
counted statements: **21 held, 8 part held and 1 overstated
(corrected).**

| # | Page (line at `f3cc436`) | Statement | Result | Evidence and limits |
| ---: | --- | --- | --- | --- |
| 1 | [Entity records](formats/entity-records.md), line 46 | L1 ODF table extent | Held | The two dwords at L1_DC.MIX+0x70C160/+0x70C198 are 0x6C4B and 11. The 147-byte stride gives +0x712D9B through +0x7133EB, and row +0x87 is +0x712E22. |
| 2 | [L13_RC notes](levels/notes/L13_RC.md), line 22 | Kind-19 trailers | Held | Both event pools walk to 243 kind-19 records. L13_RC.MIX+0x688879 is the first trailer, length 4 and index 206. |
| 3 | [L17_HC notes](levels/notes/L17_HC.md), line 20 | Kind-19 trailers | Held | Both event pools walk to 117 kind-19 records. L17_HC.MIX+0x490852 is the first trailer, length 4 and index 1. |
| 4 | [L1_DC notes](levels/notes/L1_DC.md), line 24 | Kind-19 trailers | Held (351 from the lists; the two pools hold 21 more, on placed items) | Following the four placement tables and region descriptors yields 351 distinct kind-19 offsets. The first is L1_DC.MIX+0x6E96C1, index 99. The whole pools include 21 additional placed-item trailers. |
| 5 | [L4_HJ notes](levels/notes/L4_HJ.md), line 23 | Kind-19 trailers | Held | Both pools walk to 808 kind-19 records. L4_HJ.MIX+0xC2B200 is first, index 206. |
| 6 | [L8_SJ notes](levels/notes/L8_SJ.md), line 24 | Kind-19 trailers | Held | Both pools walk to 526 kind-19 records. L8_SJ.MIX+0xCD6B36 is first, index 198. |
| 7 | [Cache initializer](lol2-cache-initializer.md), line 129 | Version and date strings | Part held: the strings, their pointers and readers, and the seed strings; not the folder names in the decoded banks | At LOLG.DAT+0x1C4714 and +0x1C4749 are the engine revision and date. The files also contain earlier dates at +0x1C5AC8 and +0x33364. This check read the literal locations; the review traced the pointers to their readers. |
| 8 | [Creature observation](lol2-creature-observation.md), line 201 | Three actor byte reductions | Held | At 0xA2351, 0xAA42D and 0xAB093, the code tests +0xA3 and enters two shift/subtract/store paths on +0xA6/+0xA7. The shifts at 0xA2375 and 0xA2394 implement the divide by four. |
| 9 | [Event producers](lol2-event-producers.md), line 181 | Pickup event join | Part held: the file join from the placed row to the kind-4 record; the click not repeated | The placed row at L1_DC.MIX+0x6FBFCE has definition 0xA4C5CBD3 at +0x20 and event offset 0x1ADA at +0x0C. Adding the pool base reaches kind 4 at +0x6EB187. This confirms the file join. The live click was not repeated. |
| 10 | [Item format](lol2-item-format.md), line 103 | Difficulty and whole ticks | Held | 0xCC0DC–0xCC0F7 clamps difficulty to 0–2, and 0xCCD61 copies it to 0xB7FB2. 0xE0CCF shifts right 16, 0xE0CD2 stores the whole time, and 0xE0CE4–0xE0CF3 updates carry. |
| 11 | [Level graph](lol2-level-graph.md), line 170 | Room-module direct calls | Held | At MCEL.MIX+0x9DF, SHAMAN.MIX+0xDC5 and SETTLE1.MIX+0x615 are memory-indirect calls. MCEL's argument string at +0xAC1 is the stated stem. |
| 12 | [Movie scenes](lol2-movie-scenes.md), line 79 | L12 movie command | Held | At L12_CM.MIX+0x95E68E the six bytes select opcode 0x15 and scene 13. L12_CMI key 0xA3C468EB points to a 14,680,498-byte WVQA, with VQHD length 42 at member +0x10. |
| 13 | [Save format](lol2-save-format.md), line 142 | Edited-save placement | Part held: the copy at `0xD0250`; the edited-save loads not repeated | The reader at 0xE6F2A calls 0xD0250, whose +0x0F,+0x14,+0x1A instructions store two dwords and the low word of the third. That code path was checked; loading the edited saves was not repeated. |
| 14 | [Script opcodes](lol2-script-opcodes.md), line 371 | Timer start | Held | L1_DC.MIX+0x6FD211 is opcode 0x0E, kind 3, index 0x0614, action 3 with argument and timer zero. Code at 0xB486F clears bit 0 and the argument test at 0xB487A skips reload when zero. |
| 15 | [Speech](lol2-speech.md), line 152 | Cue-pointer uses and player calls | Part held: the two straight call walks; not the 533 pointer uses | Disassembly from 0xE3924 to 0xE3AA6 and from 0xE4F1C to 0xE5299 reproduces the four and two direct call sequences. The separate candidate set of 533 pointer uses was not reclassified. |
| 16 | [Text tables](lol2-text-tables.md), line 91 | Eight stored tables | Held | The check matched the exact count, boundary and NUL layout across shipped MIX entries and loose copies. Eight tables contain 988 rows. The help offset is +0x1B185DF and the movie credits offset is +0x87BFDB0. The writer recheck also passed. |
| 17 | [Open questions](OPEN_QUESTIONS.md), line 83 | Q20 cache seed | Part held: seed marker, first row and strings; not the allocator callers or the decoded banks | The preserved cache has its marker at +0x42 and first row at +0x46, whose payload position is 5,070. The shipped CDCACHE.LS_ is separate. The file witnesses and the revision strings were checked. The allocator's complete caller and 15-bank decoded provenance were outside this pass. |
| 18 | [Geometry](formats/geometry.md), line 30 | Portal links | Overstated, corrected: the counts held (52,669 regions, 178,728 links, 177,774 reciprocal, 177,318 sharing the side); the role of the 86 other L1_DC links is not shown by them and is now labelled as open | From MAP +0x0C/+0x58, a separate walk gives 52,669 regions, 178,728 links, 177,774 reciprocal and 177,318 sharing the edge. L1 has 6,392 of 6,478 shared. The geometric counts alone do not assign an encounter role to the other links. The review moved the attribution of the 86 remaining L1 links to the open part of the page. |
| 19 | [Loose files](formats/loose.md), line 13 | `DAT/SETUP.EXE` layout | Held | The DAT copy is 92,160 bytes, MZ extent 0xA270, 290 relocations. NE segment tables yield 127, 42, 160, 112 and 62 relocation records. This check is for DAT/SETUP.EXE. |
| 20 | [Options shapes](formats/room-sections.md), line 41 | Shape framing and pixel count | Held | The LOCAL.MIX member has 37 flag-0 and two flag-2 shapes. A direct scan of shape 15's decoded 11,960 bytes accounts for 22,785 pixels. The original 0x151FC4–0x151FE1 distinguishes colour bytes and zero runs. |
| 21 | [VQA](formats/vqa.md), line 230 | Edited-save movie placement | Part held: the copy at `0xD025F–0xD0279`; the run not repeated | 0xD025F–0xD0279 copies X, Y and low-word heading. The static stores were checked. The restored geometry height and played/blocked outcome are runtime observations. |
| 22 | [L10_DC notes](levels/notes/L10_DC.md), line 23 | Kind-19 trailers | Held | Both pools walk to 541 kind-19 records. L10_DC.MIX+0xC7FAC1 is first, index 206. |
| 23 | [L14_HT notes](levels/notes/L14_HT.md), line 25 | Kind-19 trailers | Held | Both pools walk to 479 kind-19 records. L14_HT.MIX+0xB316D4 is first, index 206. |
| 24 | [L19_BC notes](levels/notes/L19_BC.md), line 21 | Kind-19 trailers | Held | Both pools walk to 1,060 kind-19 records. L19_BC.MIX+0x5DEB57 is first, index 206. |
| 25 | [L20_BB notes](levels/notes/L20_BB.md), line 21 | Kind-19 trailers | Held | Both pools walk to 811 kind-19 records. L20_BB.MIX+0xECD451 is first, index 8. |
| 26 | [L5_HC notes](levels/notes/L5_HC.md), line 24 | Kind-19 trailers | Held | Both pools walk to 223 kind-19 records. L5_HC.MIX+0x5A12B7 is first, index 206. |
| 27 | [L9_DR notes](levels/notes/L9_DR.md), line 24 | Kind-19 trailers | Held | Independently walking both event pools yields 301 kind-19 records. L9_DR.MIX+0x162A238 is the first, length 4 and index 206. |
| 28 | [Combat AI](lol2-combat-ai.md), line 151 | Hive executioner profile and frame | Part held: the stored definition byte, profile rows and frame record; not the full path from actor to hit | L5_HC.MIX+0x5BF2DB is 30, and the frame row at +0x5C014F gives percent 50, mask 8 and flags 0x24. GLOBAL.MIX key 0xCC491243 starts at +0x6A3AC0 and data rows 3 and 4 carry 50. The stored inputs were checked; the full actor-to-hit path was not retraced. |
| 29 | [Creature transitions](lol2-creature-transitions.md), line 117 | Profile source | Part held: the reads, the tag call and store, and the path strings; not every step of the CSV parser | Two reads occur at 0xA1C72 and 0xA1C82. The tag call at 0xA1C94 is to 0x5A268 and 0xA1CAF stores the return at +0x87. Original names at LOLG.DAT+0x1C1028/+0x1C1035 join the profile path. Not every step of the CSV parser was repeated. |
| 30 | [Executable tables](lol2-executable-tables.md), line 66 | LE fixup witness | Held | The inner MZ at LOLG.DAT+0x39024 links to the LE at +0x3BCB4. Header +0x68/+0x6C resolve to +0x3C349/+0x3C89D. Record +0x51C5C gives source 0x0878, object 2, offset 0x5C913. Adding 0x59024 reaches 0xB5937, whose code starts with PUSH ESI. |

The four statements also on the first list, checked with this one:

| Page (line at `f3cc436`) | Statement | Result |
| --- | --- | --- |
| [Cookbook](COOKBOOK.md), line 131 | Help-message location | Held |
| [Level assembly](HOW_A_LEVEL_IS_PUT_TOGETHER.md), line 18 | Load order and MAP header check | Wrong, corrected: file `+0xD3CBC` loads the name argument; the `0x244`-byte read is at `0x9CCCE–0x9CCDB` and the tag and region-count tests at `0x9CCE3–0x9CCEE`. The [script format](lol2-level-script-format.md#finding-the-geometry-entry) page cited the same old address and was corrected too |
| [Numbers](NUMBERS.md), line 465 | Form compare tree | Held |
| [Level data](formats/level-data.md), line 9 | Geometry entry selection | Held |

A review re-derived five of these from the bytes again (picked at random,
seed 146): the geometry entry selection, the version and date strings, the
eight stored tables, the edited-save movie placement and the L10_DC
trailers. All five gave the result above; the review also traced the
version and date pointers to their readers. A later review re-derived two
of the four replacements with its own readers: the executioner inputs
(definition byte 30 at `L5_HC.MIX+0x5BF2DB`, tag `EXEC` at +0x87, 50 in
data rows 3 and 4 of `GLOBAL.MIX+0x6A3AC0`, frame record
`01 08 32 00 08 00 24 00`) and the LE fixup (record at `0x51C5C` for
object 2 offset `0x5C913`, `0x5C913` + `0x59024` = `0xB5937`, which
begins with `PUSH ESI`). Both gave the result above.

## Trust round 2 on 21 November 2026

Independent readers took ten randomly sampled proved table rows from each
game's pages and checked the original files with their own readers. Across
the three games, 30 of 30 rows held within the scope checked. The full
statement was checked in 29 rows. On one Lands of Lore III texture row,
the layout held and the palette-source clause was outside the check.

All ten sampled Lands of Lore II rows held on release `07c6d79`.
The check recounted map and event rows. The page calls `0xADD36`
the dispatch site inside the routine.

A separate set of deliberately wrong statements tested what readers and
checks could catch. [Check audit](CHECK_AUDIT.md#trust-round-2-on-21-november-2026)
