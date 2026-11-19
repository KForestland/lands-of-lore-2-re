# LoL2 reverse-engineering status

**As of:** 2026-11-18. What is documented about the original game, which tool reads it, what the tools check on the game files, and what is open. This table replaces the "almost fully understood" summary of earlier pages: those pages ([understanding](lol2-understanding-2026-11.md), [current status](lol2-current-status.md), [closure summary](closure-summary.md), [final closure memo](final-closure-memo.md)) are kept as history.

Run the checks: `python3 tools/check_all.py` (with `$LOL2_DAT` set) (23 checks; all pass on the copy read).

**Running-game results** (original program under a debugger, one run each; [procedures and results](NEEDS_A_RUNNING_GAME.md)): the frame-clock writer (Q7) and the save changes of one pickup (Q11) are answered; a creature distance branch (Q10) and the level-8 controls (Q17) are partly answered; the timed message (Q9) and two movie frames (Q12) were not reached.

**Short format pages** (one per format, with a worked example from the game files): [formats/](formats/README.md), 12 pages; **level sheets**: [levels/](levels/README.md).

**Rating** (counted by `tools/rating.py`; see [how we rate](HOW_WE_RATE.md)):

<!-- rating:begin -->
- **Files read:** 81 of 83 files in `DAT` (1,915.3 of 1,915.6 MiB) are accounted for to the last byte by a reader here.
- **Rules traced:** 611 statements labelled CONFIRMED against the program or the files, 181 labelled UNCONFIRMED, on 110 current pages.
- **Seen in the running game:** 2 of 7 probes that need the original game running are answered.
- **Open questions:** 20: 3 answered, 15 mostly, 2 partly.
<!-- rating:end -->

**Columns**: *Pages*: where it is described. *Tool check*: what `--check` measures on the game files. *Open*: numbered in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

