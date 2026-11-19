# Tools

To write the inventory, level sheets and text counts together, use `full_report.py`. [Cookbook](../docs/COOKBOOK.md#write-a-full-report)

Read original LoL2 files and replay the checks cited in the reference pages. The [historical helper index](history/README.md) lists every archived script and fixture test.

## Historical cave geometry checks

See [Draracle findings](../docs/draracle-restoration.md). Run
`python3 tools/history/draracle/run_geometry_pipeline.py --game-root /path/to/lol2 --out /path/to/output`.
This requires Python 3.10+ and Capstone 5, and produces corrected geometry and
wall-record evidence from pinned original files.

Run `python3 tools/lol2_numbers.py --check` to compare the generated item, spell, creature and form tables with the page. It prints `CHECK numbers: LoL2 tables match docs/NUMBERS.md`. [Numbers at a glance](../docs/NUMBERS.md)

## Setup

- Python 3.10+
- `pip install -r requirements.txt`: Pillow (picture output), capstone (disassembly checks), numpy (movie decoder)
- `liblzo2` (`apt install liblzo2-2` on Debian/Ubuntu) for packed saves,
  level textures and the full `check_all.py` suite
- Set `LOL2_DAT` to your LoL2 `DAT/` directory path, or pass `--data`
- Some [historical helpers](history/README.md) use `OUTPUT_DIR` or `LOL2_OUT`. Give those an output directory outside the repository.

## Common options

For the reader tools below, `--help` changes nothing and `--data` or
`$LOL2_DAT` identifies the game files. Text reports print to stdout.
The schematic writes to the path you pass with `--out`.
`check_all.py` runs the configured corpus checks. Standalone checks
are marked below. Use output paths outside the repository.

## Format and rules coverage

Tool names below are relative to `tools/`. Checks describe what the named
tool actually exercises. A reference table records the documented rules
when those rules do not have a standalone file layout. For file types and
example commands, see the [format quick reference](../docs/QUICK_REFERENCE.md).

| Original format or rules table | Reader | Check | Inspect output |
|---|---|---|---|
| [MIX directories and filename keys](../docs/formats/mix.md) | `lol2_mix_parser.py`, `lol2_westwood_hash.py` | Strict directory and name-key checks | Entry offsets, sizes and hashes |
| [Cache seed and old cache rows](../docs/lol2-cache-initializer.md) | `lol2_cache_seed.py`, `lol2_inspect.py cache` | Joins shipped seed rows to texture entries | Row lengths, old positions and backup directory |
| [Room archives and WOM relocations](../docs/lol2-room-archives.md) | `lol2_media_check.py`, `lol2_inspect.py wom` | Original module framing and relocations | One module's body, dispatch and relocation offsets |
| [Level data directories](../docs/formats/level-data.md) | `lol2_source_format.py`, `lol2_level_report.py` | Geometry found and sections checked across all levels | Level reports |
| [Regions and portals](../docs/formats/geometry.md), [walls](../docs/formats/walls.md), [automap inputs](../docs/formats/maps.md) | `lol2_level_report.py`, `lol2_level_map.py`, `lol2_level_schematic.py` | Region links, wall ranges, polygons and door-candidate geometry | Wall, portal, door-candidate and placement schematic |
| [Wall verification](../docs/native-wall-verification.md), [flat spans](../docs/native-flat-wall-spans.md), [material provenance](../docs/lol2-wall-material-provenance.md), [cave geometry](../docs/draracle-restoration.md) | `history/draracle/verify_huline_wall_spans.py`, `history/draracle/run_geometry_pipeline.py` and the individual tools cited in the pages | Focused standalone replay and constructor checks | Geometry, wall coordinates and the documented witnesses |
| [ODF definitions](../docs/formats/entity-records.md), [placed objects and controls](../docs/lol2-l8-controls.md), [entity to object map](../docs/lol2-entity-object-map.md) | `lol2_entity_field_analyzer.py`, `lol2_level_report.py`, `lol2_level_schematic.py` | Definition framing, placement rows and selected joins | Entity summary, level report and numbered item and actor marks |
| [Cave object and entity tables](../docs/cave-object-catalogue.md), [entity links](../docs/cave-entity-links.md) | `history/draracle/catalogue_cave_objects.py`, `history/draracle/catalogue_cave_entities.py` | Reference witnesses in the pages | Cave object and entity catalogues |
| [Script framing](../docs/lol2-level-script-format.md) and [opcode dispatch](../docs/lol2-script-opcodes.md) | `lol2_disassemble_scripts.py`, `lol2_event_browser.py` | Both command streams in all 15 levels, with native opcode sizes | Full listing or paged group summaries and opcode meanings |
| [Trigger and predicate tables](../docs/lol2-script-events.md), [shared predicates](../docs/lol2-shared-predicates.md), [level exits](../docs/lol2-level-graph.md), [progression](../docs/PROGRESSION.md) | `lol2_event_browser.py`, `lol2_level_report.py`, `lol2_progression.py`, `lol2_plot_branches.py`, `lol2_level_notes.py` | Event and predicate joins, the exit census, the 289 non-exit plot branches and the progression page | Trigger owners, matcher operands, predicate indices, level notes and each exit's slots |
| [Script motion](../docs/lol2-script-motion.md), [event producers](../docs/lol2-event-producers.md), [timers and clocks](../docs/lol2-timer-clock.md) | `lol2_inspect.py rules`, `lol2_save_native.py` for clock witnesses | Original code revision, selected native reads and calls | Motion, event and timer reference sections with addresses |
| [Item table framing](../docs/formats/items.md), [definition fields](../docs/lol2-item-format.md) and [item handlers](../docs/lol2-item-handlers.md) | `lol2_item_labels.py`, `lol2_level_report.py`, `lol2_inspect.py item` | Definition keys, names, replacement handlers and placement links | Per-definition fields, raw row and handler address |
| [Spell table](../docs/lol2-spells.md), [dispatch](../docs/lol2-spell-dispatch.md), [item effects](../docs/lol2-item-effects.md) | `lol2_inspect.py native` and `rules` | Native table offsets and original code revision | Spell row bytes, dispatch and item effect references |
| [Combat and creature AI](../docs/lol2-combat-ai.md), [mode transitions](../docs/lol2-creature-transitions.md), [observation](../docs/lol2-creature-observation.md), [state word](../docs/lol2-object-state-word.md) | `lol2_inspect.py rules` | Original code revision. Combat and state-word behavior remain reference only | Combat formulas, creature mode, observation and state reference sections |
| [Texture banks](../docs/formats/texture-container.md), [descriptors and mips](../docs/lol2-level-texture-container.md) | `lol2_texture_container.py` | Standalone `--check` for raw and compressed mip layouts and LZO frames | Container and material reports, explicit PNG export |
| [LZO1X and Westwood LZ77](../docs/formats/compression.md) | `lol2_texture_container.py`, `lol2_decompress_westwood.py` | LZO block lengths, LZ77 synthetic self-test and container-specific witnesses | Texture framing. VQA chunks, `options.shp` and WSA deltas use the same LZ77 decoder at `0x158D58` |
| [`options.shp`](../docs/formats/room-sections.md) | `lol2_decompress_sphere.py` | Shape boundaries, stored lengths and decoded pixel counts | Shape summary and explicit frame export |
| [Sprite blocks](../docs/block-sprite-decoder.md), [cave sequences](../docs/cave-sprite-sequences.md), [creature frame groups](../docs/creature-frame-groups.md), [prop mirroring](../docs/prop-frame-mirroring.md), [special pixels](../docs/special-sprite-pixels.md) | `history/draracle/extract_block_sprite_frames.py`, `history/draracle/extract_cave_sprite_sequences.py` | Reference witnesses only | Per-cave frame and sequence reports, explicit frame export |
| [WSA panel animations](../docs/formats/compression.md) | `lol2_media_check.py`, `lol2_inspect.py wsa` | Named archive members and compressed delta spans | Animation dimensions and delta lengths and offsets |
| [AUD and sound banks](../docs/formats/sound.md), [cues](../docs/lol2-sound-cues.md), [speech](../docs/lol2-speech.md) | `lol2_aud_decode.py`, `lol2_sound_bank.py`, `lol2_speech_names.py`, `lol2_inspect.py cue` | AUD chunk lengths, cue words and native switch paths | Audio info, bank rows and footer index-to-clip lookup |
| [HMI format](../docs/lol2-music-2026-11.md) and [music selection](../docs/lol2-music-selection.md) | `lol2_hmi_midi.py`, `lol2_inspect.py hmi`, `lol2_media_check.py` | 33 HMI files and filename-table checks | Track offsets and event counts, explicit MIDI output |
| [VQA movies](../docs/formats/vqa.md), [VQA v2 framing](../docs/lol2-vqa-v2.md), [scene table](../docs/lol2-movie-scenes.md) | `lol2_vqa_v2_decode.py`, `lol2_media_check.py`, `lol2_inspect.py scene` | Frame framing, sample decodes and native scene witnesses | Movie info and per-scene level references |
| [TRR text tables](../docs/lol2-text-tables.md) | `lol2_text_tables.py`, `lol2_inspect.py trr` | Named table framing and counts | Record IDs, offsets and selected record text |
| [Loose WAV and NE setup image](../docs/formats/loose.md) | `lol2_loose.py`, `lol2_inspect.py loose` | WAV chunks and executable sections | Chunk, segment and resource offsets |
| [Save headers](../docs/lol2-save-format.md), [sections](../docs/lol2-save-sections.md), [field witnesses](../docs/lol2-save-field-witnesses.md) | `lol2_save_inspect.py`, `lol2_save_header.py`, `lol2_save_native.py` | Native selector witnesses, slot directories and decoded bounds | Field offsets, all directories and selected payloads with named fields and unknown bytes |
| [Executable LE layout and native tables](../docs/lol2-executable-tables.md) | `lol2_inspect.py native`, focused witness checkers above | Table and relocation witnesses in `check_all.py` | Read-only LE object layout, named table offsets, row bytes and handler VAs |

These views retain the limits of the source pages. For example, the
geometry view shows potential doorway locations, the cue inspector joins
audio rows, and the rule views retain the documented uncertainties about
player-visible effects and dialogue text.


### `check_all.py`

Run each `--check` and print one line each, then a summary.

```
$ python3 tools/check_all.py | sed -n '1,2p;$p'
CHECK repo_guard: N tracked files; game files, media, stray images, files over 300 KB, machine paths, words from the local list, or commit identities: none (0); private word list: not present, skipped
CHECK mix: 81 MIX files, 2905 entries; this reader and lol2_source_format.parse_mix agree and every entry lies inside its file: 81/81; index sorted by signed key: 81/81 (by unsigned key: 20); bad=none
ALL 37 CHECKS PASSED
```

### `doc_links.py`

Checks links and anchors only (it runs no command shown in the pages): every relative link, image link, `<a href>` and `#anchor` in `README.md`, `tools/README.md`, `CONTRIBUTING.md`, `docs/`, and `examples/` and `evidence/` when present. Anchors follow GitHub's heading ids. A link or heading inside a fenced example is skipped. Part of `check_all.py`.

```
$ python3 tools/doc_links.py --check
CHECK links: every relative link and anchor in the README files and docs resolves
```

### `lol2_loose.py`

Reads `AUTOPLAY.WAV` and `SETUP.EXE` through their last byte. Part of `check_all.py`. Page: `docs/formats/loose.md`.

### `lol2_inspect.py`

Small read-only views over original resource files and executable tables.
Run `python3 tools/lol2_inspect.py --data /path/to/DAT --check` to replay
the sample views. Each command below appends to
`python3 tools/lol2_inspect.py --data /path/to/DAT`.

| Append | First line or result |
|---|---|
| `cache` | `L1_DC CDCACHE.LS_+0xA8  seed length 13040404  current bank 13040404  old position 0x13CA` |
| `wom TCEL` | `TCEL.MIX+0x36  WOM entry 3  version 0x0101  2656 bytes` |
| `wsa P_LUTHER.WSA --delta 0` | `P_LUTHER.WSA LOCAL.MIX+0x1909B17  38x52  65 frames, 66 stored deltas` |
| `hmi CREDITS` | `CREDITS LOCAL.MIX+0x1A4B52B  22 HMI tracks` followed by per-track offsets and event counts |
| `cue 161` | `Cue 161 LOCALLNG.MIX+0x1B172DA  bank row 0298 +0x1B0A31C  0202024e.aud` |
| `scene 13 --level 12` | `Scene 13 citadel  LOLG.DAT+0x1CF5C0` followed by its level-12 script references |
| `trr help` | `LOCALLNG.MIX+0x1B185DF  41 records, payload starts at +0x1B1872F`. Add `--id 0` for the record's text as stored in your copy. |
| `item 68` | `Item 68 GLOBAL.MIX+0x5B9115  identity 0xE0649CBA` followed by labelled definition fields |
| `native --table spell-effects --row 20` | `spell-effects[20] LOLG.DAT+0x1CC9D0  19 0c 00 21` |
| `loose` | WAV chunk offsets, then setup segment and resource offsets |
| `rules motion` | The two opcode-motion sections from `docs/lol2-script-motion.md`. Other topics include `timers`, `spells`, `combat` and `creatures`. |

```text
$ python3 tools/lol2_inspect.py --data /path/to/DAT --check
CHECK format inspector: cache, WOM, WSA, HMI, cues, scenes, TRR, items, LE, loose files and rule references
```

Evidence is linked by format in the [coverage table](#format-and-rules-coverage).

### `lol2_save_header.py`

Reads one save slot you name (a player save, not a game file) and prints its preview, global and level offsets as JSON. Writes nothing. Pass `--check` with a slot to compare its stored level lengths with the directory.

### `lol2_save_inspect.py`

Prints the header, directories and section names of a player save
written by the game (saves are not shipped game files) to stdout. `--level 1` limits the overview to the first level block.
Use `--level 1 --section 27 --row 1` to inspect one texture animation row,
or `--global-section 2` to inspect player item records. Section offsets
are relative to the decoded payload. Unassigned bytes and XOR deltas
are shown as hex. Global sections with flag 2 currently show deltas only.
Supply the matching game-written level `.IMG`
with `--baseline` to recover the selected level's values, including its
serialized pointer words. Needs `liblzo2` for packed payloads. Field
sources are in the [save reference](../docs/lol2-save-format.md) and
[save field witnesses](../docs/lol2-save-field-witnesses.md).

```text
$ python3 tools/lol2_save_inspect.py --data /path/to/DAT --check
CHECK save inspector: 30 game-written player saves and 154 level blocks
```

That output is from the reference installation's `SAVEGAME` folder. A
fresh installation reports `CHECK save inspector: native save witnesses
checked; no save slots supplied`. Use `python3 tools/lol2_save_inspect.py
"$LOL2_SLOT"` with a slot of your own for the field-by-field overview.

### `lol2_mix_parser.py`

List a MIX archive, or extract one entry with `--out`. `--check`: agrees with `lol2_source_format.parse_mix` on every archive.

```
$ python3 tools/lol2_mix_parser.py L1_DC.MIX
MIX file: /path/to/your/LOL2/DAT/L1_DC.MIX
Entries: 3
  [  0] key=0xB1162802  offset=  7389520  size=    35028
  [  1] key=0xB1202500  offset=  7091978  size=   297542
```

### `lol2_source_format.py`

Library: strict MIX reader, level geometry entry, opcode lengths. `--check`: all archives and the 15 geometry entries.

```
$ python3 tools/lol2_source_format.py --check
CHECK source_format: 81/81 MIX files pass the strict reader (sizes, bounds, no overlap); one geometry entry (dword 0 = 18, dword 4 = 5300) in 15/15 le...
```

### `lol2_level_schematic.py`

Draws the regions, walls, portals and numbered placements as a PNG. The
amber mark means a linked side with a flat, collapsed region. These are
doorway candidates from geometry. Lighter floors are higher (the
`lol2_level_map.py` overview uses the opposite: darker = higher), and
stacked storeys can overlap. `--focus` selects a zero-based region,
outlined in cyan, and `--radius` gives map units to either side. Use a focused view for
crowded placements. [Example and field sources](../examples/README.md)

```text
$ python3 tools/lol2_level_schematic.py --data /path/to/DAT --check
CHECK level schematic: 15 levels, 52669 regions, 663 items, 1028 actor placements, 2473 collapsed portal sides
```

### `lol2_disassemble_scripts.py`

Print both command streams, event links and predicate bytes with MIX-relative offsets.
Use `--out` to write a listing outside the game directory. The
[opcode reference](../docs/lol2-script-opcodes.md) follows the native handlers.

```
$ python3 tools/lol2_disassemble_scripts.py --data /path/to/DAT L1_DC
L1_DC  geometry MIX+0x6C370A
...
$ python3 tools/lol2_disassemble_scripts.py --data /path/to/DAT --check
CHECK scripts: 15/15 levels, 42594 commands, 32 observed opcodes, 0 unsupported
```

### `lol2_event_browser.py`

Prints group offsets, triggering records, predicate rows and one-line native
opcode meanings. It includes the placed-item table. Use `--start` and
`--limit` to page through a level or select an exact `--stream`/`--group`
to see individual command offsets.
The command for [the level-1 tutorial](../docs/tutorial-one-event.md) begins
with the following lines.

```text
$ python3 tools/lol2_event_browser.py --data /path/to/DAT L1_DC --stream 1 --group 0x228e
L1_DC: groups 1–1 of 1  (opcodes in hex)
s1:0x228E MIX+0x6E7FF5  1 trigger record  opcodes 09 03 10
```

`--check` replays the browser over all 15 levels and verifies group, command and
trigger counts. Opcode and trigger evidence comes from the [opcode reference](../docs/lol2-script-opcodes.md)
and the [event matcher reference](../docs/lol2-script-events.md).

### `lol2_westwood_hash.py`

Hash entry names as the archives key them. `--check`: the documented names are keys.

```
$ python3 tools/lol2_westwood_hash.py 'SPHERE1\L1_DC\L1_DC.TE_'
SPHERE1\L1_DC\L1_DC.TE_: v1 0xB12F2907 (2972657927)  v2 0xB12F2907  ts 0xA680308A  crc 0x330D9D80
```

### `lol2_decompress_sphere.py`

Options interface shapes in `LOCAL.MIX`. `--check` validates every stored and compressed shape.

```
python3 tools/lol2_decompress_sphere.py --check
```

### `lol2_decompress_westwood.py`

Westwood LZ77. The function is at VA `0x158D58`; `--out` required. The [caller table](../docs/formats/compression.md#direct-calls-and-their-buffers) maps all eleven calls.

```
$ python3 tools/lol2_decompress_westwood.py --check
CHECK westwood: decoder self-test passed; data scan: 8 MIX entries whose first u32 exceeds the entry size, 0 of them decode to that size with this ...
```

### `lol2_entity_field_analyzer.py`

147-byte entity records of every level, JSON report (`--out`).

```
$ python3 tools/lol2_entity_field_analyzer.py --check
CHECK entities: 128 147-byte entity records, 62 types, in 15 of 15 level archives; all tags printable ASCII: True
```

### `lol2_cross_level_witnesses.py`

Tables of the B_HUMAN and WORM records across levels.

```
$ python3 tools/lol2_cross_level_witnesses.py --check
CHECK witnesses: 29 records {'WORM': 4, 'B_HUMAN': 25} found in 12 of 12 level archives
```

### `lol2_l9dr_census.py`

Exploratory census of `L9_DR.MIX` as fixed 147-byte slots (superseded by the entity analyser).

```
$ python3 tools/lol2_l9dr_census.py --check
CHECK l9dr_census (exploratory): L9_DR.MIX read as 160622 slots of 147 bytes (+144 tail); 5861 slots end in a printable tag, 137325 distinct tag st...
```

### `lol2_analyze_disarm_rearm.py`

Analyse a DOSBox guest trace (`--trace`); traces are not included. `--check` is a self-test.

```
$ python3 tools/lol2_analyze_disarm_rearm.py --check
CHECK disarm_rearm: self-test on synthetic trace events passed (no game data needed)
```

### `lol2_guest_trace_summary.py`

Summarise a DOSBox guest trace as Markdown (`--trace`, `--out`). `--check` is a self-test.

```
$ python3 tools/lol2_guest_trace_summary.py --check
CHECK guest_trace_summary: self-test on a synthetic trace passed (no game data needed)
```

### `lol2_media_check.py`

Re-read the movie scene ids, one sound-bank row, the music stem hashes and the 47 room modules. Also matches the byte at data `0x223D6` selecting the leved or global resource names. Writes nothing. Pages: `docs/lol2-movie-scenes.md`, `docs/lol2-sound-cues.md`, `docs/lol2-music-selection.md`, `docs/lol2-room-archives.md`.

```
$ python3 tools/lol2_media_check.py --data /path/to/DAT --check
CHECK media: scene limit 85; L12 opcode 21/20/210 at 9823886/9821090/9823696; citadel L12_CMI entry 21; lolg MOVIES entry 2; bank 1179 row 1049 0190108e.aud; 32 table stems and CREDITS in both formats; 47 room modules contain 8469 relocations; 15 global texture books; 640 WSA deltas
```

### `lol2_text_tables.py`

Re-read the five named message tables. Writes nothing unless `--out` is set, and then only the check line. Page: `docs/lol2-text-tables.md`.

```
$ python3 tools/lol2_text_tables.py --data /path/to/DAT --check
CHECK text: help/opt/automap/credits in LOCALLNG, credits also MOVIES entry 28, loose ERRTEXT 39 / OPTTEXT 212 / CREDITS 44; TEXT and TCEL have no TRR entry
```

### `lol2_speech_names.py`

Re-read the spoken-line format, the category switch, two `MCEL.MIX` keys, the MCEL import of the category switch and the cue-table loader, and check all 404 original cue words. Also classifies every direct cue-pointer use as a player call, a cleanup call, a compare, or the shutdown store. Writes nothing unless `--out` is set, and then only the check line. Part of `check_all.py`. Page: `docs/lol2-speech.md`.

```
$ python3 tools/lol2_speech_names.py --data /path/to/DAT --check
CHECK speech: format at file 0x1C427A; switch at 0xF133C enters eight arms through slots at 0xF131C; cue id from table 0x269CC calls 0xE3924; the reader loads 404 footer words from the EFX bank; 533 direct cue-pointer uses: 499 player calls (14 after a jmp), 11 cleanup calls, 21 word compares, 1 null test, 1 shutdown store; .aud probe is the other branch; MCEL entries 5 and 7 are 44100 Hz codec 99 (17564 and 21668 bytes); MCEL import +0xFC reaches 0xF133C
```

### `lol2_save_native.py`

Re-reads native save selector, restore and clock instructions. Also checks
the bounds and enabled modes of the ODF surface presets and texture
animation rows behind save sections 26 and 27 in all 15 levels. Part of
`check_all.py`. [Native field witnesses](../docs/lol2-save-field-witnesses.md#surface-presets-and-texture-animations)

### `lol2_cache_seed.py`

Joins the 15 shipped `CDCACHE.LS_` rows to the level texture banks by name and compares the seed sizes with each bank's first dword; also reads `CACHEBAK.MIX`. Also reads the executable's version and date strings `DOS 1.30` / `Dec 03 1997 17:51:02`, sixteen bytes at file +0x100 (`bd 01 68 0c df 07 91 0f df 07 95 0f df 07 89 10`), the seed's 15 name strings, and the art and leved folder in each bank's first block. Part of `check_all.py`. Page: `docs/lol2-cache-initializer.md`.

### `example_images.py`

Regenerates each image the repository shows (`docs/images/`, `examples/`) with its listed command and compares pixels; part of `check_all.py`.

```
$ python3 tools/example_images.py --data /path/to/DAT --check
CHECK example_images: all 2 shown images match today's tool output pixel for pixel
```

### `lol2_item_labels.py`

Join the executable's 74 item labels (data `0xC610`) to the 91-byte item definitions by the native label hash, and print the replacement definitions read by handlers 2, 8, 83 and 91–93. Prints indexes only. Page: `docs/lol2-item-handlers.md#replacement-definitions`.

```
$ python3 tools/lol2_item_labels.py --data /path/to/DAT --check
CHECK item_labels: 74 of 74 executable item labels join a definition identity; handler: definitions -> replacement 2: 57 -> 58, 8: 55 -> 56, 83: 66 -> 67, 91: 100 -> 98, 92: 101 -> 98, 93: 99 -> 98
```

### `lol2_hmi_midi.py`

Walk the 33 `HMI-MIDISONG` entries in `LOCAL.MIX` and build a standard MIDI file in memory. `--out` writes one `.mid` per song outside the repository. `--check` writes nothing. Page: `docs/lol2-music-2026-11.md`.

```
$ python3 tools/lol2_hmi_midi.py --data /path/to/DAT --check
CHECK hmi: 33 songs, 438 tracks, all end on FF 2F 00; 80067 note-ons with a duration; 32 table stems and CREDITS; standard MIDI in memory, division 120
```

### `repo_guard.py`

Fails if a game file, media file or stray image is committed. Needs no game data.

```
$ python3 tools/repo_guard.py --check
CHECK repo_guard: N tracked files; game files, media, stray images, files over 300 KB, machine paths, words from the local list, or commit identities: none (0); private word list: not present, skipped
```

## Tool Index

### Container & Compression
- `lol2_mix_parser.py` — shared Westwood MIX container parser (imported by other tools, also usable standalone)
  - example: `python3 tools/lol2_mix_parser.py --help`
- `lol2_mix_writer.py` — writes a MIX archive from (key, offset, payload) rows; `--check` rebuilds the 81 `DAT/` archives and the 6 shipped game-folder archives in memory and compares them byte for byte (`CDCACHE.MIX` is skipped, the game writes it; [MIX writing](../docs/formats/mix.md#writing))
  - example: `python3 tools/lol2_mix_writer.py --check --data /path/to/LoL2/DAT`
- `lol2_decompress_westwood.py` — Westwood LZ77 decompressor. The function is at VA `0x158D58`. No size-prefixed MIX entry decodes with it; the buffers of its eleven callers are mapped and `options.shp` uses it, other source files are open ([Q1](../docs/OPEN_QUESTIONS.md))
  - example: `python3 tools/lol2_decompress_westwood.py --help`
- `lol2_decompress_sphere.py` — reads the `options.shp` interface shapes in `LOCAL.MIX` entry 1 ([shape format](../docs/formats/room-sections.md))
  - example: `python3 tools/lol2_decompress_sphere.py --help`

### Added 2026-10
- `lol2_sound_bank.py` — list or extract the named AUD sound bank in `LOCALLNG.MIX` (1008 clips)
- `lol2_media_check.py` — one `CHECK` line for the movie scene ids, a sound-bank row, the music stem hashes and 47 room modules, among other media checks. Writes nothing. `--data` is the DAT folder. Pages: `docs/lol2-movie-scenes.md`, `docs/lol2-sound-cues.md`, `docs/lol2-music-selection.md`, `docs/lol2-room-archives.md`.
- `lol2_texture_container.py` — level `.TE_` containers (LZO1X). Decodes the ten raw flags, including `0x80A9`. Its standalone `--check --data DAT` verifies 38,361 descriptors.
- `lol2_source_format.py` + `lol2_export_scripts.py` — export a level's header tables and command streams to JSON (stdlib only)
- `lol2_level_map.py` — top-down schematic map of a level from its region table (no game pixels)
  - example: `python3 tools/lol2_level_map.py --data DAT --level 1 --out l1_map.png`
- `lol2_level_report.py` — one Markdown sheet per level (entries, counts, opcode use, exits, entity records); writes `docs/levels/`. `--check` requires each sheet there to equal the tool's text
  - example: `python3 tools/lol2_level_report.py --data DAT --out levels/`
- `lol2_progression.py` — one row per level-transition command, with the predicate on the event that names its group. `--check` requires `docs/PROGRESSION.md` to equal that table. Part of `check_all.py`.
  - example: `python3 tools/lol2_progression.py --data DAT`
- `lol2_plot_branches.py` — one row per event that tests a shared plot byte and is not one of the 72 exits. `--check` requires the marked table in `docs/lol2-shared-predicates.md` to match. Part of `check_all.py`.
  - example: `python3 tools/lol2_plot_branches.py --data DAT`
- `lol2_vqa_v2_decode.py` — VQA v2 pointer-table decoder, including 4×2 blocks and `CIND`-scheduled codebooks (needs NumPy; Pillow for `--out`). `--check` is a chunk census and one sample of each layout. `--full` walks every movie. `VPRZ`/`VPTR` movies are checked only as far as the codebook. `--out` refuses a path inside the repository

### Container Utilities
- `lol2_westwood_hash.py` — Westwood MIX hash functions (TD/RA era and TS/RA2 era)
  - example: `python3 tools/lol2_westwood_hash.py --help`

### Executable Analysis
- `lol2_parse_le.py` — DOS4GW LE (Linear Executable) header and page report for LOLG.DAT. `--out` requests explicit segment extraction.
  - example: `python3 tools/lol2_parse_le.py --help`

### Entity & Trace Analysis
- `lol2_l9dr_census.py` — L9_DR.MIX full static census (147-byte records, per-tag field invariants)
  - example: `python3 tools/lol2_l9dr_census.py --help`
- `lol2_guest_trace_summary.py` — summarize DOSBox guest-trace JSONL output into markdown
  - example: `python3 tools/lol2_guest_trace_summary.py --help`
- `lol2_analyze_disarm_rearm.py` — analyze post-A00F consumer traces (produced the 36-site, 25-offset consumer map)
  - example: `python3 tools/lol2_analyze_disarm_rearm.py --help`
- `lol2_cross_level_witnesses.py` — extract entity records across all 12 level MIX files
  - example: `python3 tools/lol2_cross_level_witnesses.py --help`

### Audio Extraction
- `lol2_aud_decode.py` — Westwood AUD → WAV decoder (IMA-ADPCM codec 99). Decodes DMUSIC.MIX music and LOCALLNG.MIX dialogue.
  - example: `python3 tools/lol2_aud_decode.py --help`

### Semantic Analysis
- `lol2_entity_field_analyzer.py` — cross-level entity descriptor field analysis (62 types, 15 levels)
  - example: `python3 tools/lol2_entity_field_analyzer.py --help`


## Shared support and additional readers

- [`cli_errors.py`](cli_errors.py) — Shared diagnostics and input path checks
- [`lol2_cli.py`](lol2_cli.py) — Shared rules for paths and explicit outputs
- [`lol2_numbers.py`](lol2_numbers.py) — Generates and compares the item, spell, creature and form tables
- [`rating.py`](rating.py) — Recomputes the counted README and status summaries

## Command-line conventions

Set `LOL2_DAT` or pass `--data` for the original game's DAT directory. Run `--help` for the tool's inputs and modes. Use `--check` for the available read-only validation and `--out` to write a result to a path you choose. Read-only listings print to stdout. `check_all.py` runs the whole suite by default. `doc_links.py` and `repo_guard.py` use repository files and need no game data.

| Difference | Why it remains |
|---|---|
| `LOL2_DAT`, where LoL1 uses `LOL1_DATA` and LoL3 uses `LOL3_DAT` | Each name follows the game's own folder: LoL1 keeps its files in `DATA`, LoL2 and LoL3 in `DAT`. Shells and scripts already set these names. |
| A positional archive, executable, save or clip | File tools can inspect one input without a full install. `lol2_parse_le.py` also accepts `LOL2_EXE` for a named program copy. |
| `--mix` under a texture subcommand | The unpacked bank is selected from one archive. The top-level `--check` scans the whole DAT folder. |
| `--trace` and `--baseline` | The input is a previously recorded trace or a specific game-written level baseline. |
| `--summary` for script notes | Summaries contain the checked-in excerpts. `--out` selects the full external listings. |
| `lol2_aud_decode.py` without `--out` | It prints the AUD header and writes nothing. Before, it wrote `<archive>_entry<N>.wav` into the current folder. A WAV is now written only to an explicit `--out` path, like every other tool. |
| Older output flags and positional arguments | Old spellings are kept as aliases and shown in `--help`. `lol2_aud_decode.py --output`, `lol2_sound_bank.py --extract`, the image check's `--out-dir` and legacy exporter positional paths still work. The [historical helpers](history/README.md) retain their original switches, including the cave pipeline's `--game-root` for pinned inputs. |

## Documentation index

`doc_index.py` reads the repository's Markdown pages and generates [docs/index.json](../docs/index.json).
Its `pages` records include the title, original path, question IDs and cited tool source paths.
`answers` uses the Page or Where column of [Open questions](../docs/OPEN_QUESTIONS.md).
`question_references` records other references to the same IDs. The top-level `questions`
object preserves the published state and lists each question's answer pages. Tool citations
include command examples. The index covers the Markdown files shipped in the repository,
including the root pages, example and evidence notes, and issue templates. In a git checkout
it reads only tracked pages, so local untracked notes do not change the check.

```bash
python3 tools/doc_index.py --out docs/index.json
python3 tools/doc_index.py --check
```

The check also runs in `check_all.py` and GitHub Actions. It needs no game data.
