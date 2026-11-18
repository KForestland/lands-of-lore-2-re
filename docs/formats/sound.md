# Sound bank, music and movies

**What and where (read 2026-11-18):**

| Data | Where | Pages |
|---|---|---|
| Sound effects and voice | `LOCALLNG.MIX` entry 4 (key 1570429112): one bank of named AUD files | [audio-inventory.md](../audio-inventory.md) |
| Music (digital) | `DMUSIC.MIX`: AUD IMA tracks; opcode 210 selects the track | [lol2-music-2026-11.md](../lol2-music-2026-11.md) |
| Music (MIDI) | `LOCAL.MIX` entry 0 is an XMIDI file (`FORM … XDIR`, then `CAT … XMID`); HMI music is not decoded ([Q15](../OPEN_QUESTIONS.md)) | — |
| Movies | VQA version 2 in room and level archives | [lol2-vqa-v2.md](../lol2-vqa-v2.md) |

## Sound bank layout

| Bank offset | Type | Meaning |
|---|---|---|
| 0x000 | text | a developer path string, zero padded |
| 0x258 | uint32 | row count (1179) |
| 0x25C | uint32 | offset of the row table |
| table | 60-byte rows | uint32 offset, uint32 size, uint32 unknown, uint32 placeholder flag, 44-byte NUL-terminated name |

Rows of size 1 are placeholders (171); the others are complete Westwood AUD files. Tool: `tools/lol2_sound_bank.py`.

## Worked example (re-run 2026-11-18)

Row 0: offset 612, size 13,894, placeholder flag 0, name `zombie1.aud`. The AUD header at offset 612:

```
22 56   3a 36 00 00   88 d5 00 00   02   63
```

| Bytes | Meaning |
|---|---|
| `22 56` | 22,050 Hz |
| `3a 36 00 00` | 13,882 bytes of compressed data (+ 12 header = the row size 13,894) |
| `88 d5 00 00` | 54,664 bytes when decoded |
| `02` | flags: 16-bit samples |
| `63` | codec 99: IMA ADPCM in chunks |

CONFIRMED: 1179 rows, 171 placeholders. Decoder: `tools/lol2_aud_decode.py`.

## AUD files stored as MIX entries

Besides the bank, 453 complete AUD files sit directly as entries in 29 of the 81 archives in `DAT/`, and 64 in 3 of the 7 game-folder archives (`DMUSIC.MIX`, `SETUP.MIX`, `GLOBAL.MIX`). `lol2_aud_decode.py --check --data <folder>` finds them by structure: the header's size field plus 12 equals the entry size, codec 99, and `0x0000DEAF` chunks that end at the entry's last byte and sum to the stated decoded size. All of them decode. CONFIRMED (re-run 2026-11-18).

- **The "22 56" entries are sounds.** At 22,050 Hz a file starts with the bytes `22 56`. An earlier tool in this repository read the 513 entries that start this way (450 in `DAT/`) as "0x2256 cell sprites" and drew them as pictures. Every one of them is a complete AUD file; that tool was removed.
- **One sample short.** In 16 files in `DAT/` and 47 in the game folder, the last chunk states one sample (2 bytes) more than its compressed bytes can hold; the decoded output is 2 bytes shorter than the header's decoded size. How the game handles the missing sample is not traced (UNCONFIRMED).
- **Stored chunks.** One `SETUP.MIX` file (entry 39, key 0xD9FF14D1, 733,186 decoded bytes) says codec 99, but every chunk's compressed size equals its decoded size and the bytes are plain 16-bit samples. The decoder copies such chunks unchanged. Whether the game plays this file, and how, is not traced (UNCONFIRMED).
