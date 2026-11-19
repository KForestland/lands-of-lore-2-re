# MIX archives

**What:** Westwood's archive format. Almost all game data sits in MIX files: 81 in `DAT/` (levels, rooms, global data) and 6 in the game folder next to `DAT/` (`LOCAL.MIX`, `LOCALLNG.MIX`, `DMUSIC.MIX`, `SETUP.MIX`, `GLOBAL.MIX`, which is a byte-identical copy of `DAT/GLOBAL.MIX`, and `CACHEBAK.MIX`). Entry names are not stored; each entry is found by a 32-bit key computed from its name ([name hash](#keys)). The installer also ships `CDCACHE.LS_` beside those archives. `CDCACHE.MIX` and `CDCACHE.LST` are written when the game runs.

**Read:** the English GOG release (88 archives). Tools: `tools/lol2_mix_parser.py`, `tools/lol2_source_format.py` (strict reader), `tools/lol2_westwood_hash.py`, `tools/lol2_mix_writer.py` (writer).

## Layout

| Offset | Type | Meaning |
|--------|------|---------|
| 0 | uint16 | entry count n |
| 2 | uint32 | data size (bytes after the index) |
| 6 | n x 12 bytes | index rows: uint32 key, uint32 offset (from the start of the data), uint32 size |
| 6 + 12n | data size | entry data |

All little-endian. The file is exactly 6 + 12n + data size bytes; entries lie inside the data and do not overlap. Index rows are sorted by key read as a **signed** 32-bit number. CONFIRMED on 87 of the 88 archives: `lol2_mix_parser.py --check`, run once with `--data` on `DAT/` (81/81, signed order 81/81) and once on the game folder (6/7, signed order 6/6); unsigned order holds in only 21 of the 87 (the same check prints both counts). The exception is `CDCACHE.MIX`, and it is not shipped data.

`CACHEBAK.MIX` is 131 bytes, dated with the install (2024-01-07). It is 5 index rows (each entry 13 bytes) and then five copies of the 13 bytes `ECHO is OFF` plus CR LF. `CDCACHE.LS_` is 4,008 bytes and has the same install date. It is a name index, not a MIX archive: the first u32 is 168, the end of a table of 21 slots (a u32 record offset and a u32 tag). Those slots cover 15 unique records of 256 bytes, one per level texture. The name is a NUL-terminated string at byte 8. A state dword and a length dword sit at byte `0xD8`. A pointer dword sits at byte `0xE8`. Every state in the shipped file is `0xFFFFFFFF` (-1).

`CDCACHE.MIX` and `CDCACHE.LST` are written when the game runs. What they hold depends on that run, so a directory measured in one copy is not the format. On the copy read for this note (both files dated 2026-10-20), `CDCACHE.MIX` is 90,037,470 bytes. Its first 66 bytes are the `CACHEBAK.MIX` header, including the declared data size of 65, but the 65 bytes are not the `ECHO is OFF` text. `CDCACHE.LST` has the same 15-record shape. Three records are state 2 and the other 12 are state -1:

| Record name | State | Pointer | Length |
|---|---:|---:|---:|
| `sphere3\l20_bb\l20_bb.te_` | 2 | 5,070 | 28,451,111 |
| `sphere1\l1_dc\l1_dc.te_` | 2 | 28,456,181 | 13,040,404 |
| `sphere1\l3_dh\l3_dh.te_` | 2 | 41,496,585 | 10,799,733 |

The same three offsets appear in the allocator rows of this copy: the [native initializer](../lol2-cache-initializer.md) puts a 4-byte marker at file offset 66 and 25-byte rows from offset 70. A fourth record on this copy, at file offset 52,296,318 for 37,703,682 bytes, is not a state-2 name. The shipped `CDCACHE.LS_` pointers and lengths are not these values: its `l1_dc` pointer is 5,066, and its `l20_bb` length is 27,801,780. Another written copy (the reference installation, files dated 2026-04-04) differs: two state-2 records, `l1_dc` at 5,070 and `l20_bb` at 13,045,474, and its third 25-byte record is (41,496,585, 48,503,415). These numbers differ between copies. The [native initializer](../lol2-cache-initializer.md) identifies the marker, allocator row layout and 15 shipped lengths. The parser in `tools/history/draracle/lol2_cache_named_wall_fixture.py` reads the 256-byte records.

