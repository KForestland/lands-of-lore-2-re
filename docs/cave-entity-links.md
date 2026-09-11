# Cave entity source links

`catalogue_cave_entities.py` verifies the pinned L1_DC.MIX source entry
2971019266. Header +0x10 points to11 named147-byte definitions at27723;
+0x14 points to a340-byte table at27383. Header +0x48 is11, +0x4C is340.

Across all11 definitions, byte46 counts four-byte table entries and the
unaligned dword at55 gives their table-relative start. These partition
85 entries exactly, without overlap, gaps or leftover bytes. Byte47 is
separate: treating the complete word46 as the count fails for variants.
This corrects the older inferred `f23 low = entity slot` label for this
source fixture. Entry byte meanings still require native consumer tracing.

```sh
python3 tools/draracle/catalogue_cave_entities.py --game-root /path/to/lol2 --out /tmp/cave-entities
```

The tool also decodes all five mips of resource966 with the checked28E
row-span decoder and original palette. Visual inspection resembles a roach.
No named-definition-to-descriptor link, world scale or spawn is established.
Adjacent resources967 onward use1246 encoding; applying the scenery row
format to those would be incorrect. The generated review.html shows the
image and source definition table. Original data remains outside Git.

Validation:11 definitions,85 entries,340 table bytes,5 image mips;37 unit
tests pass, including overlap/tail rejection and byte47 separation. No live
capture or Godot enemy integration is claimed. Next trace the native table
consumer and1246 decoder before restoring creature animation and placement.
