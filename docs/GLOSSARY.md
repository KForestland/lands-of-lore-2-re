# Glossary

Words used across these pages, in plain terms.

| Term | Meaning |
|------|---------|
| LoL2 | *Lands of Lore: Guardians of Destiny* (Westwood Studios, 1997, DOS/Windows). |
| Original | The released game's own files and program. Every fact in this repository is about the original game. |
| CONFIRMED / UNCONFIRMED | CONFIRMED: checked on the game files or in the original program's code. UNCONFIRMED: inferred, not yet checked. |
| Native | In or from the original program (`LOLG.DAT` and its loader), as opposed to a reimplementation. |
| Q1 … Q20 | Numbered open questions, see [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). |
| MIX | Westwood's archive: a 6-byte header (entry count, data size), 12-byte rows (key, offset, size), then the data. Almost all game data lives in the 81 MIX files under `DAT/`; seven more (`LOCAL`, `LOCALLNG`, `DMUSIC`, `SETUP`, `GLOBAL`, `CACHEBAK`, `CDCACHE`) sit next to it ([MIX page](formats/mix.md)). |
| Key | A MIX entry's name is not stored; its key is a hash of the name (`ww_hash_v1`, `tools/lol2_westwood_hash.py`). |
| Level archive | `DAT/L<n>_<xx>.MIX`, one per level (15), e.g. `L1_DC` = level 1, Draracle's Caverns. |
| Room archive | `DAT/<ROOM>.MIX` for a self-contained room, with a room module (`WOMS\<ROOM>_.WOM`), movies and sprites. |
| Geometry entry | The one entry in a level archive whose header starts with 18 and 5300; the level's regions, walls and floors. |
| Region | A walkable area of a level, joined to others by portals; the engine draws only regions it reaches through portals. |
| Entity record | A 147-byte object record (135-byte body and a 12-byte name tag such as `B_HUMAN`). |
| Script, opcode | Levels run Westwood script commands; each command starts with an opcode (the native size table knows 37 opcodes, 32 of them occur in the 15 levels), its length fixed per opcode. |
| AUD | Westwood's compressed audio (IMA ADPCM). |
| VQA | Westwood's video format (version 2 in LoL2). |
| LCW / format 80 | Westwood's byte-oriented LZ compression, also used by Lands of Lore 1. |
| `LOLG.DAT` | The game's main program despite its name: an MZ stub with a DOS/4G-style extender and a 32-bit LE program (signature `LE` at file offset 0x3BCB4 in the copy read). Addresses are cited as virtual addresses (VA). |
| Draracle | The first cave level (`L1_DC`) is the Draracle's cave; `tools/draracle/` holds the geometry and wall checks first written for it. |
| Region, portal | A region is a four-sided floor/ceiling polygon; a side that names a neighbouring region is a portal (an opening), a side without one is a wall ([geometry](formats/geometry.md)). Height values grow upward: the ceiling word is at least the floor word in 52,495 of 52,669 regions. |
| Connector, subdivision | Special region links that do not share the side's two vertices: short connector regions between rooms, and floor subdivisions owned by a parent region ([cave page](draracle-restoration.md)). |
| Room archive, WOM | One of the archives the executable opens by room name (46 names, plus `ARENA`); each carries a `WOMS\<ROOM>_.WOM` entry ([room archives](lol2-room-archives.md)). |
| Companion archive | `L<n>_<xx>I.MIX` next to a level archive: its movies and sounds. |
| VA, file offset, data address | A VA is an address in the program's code as loaded; file offset = VA + 0x37000. A data address is an offset in the program's data object; file offset = data address + 0x1C1024 ([executable tables](lol2-executable-tables.md)). |
| Witness | A concrete sample (a record, file or capture) used to test a claim. |
| Pinned | A tool that checks the SHA-256 of its input and refuses other editions. |
| `ww_hash_v1`, `v2`, `crc`, `ts` | Variants of Westwood's archive name hash in `tools/lol2_westwood_hash.py`; LoL2 keys use `v1`. |
| Longplay | A full recorded playthrough of the original game, used only to place levels in story order; it is not published here. |
