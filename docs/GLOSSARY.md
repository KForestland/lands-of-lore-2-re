# Glossary

Words used across these pages, in plain terms.

## Shared words

These words mean the same thing in the notes for all three Lands of Lore games.

| Term | Meaning |
|------|---------|
| Original | The released game's own files and program. Every fact in this repository is about the original game. |
| CONFIRMED / UNCONFIRMED | CONFIRMED: proved from the program code or the files. UNCONFIRMED: a reading not yet proved. |
| Answered / Mostly answered / Partly answered | The state words of [open questions](OPEN_QUESTIONS.md). *Answered*: nothing is left to settle from the files or the program. *Mostly answered*: the main question is settled; named details remain. *Partly answered*: part is settled; the main point is open. A row that says 'answered for' a setup (one renderer, one device) counts as answered for that setup only. |
| Native | In or from the original game program, as opposed to a reimplementation. |
| Open question | A numbered question on the [open-questions page](OPEN_QUESTIONS.md). |
| Archive | A file that holds many pieces of game data. |
| Entry | One piece of data stored inside an archive. |
| Level | One place the player walks through, stored as its own set of files. |
| Level sheet | One page per level, written by a tool from that level's files. |
| Schematic | A top-down line drawing of a level from its map data, with no game pixels. |
| Script | Commands the game runs for a level, an item, or a cut-scene. |
| Opcode | The number that begins one script command and selects what it does. |
| Event | A script that runs when something happens, such as a click, a step, or a timer. |
| Item | An object the player can carry, or that a level places in the world. |
| Creature | A living opponent or other character placed in a level. Monster means the same on these pages. |
| Placement | One recorded place where a level puts an item, a creature, or another object. |
| Save slot | One file the original game wrote for a game in progress. Tools may read it; this repository does not store it. |
| Probe | One check that needs the original game running. |
| Rating | The four counted lines near the top of the README, written by `tools/rating.py`. |
| Files read | A file whose every byte a tool here assigns to a known header, directory, entry or other named part; what is inside an entry may still be only partly understood. Files the game writes into the data folder while it runs are added to the total and count as read only if a reader walks them. Which folder is counted: [how we rate](HOW_WE_RATE.md). |
| History page | A page marked **History** at its top: an older note kept as a record. The rating does not count it; where it differs, the current pages are right. |
| File offset | The position of a byte in a file on disk. |
| Spell | A magic effect the player casts. Its cost is stored in the game's tables. |
| Dialogue | Lines a character says, or that the game prints. |
| Music | The game's songs. A music tool can list or convert them. The tools do not play sound. |
| Combat | How an attack is resolved: whether it hits, and what the hit changes. |
| Hash | A number computed from other bytes. A file hash identifies a whole file. A name hash stands in for a file name. |
| LCW, format 80 | Westwood's byte-oriented compression, also called format 80. |
| Mod kit | `tools/modkit.py`: it unpacks the game's text and number tables into files you can edit and builds changed copies of the archives into a new folder ([tools](../tools/README.md)). |
| Patch | A small file (`lol-patch-2`) listing changed bytes, the bytes they replace and the game it is for, made and applied by `tools/patch.py` ([patch format](formats/patch.md)). A *data patch* changes archives and tables; a *program patch* changes the game program and fits only the file with the recorded SHA-256. |
| Undo patch | The `undo.json` that `patch.py apply` writes beside the patched files; applied to the patched copy it gives back the original bytes. |
| Copy of the game | A separate copy of your game folder for trying changes. The tools never write into the game folder you give them. |

## This game

