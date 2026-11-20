# LoL2 reverse-engineering status

What is documented about the original game, which tool reads it, what the tools check on the game files, and what is open. This table replaces the "almost fully understood" summary of earlier pages: those pages ([understanding (history)](lol2-understanding-2026-11.md), [current status (history)](lol2-current-status.md), [closure summary (history)](closure-summary.md), [final closure memo (history)](final-closure-memo.md)) are kept as history.

Run the checks: `python3 tools/check_all.py` with `$LOL2_DAT` set: 47 checks, all pass on the English DOS 1.30 copy with the listed requirements.

**Running-game results.** Answered probes are counted in the rating; which ones and how: [NEEDS_A_RUNNING_GAME](NEEDS_A_RUNNING_GAME.md#answered-probes). Runs on hand-edited copies of a game-written save: [edited saves](EDITED_SAVES.md).

**Short format pages** (one per format, with a worked example from the game files): [formats/](formats/README.md), 13 pages; **level sheets**: [levels/](levels/README.md).

**Rating** (counted by `tools/rating.py`; see [how we rate](HOW_WE_RATE.md)):

<!-- rating:begin -->
- **Files read:** 83 of 83 files in `DAT` (1,915.6 of 1,915.6 MiB) have their whole layout read by a tool here: every byte belongs to a known header, directory, entry, chunk, segment or resource, or to zero padding between them; the DOS part of `SETUP.EXE` is counted by its length (what is inside an entry may still be only partly understood).
- **Rules traced:** the pages mark 758 statements CONFIRMED (proved from the program code or the files) and 179 UNCONFIRMED (a reading not yet proved), on 125 current pages; old notes kept as history are not counted.
- **Seen in the running game:** 4 of 9 probes that need the original game running are answered (a question can have more than one probe); 0 of them rest on edited saves only.
- **Open questions:** 20 numbered questions: 5 answered, 14 mostly answered, 1 partly answered.
<!-- rating:end -->

**Columns**: *Pages*: where it is described. *Tool check*: what `--check` measures on the game files. *Open*: numbered in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

| Area | Pages | Tool check | Open |
|------|-------|-----------|------|
| MIX archives | [format page](formats/mix.md), [glossary](GLOSSARY.md), [texture container](lol2-level-texture-container.md) | `lol2_mix_parser` and `lol2_source_format` agree on all 81 MIX files in `DAT/` (2905 entries; sizes, bounds, no overlap; signed key order 81/81); game folder 6/7 | Q20 |
| Loose DAT files | [format page](formats/loose.md) | `lol2_loose`: `AUTOPLAY.WAV` and `SETUP.EXE` are read to the last byte. Whether the game opens them is open | which program opens them ([loose](formats/loose.md)) |
| Entry names and keys | [texture container](lol2-level-texture-container.md#entry-name-and-key-proven) | `lol2_westwood_hash`: the texture entry name is a key in 15/15 level archives, the room module name in 47 room archives | Q3 |
| Compression | [compression](formats/compression.md), [options shapes](formats/room-sections.md) | `LOCAL.MIX` entry 1: all 39 `options.shp` shapes reach their expected lengths and dimensions (`lol2_decompress_sphere`). Westwood LZ77 at VA `0x158D58`: self-test passes; no size-prefixed MIX entry decodes; all eleven callers' buffers mapped, source filenames open | Q1 |
| Level geometry | [geometry format page](formats/geometry.md), [draracle-restoration](draracle-restoration.md), [native wall verification](native-wall-verification.md) | one geometry entry per level archive, 15/15 (`lol2_source_format`); 52,669 regions, all vertex and neighbour indices in range, 99.5% of 178,728 portal links reciprocal (`lol2_level_report`) | Q16 |
| Levels, rooms, exits | [level sheets](levels/README.md), [level graph](lol2-level-graph.md), [progression](PROGRESSION.md) | `lol2_level_report`: 15/15 level archives read, texture container found by name hash in 15, 72 level-transition commands (same as the level graph's exit table); 253 held-item identity tests across the four main tables. The placed-item table yields another 57 group references | Q3, Q18 |
| Level scripts | [opcode reference](lol2-script-opcodes.md), [events, timers, predicates](lol2-script-events.md), [script format](lol2-level-script-format.md), [engine facts](lol2-script-engine-facts-2026-10.md), [addendum](lol2-script-engine-facts-2026-10-addendum.md) | `lol2_disassemble_scripts`: 15/15 levels, 42,594 commands, 32 observed opcodes, 0 unsupported; handlers of all 37 opcodes located. `lol2_plot_branches`: 289 events outside the exits, 287 groups, 28 shared slots. `lol2_instance_field`: opcode 2 selectors 0 through 66, opcode 6 has 13 arms, opcode 9 has 35, opcode 15 has 113 | Q4–Q7, Q17 |
| Entities and objects | [entity object map](lol2-entity-object-map.md), [object state word](lol2-object-state-word.md), [cave object catalogue](cave-object-catalogue.md) | 128 entity records of 62 types in 15/15 level archives (`lol2_entity_field_analyzer`); 29 B_HUMAN/WORM records in 12 levels | Q18 |
| Items | [Item format](formats/items.md), [grants and effects](lol2-item-effects.md), [item handlers](lol2-item-handlers.md) | [Grant census command](lol2-item-effects.md#reproduce-the-grant-census) checks 876 grants against the 170 item identities in the definitions. `lol2_instance_field`: 16 instance byte +5 sites | Q8 |
| Walls and textures | [walls](formats/walls.md), [texture container](lol2-level-texture-container.md), [wall material provenance](lol2-wall-material-provenance.md), [texture map inventory](texture-map-inventory.md), [wall texture review](wall-texture-review.md) | `lol2_texture_container.py --check` (separate from check_all because it needs the system liblzo2): 15 levels, 38,361 descriptors, 2,039 raw, 881 movie names; the row-span reader walks 30,593 row-span mips and the four `0x02AC` mips to their last byte (2,291,765 row headers). The `tools/history/draracle/` pipeline has its own tests | Q14 payloads, Q16 |
| Sprites | [block sprite decoder](block-sprite-decoder.md), [creature frame groups](creature-frame-groups.md) | `lol2_texture_container.py --check`: the 27,889 `0x1246` frame descriptors in the 15 level texture banks partition into 1,844 consecutive groups (size at `+0x08`, ordinal at `+0x09`; none outside a group, none in two) | |
| Sound and music | [format page](formats/sound.md), [audio inventory](audio-inventory.md), [music](lol2-music-2026-11.md), [XMIDI](formats/xmi.md) | `lol2_aud_decode`: 453 AUD entries in 29 `DAT/` archives decode (437 exactly, 16 one sample short). `lol2_hmi_midi`: 33 named songs, including the direct CREDITS path, 438 tracks, standard MIDI in memory. `lol2_xmi_reader`: all 33 FORM scores in LOCAL.MIX | native XMIDI selection and the last sample of 16 AUD entries |
| Movies | [VQA format page](formats/vqa.md), [VQA v2](lol2-vqa-v2.md), [movie scenes](lol2-movie-scenes.md) | `lol2_vqa_v2_decode --check`: census and one sample of each layout. `--full`: 1,109 pointer tables pass; 837 pointer-stream movies, 52,187 indexed frames expanded in memory; 2 relative-reference frames, whose packets' command extents `--check` pins (frame 492's packet ends after 1,059 of 32,000 bytes). `lol2_media_check`: scene table and two worked movies | Q12: displayed pixels of the two pointer-table frames 115 and 492 (absolute-mode LCW) |
| Combat | [Combat and creature decisions](lol2-combat-ai.md), [creature transitions](lol2-creature-transitions.md), [executioner combat evidence](executioner-combat-evidence.md) | Bounded arithmetic replay in `tools/history/draracle/` | Q10 |
| Spells | [Costs, acquisition and rewards](lol2-spells.md), [spell dispatch](lol2-spell-dispatch.md) | `lol2_numbers --check`: the effect rows at `LOLG.DAT+0x1CC980` and school rows at `+0x1CCB44` join across all 113 effects | Q9 |
| Saves | [Native save format](lol2-save-format.md), [save sections](lol2-save-sections.md) | 27 slots from the reference `SAVEGAME` folder (written by the original game during one player's play, not shipped) and 149 nonempty level blocks checked; 6,765 nonempty level spans decode to their stated lengths; one pickup compared in a running game ([save sections](lol2-save-sections.md#controlled-pickup-in-l20_bb)) | Q11 |
| Executable | [Addresses and tables](lol2-executable-tables.md) | `lol2_parse_le`: the DOS 1.30 LE header, 5 objects, all 340 page-map rows, 341 fixup boundaries (337,375 record bytes) and the last page reaching the end of `LOLG.DAT` | |
| Text | [Message tables](lol2-text-tables.md), [spoken lines](lol2-speech.md) | `lol2_text_tables.py` re-reads the five named TRR tables. `lol2_speech_names.py` re-reads the name format, the category switch, two `MCEL.MIX` keys, the MCEL import of the switch and the cue-table loader, checks all 404 cue words, and resolves the 3134 indirect calls of the 47 room modules | Q13 |

## Tools

The top-level tools answer `--help`, take `--data` (or `$LOL2_DAT`) and write only where you tell them, never inside the repository. Those listed in `check_all.py` have a `--check`. The other tools and the `tools/history/draracle/` pipeline still use their own options.

## Corrections to earlier pages

1. The game wall texture and decoded tile images in `examples/` were removed (asset policy); the README picture (`docs/images/l1_dc_regions.png`) is now drawn by a tool from the level's region table.
2. `lol2_l9dr_census.py` reads the whole `L9_DR.MIX` as 147-byte records from offset 0; it is marked exploratory (5,861 of 160,622 slots carry a printable tag). Use `lol2_entity_field_analyzer.py` for the real entity records.
3. The Westwood LZ77 function is at VA `0x158D58`. A scan that treats a MIX entry's first u32 as an output size still matches no entry. The source, destination and capacity of all eleven direct callers are mapped; which files reach them stays open (Q1).
