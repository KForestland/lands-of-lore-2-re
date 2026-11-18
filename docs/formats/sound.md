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
