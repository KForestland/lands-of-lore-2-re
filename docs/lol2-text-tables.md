# Message tables

The executable loads five named message files through one reader. Each file is a count, an id table, an offset table, and NUL-terminated records. `TEXT.MIX` and `TCEL.MIX` are not these files. They are two of the 46 room archives ([room archives](lol2-room-archives.md)).

`tools/lol2_text_tables.py --check` re-reads the four tables inside `LOCALLNG.MIX`, the same credits table in `MOVIES.MIX`, the three loose copies beside the game, and the two room archives. It writes nothing.

`LOLG.DAT` in this note is the 1,977,007-byte image whose sha256 begins `b27a3534`. A code address is a file offset minus `0x37000`. A data address is a file offset minus `0x1C1024`.

## Where the files are

CONFIRMED for the names, the archive keys, and the sizes. The name hash is `ww_hash_v1` ([MIX](formats/mix.md)). `LOCALLNG.MIX` is the archive next to the game, not inside `DAT/`. It has 6 entries. Four of them are message tables. Entry 2 is the movie whose name hashes as `OUTTAKES\TITLE_E.VQA`. Entry 4 hashes as `global\sounds.efx`. Neither is a message table.

| File | Where | Entry | Bytes | Records |
| --- | --- | --- | --- | --- |
| `automap.trr` | `LOCALLNG.MIX` | 0 | 4383 | 364 |
| `opttext.trr` | `LOCALLNG.MIX` | 1 | 4328 | 202 |
| `helptext.trr` | `LOCALLNG.MIX` | 3 | 3851 | 41 |
| `credits.trr` | `LOCALLNG.MIX` | 5 | 6041 | 43 |
| `credits.trr` | `DAT/MOVIES.MIX` | 28 | 6041 | 43 |
| `ERRTEXT.TRR` | beside the game | loose file | 2444 | 39 |
| `OPTTEXT.TRR` | beside the game | loose file | 4587 | 212 |
| `CREDITS.TRR` | beside the game | loose file | 6151 | 44 |

`MOVIES.MIX` entry 28 is byte-identical to the `LOCALLNG.MIX` credits table. The loose `OPTTEXT.TRR` and `CREDITS.TRR` are not the archive copies: both differ from the first byte, and both have more records. `errtext.trr` is not a key in `LOCALLNG.MIX`. `LANGUAGE.ENG`, beside the game, is the two bytes CR LF. It is not a table. The executable also names `LANGUAGE.JAP`, `LANGUAGE.FRE`, and `LANGUAGE.GER`. Those three files are not beside this copy of the game.

A scan of every entry of every MIX archive in the game folder, plus the three loose `.TRR` files, found this layout in eight places: the four `LOCALLNG` tables, `MOVIES` entry 28, and the three loose files. No room archive has an entry in this layout. The hash of `WOMS\<ROOM>_.WOM` is the code entry already described on the room-archive page, the one that begins `This is a linear executable dll`.

## The reader

CONFIRMED. VA `0xCF014` is the reader. It is called directly with `helptext.trr` at VA `0x6FC63`, `0x6FDB4`, and `0x70C47` (three copies of the name, at data `0x5B0`, `0x5E3`, and `0x608`). It is called with `opttext.trr` at `0x6FD93`, `0xB93CF`, `0xCB9D4`, and `0xCC310` (data `0x5D7`, `0x1425`, `0x16E4`, `0x1AD4`). It is called with `automap.trr` at `0x145C49` (data `0x41AE`).

VA `0xDE048` allocates the same 16-byte block and calls `0xCF014` with its second argument. VA `0xCABA1` passes `credits.trr` (data `0x16CB`). VA `0x14E6B4` passes `errtext.trr` (data `0x4271`), after VA `0x14E698` has probed data `0x4265` through VA `0x118934`. Those are the nine direct calls of the reader found from file `0x90024` through `0x1C1024`. No other filename is passed to it.

The reader opens the name through VA `0x118730`. It reads one dword, the count, into the block. It reads `count` more dwords into a buffer at block+4. It reads `count + 1` dwords into a buffer at block+8, then subtracts `8 * count + 4` from each of them. It allocates `file_size - (8 * count + 4)` bytes at block+12 and reads that many bytes. The bytes actually still in the file at that point are four fewer, because the read starts at file offset `8 * count + 8`. VA `0x15F44C` then walks the heap. For each byte it looks through the nine bytes at data `0x19720` and, on a match, stores the byte at the same index in data `0x1972C`.

Those nine source bytes are `CF E1 E6 EF F5 F8 F9 FC FD`. The nine stored in their place are `B0 B1 B2 B3 B4 B5 B6 B7 B8`. None of the eight tables above contains a source byte, so the records on disk are the records the reader keeps.

**CONFIRMED.** The TRR reader opens in mode 1
(`0xCF025–0xCF041`). The ordinary file slot's vtable
at `LOLG.DAT+0x1CB810` routes +0x1C to `0xF1944` and
+0x20 to `0x118440`. On a fresh file slot the mode-1 path
tests the loose filename first
(`0x118454–0x118468 → 0x116340 → 0x124425`).
The helper tries the DOS open call at `0x154240–0x154246`.
Success branches to the local open at `0x11846A`. The
archive lookup `0x11C104` is reached at `0x1184AA` after a
failed test. A mounted archive and a loose file can therefore
both exist, and a successful loose open wins in this path.
For the two options witnesses read above that selects the
212-record loose copy when the path resolves in the DOS
working directory. The separate existence probe at
`0x11839C` uses a different order.

