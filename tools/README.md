# Tools

Curated analysis and extraction tools for LoL2 reverse engineering.

## Setup

- Python 3.8+
- Pillow (`pip install Pillow`) — required only for visual output tools (sprite decode, geometry cracker, wall mesh)
- Set `LOL2_DAT` to your LoL2 `DAT/` directory path
- Set `OUTPUT_DIR` or `LOL2_OUT` for extracted output (defaults to current directory)

## Tool Index

### Container & Compression
- `lol2_mix_parser.py` — shared Westwood MIX container parser (imported by other tools, also usable standalone)
- `lol2_decompress_westwood.py` — Westwood LZ77 decompressor (proven from LOLG.DAT disassembly)
- `lol2_decompress_sphere.py` — Sphere engine LZ77 with chained room-group decoding (for LOCAL.MIX room sub-sections)

### Container Utilities
- `lol2_westwood_hash.py` — Westwood MIX hash functions (TD/RA era and TS/RA2 era)

### Executable Analysis
- `lol2_parse_le.py` — DOS4GW LE (Linear Executable) parser for LOLG.DAT
- `lol2_extract_segments.py` — extract code/data segments from LOLG.DAT for Ghidra

### Entity & Trace Analysis
- `lol2_l9dr_census.py` — L9_DR.MIX full static census (147-byte records, per-tag field invariants)
- `lol2_guest_trace_summary.py` — summarize DOSBox guest-trace JSONL output into markdown
- `lol2_analyze_disarm_rearm.py` — analyze post-A00F consumer traces (produced the 36-site, 25-offset consumer map)
- `lol2_cross_level_witnesses.py` — extract entity records across all 12 level MIX files

### Asset Extraction
- `lol2_vqa_decode.py` — VQA (Vector Quantization Animation) video/audio chunk parser
- `lol2_sprite_decode.py` — Westwood 0x2256 Cell sprite decoder (8bpp/4bpp, requires Pillow)
- `lol2_geometry_cracker.py` — level geometry parser and 2D map visualizer (requires Pillow)
- `lol2_wall_mesh.py` — 3D OBJ wall mesh generator from decoded face records

### Trace Configuration
- `run_lol2_l9_watch.sh` — baked wrapper for L9_DR.MIX watch configuration
