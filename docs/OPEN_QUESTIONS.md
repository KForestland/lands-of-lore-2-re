# Open questions

Numbered so the pages and [`STATUS.md`](STATUS.md) can point at them. Each is something not yet known about the ORIGINAL game's files or rules. When one is answered, its page is updated and the entry says so. Sources: the repo's own "still open" lists ([understanding](lol2-understanding-2026-11.md#still-open), [script engine facts](lol2-script-engine-facts-2026-10.md#still-open)) and the checks added on 2026-11-18.

## At a glance

One line per question: its state and what would settle what is left.

| ID | State | What would settle the rest |
|---|---|---|
| Q1 | Open | Find a caller of the LZ77 routine at `0x158D58` whose input is a known file; no MIX entry decodes with it |
| Q2 | Partly | Trace the reader of `LOCAL.MIX` stored sections to see whether the payload starts at byte 10 or 12 |
| Q3 | Mostly | Find how `ARENA` is opened (it is not in the room table at `0x1CFA90`) |
| Q4 | Partly | Trace the remaining subcommands and virtual continuations of opcodes 18 and 196 |
| Q5 | Partly | Trace the remaining event producers and render-parameter readers |
| Q6 | Partly | Map which shared-array indexes gate each remaining plot branch |
| Q7 | Partly | Capture the first store to each elapsed cell after the main update restarts |
| Q8 | Mostly | Trace the 0xF7030 projectile variants to their target receivers, and resolve the definitions that handlers 2, 8, 83 and 91–93 swap in |
| Q9 | Mostly | Trace the effect-15 receiver, effect-17 collision and effect-32/33 writebacks; find the producer of timed message 0x26 and how unlinked groups such as L1 group 13584 are entered |
| Q10 | Partly | Trace the remaining AI mode branches and descriptor flags |
| Q11 | Partly | Compare an original save pair written before and after one known pickup |
| Q12 | Partly | Decode the remaining codebook layouts (see the page) |
| Q13 | Partly | Find where character dialogue is stored |
| Q14 | Mostly | Decode the non-raw payloads (`0x1246` and the payload-length flags) |
| Q15 | Mostly | Name the stem of key `0x1305A4F0`; the `FORM` entries in `LOCAL.MIX` are a different container |
| Q16 | Partly | Trace wall spans, UVs and openings beyond the traced span |
| Q17 | Partly | Trace the visible geometry and input conditions of L8 controls 69 and 114 |
| Q18 | Partly | Trace the gameplay producers of the unresolved events |
| Q19 | Answered | — |
| Q20 | Open | Trace how the game builds its cache from `CACHEBAK.MIX` and `CDCACHE.LS_` |

## Questions

| ID | Question | Page |
|----|----------|------|
| Q1 | Which LoL2 data, if any, uses the Westwood LZ77 variant with a leading mode byte (`tools/lol2_decompress_westwood.py`)? No MIX entry whose first u32 looks like a size decodes with it | [formats/compression.md](formats/compression.md) |
| Q2 | `LOCAL.MIX` entry 1: the two stored (uncompressed) sections 0 and 15 are 2 bytes shorter than their headers state. Is the header 10 bytes for stored sections, or the size counted differently? | [formats/room-sections.md](formats/room-sections.md) |
| Q3 | Room archives: the level graph lists 45 room archives with a `WOMS\<ROOM>_.WOM` module plus 3 movie-only ones; the hash check finds the WOM name in 47 archives. Which count is right, and what are the two extra?. **Answered in part:** 47 archives carry a `WOMS\<ROOM>_.WOM` key; they are the 46 room archives the executable names in its table at file `0x1CFA90` ([lol2-room-archives.md](lol2-room-archives.md)) plus `ARENA`, which the table does not name. How `ARENA` is opened is open | [lol2-level-graph.md](lol2-level-graph.md) |
| Q4 | What do the remaining subcommands and virtual continuations do? The opcode 18 updater and opcode 196 post-call stores are mapped. | [Opcode table](lol2-script-opcodes.md), [motion](lol2-script-motion.md) |
| Q5 | What are the remaining event producers and render-parameter roles? Object kind 1 is traced to its native consumer. | [Event producers](lol2-event-producers.md) |
| Q6 | Which shared-array indexes and values gate the remaining plot branches? Type 7 is mapped and has zero predicate rows in the DOS corpus. | [Shared predicates](lol2-shared-predicates.md) |
| Q7 | What writes each live elapsed cell from the registered clock? Reload units, PIT divisor and a saved elapsed-cell witness are mapped. | [Timer clocks](lol2-timer-clock.md) |
| Q8 | What do the remaining item-use handlers do? **Mostly answered:** all 108 indexes have a native mode and effect ([handlers](lol2-item-handlers.md#remaining-modes-and-effects)), including the twelve movie items. **Still open:** the `0xF7030` variant receivers, the replacement definitions (2, 8, 83, 91–93), what instance +5 means in play, and game-facing names of several player flags | [Native item handlers](lol2-item-handlers.md) |
| Q9 | What are the downstream spell effects and quest inputs to each lesson? **Mostly answered:** one downstream payload for each of the 35 player-dispatch IDs, and the level grants that feed each lesson item ([spell dispatch](lol2-spell-dispatch.md#payloads-of-the-35-player-slots)). **Still open:** the effect-15 receiver, effect-17 collision, effect-32/33 writebacks, the controller-channel names, the message-0x26 producer, and the entry route of unlinked stream-1 groups | [Player spell dispatch](lol2-spell-dispatch.md) |
| Q10 | What drives the remaining AI transitions and descriptor flags? The paired observation fields, several deeper mode branches and two hit paths that set +0xA3 are mapped. | [Creature observation](lol2-creature-observation.md) |
| Q11 | What are the gameplay roles of the remaining save sections and header fields? The placed-item row and recipient-pool write paths are mapped. A controlled before/after pickup pair remains open. | [Native save section descriptors](lol2-save-sections.md), [field witnesses](lol2-save-field-witnesses.md) |
| Q12 | Movies. **Answered for pointer tables:** 1,109 movies, including 4×2 blocks, byte-13 value 0 (the `CIND` schedule) and the raw chunks in `POOL.MIX` entry 4 ([formats/vqa.md](formats/vqa.md)). **Still open:** the 837 `VPRZ`/`VPTR` streams, and two `VPTZ` frames (`L20_BBI.MIX` entry 25 frame 115, `SPKSTON2.MIX` entry 4 frame 492). Scene ids are the 86-name table ([lol2-movie-scenes.md](lol2-movie-scenes.md)) | [lol2-vqa-v2.md](lol2-vqa-v2.md), [formats/vqa.md](formats/vqa.md) |
| Q13 | Text: where the dialogue and message tables are stored, and their format. **Answered for the message tables (help, options, automap, credits, error text); character dialogue is still open:** five TRR names, one reader, record layout in [lol2-text-tables.md](lol2-text-tables.md). `TEXT.MIX` and `TCEL.MIX` are room archives. The `WOMS` line path is an `.aud` name. Whether the open prefers the loose file or the MIX entry is still open | [lol2-text-tables.md](lol2-text-tables.md) |
| Q14 | Texture flags other than 0xA9. **Answered for layout:** ten flags, including `0x80A9`, share the raw 8-bit layout (2,039 descriptors); column storage is shown on eight of them (not `0x20E1`, `0x80E1`). `0x0143`, `0x0161` and `0x0342` are 22-byte `.vqa` names (881). **Still open:** the non-raw payloads of `0x1246` (27,889) and the other payload-length flags (layout open), and what flag bits `0x8000` and `0x2000` mean | [lol2-level-texture-container.md](lol2-level-texture-container.md) |
| Q15 | HMI-MIDI music. **Answered:** 33 `HMI-MIDISONG` entries, the event stream, and a standard-MIDI converter in [lol2-music-2026-11.md](lol2-music-2026-11.md). One key (`0x1305A4F0`) has no stem. The 33 `FORM` entries in `LOCAL.MIX` are a different container | [lol2-music-2026-11.md](lol2-music-2026-11.md) |
| Q16 | Wall-span geometry, UVs and special openings beyond the traced span; the Huline Temple interior portals. **Partly answered** ([formats/walls.md](formats/walls.md)): the wall table, each region's run of rows (traced at 0xF4370) and the code bits; all 88,994 rows of the 15 levels partition exactly; most Huline Temple rows are upper/lower pieces on portal sides (a window example in L14_HT) | [lol2-wall-material-provenance.md](lol2-wall-material-provenance.md), [draracle-restoration.md](draracle-restoration.md) |
| Q17 | L8 controls 69 and 114. Direct events, motion, link and unlink commands mapped. Visible geometry and some input conditions remain open | [L8 controls](lol2-l8-controls.md) |
| Q18 | What gameplay conditions produce the unresolved events and indirect effects in the 15 indexed levels? | [Per-level script notes](levels/notes/README.md) |
| Q19 | **Answered.** The level ODF entry stores the 147-byte definitions at header u32 +0x10 with count at +0x48, verified in all 15 level archives and in the native reader | [formats/entity-records.md](formats/entity-records.md) |
| Q20 | The texture cache. The game ships `CACHEBAK.MIX` (131 bytes) and `CDCACHE.LS_` (4,008 bytes); when it runs it writes `CDCACHE.MIX` (about 90 MB) and `CDCACHE.LST` in the game folder. What the shipped files hold, and how the game builds the cache from them, is open. Measurements of a written `CDCACHE.MIX` (decoded level texture blobs, e.g. L1_DC at file offset 5,070 in one copy) describe one installation's run-time state, not shipped data | [formats/mix.md](formats/mix.md) |
