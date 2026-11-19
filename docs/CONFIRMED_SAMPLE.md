# Re-deriving a sample of confirmed statements

A sample of 30 statements labelled confirmed was taken from the current
pages and checked again from the original bytes: the archives in `DAT/`
and beside the game, `LOLG.DAT` disassembled at code address = file offset
minus `0x37000`, and the shipped cache seed. No game, emulator or debugger
was run, so the running-game part of a statement is listed as not repeated.
The list was fixed before any statement on it was checked.

"Held" means the bytes give the same values as the page. "Part held"
means the checked part held and a broader part of the same statement
was not re-checked. "Wrong" and "Overstated" statements were corrected
on the page.

## Second sample (19–20 November 2026)

Every third page from the second page on, the last statement on it that
names an address or offset; level-note tables give their last row. The
list was fixed at 23:01 UTC on 19 November; the first byte for it was read
at 23:07. A first sample, taken by a different rule, is still being
checked and is not recorded here yet. Four statements on this list are
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