| Area | Pages | Tool check | Open |
|------|-------|-----------|------|
| MIX archives | [format page](formats/mix.md), [glossary](GLOSSARY.md), [texture container](lol2-level-texture-container.md) | `lol2_mix_parser` and `lol2_source_format` agree on all 81 MIX files in `DAT/` (2905 entries; sizes, bounds, no overlap; signed key order 81/81); game folder 6/7 | Q20 |
| Entry names and keys | [texture container](lol2-level-texture-container.md#entry-name-and-key-proven) | `lol2_westwood_hash`: the texture entry name is a key in 15/15 level archives, the room module name in 47 room archives | Q3 |
| Compression | [compression](formats/compression.md), [options shapes](formats/room-sections.md) | `LOCAL.MIX` entry 1: all 39 `options.shp` shapes reach their expected lengths and dimensions (`lol2_decompress_sphere`). Westwood LZ77 at VA `0x158D58`: self-test passes; no size-prefixed MIX entry decodes; all eleven callers' buffers mapped, source filenames open | Q1 |
| Level geometry | [geometry format page](formats/geometry.md), [draracle-restoration](draracle-restoration.md), [native wall verification](native-wall-verification.md) | one geometry entry per level archive, 15/15 (`lol2_source_format`); 52,669 regions, all vertex and neighbour indices in range, 99.5% of 178,728 portal links reciprocal (`lol2_level_report`) | Q16 |
| Levels, rooms, exits | [level sheets](levels/README.md), [level graph](lol2-level-graph.md) | `lol2_level_report`: 15/15 level archives read, texture container found by name hash in 15, 72 level-transition commands (same as the level graph's exit table); 253 held-item identity tests across the four main tables. The placed-item table yields another 57 group references | Q3, Q18 |
| Level scripts | [opcode reference](lol2-script-opcodes.md), [events, timers, predicates](lol2-script-events.md), [script format](lol2-level-script-format.md), [engine facts](lol2-script-engine-facts-2026-10.md), [addendum](lol2-script-engine-facts-2026-10-addendum.md) | `lol2_disassemble_scripts`: 15/15 levels, 42,594 commands, 32 observed opcodes, 0 unsupported; handlers of all 37 opcodes located | Q4–Q7, Q17 |
| Entities and objects | [entity object map](lol2-entity-object-map.md), [object state word](lol2-object-state-word.md), [cave object catalogue](cave-object-catalogue.md) | 128 entity records of 62 types in 15/15 level archives (`lol2_entity_field_analyzer`); 29 B_HUMAN/WORM records in 12 levels | Q18 |
| Items | [Item format](formats/items.md), [grants and effects](lol2-item-effects.md), [item handlers](lol2-item-handlers.md) | [Grant census command](lol2-item-effects.md#reproduce-the-grant-census) checks 876 grants against the 170 item identities in the definitions | Q8 |
| Walls and textures | [walls](formats/walls.md), [texture container](lol2-level-texture-container.md), [wall material provenance](lol2-wall-material-provenance.md), [texture map inventory](texture-map-inventory.md) | `lol2_texture_container.py --check` (separate from check_all because it needs the system liblzo2): 15 levels, 38,361 descriptors, 2,039 raw, 881 movie names. The `tools/draracle/` pipeline has its own tests | Q14 payloads, Q16 |
| Sprites | [block sprite decoder](block-sprite-decoder.md), [creature frame groups](creature-frame-groups.md) | — | |
| Sound and music | [format page](formats/sound.md), [audio inventory](audio-inventory.md), [music](lol2-music-2026-11.md) | `lol2_aud_decode`: 453 AUD entries in 29 `DAT/` archives decode (437 exactly, 16 one sample short). `lol2_hmi_midi`: 33 named songs, including the direct CREDITS path, 438 tracks, standard MIDI in memory | the 33 `FORM` entries in `LOCAL.MIX` |
| Movies | [VQA format page](formats/vqa.md), [VQA v2](lol2-vqa-v2.md), [movie scenes](lol2-movie-scenes.md) | `lol2_vqa_v2_decode --check`: census and one sample of each layout. `--full`: 1,109 pointer tables pass; 837 pointer-stream codebooks, pixels not expanded; 2 relative-reference frames. `lol2_media_check`: scene table and two worked movies | Q12 pointer stream, two frames in pointer-table movies (absolute-mode LCW) |
| Combat | [Combat and creature decisions](lol2-combat-ai.md), [creature transitions](lol2-creature-transitions.md), [executioner combat evidence](executioner-combat-evidence.md) | Bounded arithmetic replay in `tools/draracle/` | Q10 |
| Spells | [Costs, acquisition and rewards](lol2-spells.md), [spell dispatch](lol2-spell-dispatch.md) | — | Q9 |
| Saves | [Native save format](lol2-save-format.md), [save sections](lol2-save-sections.md) | 27 slots from the reference `SAVEGAME` folder (written by the original game during one player's play, not shipped) and 149 nonempty level blocks checked; 6,765 nonempty level spans decode to their stated lengths; one pickup compared in a running game ([save sections](lol2-save-sections.md#controlled-pickup-in-l20_bb)) | Q11 |
| Executable | [Addresses and tables](lol2-executable-tables.md) | — | |
| Text | [Message tables](lol2-text-tables.md), [spoken lines](lol2-speech.md) | `lol2_text_tables.py` re-reads the five named TRR tables. `lol2_speech_names.py` re-reads the name format, the category switch, two `MCEL.MIX` keys and the MCEL import of the switch (not part of `check_all.py`) | Q13 |

## Tools

The top-level tools answer `--help`, take `--data` (or `$LOL2_DAT`) and write only where you tell them, never inside the repository. Those listed in `check_all.py` have a `--check`. The other tools and the `tools/draracle/` pipeline still use their own options.

## Corrections made in this pass (2026-11-18)

1. The game wall texture and decoded tile images in `examples/` were removed (asset policy); the README picture is now drawn by a tool from tile indices.
2. `lol2_l9dr_census.py` reads the whole `L9_DR.MIX` as 147-byte records from offset 0; it is marked exploratory (5,861 of 160,622 slots carry a printable tag). Use `lol2_entity_field_analyzer.py` for the real entity records.
3. The Westwood LZ77 function is at VA `0x158D58`. A scan that treats a MIX entry's first u32 as an output size still matches no entry. The source, destination and capacity of all eleven direct callers are mapped; which files reach them stays open (Q1).
