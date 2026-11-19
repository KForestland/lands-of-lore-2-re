# Room archives

The executable names 46 MIX archives from a table of short names. `TEXT` and `TCEL` are two of those archives. They are not a text container. The game's message tables (help, options, automap, credits and error text) are the TRR files in [the text-table note](lol2-text-tables.md). Where character dialogue is stored is still open.

Each of the 46 archives has one entry that begins with the banner `This is a linear executable dll`. That entry is a header plus executable bytes. `TEXT` and `TCEL` are the worked example of the name table and of that entry.

`tools/lol2_media_check.py --check` re-reads the 46 names, the one code entry in each archive, and the `TEXT` and `TCEL` directories. It writes nothing.

## The 46 names

CONFIRMED. The table is 46 dwords at file `0x1CFA90` (data `0xEA6C`). Each dword is the data offset of a name. VA `0xED428` walks the table by fours while the offset is below `0xB8`. It calls VA `0x1501A0` with the looked-up name and the table name. That compare folds `A`–`Z` to lower case on both sides and returns the difference of the bytes where they stop, so a zero return is an exact match. The matcher then returns the index. A name that matches nothing is passed to VA `0x1501EC` with the format `Wom[%s] does not exist!` (data `0x31A4`) and the matcher returns 0. Index 0 is the real name `pool_`, so the return value alone does not separate "no match" from `pool_`. A scan of direct calls from file `0x57000` to `0x1A0000` found no `E8` into VA `0xED428`.

| Index | Name | Index | Name | Index | Name |
| --- | --- | --- | --- | --- | --- |
| 0 | pool_ | 16 | tcel_ | 32 | cfall_ |
| 1 | cave_ | 17 | tdoor_ | 33 | dragon_ |
| 2 | skel_ | 18 | tint_ | 34 | hive1_ |
| 3 | ment_ | 19 | liz_ | 35 | hive2_ |
| 4 | mcel_ | 20 | stat_ | 36 | hive3_ |
| 5 | mgar_ | 21 | empt_ | 37 | hive4_ |
| 6 | moff_ | 22 | shaman_ | 38 | tmpldor_ |
| 7 | mlib_ | 23 | shbak_ | 39 | settle1_ |
| 8 | wpn_ | 24 | herb_ | 40 | settle2_ |
| 9 | sever_ | 25 | daniel_ | 41 | settle3_ |
| 10 | runecl_ | 26 | hut1_ | 42 | settle4_ |
| 11 | runes_ | 27 | hut2_ | 43 | wpnext_ |
| 12 | village_ | 28 | dslave_ | 44 | text_ |
| 13 | can_ | 29 | slaves_ | 45 | altar_ |
| 14 | chut_ | 30 | chv_ |  |  |
| 15 | magic_ | 31 | balcony_ |  |  |

## How a name becomes a file

CONFIRMED. VA `0xED470` takes the index. If a handle is already stored at data `0xDB568`, it is closed through VA `0x11C654`. The function copies the table name onto the stack, scans for the byte `0x5F`, and writes 0 there. It then appends the string `.mix` at data `0x31BC`. So `text_` becomes `text.mix` and `tcel_` becomes `tcel.mix`. It allocates `0x24` bytes through VA `0x14FFF4`, passes that block and the built name to VA `0x11C654`, and stores the result at data `0xDB568` and the index at data `0xDB47C`.

The copy does not itself change case. The compare that selected the index already folded case. The files on disk are `DAT/TEXT.MIX` and `DAT/TCEL.MIX`. Whether VA `0x11C654` folds the filename was not read.

The same cut-and-append names the other 44 archives. `DAT/TDOOR.MIX` is a MIX of 11 entries and `DAT/TINT.MIX` is a MIX of 92. Their entries other than the code entry were not framed.

## The extra ARENA archive

**CONFIRMED.** `DAT/ARENA.MIX` has two entries. Directory entry 1
at file +0x12 carries key `0x0CBF521D`, the hash of
`WOMS\ARENA_.WOM`. It points to `+0x1E`, length `0x5E8`, and has
the same executable-module prefix as the table-bound room modules.
Entry 0 at `+0x606` is a 13-byte marker. The executable room-name table
at `LOLG.DAT+0x1CFA90` has no `arena_` row.

**CONFIRMED.** All three direct callers of the table-based archive
builder `0xED470` use its indexed path (`0xED5B5`, `0xED72A`,
`0xEDB5A`). The name-driven caller searches the same table in
`0xEDADD–0xEDB43`. On a miss, it selects index 0 before it calls
`0xED470` (`0xEDB47–0xEDB5A`). Formatting a `.WOM` name follows at
`0xEDB62–0xEDB89`. This path cannot supply `arena.mix` through a
matching room-table row.

The code object has 28 direct calls to archive constructor
`0x11C654`. The 15 calls in `0x95E07–0x9A63C` build the
`SPKSTON%d.MIX` name (`LOLG.DAT+0x1C1BD4`). The two dynamic
movie-path calls at `0x9BFAC` and `0x9C02B` use a stem from
`[0xCA20 + 8*i]`; the suffixes at `LOLG.DAT+0x1C1BFE` and
`+0x1C1C03` are `.MIX` and `I.MIX` (`0x9BE06–0x9BE40`,
`0x9BFDC–0x9C02B`). The remaining calls use the following names. File offsets in the
right column refer to the original executable.