| Term | Meaning |
|------|---------|
| LoL2 | *Lands of Lore: Guardians of Destiny* (Westwood Studios, 1997, DOS/Windows). |
| DAT folder | The directory of this game's data files, which the tools read. Set `LOL2_DAT` to it. |
| MIX | Westwood archive: a u16 count, a u32 data size, 12-byte rows of key, offset and size, then the data. Almost all of this game's data lives in the 81 MIX files under `DAT/`; six more (`LOCAL`, `LOCALLNG`, `DMUSIC`, `SETUP`, `GLOBAL`, `CACHEBAK`) sit next to it ([MIX page](formats/mix.md)). |
| Cache | A large file the game writes when it runs, separate from the archives it shipped with. Here that file is `CDCACHE.MIX`. |
| Key, name hash | The number an archive stores instead of a name. It is a hash of the name. This game uses `ww_hash_v1` (`tools/lol2_westwood_hash.py`). |
| Level archive | `DAT/L<n>_<xx>.MIX`, one per level (15), e.g. `L1_DC` = level 1, Draracle's Caverns. |
| Geometry entry | The one entry in a level archive whose header starts with 18 and 5300; the level's regions, walls and floors. |
| Entity record | A 147-byte object record (135-byte body and a 12-byte name tag such as `B_HUMAN`). |
| Script stream | Levels run commands whose length is fixed per opcode. The native size table knows 37 opcodes, and 32 of them occur in the 15 levels. |
| Trigger | The record that says when an event starts. |
| Predicate | A test a script checks before it continues. |
| Geometry | The shape of a level: its floors, walls and openings. |
| AUD | Westwood's compressed audio. The samples use IMA ADPCM. |
| IMA ADPCM | A compressed sound encoding. This game's AUD samples use it. |
| VQA | Westwood's vector-quantized movie format. This game uses version 2. |
| WSA | An animation: a first picture, then the differences (deltas) to each next frame. |
| MIDI | A standard music file (`.mid`). The music tools can write one; they do not play it. |
| Chunk, FORM | A named block inside a larger file. FORM is the header some of this game's music files use. |
| `LOLG.DAT` | The game's main program despite its name: an MZ stub with a DOS/4G-style extender and a 32-bit LE program (signature `LE` at file offset 0x3BCB4 in the copy read). Addresses are cited as virtual addresses (VA). |
| Draracle | The first cave level (`L1_DC`) is the Draracle's cave; `tools/history/draracle/` holds the geometry and wall checks first written for it. |
| Region, portal | A part of a level the game tracks separately. Here it is a four-sided floor and ceiling polygon; a side that names a neighbour is a portal, and a side that does not is a wall ([geometry](formats/geometry.md)). Height values grow upward: the ceiling word is at least the floor word in 52,495 of 52,669 regions. |
| Connector, subdivision | Special region links that do not share the side's two vertices: short connector regions between rooms, and floor subdivisions owned by a parent region ([cave page](draracle-restoration.md)). |
| Room archive, WOM | One of the archives the executable opens by room name (46 names, plus `ARENA`); each carries a `WOMS\<ROOM>_.WOM` entry ([room archives](lol2-room-archives.md)). |
| Companion archive | `L<n>_<xx>I.MIX` next to a level archive: its movies and sounds. |
| VA | An address in the program after it is loaded. For this program's code, file offset = VA + 0x37000. A data address is an offset in the program's data object; file offset = data address + 0x1C1024 ([executable tables](lol2-executable-tables.md)). |
| Witness | A concrete sample (a record, file or capture) used to test a claim. |
| Pinned | A tool that checks the SHA-256 of its input and refuses other editions. |
| `ww_hash_v1`, `v2`, `crc`, `ts` | Variants of Westwood's archive name hash in `tools/lol2_westwood_hash.py`; LoL2 keys use `v1`. |
| Longplay | A full recorded playthrough of the original game, used only to place levels in story order; it is not published here. |
| ODF | A level's object definitions. Each record here is 147 bytes ([entity records](formats/entity-records.md)). |
| `.TE_` | A level's texture pack, stored under a name ending in `.TE_`. Inside the level MIX it is packed as LZO1X blocks ([texture container](formats/texture-container.md)). |
| LZO, LZO1X | A compression method. Packed textures need the system library `liblzo2` to unpack. |
| Actor | A creature placement. The schematic marks one with the letter A. |
| TRR | A message-table file (help, options, automap, credits, error text; [text tables](lol2-text-tables.md)). |
| HMI | The song format used for this game's music. The music tool writes these songs as standard MIDI ([music](lol2-music-2026-11.md)). |
| LSV | A per-level file (`.LSV`) stored with a save slot ([saves](lol2-save-format.md)). |
| Sphere | The game's name for a world area: archive paths begin `SPHERE1\`, `SPHERE2\` ...; `lol2_decompress_sphere.py` carries the name for historical reasons; it reads the `options.shp` shapes in `LOCAL.MIX`. |
| Cue, spoken cue | A cue is a 16-bit id the sound player takes. It selects one row, a named clip, of the 1,179-row sound bank in `LOCALLNG.MIX` ([sound cues](lol2-sound-cues.md)). A spoken cue is one of the 404 cue words in the speech cue table at the end of that bank; `lol2_inspect.py cue 161` prints word 161 and its bank row ([spoken lines](lol2-speech.md)). |
| Event group, stream number | A level has two command streams, 0 and 1. Region records name groups in stream 0 and object records name groups in stream 1. A group is the run of commands a trigger record starts, named by its offset in that stream: `--stream 1 --group 0x228e` is group 0x228E of stream 1 ([script format](lol2-level-script-format.md)). |
| UV | Texture coordinates: which point of a texture is drawn at a point of a wall or floor. How the game picks wall UVs is partly open (Q16). |
| Codebook | In a VQA movie, the table of small pixel blocks (vectors of 4 x 4 or 4 x 2 bytes) that each frame's pointer table picks from. A full book comes in `CBFZ` or `CBF0`; a new book may also arrive in parts (`CBPZ`, `CBP0`) over several frames ([VQA v2](lol2-vqa-v2.md)). |
| Item definition, identity | An item definition is one of the 170 item types: a 91-byte record in a `GLOBAL.MIX` entry. Its identity is the u32 at record +0x18, different in every record ([items](formats/items.md)). |
| `MIX+0x…`, `Slot+0x…` | How tool output names a place in a file. `MIX+0x6E7FF5` is a file offset in the named MIX archive (`L1_DC.MIX+0x6E7FF5` names the archive). `Slot+0x0180` is a file offset in a save slot. |
| Autosave | The save slot the game writes by itself, shown with the name `**AUTOSAVE**`. It has the same layout as a player's own saves ([save slots](lol2-save-format.md)). |
| NE, segment, resource | NE (New Executable) is the Windows program format of `SETUP.EXE`, which begins with a separate DOS (MZ) program. A segment is one of its five code or data blocks, each followed by a count and 8-byte records. A resource is one of the five data blocks at its end ([loose files](formats/loose.md)). |
| Texture container | A level's `SPHERE<n>\<LEVEL>\<LEVEL>.TE_` entry: a total decoded size, then LZO1X blocks of 1 MiB decoded each and a zero trailer. It holds the level's wall and floor textures ([texture container](formats/texture-container.md)). |

