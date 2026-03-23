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

All 33 entries are **consistent with Westwood AUD format** at 22050 Hz (header structure matches, not yet confirmed by successful decode):
- Header: `u16 freq=22050, u32 data_size, u8 type, u8 flags`
- Compression types observed: type 30 and type 254 (Westwood IMA ADPCM variants)
- Entry sizes: 1.5–3.8 MB each (2–5 minutes of audio per track)
- Total decompressed estimate: ~40 minutes of music

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
| 0 | 4.4 KB | Index/header | — |
| 1 | 4.3 KB | Index/header | — |
| 2 | 3.4 MB | FORM/IFF | Instrument/sample bank |
| 3 | 3.9 KB | Index/header | — |
| 4 | 25.0 MB | Dialogue blob | Development path: `F:\PROJECTS\LOL_2\LEVED\GLOBAL\AUD` — main dialogue audio data |
| 5 | 6.0 KB | Index/header | — |

The 25 MB dialogue blob starts with a Westwood development filesystem path, followed by audio data. This contains all in-game voice dialogue.

## VQA Video Audio (DAT/MOVIES.MIX, 179 MB)

VQA files contain embedded SND0/SND1/SND2 audio chunks. A VQA decoder exists (`lol2_vqa_decode.py`) that identifies these chunks. Audio is typically 22050 Hz 16-bit PCM.

## Audio Subsystems Summary

| Subsystem | Source | Format | Decoder needed |
|-----------|--------|--------|---------------|
| Soundtrack | DMUSIC.MIX | Westwood AUD (22050 Hz, IMA ADPCM) | AUD decompressor (Westwood codec) |
| MIDI Music | LOCAL.MIX | HMI-MIDI + FORM/IFF instruments | HMI-MIDI parser + IFF sample loader |
| Dialogue | LOCALLNG.MIX | Dialogue blob with dev path header | Blob sub-entry parser (offset table at header entries) |
| Sound Effects | Likely in LOCAL.MIX or level MIX files | Unknown | TBD |
| Video Audio | MOVIES.MIX | VQA SND chunks (PCM) | VQA decoder (partially exists) |
| AdLib Music | DRUM.BNK + MELODIC.BNK + HMI files | OPL3 instrument banks | BNK parser + HMI sequencer |

## Extraction Status

- **Identified**: All major audio containers enumerated with format analysis
- **Not yet extracted**: Individual audio tracks from DMUSIC.MIX, dialogue clips from LOCALLNG.MIX
- **Tooling exists**: MIX parser, VQA chunk identifier
- **Tooling needed**: Westwood AUD decompressor, HMI-MIDI to standard MIDI converter, dialogue blob sub-entry parser
