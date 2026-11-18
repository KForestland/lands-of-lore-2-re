# Open questions

Numbered so the pages and [`STATUS.md`](STATUS.md) can point at them. Each is something not yet known about the ORIGINAL game's files or rules. When one is answered, its page is updated and the entry says so. Sources: the repo's own "still open" lists ([understanding](lol2-understanding-2026-11.md#still-open), [script engine facts](lol2-script-engine-facts-2026-10.md#still-open)) and the checks added on 2026-11-18.

| ID | Question | Page |
|----|----------|------|
| Q1 | Which LoL2 data, if any, uses the Westwood LZ77 variant with a leading mode byte (`tools/lol2_decompress_westwood.py`)? No MIX entry whose first u32 looks like a size decodes with it | tools |
| Q2 | `LOCAL.MIX` entry 1: the two stored (uncompressed) sections 0 and 15 are 2 bytes shorter than their headers state. Is the header 10 bytes for stored sections, or the size counted differently? | [lol2-level-texture-container.md](lol2-level-texture-container.md) |
| Q3 | Room archives: the level graph lists 45 room archives with a `WOMS\<ROOM>_.WOM` module plus 3 movie-only ones; the hash check finds the WOM name in 47 archives. Which count is right, and what are the two extra? | [lol2-level-graph.md](lol2-level-graph.md) |
| Q4 | The full script opcode table: 37 opcodes have known command lengths (native routine 0x645E0); the meaning of every arm (open: opcode 14 arm 5, opcode 9 arm 6, opcode 18 drift speed, the rest of opcode 196) | [lol2-script-engine-facts-2026-10.md](lol2-script-engine-facts-2026-10.md) |
| Q5 | Record kinds and the events that run them; caller paths for control and prop events | same |
| Q6 | Global variables, flags and predicates (the soul value and branch flags) as stored by the original | — |
| Q7 | Timers and the game clock: units and kinds | same |
| Q8 | Items beyond the record format: which script groups grant which item, and each item-use handler's effect | [lol2-item-format.md](lol2-item-format.md) |
| Q9 | Spells: costs, effects, teaching | — |
| Q10 | Combat and monster behaviour beyond the one traced encounter | [executioner-combat-evidence.md](executioner-combat-evidence.md) |
| Q11 | The save file layout | — |
| Q12 | Movies: the control table that maps scenes to VQA files; full codebooks for every movie | [lol2-vqa-v2.md](lol2-vqa-v2.md) |
| Q13 | Text: the TEXT/TCEL container and the dialogue tables | — |
| Q14 | Texture flags other than 0xA9 (including 0x80A9) | [lol2-level-texture-container.md](lol2-level-texture-container.md) |
| Q15 | HMI-MIDI music: format and conversion | [lol2-music-2026-11.md](lol2-music-2026-11.md) |
| Q16 | Wall-span geometry, UVs and special openings beyond the traced span; the Huline Temple interior portals | [lol2-wall-material-provenance.md](lol2-wall-material-provenance.md), [draracle-restoration.md](draracle-restoration.md) |
| Q17 | The L8 control records for the cache ladder (control 69) and the tree bridge (control 114) | — |
| Q18 | Per-level puzzle records: what each level's scripts and object records do, level by level | — |