## Reader tools

| Term | Meaning |
| --- | --- |
| Level plan | An overhead drawing from the level's geometry. The HTML plan opens in a web browser and lets you choose a map feature to read its details. |
| Gate | A script condition that can control a level change. See [Progression](PROGRESSION.md). |
| Output folder | A directory you choose for the files a tool writes. The level and media tools use a new folder outside the game and the repository. |
| MKV | Matroska, the file container used for the movie conversion. It can hold video and audio in one file. |
| FFV1 | The lossless video encoding inside the converted MKV. |
| FFmpeg, FFprobe | Tools used to write the movie and count the frames and samples in the result. |
| PCM | Sound stored as a series of sample values. The WAV export writes those values without compression. |
| Kind 12 event 2 | A region event record with kind byte 12 and event byte 2. These numbers identify the rule the engine checks. See [script events](lol2-script-events.md). |
| Stream / group | One of the two stored command streams and the offset of the ordered commands within it. A group starts at the offset listed on the plan. |
| Selector | A marker in the exit table for paired tests of the same slot against 0 and 1. See [Progression](PROGRESSION.md#exit-commands). |

In the plan legend, a **collapsed portal side** borders a region whose floor and ceiling meet. The schematic marks it as a doorway candidate. See [walls](formats/walls.md).
