# Spoken lines

Message tables are a different container ([message tables](lol2-text-tables.md)). This page is the name the category arms format, and the cue id they hand to the sound player. No line of speech is copied here.

`tools/lol2_speech_names.py --check` re-reads the format bytes, the switch, the eight arms, the branch, and two archive keys. It writes nothing unless `--out` is set, and then only the check line. It is not one of the 20 checks.

`LOLG.DAT` in this note is the 1,977,007-byte image whose sha256 begins `b27a3534`. A code address is a file offset minus `0x37000`. A data address is a file offset minus `0x1C1024`. An object-2 slot stored in the file plus `0x59024` is the address used below.

## The name

CONFIRMED. VA `0xEE784` formats a stack buffer through VA `0x150158`. The format is data `0x3256`, file `0x1C427A`: `WOMS\%s\%02d%03d%02d%c`. The `%s` is the runtime buffer at data `0xDB504`, which is past the file. The three numbers are the three arguments, and the character pushed for `%c` is `0x45`.

The same format is stored again at data `0x3272` and data `0x32C8`. Data `0x1394` is the different format `%s\%s.aud`. The suffix the other branch copies is data `0x326D`, `.aud`.

## The switch

CONFIRMED. VA `0xF133C` is one function. It pushes `ebx`, `esi`, and `edi`. It returns through VA `0xF0F72` if the argument's bit is already set in the dword at data `0xDB500`, ORs the argument in, and clears the low byte once all eight bits are set. It then draws a value `r` from 0 through 7 by calling VA `0x12415C` with `7`, `0`, and data `0x221D8`. While bit `r` of the dword at data `0xDB500` is set, it draws again. It then sets that bit and jumps through `cs:[eax*4 + 0x982F8]`.

The eight dwords are at VA `0xF131C`, which is `0x982F8 + 0x59024`. Each stored dword plus `0x59024` is the arm, in table order. Draw `r` enters row `r`.

| r | Stored dword | Arm | Category | Bit |
| --- | --- | --- | --- | --- |
| 0 | `0x983A2` | `0xF13C6` | `0x38` | `0x01` |
| 1 | `0x983C0` | `0xF13E4` | `0x15` | `0x02` |
| 2 | `0x983E1` | `0xF1405` | `0x1B` | `0x04` |
| 3 | `0x98402` | `0xF1426` | `0x3A` | `0x08` |
| 4 | `0x98423` | `0xF1447` | `0x1A` | `0x10` |
| 5 | `0x98444` | `0xF1468` | `0x21` | `0x20` |
| 6 | `0x98465` | `0xF1489` | `0x39` | `0x40` |
| 7 | `0x98486` | `0xF14AA` | `0x14` | `0x80` |

These are tails of that switch, not separate functions. Each pushes `0x18`, one category, and `2`, calls VA `0xEE784`, ORs its bit into the byte at data `0xDB500`, then pops `edi`, `esi`, and `ebx` and returns.

The formatted name for those arguments is `WOMS\<stem>\02<category as three digits>24E.aud`. The builder does not open it on this path.

## The cue id

CONFIRMED. VA `0xEE7D8` joins VA `0xEE8AC` when the first argument is `1`, `2`, or `0x64`. VA `0xEE8B3` joins VA `0xEEA6D` when that argument is not `0x64`. At VA `0xEEA6D`, `cmp esi, 2` leaves for VA `0xEEC35` when the first argument is not `2`, and `cmp ebx, 0x14` / `jle` leaves for the same address when the third argument is at most `0x14`. The eight arms pass `2` and `0x18`, so they stay. They copy the category into `ebx` and add `0x8D`.

When bit 0 of the byte at data `0x269C4` is clear, they read a cue id from the runtime u16 table whose pointer is data `0x269CC`, at index `category + 0x8D`, and call VA `0xE3924`. The pointer and the flag byte are past the end of the file. The indexes are `161`, `162`, `167`, `168`, `174`, `197`, `198`, and `199`. VA `0xE3924` is the player opcode 20 also calls. That player joins the cue id to the bank row with the same index ([sound cues, Native bank join](lol2-sound-cues.md#native-bank-join)), so these arms play through that path.

VA `0xEEC42` is the other branch. It copies data `0x326D` onto the formatted name. It is reached only through VA `0xEEC35`, and only when the dword at data `0xDB4C8` is 0. These eight arms do not reach it.

## Keys that match two formatted names

CONFIRMED as keys, not as the files these arms open. `ww_hash_v1` of `WOMS\MCEL\0202024E.aud` (category `0x14`) is `DAT/MCEL.MIX` entry 5, 17,564 bytes. `WOMS\MCEL\0202624E.aud` (category `0x1A`) is entry 7, 21,668 bytes. Both headers are rate 44,100, flags `2`, codec `99`, and the compressed-size field equals the entry length minus 12. `WOMS\MCEL\0312002E.aud` hashes to the same value as the first name, `0x9A7F3A86`, so that hash is one entry under two names.

## How a script selects a line

Opcode 20 is the script path on the sound-cue page: a 10-byte command, the u16 at bytes 4 and 5, then VA `0xE3924`. The eight arms reach the same player with the runtime table word, not with a script operand.

## Cue consumers after playback starts

**CONFIRMED.** The category arm passes a null event object and the
u16 cue to `0xE3924` (`0xEEAC2–0xEEAF9`). It stores the returned
voice handle at `[0xDB494]+0x90` and the category-derived table
index at `+0x94` (`0xEEB0A–0xEEB17`). The later loops use the
handle to get the live voice from `[0x267A0 + 4*handle]`.
They test voice +0x26 bit 2 and compare voice +4 against the same
u16 table cue (`0xEEB39–0xEEB79`, `0xEEB9A–0xEEBD3`).
The loops call the room update at `0xEE010`, which services sound
at `0xEE023`, while waiting for those conditions. These reads use
the cue as a voice identifier.

**CONFIRMED.** The sound player's event callback requires a nonnull
event object, both when it admits playback and on cleanup
(`0xE3BCC–0xE3BEB`, `0xE3824–0xE3841`). The category call does
not supply one. The indexed bank lookup at `0xE4CEF–0xE4CF8`
reads the payload for that cue from the EFX bank. The shutdown
path frees the table pointer at `0x14EA84–0x14EA9C`.

**UNCONFIRMED.** A text reader keyed by the cue. The category
call-through, its two completion loops, and the sound admission
and cleanup branches show no conversion from cue ID to text.
The five known TRR tables from `0xCF014` also have different row
counts from the 1,179-row EFX bank. To settle a separate text
path, trace the post-call owners of `[0xDB494]+0x90/+0x94`
and imported room-module draw callbacks, then identify a reader
that uses the same cue ID to select a text record. A count or a
matching filename alone cannot establish that join.
