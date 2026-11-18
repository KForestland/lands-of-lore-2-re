# Glossary

Words used across these pages, in plain terms.

| Term | Meaning |
|------|---------|
| LoL2 | *Lands of Lore: Guardians of Destiny* (Westwood Studios, 1997, DOS/Windows). |
| Original | The released game's own files and program. Every fact in this repository is about the original; nothing here describes a remake. |
| CONFIRMED / UNCONFIRMED | CONFIRMED: checked on the game files or in the original program's code. UNCONFIRMED: inferred, not yet checked. |
| Native | In or from the original program (`LOLG.DAT` and its loader), as opposed to a reimplementation. |
| Q1 … Q18 | Numbered open questions, see [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). |
| MIX | Westwood's archive: a 6-byte header (entry count, data size), 12-byte rows (key, offset, size), then the data. Almost all game data lives in MIX files under `DAT/`; `LOCAL.MIX` and `LOCALLNG.MIX` sit next to it. |
| Key | A MIX entry's name is not stored; its key is a hash of the name (`ww_hash_v1`, `tools/lol2_westwood_hash.py`). |
| Level archive | `DAT/L<n>_<xx>.MIX`, one per level (15), e.g. `L1_DC` = level 1, Draracle's Caverns. |
| Room archive | `DAT/<ROOM>.MIX` for a self-contained room, with a room module (`WOMS\<ROOM>_.WOM`), movies and sprites. |
| Geometry entry | The one entry in a level archive whose header starts with 18 and 5300; the level's regions, walls and floors. |
| Region | A walkable area of a level, joined to others by portals; the engine draws only regions it reaches through portals. |
| Entity record | A 147-byte object record (135-byte body and a 12-byte name tag such as `B_HUMAN`). |
| Script, opcode | Levels run Westwood script commands; each command starts with an opcode (37 known), its length fixed per opcode. |
| AUD | Westwood's compressed audio (IMA ADPCM). |
| VQA | Westwood's video format (version 2 in LoL2). |
| LCW / format 80 | Westwood's byte-oriented LZ compression, also used by Lands of Lore 1. |
| `LOLG.DAT` | The game's main program despite its name: an MZ stub with a DOS/4G-style extender and a 32-bit LE program (signature `LE` at file offset 0x3BCB4 in the copy read). Addresses are cited as virtual addresses (VA). |