## Record layout

CONFIRMED on all eight files. Little-endian.

| Offset | What |
| --- | --- |
| 0 | `u32` count `N` |
| 4 | `N` dwords, the record ids |
| `4 + 4N` | `N + 1` dwords, offsets relative to file byte 4 |
| `8N + 8` | the records |

The stored offsets count from file byte 4, just after the count, so the first one is `8N + 4`; that value is also the rebase the reader subtracts. The last stored offset is the file size minus 4. Record `i` is the bytes from file offset `offset[i] + 4` up to `offset[i + 1] + 4`. Each record contains exactly one NUL, and that NUL is its last byte. The next record starts at the next byte. The offsets are strictly increasing.

The id table is not always `0 .. N-1`. In the archive copy of `helptext.trr` the 41 ids are `0` through `49` except `10` through `18`. The other archive tables, and loose `ERRTEXT.TRR`, use `0 .. N-1`.

## Worked example

CONFIRMED. Archive `helptext.trr`, 3851 bytes, count 41.

The id table occupies file `4` through `167`. The offset table occupies file `168` through `335`: 42 dwords. Its first value is 332 and its last is 3847. The heap starts at file 336 and is 3515 bytes. `332` is `8 * 41 + 4`, and `3847` is `3851 - 4`.

Five of the 41 records are a single NUL. One record contains byte `0x07` and no other byte below 32. The other 35 records are bytes in the printable ASCII range, tab, CR, or LF, plus the trailing NUL. The first record is 262 bytes including that NUL. The longest record is 369 bytes including the NUL.

`automap.trr` uses the same framing and different payloads. Of its 364 records, 285 are a single NUL, 22 are non-empty printable ASCII, and 57 contain byte `0x07` and no other byte below 32. `opttext.trr` in the archive has 11 empty records and 2 records that contain byte `0x11`. Its loose copy has the same two counts and 212 records instead of 202. Archive `credits.trr` has no empty record. Two of its records contain byte `0x81` or `0x82` and no other byte above 126. Loose `ERRTEXT.TRR` has 39 records, all printable ASCII with the trailing NUL. Across those 39 records, byte `0x0A` occurs 10 times and byte `0x5E` occurs 9 times.

## What this is not

The eight callers of VA `0xEE784` build a path with the format at data `0x3256`, `WOMS\%s\%02d%03d%02d%c`. The `%s` is the runtime buffer at data `0xDB504`, which is past the file-backed part of object 5. The character pushed for `%c` is `0x45`. Each caller passes `2`, then one of `0x14`, `0x15`, `0x1A`, `0x1B`, `0x21`, `0x38`, `0x39`, `0x3A`, then `0x18`. Because the first number is `2`, the builder joins VA `0xEE8AC`. Later, at VA `0xEEC42`, a path in this function appends the string at data `0x326D`, which is `.aud`, and probes the buffer with VA `0x118934`. Hashing `WOMS\<stem>\02<mid>24E` for all 81 MIX stems and those eight middle numbers finds no MIX key; with `.aud` appended, `WOMS\MCEL\0202024E.aud` and `WOMS\MCEL\0202624E.aud` are keys in `DAT/MCEL.MIX` (entries 5 and 7, 17,564 and 21,668 bytes). That path is an audio name. It is not one of these tables. The eight callers take the `0xEEA6D` branch to `0xE3924` and do not reach the `.aud` append at `0xEEC42` (reached only via `0xEEC35` when the dword at data `0xDB4C8` is 0). See [spoken lines](lol2-speech.md).

No sentence from a record is copied here.

## What would settle the rest

The eight callers take the `0xEEA6D` branch and do not reach the `.aud` append; that is on the [spoken lines](lol2-speech.md) page. What reads text for the cue id they pass to VA `0xE3924` is still open. A second text reader, one that does not call VA `0xCF014`, would be a different container.

## Writing the stored tables

**CONFIRMED.** `tools/lol2_text_writer.py --check --data /path/to/DAT`
reconstructs the eight copies in the table above, with 988 stored rows.
The writer calculates the relative boundaries from the ordered ID and
message fields, including empty messages and control bytes. The
`--list` offsets include `LOCALLNG.MIX+0x1B185DF` for the help
table and `MOVIES.MIX+0x87BFDB0` for the second archive copy of
credits. The loose tables start at file +0. The check compares the
original bytes before any substitution by `0x15F44C`.

**UNCONFIRMED.** A separate LoL2 table that maps spoken cues to text.
The TRR scan covered every MIX archive in `DAT` and beside it (except
`CDCACHE.MIX`) and the loose TRRs, and finds only the eight tables
above; the nine direct calls of the loader `0xCF014` name only the five message
files. The eight spoken-line arms pass a cue to `0xE3924`, which stores it on the voice at
`0xE3A08` ([Q13 close-out](lol2-speech.md#q13)). **Test:** the 47 room
modules' 3134 absolute indirect calls resolve to 63 host functions, and
none of those calls `0xCF014` directly; host +0xC4 reaches it four
calls deep, in the options menu `0xB9204`. Host slot +0x13C (`0xF16D8`)
indexes the cue words and calls `0xE4004`. A text reader outside those
63 functions, or a second container not read through `0xCF014`, would
settle it. Until then this is [Q13](OPEN_QUESTIONS.md), partly answered.