## Writing

`tools/lol2_mix_writer.py` writes an archive from (key, offset, payload) rows and the data size: the index rows in the order given, then the data with each payload at its offset and any byte no row covers set to zero. It rejects a row outside the data and two rows that overlap.

**CONFIRMED** on the 87 shipped archives: `lol2_mix_writer.py --check --data DAT/` reads each archive, writes it again from its own rows in memory and compares. All 81 in `DAT/` and the 6 shipped ones beside it are byte-identical, 3,463 rows, and the strict reader sees the same rows in the copy. Nothing is written to disk. Two measurements on the same 87 archives (independent script over `lol2_mix_parser.read_mix_with_hashes`, 2026-11-19):

- **Row order is not data order.** Rows follow signed key order (above); the payloads sit in another order in 82 of the 87 archives, so a writer must keep each row's offset and may not lay payloads out in row order. `DAT/L1_DC.MIX` in the [worked example](#worked-example) is one: entry 2 is the first in the data.
- **No vacant bytes.** No row is empty, no two rows overlap, there is no gap between payloads, the first starts at data offset 0 and the last ends at the data size: the check prints 0 zero-padding bytes. The writer's zero fill is therefore exercised only by the synthetic test (`tests/test_round_trip.py`, a gap before, between and after two out-of-order rows), not by shipped data.

`CDCACHE.MIX` is left out of the check. The game writes it when it runs, and its contents depend on that run (below), so it is not an original to compare against.

## Keys

The key is `ww_hash_v1` of the entry name in upper case, Westwood's rolling hash of the TD/RA era: the name is taken 4 bytes at a time as a little-endian word and accumulated with a rotate-left-by-1 and add (`tools/lol2_westwood_hash.py`). CONFIRMED on the data with names the game uses: `SPHERE<n>\<LEVEL>\<LEVEL>.TE_` is a key in 15/15 level archives and `WOMS\<ROOM>_.WOM` in 47 room archives (`lol2_westwood_hash.py --check`). Other names are not known yet; most entries are identified by content.

## Worked example

`DAT/L1_DC.MIX` (7,424,548 bytes) starts:

```
03 00   fa 49 71 00   02 28 16 b1  26 c1 70 00  d4 88 00 00   …
```

| Bytes | Meaning |
|-------|---------|
| `03 00` | 3 entries |
| `fa 49 71 00` | 0x7149FA = 7,424,506 bytes of data = 7,424,548 − 6 − 3 x 12 |
| `02 28 16 b1` | entry 0 key 0xB1162802 |
| `26 c1 70 00` | entry 0 offset 0x70C126 = 7,389,478 in the data, i.e. file offset 7,389,478 + 42 = 7,389,520 |
| `d4 88 00 00` | entry 0 size 0x88D4 = 35,028 |

The three entries sit at file offsets 7,389,520 (35,028 bytes), 7,091,978 (297,542 bytes) and 42 (7,091,936 bytes). Entry 2's key, 0xB12F2907, is `ww_hash_v1("SPHERE1\L1_DC\L1_DC.TE_")`: it is the level's texture container ([lol2-level-texture-container.md](../lol2-level-texture-container.md)).

## Open

- Names for most entries ([Q3](../OPEN_QUESTIONS.md) concerns how `ARENA.MIX` is opened).
- Which original edition supplied the 12 older lengths in `CDCACHE.LS_` that differ from the shipped bank headers ([seed comparison](../lol2-cache-initializer.md#shipped-lengths-compared-to-shipped-banks)).
