# Tools

Curated analysis and extraction tools for LoL2 reverse engineering.

## Draracle Caverns geometry checks

See [Draracle findings](../docs/draracle-restoration.md). Run
`python3 tools/draracle/run_geometry_pipeline.py --game-root /path/to/lol2 --out /path/to/output`.
This requires Python 3.10+ and Capstone 5, and produces corrected geometry and
wall-record evidence from pinned original files.

## Setup

- Python 3.10+
- `pip install -r requirements.txt`: Pillow (picture output), capstone (disassembly checks), numpy (movie decoder)
- Optional: the system LZO library (`apt install liblzo2-2`) for `lol2_texture_container.py`
- Set `LOL2_DAT` to your LoL2 `DAT/` directory path, or pass `--data`
- Older tools may use `OUTPUT_DIR` / `LOL2_OUT`; never point them inside this repository

## Common options (2026-11-18)

The tools below follow one set of rules: `--help` changes nothing; the game's `DAT` folder comes from `--data` or `$LOL2_DAT` (no built-in path); nothing is written unless you pass `--out` (or `--png`); `--check` prints one `CHECK` line and exits 0 when it passes. `check_all.py` runs them all. Run examples outside the repository; `.gitignore` and `repo_guard.py` keep game files and media out of it.


### `check_all.py`

Run every `--check` (20) and print one line each, then a summary.

```
$ python3 tools/check_all.py | sed -n "1,2p;21p"
CHECK repo_guard: N tracked files; game files, media, stray images, files over 300 KB, machine paths, words from the local list, or commit identities: none (0); private word list: not present, skipped
CHECK mix: 81 MIX files, 2905 entries; this reader and lol2_source_format.parse_mix agree and every entry lies inside its file: 81/81; index sorted by signed key: 81/81 (by unsigned key: 20); bad=none
ALL 20 CHECKS PASSED
```

### `lol2_save_header.py`

Reads one save slot you name (a player save, not a game file) and prints its preview, global and level offsets as JSON. Writes nothing. It has no `--check`, so it is not one of the `check_all.py` checks.

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

### `lol2_westwood_hash.py`

Hash entry names as the archives key them. `--check`: the documented names are keys.

```
$ python3 tools/lol2_westwood_hash.py 'SPHERE1\L1_DC\L1_DC.TE_'
SPHERE1\L1_DC\L1_DC.TE_: v1 0xB12F2907 (2972657927)  v2 0xB12F2907  ts 0xA680308A  crc 0x330D9D80
```

### `lol2_decompress_sphere.py`

Room layouts in `LOCAL.MIX` entry 1 (LCW sections); a section as text or PNG of tile numbers.

```
$ python3 tools/lol2_decompress_sphere.py | head -3
Section  0: 128x128 flags=0x0000 raw=16382 bytes
Section  1:   5x32  flags=0x5A5A placed=160 void=  0
Section  2:  32x5   flags=0x8000 placed=160 void=  0
```

### `lol2_decompress_westwood.py`

Westwood LZ77. The function is at VA `0x158D58`; `--out` required. Which buffer each call decompresses is open (Q1).

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

Re-read the movie scene ids, one sound-bank row, the music stem hashes and the 46 room-archive code entries. Writes nothing. Pages: `docs/lol2-movie-scenes.md`, `docs/lol2-sound-cues.md`, `docs/lol2-music-selection.md`, `docs/lol2-room-archives.md`.

```
$ python3 tools/lol2_media_check.py --data /path/to/DAT --check
CHECK media: scene limit 85; L12 opcode 21/20/210 at 9823886/9821090/9823696; citadel L12_CMI entry 21; lolg MOVIES entry 2; bank 1179 row 1049 0190108e.aud; 32 AUD in DMUSIC and 32 HMI in LOCAL; DMUSIC entry 16 unmatched; 46/46 room archives carry the code banner
```

### `lol2_text_tables.py`

Re-read the five named message tables. Writes nothing unless `--out` is set, and then only the check line. Page: `docs/lol2-text-tables.md`.

```
$ python3 tools/lol2_text_tables.py --data /path/to/DAT --check
CHECK text: help/opt/automap/credits in LOCALLNG, credits also MOVIES entry 28, loose ERRTEXT 39 / OPTTEXT 212 / CREDITS 44; TEXT and TCEL have no TRR entry
```

### `lol2_speech_names.py`

Re-read the spoken-line format, the category switch, and two `MCEL.MIX` keys. Writes nothing unless `--out` is set, and then only the check line. Not one of the 20 `check_all.py` checks. Page: `docs/lol2-speech.md`.

```
$ python3 tools/lol2_speech_names.py --data /path/to/DAT --check
CHECK speech: format at file 0x1C427A; switch at 0xF133C enters eight arms through slots at 0xF131C; cue id from table 0x269CC calls 0xE3924; .aud probe is the other branch; MCEL entries 5 and 7 are 44100 Hz codec 99 (17564 and 21668 bytes)
```

