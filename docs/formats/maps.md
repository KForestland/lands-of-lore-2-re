# Level maps

**What:** a level's map follows from its [geometry](geometry.md): each region is a four-sided polygon over the vertex table, and its neighbour words say which sides are walls and which are open. `tools/lol2_level_map.py` draws this as a top-down picture, with north up:
- each region is filled with a shade of its floor height (darker = higher);
- wall sides are dark lines;
- portal sides are light lines.

The picture is a plot of numbers from the level data entry and contains no game pixels.

```bash
python3 tools/lol2_level_map.py --data <DAT> --level 1 --size 900 --out l1_map.png   # the picture below
python3 tools/lol2_level_map.py --check --data <DAT>
```

**CONFIRMED** (re-run 2026-11-18): the 15 levels hold 52,669 region polygons, and each one has four distinct corners inside the vertex table.

## Worked example

![L1_DC regions drawn from the region table](../images/l1_dc_regions.png)

*L1_DC: 1,954 regions with floor heights from −1000 to 580. The level runs as one long cave from south to north.*

Following the portal links splits L1_DC into 9 groups that no portal connects (listed in the [level sheet](../levels/L1_DC.md), section "Regions and portals"):
- the main cave, 1,933 regions;
- the square at the top right, 14 regions, whose interior lines are portals between its own regions;
- 7 single regions, the small dark blocks.

How the game reaches the separate groups is not traced. The [level sheet](../levels/L1_DC.md) lists the exits and the objects that start them.

## Not covered

- **The game's own automap markers are CONFIRMED.** The opcode arm at `0x64DB7` marks a 12-byte input row; the map builder iterates those rows at `0x145F2C` and emits six-byte records. The [L66 save row](../lol2-save-field-witnesses.md#native-field-and-payload-cross-reference) gives the activated bit and field sources. **UNCONFIRMED.** Which region fields the original uses for visited-area shading. Trace the region-plane reads from the map update called at `0x146268`.
- **Several floors over one spot:** levels with storeys, such as the Huline Temple and the Hive, overlap in a top-down picture. Separating them needs the drawer's portal rules ([Q16](../OPEN_QUESTIONS.md)).
