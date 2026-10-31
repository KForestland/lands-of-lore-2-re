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

## LOCALLNG.MIX — Named AUD Sound Bank (28 MB, 6 entries)

Updated 2026-10-31. Earlier versions of this note called entry 4 "1008
concatenated AUD dialogue clips". The entry is in fact an indexed, named bank.

| Entry | Key | Size | Content |
|-------|-----|------|---------|
| 0 | 2588158451 | 4.4 KB | Small table (not re-checked here) |
| 1 | 2924233755 | 4.3 KB | Small table (not re-checked here) |
| 2 | 4238663987 | 3.4 MB | FORM/IFF data (not re-checked here) |
| 3 | 1010037751 | 3.9 KB | Small table (not re-checked here) |
| 4 | 1570429112 | 25.0 MB | **Named AUD bank, 1179 rows** |
| 5 | 1846428659 | 6.0 KB | Small table (not re-checked here) |

### Bank layout (PROVEN)

| Offset | Type | Meaning |
|--------|------|---------|
| `+0x000` | string | Dev path `F:\PROJECTS\LOL_2\LEVED\GLOBAL\AUD`, zero padded |
| `+0x258` | u32 | Row count: `1179` |
| `+0x25C` | u32 | Row-table offset in the bank: `24938684` |
| table | 60-byte rows | `u32 offset`, `u32 size`, `u32` unknown, `u32` placeholder flag, name (NUL-terminated, from `+16`) |

- Clips start at `+0x264` (612) and are packed back to back in row order; the row table follows the last clip.
- `1008` rows hold complete Westwood AUD files. All `1008` are 22050 Hz, mono, 16-bit (flags `2`), codec `99` (IMA-ADPCM), and every clip is a clean walk of `0xDEAF` chunks whose length equals header size + 12.
- `171` rows have size `1` and placeholder flag `1`. Their names also appear as sound names (for example `bird1.aud`, `arrow4.aud`); what the engine does with them is OPEN.
- Names are file names such as `zombie1.aud`, `dripcav5.aud`, `hitdoor1.aud`, `drgbrth1.aud`. `432` of the `1179` names are 8 hex digits (for example `0186304e.aud`); these are LIKELY speech or numbered cues, not traced.
- `808` bytes after the row table are not interpreted.
- The old "1008 clips" count was the number of real clips; the "first clip 1.24 s" is row 0, `zombie1.aud`.

Evidence: the game-side creature-audio staging tool used by the Godot port
selects this entry by key, asserts `count == 1179` and the table offset,
reads rows as above, and checks rate, codec, flags and the `0xDEAF` chunk
walk for every clip it stages. `tools/lol2_sound_bank.py` re-runs the same
checks over all rows; run against a GOG install it reports `1179` rows,
`1008` clips, `171` placeholders, all `22050 Hz codec 99 mono 16-bit`.
Row 0 decodes with `tools/lol2_aud_decode.py --raw` to the same PCM length
as ffmpeg (54664 bytes).

So the named LoL2 sound effects live here, in one bank. Whether level MIX
files carry further sound data was not checked. Which game event plays which row is only traced for the
cues the Godot port has staged; a full cue map is OPEN.

```bash
python3 tools/lol2_sound_bank.py ./lol2_game/LOCALLNG.MIX            # list
python3 tools/lol2_sound_bank.py ./lol2_game/LOCALLNG.MIX --extract OUT --index 0
python3 tools/lol2_aud_decode.py --raw OUT/0000_zombie1.aud -o zombie1.wav
```

## VQA Video Audio (DAT/MOVIES.MIX, 179 MB)

VQA files contain embedded SND0/SND1/SND2 audio chunks. A VQA decoder exists (`lol2_vqa_decode.py`) that identifies these chunks. Audio is typically 22050 Hz 16-bit PCM.

## Audio Subsystems Summary

| Subsystem | Source | Format | Decoder status |
|-----------|--------|--------|---------------|
| Soundtrack | DMUSIC.MIX | Westwood AUD (22050 Hz, IMA-ADPCM codec 99) | **1 track verified** — tool exists for all 33 tracks (~116 min est.) |
| MIDI Music | LOCAL.MIX | HMI-MIDI + FORM/IFF instruments | Identified, HMI-MIDI parser needed |
| Sound effects / voice bank | LOCALLNG.MIX entry 4 (key 1570429112) | Named bank: 1179 rows, 1008 AUD clips (22050 Hz mono, codec 99) + 171 placeholders | **Layout proven**; all 1008 clips pass header/chunk checks (`tools/lol2_sound_bank.py`) |
| Video Audio | MOVIES.MIX | VQA SND chunks (PCM) | VQA chunk parser exists |
| AdLib Music | DRUM.BNK + MELODIC.BNK + HMI files | OPL3 instrument banks | BNK parser needed |

## Extraction Status

- **Verified**: 1 music track decoded and verified from DMUSIC.MIX; the LOCALLNG.MIX sound bank layout is proven and all 1008 clips pass header and chunk checks. Bulk extraction of the 33 music tracks has not been run and verified.
- **Tooling published**: `tools/lol2_aud_decode.py` (Westwood AUD → WAV), `tools/lol2_sound_bank.py` (LOCALLNG.MIX bank list/extract), `tools/lol2_mix_parser.py`, `tools/lol2_vqa_decode.py`
- **Still needed**: HMI-MIDI to standard MIDI converter, AdLib BNK parser, a full cue-to-row map for the sound bank

## Open Items

- **Music extraction**: sample-verified — 1 track decodes to WAV via `tools/lol2_aud_decode.py`. Previous "type 30/254" claims were caused by misreading the 12-byte header as 8 bytes; actual codec is standard 99 (IMA-ADPCM). Bulk extraction of all 33 tracks has not yet been run and verified.
- **Sound bank**: layout and clip format proven (see above). Open: the meaning of the 171 size-1 placeholder rows, the unknown row dword at `+8`, the 808-byte trailer, whether the hex-named rows are speech, and what entries 0, 1, 3, 5 index.
- **HMI-MIDI**: 33 MIDI music scores in LOCAL.MIX need a HMI-to-standard-MIDI converter for modern playback.
- **AdLib banks**: DRUM.BNK and MELODIC.BNK instrument definitions not yet parsed.
