# LoL2 Audio & Music Inventory

Date: 2026-03-23

## Overview

LoL2 uses multiple audio systems: Westwood AUD for digital audio, HMI-MIDI for music sequencing, FORM/IFF for instrument data, AdLib/OPL3 for synthesis, and VQA for video audio.

## Standalone Files

| File | Size | Format | Purpose |
|------|------|--------|---------|
| `DAT/AUTOPLAY.WAV` | 145 KB | RIFF WAVE, 16-bit mono 22050 Hz | Autoplay/intro audio |
| `DRUM.BNK` | 5.3 KB | AdLib percussion instrument bank | OPL3 percussion |
| `MELODIC.BNK` | 5.3 KB | AdLib melodic instrument bank | OPL3 melodies |
| `TEST1.HMI` | 4.1 KB | HMI MIDI | Test/debug music |

## DMUSIC.MIX — Music (78 MB, 33 entries)

All 33 entries are **confirmed Westwood AUD format**. Decode has been sample-verified on 1 track; a bulk-decoding tool exists for all 33 but bulk output has not been run and verified:
- Header: `u16 freq, u32 comp_size, u32 output_size, u8 flags, u8 codec`
- Codec: 99 (standard IMA-ADPCM), NOT the previously reported types 30/254 (those were misread from wrong header offsets)
- Actual header is 12 bytes, not 8: the extra u32 output_size field shifts the type/flags bytes
- Chunk format: 8-byte headers (`u16 chunk_comp, u16 chunk_decomp, u32 magic=0x0000DEAF`)
- 32 tracks at 22050 Hz mono, 1 track (entry 10) at 44100 Hz mono
- Total decoded duration: **~116 minutes** of music across 33 tracks
- Decoder: `tools/lol2_aud_decode.py`

## LOCAL.MIX — Music & Data (27 MB, 104 entries)

| Format | Count | Purpose |
|--------|-------|---------|
| HMI-MIDI | 33 | MIDI music scores (for AdLib/SB playback) |
| FORM/IFF | 33 | Instrument/sample data for MIDI playback |
| Other data | 38 | Sprite data, palette data, lookup tables (Entry 50 = 335 sprites, Entry 94 = VGA palette) |

HMI-MIDI files are Westwood's MIDI variant used with Human Machine Interfaces audio drivers. Each HMI-MIDI file pairs with a FORM/IFF instrument bank.

## LOCALLNG.MIX — Dialogue (28 MB, 6 entries)

| Entry | Size | Format | Content |
|-------|------|--------|---------|
| 0 | 4.4 KB | Index table | 268 sequential u32 values (dialogue clip index) |
| 1 | 4.3 KB | Index table | 202 sequential u32 values (secondary index) |
| 2 | 3.4 MB | FORM/IFF | Instrument/sample bank |
| 3 | 3.9 KB | Index table | 41 sequential u32 values (tertiary index) |
| 4 | 25.0 MB | Dialogue blob | 612-byte header (dev path `F:\PROJECTS\LOL_2\LEVED\GLOBAL\AUD`), then **1008 concatenated Westwood AUD streams** |
| 5 | 6.0 KB | Index table | 43 sequential u32 values (quaternary index) |

The 25 MB dialogue blob contains 1008 concatenated Westwood AUD clips (same codec 99 IMA-ADPCM as DMUSIC.MIX). The index entries in entries 0, 1, 3, 5 map dialogue IDs to clip positions within the blob. First clip successfully decoded: 1.24 seconds, 22050 Hz mono.

## VQA Video Audio (DAT/MOVIES.MIX, 179 MB)

VQA files contain embedded SND0/SND1/SND2 audio chunks. A VQA decoder exists (`lol2_vqa_decode.py`) that identifies these chunks. Audio is typically 22050 Hz 16-bit PCM.

## Audio Subsystems Summary

| Subsystem | Source | Format | Decoder status |
|-----------|--------|--------|---------------|
| Soundtrack | DMUSIC.MIX | Westwood AUD (22050 Hz, IMA-ADPCM codec 99) | **1 track verified** — tool exists for all 33 tracks (~116 min est.) |
| MIDI Music | LOCAL.MIX | HMI-MIDI + FORM/IFF instruments | Identified, HMI-MIDI parser needed |
| Dialogue | LOCALLNG.MIX | 1008 concatenated Westwood AUD clips | **1 clip verified** (1.24s) — tool exists for all 1008 clips |
| Sound Effects | Likely in LOCAL.MIX or level MIX files | Unknown | TBD |
| Video Audio | MOVIES.MIX | VQA SND chunks (PCM) | VQA chunk parser exists |
| AdLib Music | DRUM.BNK + MELODIC.BNK + HMI files | OPL3 instrument banks | BNK parser needed |

## Extraction Status

- **Verified**: 1 music track decoded and verified from DMUSIC.MIX; 1 dialogue clip decoded and verified from LOCALLNG.MIX. Tool exists (`tools/lol2_aud_decode.py`) for bulk extraction of all 33 music tracks and 1008 dialogue clips, but bulk extraction has not been run and verified.
- **Tooling published**: `tools/lol2_aud_decode.py` (Westwood AUD → WAV), `tools/lol2_mix_parser.py`, `tools/lol2_vqa_decode.py`
- **Still needed**: HMI-MIDI to standard MIDI converter, AdLib BNK parser, sound effect location confirmation

## Open Items

- **Music extraction**: sample-verified — 1 track decodes to WAV via `tools/lol2_aud_decode.py`. Previous "type 30/254" claims were caused by misreading the 12-byte header as 8 bytes; actual codec is standard 99 (IMA-ADPCM). Bulk extraction of all 33 tracks has not yet been run and verified.
- **Dialogue extraction**: Entry 4 contains 1008 concatenated AUD clips. First clip decoded successfully (1.24s). Full extraction still requires parsing the index tables (entries 0, 1, 3, 5) to map dialogue IDs to clip offsets, even though the index structure now looks straightforward.
- **Sound effects**: container and format not yet confirmed. Likely embedded in LOCAL.MIX or individual level MIX files as Westwood AUD entries.
- **HMI-MIDI**: 33 MIDI music scores in LOCAL.MIX need a HMI-to-standard-MIDI converter for modern playback.
- **AdLib banks**: DRUM.BNK and MELODIC.BNK instrument definitions not yet parsed.
