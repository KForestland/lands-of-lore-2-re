# What's new

Newest first. One line per answered question, new tool or visible change. Details are on the linked pages; the counts are in the [rating](../README.md#rating).

## 19 November 2026

- **Files read to the last byte.** `lol2_loose.py` walks `AUTOPLAY.WAV` and `SETUP.EXE`, the two `DAT` files that are not MIX archives ([loose files](formats/loose.md)).
- **Counted rating.** The README and [STATUS](STATUS.md) show four counted lines instead of a percentage; [how we rate](HOW_WE_RATE.md) explains them.
- **Interface shapes (Q2, answered).** The `LOCAL.MIX` entry once read as room data is `options.shp`, the options-screen pictures ([shape format](formats/room-sections.md)).
- **Credits music (Q15, answered).** The last unnamed music key is `MUSIC\CREDITS.HMI`.
- **Compression (Q1).** Every place the program unpacks LZ77 data is identified, with its buffers ([compression](formats/compression.md)).
- **Scripts and levels (Q4, Q5, Q6, Q18).** Every level exit and its condition is listed, and every script group now has a known way in.
- **Items and spells (Q8, Q9).** The items that become "burnt" or "empty" after use are named through the program's own label table, and each kind of thrown or fired object's hit is traced ([items](lol2-item-handlers.md), [spells](lol2-spell-dispatch.md)).
- **Timers and saves (Q7, Q11).** How a save restores the game clock and how the menu pauses it; a table of every save section's reader and writer.
- **Textures, walls and movies (Q12, Q14, Q16, Q20).** Texture rows, wall spans with a replay of the original routine, movie pointer streams, and the shipped cache seed file.
- **Level-8 controls (Q17).** The two controls are joined to their geometry and the input path.
- **Pictures.** Two unreadable example images were removed; the level map is regenerated and compared by its check.
- **New checks:** `rating.py`, `example_images.py`, `lol2_item_labels.py`, `lol2_save_native.py`, `lol2_cache_seed.py`, and a Huline wall replay check.

## 18 November 2026

- **Running-game results.** The game clock's writer, a creature distance branch, the save rows after a pickup and the level-8 control objects were observed in the original game ([NEEDS_A_RUNNING_GAME](NEEDS_A_RUNNING_GAME.md)).
- **Guides.** [Start here](START_HERE.md), [how the game works](HOW_THE_GAME_WORKS.md), a [quick reference](QUICK_REFERENCE.md) and a [worked example](tutorial-one-event.md).
- **All 108 item-use handlers**, the spell payloads, spoken-line selection, texture flags and the CDCACHE files as run-time state.
