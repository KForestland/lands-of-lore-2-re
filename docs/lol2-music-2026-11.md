# LoL2 music: DMUSIC.MIX is decodable (November 2026)

Research by the decode agent (Grok), reviewed by the lead agent (Opus), for the LoL2 Classic remake. Offsets are from the
GOG release (`LOLG.DAT` sha256 `b27a3534…5766775`; `DMUSIC.MIX` size 81,208,196). No audio is included here: a remake
converts the music from the player's own copy.

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
| `MELODIC.BNK` / `DRUM.BNK` are AdLib FM banks for the HMI MIDI path; the MIDI scores are LIKELY the 33 `HMI-MIDI` entries in `LOCAL.MIX` | banks proven, scores likely |
| The GOG copy has no CD audio tracks | proven for this copy; retail discs likely the same |
| Which MIX entry belongs to which stem (the MIX ids are hashes; common hash functions did not match) | **open** |

## What is still open

- The stem-to-entry mapping (help welcome: a list of which soundtrack piece plays in which level or scene).
- What the volume-like words stored by opcode 210 arms 4 to 9 mean.