### `lol2_hmi_midi.py`

Walk the 33 `HMI-MIDISONG` entries in `LOCAL.MIX` and build a standard MIDI file in memory. `--out` writes one `.mid` per song outside the repository. `--check` writes nothing. Page: `docs/lol2-music-2026-11.md`.

```
$ python3 tools/lol2_hmi_midi.py --data /path/to/DAT --check
CHECK hmi: 33 songs, 438 tracks, all end on FF 2F 00; 80067 note-ons with a duration; 32 named, 1 unnamed; standard MIDI in memory, division 120
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
- `lol2_decompress_westwood.py` — Westwood LZ77 decompressor. The function is at VA `0x158D58`. No size-prefixed MIX entry decodes with it; which buffer each call reads is open ([Q1](../docs/OPEN_QUESTIONS.md))
  - example: `python3 tools/lol2_decompress_westwood.py --help`
- `lol2_decompress_sphere.py` — LCW variant with chained room-group decoding, for the `LOCAL.MIX` entry 1 room sections ([room sections](../docs/formats/room-sections.md))
  - example: `python3 tools/lol2_decompress_sphere.py --help`

### Added 2026-10
- `lol2_sound_bank.py` — list or extract the named AUD sound bank in `LOCALLNG.MIX` (1008 clips)
- `lol2_media_check.py` — one `CHECK` line for the movie scene ids, one sound-bank row, the music stem hashes and the 46 room-archive code entries. Writes nothing. `--data` is the DAT folder. Pages: `docs/lol2-movie-scenes.md`, `docs/lol2-sound-cues.md`, `docs/lol2-music-selection.md`, `docs/lol2-room-archives.md`.
- `lol2_texture_container.py` — level `.TE_` containers (LZO1X; needs system liblzo2). Decodes the ten raw flags, including `0x80A9`. `--check --data DAT` pins 38,361 descriptors; it is not one of the 20 `check_all.py` checks, because it needs liblzo2
- `lol2_source_format.py` + `lol2_export_scripts.py` — export a level's header tables and command streams to JSON (stdlib only)
- `lol2_level_map.py` — top-down schematic map of a level from its region table (no game pixels)
  - example: `python3 tools/lol2_level_map.py --data DAT --level 1 --out l1_map.png`
- `lol2_level_report.py` — one Markdown sheet per level (entries, counts, opcode use, exits, entity records); writes `docs/levels/`
  - example: `python3 tools/lol2_level_report.py --data DAT --out levels/`
- `lol2_vqa_v2_decode.py` — VQA v2 pointer-table decoder, including 4×2 blocks and `CIND`-scheduled codebooks (needs NumPy; Pillow for `--out`). `--check` is a chunk census and one sample of each layout. `--full` walks every movie. `VPRZ`/`VPTR` movies are checked only as far as the codebook. `--out` refuses a path inside the repository

### Container Utilities
- `lol2_westwood_hash.py` — Westwood MIX hash functions (TD/RA era and TS/RA2 era)
  - example: `python3 tools/lol2_westwood_hash.py --help`

### Executable Analysis
- `lol2_parse_le.py` — DOS4GW LE (Linear Executable) parser for LOLG.DAT
  - example: `python3 tools/lol2_parse_le.py --help`
- `lol2_extract_segments.py` — extract code/data segments from LOLG.DAT for Ghidra
  - example: `python3 tools/lol2_extract_segments.py --help`

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

### Texture Extraction
- `lol2_wall_texture_extract.py` — SUPERSEDED: an early reading of `LOCAL.MIX` entry 1 as a wall texture atlas. The entry holds room tile grids ([room sections](../docs/formats/room-sections.md)); kept only for its recorded examples
  - example: `python3 tools/lol2_wall_texture_extract.py --help`

### Asset Extraction
- `lol2_vqa_decode.py` — VQA (Vector Quantization Animation) video/audio chunk parser
  - example: `python3 tools/lol2_vqa_decode.py --help`
- `lol2_lcw.py` — Westwood LCW (format 80) decompressor, a library for `lol2_verify_wall_atlas_candidate.py`
- `lol2_geometry_cracker.py` — level geometry parser and 2D map visualizer (requires Pillow)
  - example: `python3 tools/lol2_geometry_cracker.py --help`
- `lol2_wall_mesh.py` — 3D OBJ wall mesh generator from decoded face records
  - example: `python3 tools/lol2_wall_mesh.py --help`

### Semantic Analysis
- `lol2_entity_field_analyzer.py` — cross-level entity descriptor field analysis (62 types, 15 levels)
  - example: `python3 tools/lol2_entity_field_analyzer.py --help`

