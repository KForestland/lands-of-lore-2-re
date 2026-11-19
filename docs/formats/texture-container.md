# Level texture container (.TE_)

**What:** each level archive holds `SPHERE<n>\<LEVEL>\<LEVEL>.TE_`, the level's wall and floor textures, compressed in LZO1X blocks. Full notes (blob header, sections, the ten raw flags, the movie-name records): [lol2-level-texture-container.md](../lol2-level-texture-container.md). Tool: `tools/lol2_texture_container.py` (needs the system `liblzo2`).

## Layout

```
uint32 total decoded size
repeat until the total is reached:
    uint32 compressed size
    LZO1X block (1 MiB decoded, the last block the remainder)
uint32 0   (trailer)
```

## Worked example

`L1_DC.MIX` entry 2 (key 0xB12F2907 = `ww_hash_v1("SPHERE1\L1_DC\L1_DC.TE_")`, 7,091,936 bytes) starts `14 fb c6 00  d7 22 06 00`: total decoded size 0xC6FB14 = 13,040,404 bytes, then the first block's compressed size 0x622D7 = 402,135 bytes. Thirteen blocks follow (12 of 1 MiB and the remainder), then the 4-byte zero trailer, which ends exactly at the entry's last byte. A run can store that decode in `CDCACHE.MIX`; the offset is run-time state ([MIX](mix.md)).

## Open

Non-raw texture payloads (layout open), including flag `0x1246` ([Q14](../OPEN_QUESTIONS.md)); wall spans and UVs ([Q16](../OPEN_QUESTIONS.md)). The ten raw flags and the 22-byte `.vqa` name records are confirmed on the level containers.
