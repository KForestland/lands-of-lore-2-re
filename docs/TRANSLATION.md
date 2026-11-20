# Translate the original text

Use Python 3.10 or newer. These commands read the installation you supply and
write to new folders you name. Run them from this repository. Give `--data`
the same original game folder each time.

```sh
python3 tools/lol.py translate export --data "/path/to/game" --out "/path/to/private tables"
python3 tools/lol.py translate build --data "/path/to/game" --work "/path/to/private tables" --out "/path/to/translated files"
python3 tools/lol.py translate verify --data "/path/to/game" --work "/path/to/private tables" --out "/path/to/translated files"
```

Open a CSV from the export and import all four columns as text. Set only the
`new` column. A blank cell keeps the current string. Type `\e` for an empty
string. Copy codes such as `\x0D` when they appear in the original and use
`\\` for a literal backslash. Keep UTF-8 CSV, the column names, the row order
and the manifest. A locked row has another use in the game. Keep its new cell
blank. Build rereads each changed archive. Verify compares every output byte to
the result computed from the original and your CSVs. To try the output, copy it
over a separate copy of your game.

**Keep your CSVs, the manifest and the rebuilt files private. The CSVs
contain original game text.**

**CONFIRMED.** The export includes loose TRRs and matching tables in the MIX
directories. `LOCALLNG.MIX+0x1B174C0`, `+0x1B1AC83`, `+0x1B185DF` and
`+0x1B194EA` witness the four localized tables. The [round-trip page](ROUND_TRIP.md)
explains their 32-bit offset directory. “No limit” means there is no fixed
per-string field size. The file and archive offset ranges still apply.

**CONFIRMED.** For credits, the mode-1 reader tries loose `CREDITS.TRR`
first (`LOLG.DAT` VAs `0xCABA1 → 0xDE048 → 0xCF014`, then the loose
test at `0x118454–0x118468`). The two tables labelled `6E0E43F3` are its
byte-identical archive alternatives. They are stored in `DAT/MOVIES.MIX`
and `LOCALLNG.MIX` and remain separately labelled by source in the
manifest. [Message table lookup](lol2-text-tables.md#the-reader)

## Check characters before building

```sh
python3 tools/lol.py translate fonts --data "/path/to/game"
```

The list comes from the installed bitmap fonts. Build checks each edited
row against the font or fonts identified for that table. The warning names
the CSV row and suggests a substitute when one is available. An input
character the writer cannot encode stops the build. For a table whose
font is still unconfirmed, use the font listing to check likely choices.

**CONFIRMED.** `LOLG.DAT+0x1C538F` and `+0x1C5399` name the two standard
fonts. Their FNT entries start at `LOCAL.MIX+0x194156C` and `+0x1940B9B`.
The two option fonts are at `LOCAL.MIX+0x193B8E3` and `+0x193F14A`.
Two setup font entries with the same header signature start at
`SETUP.MIX+0x4512` and `+0xF5F2C`. The tool lists them by archive key.
The four LOCAL fonts have signature `0x0500` at `+0x02` and last index
`0xB8` at `+0x11`. At the same offset the SETUP entries hold `0xEE`
(at `+0x4512`) and `0xF1` (at `+0xF5F2C`). Build checks options, help and automap
text against the two option fonts. The options path names the fonts
at VAs `0x6FCDF` and `0x6FD2E`, and the automap chooses between
them at `0x145B84–0x145B95` before opening `automap.trr`. The visible Latin accents at indexes `0x80` through `0xAF`
follow CP437, including the accented C at `0x80` and the opening and
closing guillemets at `0xAE` and `0xAF`. The editor preserves bytes from
`0xB0` onward with escapes. Leave those escapes in place when unsure what
they mean in the original text.

## Verify a private translation patch

```sh
python3 tools/lol.py patch make "/path/to/translated files" --data "/path/to/game" --title "My translation" --out "/path/to/translation.json"
python3 tools/lol.py patch apply "/path/to/translation.json" --data "/path/to/game" --out "/path/to/test copy"
```

The patch checks the SHA-256 of each replaced span and makes a matching
undo file. Keep `undo.json` private because it holds original game bytes. If the size limit rejects the patch,
use smaller batches or keep replacements the same encoded size. A single
longer early row can shift enough offsets to hit the limit. You can still
keep the rebuilt files for your private copy.
See the [shared patch format](formats/patch.md).
