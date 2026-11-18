# LoL2 reverse-engineering status

**As of:** 2026-11-18. What is documented about the original game, which tool reads it, what the tools check on the game files, and what is open. This table replaces the "almost fully understood" summary of earlier pages: those pages ([understanding](lol2-understanding-2026-11.md), [current status](lol2-current-status.md), [closure summary](closure-summary.md), [final closure memo](final-closure-memo.md)) are kept as history.

Run the checks: `python3 tools/check_all.py --data <DAT>` (15 checks; all pass on the copy read).

**Short format pages** (one per format, with a worked example from the game files): [formats/](formats/README.md) — MIX, level data, texture container, room sections, entity records, items, sound.

**Columns**: *Pages*: where it is described. *Tool check*: what `--check` measures on the game files. *Open*: numbered in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

| Area | Pages | Tool check | Open |
|------|-------|-----------|------|
| MIX archives | [format page](formats/mix.md), [glossary](GLOSSARY.md), [texture container](lol2-level-texture-container.md) | `lol2_mix_parser` and `lol2_source_format` agree on all 81 MIX files in `DAT/` (2905 entries; sizes, bounds, no overlap; signed key order 81/81); game folder 6/7 | Q20 |
| Entry names and keys | [texture container](lol2-level-texture-container.md#entry-name-and-key-proven) | `lol2_westwood_hash`: the texture entry name is a key in 15/15 level archives, the room module name in 47 room archives | Q3 |
| Compression | tool docstrings | LCW sections of `LOCAL.MIX` entry 1: 37/37 decode (`lol2_decompress_sphere`); Westwood mode-byte variant: decoder self-test only | Q1, Q2 |
| Level geometry | [geometry format page](formats/geometry.md), [draracle-restoration](draracle-restoration.md), [native wall verification](native-wall-verification.md) | one geometry entry per level archive, 15/15 (`lol2_source_format`); 52,669 regions, all vertex and neighbour indices in range, 99.5% of 178,728 portal links reciprocal (`lol2_level_report`) | Q16 |
| Levels, rooms, exits | [level sheets](levels/README.md), [level graph](lol2-level-graph.md) | `lol2_level_report`: 15/15 level archives read, texture container found by name hash in 15, 72 level-transition commands (same as the level graph's exit table); 253 held-item tests, all naming an item-table identity | Q3, Q18 |
| Level scripts | [opcode reference](lol2-script-opcodes.md), [events, timers, predicates](lol2-script-events.md), [script format](lol2-level-script-format.md), [engine facts](lol2-script-engine-facts-2026-10.md), [addendum](lol2-script-engine-facts-2026-10-addendum.md) | `lol2_disassemble_scripts`: 15/15 levels, 42,594 commands, 32 observed opcodes, 0 unsupported; handlers of all 37 opcodes located | Q4–Q7, Q17 |
| Entities and objects | [entity object map](lol2-entity-object-map.md), [object state word](lol2-object-state-word.md), [cave object catalogue](cave-object-catalogue.md) | 128 entity records of 62 types in 15/15 level archives (`lol2_entity_field_analyzer`); 29 B_HUMAN/WORM records in 12 levels | Q18 |
| Items | [Item format](formats/items.md), [grants and effects](lol2-item-effects.md) | [Grant census command](lol2-item-effects.md#reproduce-the-grant-census) checks all 876 identities against the definitions | Q8 |
| Walls and textures | [texture container](lol2-level-texture-container.md), [wall material provenance](lol2-wall-material-provenance.md), [texture map inventory](texture-map-inventory.md) | the `tools/draracle/` pipeline has its own tests | Q14, Q16 |
| Sprites | [block sprite decoder](block-sprite-decoder.md), [creature frame groups](creature-frame-groups.md) | — | |
| Sound and music | [format page](formats/sound.md), [audio inventory](audio-inventory.md), [music](lol2-music-2026-11.md) | `lol2_aud_decode`: 453 AUD entries in 29 `DAT/` archives decode (437 exactly, 16 one sample short) | Q15 |
| Movies | [VQA v2](lol2-vqa-v2.md) | — | Q12 |
| Combat | [Combat and creature decisions](lol2-combat-ai.md), [executioner combat evidence](executioner-combat-evidence.md) | Bounded arithmetic replay in `tools/draracle/` | Q10 |
| Spells | [Costs, acquisition and rewards](lol2-spells.md) | — | Q9 |
| Saves | [Native save format](lol2-save-format.md) | 27 reference slots and 149 nonempty level blocks checked | Q11 |
| Executable | [Addresses and tables](lol2-executable-tables.md) | — | |
| Text | — | — | Q13 |

## Tools

The top-level tools answer `--help`. The 10 that had no argument handling now take `--data` (or `$LOL2_DAT`), write only with `--out`, and have a `--check`; `check_all.py` runs them and `repo_guard.py` (no game files, media or stray images may be committed). The other tools and the `tools/draracle/` pipeline still use their own options; giving them `--check` is the next tool step.

## Corrections made in this pass (2026-11-18)

1. The game wall texture and decoded tile images in `examples/` were removed (asset policy); the README picture is now drawn by a tool from tile indices.
2. `lol2_l9dr_census.py` reads the whole `L9_DR.MIX` as 147-byte records from offset 0; it is marked exploratory (5,861 of 160,622 slots carry a printable tag). Use `lol2_entity_field_analyzer.py` for the real entity records.
3. The Westwood LZ77 tool's own header convention matches no MIX entry (Q1).
