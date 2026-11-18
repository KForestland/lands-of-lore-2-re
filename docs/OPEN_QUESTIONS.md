# Open questions

Numbered so the pages and [`STATUS.md`](STATUS.md) can point at them. Each is something not yet known about the ORIGINAL game's files or rules. When one is answered, its page is updated and the entry says so. Sources: the repo's own "still open" lists ([understanding](lol2-understanding-2026-11.md#still-open), [script engine facts](lol2-script-engine-facts-2026-10.md#still-open)) and the checks added on 2026-11-18.

| ID | Question | Page |
|----|----------|------|
| Q1 | Which LoL2 data, if any, uses the Westwood LZ77 variant with a leading mode byte (`tools/lol2_decompress_westwood.py`)? No MIX entry whose first u32 looks like a size decodes with it | tools |
| Q2 | `LOCAL.MIX` entry 1: the two stored (uncompressed) sections 0 and 15 are 2 bytes shorter than their headers state. Is the header 10 bytes for stored sections, or the size counted differently? | [lol2-level-texture-container.md](lol2-level-texture-container.md) |
| Q3 | Room archives: the level graph lists 45 room archives with a `WOMS\<ROOM>_.WOM` module plus 3 movie-only ones; the hash check finds the WOM name in 47 archives. Which count is right, and what are the two extra? | [lol2-level-graph.md](lol2-level-graph.md) |
| Q4 | What do the remaining subcommands and virtual continuations do, including opcode 18 drift and opcode 196 post-call writes? | [Opcode table](lol2-script-opcodes.md) |
| Q5 | What consumes object kind 1, and which player and object actions supply the remaining event IDs? | [Event records](lol2-script-events.md#event-records) |
| Q6 | Which shared-array indexes and values gate the remaining plot branches, and what does predicate operand type 7 return? | [Predicates and shared bytes](lol2-script-events.md#predicates-and-shared-bytes) |
| Q7 | What produces the timer elapsed cells, and how do they convert to wall-clock units? | [Object timers](lol2-script-events.md#object-timers) |
| Q8 | What do the remaining item-use handlers do, and how do they interpret the instance fields? | [Native item handlers](lol2-item-handlers.md) |
| Q9 | What are the remaining spell effects and lesson conditions? | [Native spell tables](lol2-spells.md) |
| Q10 | What drives the remaining AI transitions and descriptor flags? | [Native creature transitions](lol2-creature-transitions.md) |
| Q11 | What are the gameplay roles of the remaining save sections and header fields? The placed-item row and recipient-pool write paths are mapped. A controlled before/after pickup pair remains open. | [Native save section descriptors](lol2-save-sections.md) |
| Q12 | Movies: full codebooks for every movie, and the 14 partial-codebook movies the decoder does not handle. **Partly answered:** scripts pick a movie by scene id through an 86-name table ([lol2-movie-scenes.md](lol2-movie-scenes.md)) | [lol2-vqa-v2.md](lol2-vqa-v2.md), [formats/vqa.md](formats/vqa.md) |
| Q13 | Text: where the dialogue and message tables are stored, and their format. `TEXT.MIX` and `TCEL.MIX` are not text containers: they are 2 of the 46 room archives ([lol2-room-archives.md](lol2-room-archives.md)) | — |
| Q14 | Texture flags other than 0xA9 (including 0x80A9) | [lol2-level-texture-container.md](lol2-level-texture-container.md) |
| Q15 | HMI-MIDI music: format and conversion of the 33 `HMI-MIDISONG` entries in `LOCAL.MIX` (32 are the `MUSIC\<stem>.HMI` files, [lol2-music-selection.md](lol2-music-selection.md)) | [lol2-music-2026-11.md](lol2-music-2026-11.md) |
| Q16 | Wall-span geometry, UVs and special openings beyond the traced span; the Huline Temple interior portals. **Partly answered** ([formats/walls.md](formats/walls.md)): the wall table, each region's run of rows (traced at 0xF4370) and the code bits; all 88,994 rows of the 15 levels partition exactly; most Huline Temple rows are upper/lower pieces on portal sides (a window example in L14_HT) | [lol2-wall-material-provenance.md](lol2-wall-material-provenance.md), [draracle-restoration.md](draracle-restoration.md) |
| Q17 | The L8 control records for the cache ladder (control 69) and the tree bridge (control 114) | — |
| Q18 | Per-level puzzle records: what each level's scripts and object records do, level by level | — |
| Q19 | The 147-byte entity records: which structure in the level archive holds them (the tools find them by searching for name tags) | [formats/entity-records.md](formats/entity-records.md) |
| Q20 | `CDCACHE.MIX` in the game folder: its index (5 entries, 65 data bytes) matches `CACHEBAK.MIX`, but the file is about 90 MB; the bytes after it include decoded level texture blobs (L1_DC at file offset 5,070, L20_BB at 13,045,474, byte-identical); how they are indexed, and when the game writes them | [formats/mix.md](formats/mix.md) |
