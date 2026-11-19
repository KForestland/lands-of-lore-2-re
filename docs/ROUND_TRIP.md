# Round-trip proof for LoL2

Five writers read the original DOS 1.30 files, build a replacement in memory and compare it with the original. Nothing is written to disk. "Byte-identical" means the rebuilt file equals the original file. "Decode-identical" means the rebuilt compressed data reads back to the same bytes as the original, while the compressed bytes themselves may differ.

| Writer | What is rebuilt | Comparison | Counts |
|---|---|---|---|
| `lol2_mix_writer.py` | MIX archives from their directory rows | Byte-identical | 81 archives in `DAT` and the 6 shipped beside it, 3,463 rows; `CDCACHE.MIX` left out |
| `lol2_westwood_writer.py` | Westwood LZ77 streams, re-encoded with a new encoder | Decode-identical; 1 of 37 shapes, 20 of 640 deltas and 0 of 15 texture streams also match the stored bytes | 37 compressed `options.shp` shapes, 640 WSA deltas in 21 panels, 15 `global.tex` texture streams |
| `lol2_save_writer.py` | Game-written save slots from their fields | Byte-identical; the stored LZO chunks are copied, so no compressor is tested | 30 saves and 154 level blocks in the working installation, 27 and 149 in the reference copy (your saves give other counts) |
| `lol2_level_writer.py` | Command streams, event pools and predicate rows of the 15 level MIXes from their parsed fields | Byte-identical archives, but only 559,799 of 164,076,323 bytes (0.34 %) are in rebuilt sections; geometry, placements, textures and the other members are copied, and 66,079 unmapped record bytes plus one unreferenced L12 pair are copied inside the rebuilt sections | 42,594 commands, 9,678 group heads, 22,976 distinct event records (17,372 object, 5,604 region), 5,084 terminators, 3,825 predicate rows |
| `lol2_text_writer.py` | TRR message tables from their parsed IDs and strings | Byte-identical; count, IDs, offset directory and NUL terminators are regenerated, message bytes come from the parsed strings | All 8 retail tables: 3 loose (`CREDITS`, `ERRTEXT`, `OPTTEXT`), 1 in `MOVIES.MIX`, 4 in `LOCALLNG.MIX`; 988 messages |

## MIX

**CONFIRMED.** The writer emits the u16 entry count at +0, the u32 data size at +2, the 12-byte rows from +6 in their stored order (key, offset from the start of the data, size), then the data with each payload at its stored offset. The payloads are not in row order in 82 of the 87 archives, so the writer keeps each row's offset. The shipped archives have no gaps, so the zero fill between payloads is exercised only by the synthetic test. The game writes `CDCACHE.MIX` when it runs, so it is not an original to compare against. [MIX writing](formats/mix.md#writing) · [Cache initializer](lol2-cache-initializer.md)

## Westwood LZ77

**CONFIRMED.** The decoder at `0x158D58` reads the first source byte at `0x158D6C`. Zero selects relative long back-references (a distance back from the write position) and is consumed; any other value is the first command, and long back-references are then offsets from the start of the output. The encoder writes literals, fills and long back-references in either mode. The writer rebuilds the `options.shp` size fields and the WSA frame offsets, then re-reads every stream through the decoder. The 15 texture streams are those named by the table at `LOCAL.MIX+0x339FA5`. All the measured original streams use the absolute mode; the relative mode is covered by the synthetic tests. This proves that the format can be written, not that the original compressor is reproduced. VQA packets are not part of this check. [Compression commands](formats/compression.md#westwood-lz77-with-a-mode-byte) · [Options shapes](formats/room-sections.md)

## Save slots

**CONFIRMED.** The writer reads each slot into fields and writes it again. It regenerates the total size at +0x2C, the global section and level offsets from +0x18E and the level lengths at +0x20A–0x259. Each nonempty level block gets its total size, the 68 section starts at block +0x0D8 and the 68 expanded lengths at +0x1E8. Each LZO chunk gets its `u32 raw_size, u32 packed_size` header back and keeps its stored bytes. The rebuilt slot is then read back and its preview, compressed global sections and compressed level sections are decoded. [Slot header and directory](lol2-save-format.md#slot-header-and-directory) · [Level blocks](lol2-save-format.md#level-blocks) · [LZO chunks](lol2-save-format.md#compression-and-worked-example)

## Level scripts

**CONFIRMED.** Each command is read into opcode, selector, target and the named fields for its opcode, and written back from them; each event record is read into its kind and named fields and gets its length byte back. Records keep their stored pool offsets, and a mutated command or predicate re-reads with the change through `lol2_export_scripts.py` and `lol2_progression.py`. Only the script sections are rebuilt, so this proves their layout, not the geometry or textures. The two bytes `02 00` at `L12_CM.MIX+0x967D14` (region pool +0x394) are referenced by no descriptor, command or record and are copied. [Writing the stored fields](lol2-level-script-format.md#writing-the-stored-fields)

## Text tables

**CONFIRMED.** A TRR is a u32 count, the u32 message IDs, then count + 1 u32 offsets (counted from +4), then the NUL-terminated messages. The writer rebuilds the whole table from (ID, message) rows; IDs may repeat and be sparse. It finds the three loose tables beside `DAT` and the five stored inside MIX archives.

## Run the checks

```bash
python3 tools/lol2_mix_writer.py --data "$LOL2_DAT" --check
python3 tools/lol2_westwood_writer.py --data "$LOL2_DAT" --check
python3 tools/lol2_save_writer.py --data "$LOL2_DAT" --check
python3 tools/lol2_level_writer.py --data "$LOL2_DAT" --check
python3 tools/lol2_text_writer.py --data "$LOL2_DAT" --check
python3 -m unittest tests.test_round_trip tests.test_level_text_write
```

All five run in `tools/check_all.py`; none has an output option. The save writer reads the `SAVEGAME` folder beside `DAT`, or one slot you name; with no saves there it checks only a synthetic slot. The unit tests use synthetic archives, streams and slots and need no game files.