| Constructor call | Name source | File offset |
|---|---|---|
| `0x9BCAE`, `0x9BF88` | `GLOBAL.MIX` | `+0x1C1BF1` |
| `0xBDB3C` | `MOVIES.MIX` | `+0x1C24ED` |
| `0xC4B0E` | `MOVIES.MIX` | `+0x1C257B` |
| `0xED54A` | room-table name with the suffix appended in `0xED470` | table `+0x1CFA90` |
| `0x119C4E` | `CDCACHE.MIX` | `+0x1C493B` |
| `0x11A738` | `DMUSIC.MIX` | `+0x1C4A01` |
| `0x14E778` | `LOCAL.MIX` | `+0x1C5352` |
| `0x14E7C8` | `LOCALLNG.MIX` | `+0x1C5376` |
| `0x14F081` | `MOVIES.MIX` | `+0x1C54C1` |
| `0x14F227` | `MOVIES.MIX` | `+0x1C54DE` |

The only case-insensitive `arena` text in `LOLG.DAT` is the movie
stem `arenaapr` at `+0x1C3D1A`. Room-related external literals
survive in `SHAMAN.MIX+0x248B`, `SETTLE1.MIX+0x73C` and
`L8_SJ.MIX+0xD10AD9`. The host passes its callback table at data
`0xE92C` from `0xEDCC3` and invokes the loaded module with
selector 0 at `0xEF881`. The Arena module copies the first 53
entries, starting at module +0x125 (file `ARENA.MIX+0x143`).
The first external call at file `ARENA.MIX+0x377` takes table
offset +0x18, which resolves to `0xEF028` via file
`LOLG.DAT+0x1CF968`. The module's direct absolute-indirect
instruction sites select host offsets `0x18`, `0x1C`,
`0x54`, `0x6C` and `0x88`.

**UNCONFIRMED.** Whether the retail game opens `ARENA.MIX` by a
secondary route. The direct constructor calls and the fixed imports
above give no such witness. Trace the room-related indirect calls
from the shipped WOM modules into their host wrappers and record
whether an archive constructor receives the exact name.
The archive's presence alone leaves it open.

## The code entry

CONFIRMED for the banner, the two shared dwords and the four prologue bytes. This pass opened every archive the table names. Each file is `DAT/<name>.MIX` after the trailing `_` is cut off. Each of the 46 archives has exactly one entry whose first 32 bytes are the banner: the 31 characters `This is a linear executable dll` and a newline. After the banner, three little-endian dwords: `0x101`, a middle dword that differs from archive to archive, and `0x34`. At offset `0x64` the bytes are `53 56 57 55`, which is `push ebx` / `push esi` / `push edi` / `push ebp`. That entry is not always member 0.

The native reader checks the version at `0xDF7E2–0xDF7FA`. It
then reads three dwords, the body length (+0x24), dispatch offset
(+0x28) and relocation count (+0x2C). It allocates body length plus
eight and writes a jump whose target is the body start plus the
dispatch offset (`0xDF80F–0xDF885`). The body begins at member
+0x30. Each four-byte relocation after that body names a position
where the module base is added to the dword already there
(`0xDF88D–0xDF8BD`). All 47 modules end exactly after their
8,469 relocation entries, and all those positions and their stored
target offsets lie in their bodies. The data includes 46 modules
with dispatch offset `0x34` and Arena with `0x2C`.

For `TEXT`, body length `0x698` and dispatch offset `0x34` put
the entry at member +0x64. Its 107 relocation dwords start at
member +0x6C8. `TCEL` uses body length `0x838` and has 126
relocations. Arena's dispatch starts at member +0x5C, and
its 72 relocation dwords start at +0x4C8.

## Worked example

CONFIRMED for the directory and the first bytes of each entry. `TEXT.MIX` is 684,287 bytes and holds 3 entries. `TCEL.MIX` is 3,816,289 bytes and holds 4.

| Archive | Index | Key | Size | First bytes |
| --- | --- | --- | --- | --- |
| TEXT.MIX | 0 | `0xA9DCD821` | 2164 | the 32-byte banner, then `0x101`, `0x698`, `0x34` |
| TEXT.MIX | 1 | `0x5874DA13` | 13 | `ECHO is OFF` then CR LF |
| TEXT.MIX | 2 | `0x695103AB` | 682068 | `FORM` / `WVQA` |
| TCEL.MIX | 0 | `0xC940F364` | 797762 | `FORM` / `WVQA` |
| TCEL.MIX | 1 | `0x0C6CDA03` | 13 | `ECHO is OFF` then CR LF |
| TCEL.MIX | 2 | `0x59D0F84B` | 3015804 | `FORM` / `WVQA` |
| TCEL.MIX | 3 | `0x5DD4D811` | 2656 | the same banner, then `0x101`, `0x838`, `0x34` |

Index 44 is `text_`. The builder cuts at `_` and appends `.mix`, which is the name of `DAT/TEXT.MIX`. Its code entry is member 0. Index 16 is `tcel_`, and the same steps name `DAT/TCEL.MIX`. Its code entry is member 3.

The 13-byte member is those exact bytes in both archives. It is a whole member, not a line of speech.

The movie entries use the same `VQHD` layout as [the movie note](lol2-movie-scenes.md). TEXT entry 2 and TCEL entry 0 begin with words 2, 0, 30, 640, 400. TCEL entry 2 begins with words 2, 1, 117, 640, 400. No frame was decoded.

## Dialogue

`TEXT.MIX` and `TCEL.MIX` are not message tables. Each holds a code entry, the 13-byte `ECHO is OFF` member, and `FORM` / `WVQA` movies. The message tables (help, options, automap, credits and error text) are [the TRR files](lol2-text-tables.md). Where character dialogue is stored is still open ([Q13](OPEN_QUESTIONS.md)).

## What would settle it

Trace an indirect room callback that supplies the exact name `ARENA.MIX`, or identify an alternate shipped executable whose archive table lists it.
