# LoL2 music: DMUSIC.MIX is decodable (November 2026)

Offsets are from the GOG release (`LOLG.DAT` sha256 `b27a3534…5766775`; `DMUSIC.MIX` size 81,208,196). No audio is
included here; convert the music from your own copy.

## Verdict

`DMUSIC.MIX` is a Westwood MIX holding **33 Westwood AUD tracks, codec 99 (IMA ADPCM)**. All 33 decode to PCM with the same
low-nibble-first IMA decoder already used for LoL2 speech (predictor and step index start at 0 and carry across chunks).

| Fact | Grade |
| --- | --- |
| MIX header: `u16` count 33, `u32` data size, then 33 x (`u32` id, `u32` offset, `u32` size); body at file offset 402; sizes cover the body with no gap or overlap | proven |
| Every entry: 12-byte AUD header (`u16` rate, `u32` compressed size, `u32` output size, `u8` flags 0x02, `u8` codec 99); chunks `u16` size, `u16` decompressed size, `u32` id `0x0000DEAF` | proven |
| 32 tracks at 22050 Hz, one at 44100 Hz; lengths about 1.5 to 6 minutes | proven |
| The executable builds the track name from `MUSIC\%s.AUD` or `MUSIC\%s.HMI` with a table of 34 stems; script opcode 210 (arms 0/1) selects the stem by index | proven |
| One global byte picks digital (AUD) or MIDI (HMI) for the whole game; the GOG install is set to digital | proven |
| `MELODIC.BNK` / `DRUM.BNK` are AdLib FM banks for the HMI MIDI path; the MIDI scores are the 33 `HMI-MIDISONG` entries in `LOCAL.MIX` | banks proven, scores proven below |
| The GOG copy has no CD audio tracks | proven for this copy; retail discs likely the same |
| Which MIX entry belongs to which stem | closed in [the selection note](lol2-music-selection.md): both hashes of `MUSIC\stem.AUD` hit 32 of the 33 entries |

## HMI-MIDISONG scores

`LOCAL.MIX` holds 33 entries that start with the 18 bytes `HMI-MIDISONG061595`. The same bytes are at `LOLG.DAT` file `0x1C5D90` (object-5 cell `0x4D6C`). VA `0x16A8C9` compares the loaded buffer with that string and stores error `0x0E` when it does not match.

32 of the 33 keys are `ww_hash_v1` of `MUSIC\<stem>.HMI` for the 32 real stems in the table at file `0x1CE10C` ([the selection note](lol2-music-selection.md)). The remaining key is `0x1305A4F0`. That table has no name for it.

`tools/lol2_hmi_midi.py --check` re-reads the songs, walks every track to its end marker, and builds a standard MIDI file in memory. It writes nothing.

### Song

CONFIRMED except where a row says otherwise.

| Offset | Bytes | Meaning |
| --- | --- | --- |
| `0x00` | 18 | the magic above, then a NUL |
| `0x21` | 1 | `0` in all 33 songs. Bit `0x40` clear means the dwords the loader fixes are file-relative. It adds the song base to the dwords at `0x22`, `0xF4`, `0xD6`, `0xDA` and `0xE8` |
| `0xA6` | 32 | zero in all 33 songs. `0x166500` is a memory copy (`rep movsd/movsb`): the call at `0x16A94A` copies 32 bytes from the caller's argument at `[ebp+0x14]` into song +0xA6, so the block is filled at load time and is zero in the file |
| `0xD2`, `0xD4` | u16 | `120` in all 33 songs. The event player that was read does not load them |
| `0xE4` | u16 | track count. The high half of the dword is 0, and the loader sign-extends the word. This copy has 438 tracks |
| `0xE8` | u32 | file-relative offset of the track table. Each u32 points at the bytes `HMI-MIDITRACK` |

### Track and events

CONFIRMED. A track starts with `HMI-MIDITRACK`. Byte `+0x21` is 0 in all 438 tracks, so the dword at `+0x57` is relative to the track. VA `0x17A12D` adds the track base, stores the sum at `+0x5B` (the event cursor), then reads one MIDI variable-length quantity into the delay at `+0x53` (VA `0x17B641` shifts in 7-bit groups until the high bit is clear).

Byte `+0x7B` is the channel, 0 through 15, and the next byte is 0. The player sends that channel. Of the 110,287 events, 6,172 store their own status byte (the rest reuse the previous one); 1,215 of the events have a status low nibble different from this channel.

The loop at VA `0x16B04E` reads the cursor. A byte of `0x80` or higher is a new status and is saved at track `+0x42`. A lower byte reuses the saved status. VA `0x17A6B1` consumes the event:

| High nibble | What the player takes | What happens next |
| --- | --- | --- |
| `0x90` | status if it was present, note, velocity, then a variable-length duration | returns 1. The caller reads the next delay. The duration is not that delay. The player stores it and later sends a note-on with velocity 0 (VA `0x17A832`) |
| `0xB0`, `0xA0`, `0xE0` | status if present, plus two data bytes | returns 1, then a delay |
| `0xC0`, `0xD0` | status if present, plus one data byte | returns 1, then a delay. This copy has program changes and no channel-pressure events |
| `0xFF` then `0x2F 0x00` | end of track | returns 0. The caller does not read another delay |

This copy has no stored note-off. The counts are 80,067 note-ons, 22,243 controllers, 6,188 pitch bends, 1,289 polyphonic-pressure events and 500 program changes.

405 tracks end on `FF 2F 00` at the next track. The other 33, one in each song, have the same 16 bytes after that marker: `*`, the four characters `.mid`, a NUL, then zeros. The end-of-track handler does not read them.

### Worked example

The shortest song is `LOCAL.MIX` key `0xD9023FF9`, 5,442 bytes, 6 tracks. Track 0 uses channel 0. Its event pointer is track `+0xBA`. The first delay is 0, so three events share tick 0: controller `0x69` value 1, controller 7 value `0x7F`, controller `0x77` value 1.

### Standard MIDI

The tool writes a format-1 file per song. The division is 120, the value of the two header words. It writes no tempo event, so a standard player uses 120 beats per minute. Whether the game's timer uses that rate was not traced. Controller numbers `0x67`–`0x6C` and `0x77` are handled by the player itself (switch at `0x17AD68`; for example `0x69` calls `0x17B6D5` or `0x17BB0D`, and `0x77` calls a callback at song +0x12A). In this copy that is 11,340 events (`0x77` ×10,464, `0x69` ×876). The converter copies them unchanged as ordinary controllers 119 and 105, so any loop or branch behaviour they carry is not reproduced. Each note-on becomes a note-on plus a note-off (status `0x80`, velocity 0) that many ticks later. The channel is the track byte. `--out` writes the files outside the repository; `--check` does not.

## What is still open

- What the scaled words stored by opcode 210 arms 4 to 9 change in playback. The stores themselves are in [the selection note](lol2-music-selection.md).
- The 33 `FORM` entries in `LOCAL.MIX` (entry 0 starts `FORM` / `XDIR`). They are not HMI songs.
- Whether the game's timer matches the 120-tick division above.
