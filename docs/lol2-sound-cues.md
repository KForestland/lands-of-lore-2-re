# Sound cue ids

Opcode 20 hands the sound player a 16-bit id. The id is the word at bytes 4 and 5 of the 10-byte command. A named bank of 1,179 rows sits in `LOCALLNG.MIX`. This pass did not find the instruction that turns the id into one of those rows, so the row named below is the row at that index, and the claim that opcode 20 plays it stays open.

`tools/lol2_media_check.py --check` re-reads the worked-example command, the row count and row 1049. It writes nothing.

## The command

CONFIRMED. Opcodes 1 through 24 enter the low dispatcher at VA `0xB6B6E`. The dispatcher decrements the opcode and jumps through the 24 slots at VA `0xB589C`, using the same `+ 0x59024` adjustment described in [the movie note](lol2-movie-scenes.md). Opcode 20 and opcode 24 both enter VA `0xB5BDC`.

When the opcode byte is `0x14`, that site zero-extends the word at bytes 4–5 and calls VA `0xE3924` with five arguments: the sound object at data `0x23C68`, that word, the register `ebx` left by the dispatcher, a pointer to byte 6, and the constant 1. Bytes 1, 2 and 3 are not read. Opcode 24 reaches the same site and, because the byte is not `0x14`, calls VA `0xE3D2C`. [The opcode reference](lol2-script-opcodes.md) describes that call: it passes the object, a pointer to byte 6, and the word at bytes 4–5.

The high dispatcher's compare at VA `0x649A9` is `cmp al, 0x15`. Opcodes below 21 leave that compare. Opcode 20 is not on that path.

Command stream 1 of `DAT/L12_CM.MIX` frames exactly with opcode 20 as 10 bytes. That stream holds 42 of these commands.

## What the player does with the id

CONFIRMED as far as the bounds check.

VA `0xE3924` takes the word as its second argument. It rejects the call when the word is greater than or equal to the dword at `[object + 0x1C]`. It then reads the byte at `[pointer + 1]`, which is command byte 7, and tests bit 1 of that byte. Later it stores the id on a voice slot. The helper at VA `0xE529C` compares the id with ids already stored on voice slots. Nothing in that helper multiplies by 60 or reads the bank.

The object address `0x23C68` is past the initialised image, so the file does not hold the limit. What writes `[object + 0x1C]` was not found.

## The named bank

CONFIRMED as a layout. `LOCALLNG.MIX` entry key 1570429112 is 25,010,232 bytes. The executable opens it by pushing the string `LOCALLNG.MIX` (file `0x1C535C`, data `0x4338`) and calling VA `0x118934` at VA `0x14E785`.

Inside the entry, dword `+0x258` is 1179 and dword `+0x25C` is 24938684, the file position of the row table within the entry. Each row is 60 bytes: a u32 clip offset, a u32 size, a u32 that was not interpreted, a u32 flag, and a NUL-terminated name from byte 16. Row 0 is `zombie1.aud` and its clip starts at byte 612. The same layout is the one [the audio inventory](audio-inventory.md) already checks with `tools/lol2_sound_bank.py`. This pass re-read the count, the table offset and two rows. It did not walk all 1,179 clips.

## Worked example

CONFIRMED for the command bytes and for the row that has this index. UNCONFIRMED as the clip the command plays.

`DAT/L12_CM.MIX` command stream 1, file offset 9821090:

```
14 03 04 00 19 04 ff fd fa fa
```

Opcode `0x14`. Bytes 2–3 are `0x0004` and are not read here. The word at bytes 4–5 is `0x0419`, which is 1049. Bytes 6–9 are `ff fd fa fa`. Byte 7 is `0xFD`, so bit 1 is set and the player's test of that bit takes the nonzero side.

1049 is below 1179. Row 1049 is named `0190108e.aud`, size 15652, flag 0. The clip's 12-byte header is rate 22050, flags 2, codec 99.

## What would settle it

A store of the bank's dword at `+0x258` into `[object + 0x1C]`, and an address calculation `row table + id * 60` that uses the word from bytes 4–5. Until then the id is the argument of the sound player, and the row name is only the name stored at that index.

Also still open: what bytes 6–9 mean beyond bit 1 of byte 7, and what `ebx` is at the call.
