# MIX archives

**What:** Westwood's archive format. Almost all game data sits in MIX files: 81 in `DAT/` (levels, rooms, global data) and 7 in the game folder next to `DAT/` (`LOCAL.MIX`, `LOCALLNG.MIX`, `DMUSIC.MIX`, `SETUP.MIX`, `GLOBAL.MIX` (a byte-identical copy of `DAT/GLOBAL.MIX`), `CACHEBAK.MIX` and `CDCACHE.MIX`). Entry names are not stored; each entry is found by a 32-bit key computed from its name ([name hash](#keys)).

**Read:** the English GOG release (88 archives). Tools: `tools/lol2_mix_parser.py`, `tools/lol2_source_format.py` (strict reader), `tools/lol2_westwood_hash.py`.

## Layout

| Offset | Type | Meaning |
|--------|------|---------|
| 0 | uint16 | entry count n |
| 2 | uint32 | data size (bytes after the index) |
| 6 | n x 12 bytes | index rows: uint32 key, uint32 offset (from the start of the data), uint32 size |
| 6 + 12n | data size | entry data |

All little-endian. The file is exactly 6 + 12n + data size bytes; entries lie inside the data and do not overlap. Index rows are sorted by key read as a **signed** 32-bit number. CONFIRMED on 87 of the 88 archives: `lol2_mix_parser.py --check`, run once with `--data` on `DAT/` (81/81, signed order 81/81) and once on the game folder (6/7, signed order 6/6); unsigned order holds in only 21 of the 87. The exception is `CDCACHE.MIX`: it has the same 131-byte header as `CACHEBAK.MIX` (5 entries, 65 data bytes) but is about 90 MB long; the bytes after the index are not covered by it. They include the decoded level texture blobs: the LZO-decoded `L1_DC` texture container (13,040,404 bytes) is byte-identical to `CDCACHE.MIX` from file offset 5,070, and `L20_BB`'s (28,451,111 bytes) from offset 13,045,474 (re-checked 2026-11-18 with `lol2_texture_container.py blob`). How the cache indexes them is open ([Q20](../OPEN_QUESTIONS.md)). The signed order fits a binary search over signed keys; the lookup routine in `LOLG.DAT` was not traced here (UNCONFIRMED).

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

- Names for most entries ([Q3](../OPEN_QUESTIONS.md) concerns the room count).
- The layout of `CDCACHE.MIX` beyond its index ([Q20](../OPEN_QUESTIONS.md)).
