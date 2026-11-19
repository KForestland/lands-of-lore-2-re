# Loose DAT files

**What:** the two files in `DAT` that are not MIX archives: `AUTOPLAY.WAV`
(147,970 bytes) and `SETUP.EXE` (92,160 bytes). Tool: `tools/lol2_loose.py`.

**CONFIRMED.** `AUTOPLAY.WAV` is a RIFF WAVE whose size field plus 8 equals
the file length. `fmt ` at file +0x0C is 16 bytes: format 1, one channel,
22,050 Hz, 44,100 bytes per second, alignment 2, 16 bits. The `data` chunk
is 147,798 bytes. A `LIST`/`INFO` chunk of 120 bytes follows. Its subchunks
are `ICOP` 40, `ICRD` 11, `IENG` 16 and `ISFT` 16, and the odd pad after
`ICRD` makes the list end at the last byte.

**CONFIRMED.** `SETUP.EXE` is an NE program. The MZ image ends at file
+0xA270, where the bytes are `NE`, and the header's tables run from there
through the nonresident name `Guardians Setup Parser` (26 bytes). The
resident module name is `SETUP`. Five segments follow, each with flag bit
0x0100 set. A uint16 count and that many 8-byte records follow each
segment: 127, 42, 160, 112 and 62. Zero bytes fill from each record list
to the next aligned object. Five resources then run from file +0x15C00 to
the last byte.

**UNCONFIRMED** (what opens `AUTOPLAY.WAV`). `LOLG.DAT` (1,977,007 bytes)
contains neither `AUTOPLAY` nor `.WAV` nor `.wav`. Settling test: a
file-open trace that shows whether the game opens the name.

**UNCONFIRMED** (what opens `DAT/SETUP.EXE`). `LOLG.DAT+0x1C4B0E` is the
lowercase name inside the sentence at +0x1C4AEE, and `ERRTEXT.TRR+0x747`
is `Please run SETUP.EXE.` Neither string is an open of this file.
Settling test: a file-open trace that shows whether the game opens it.
