# What's new

Newest first. One line per question worked on, new tool or visible change; each question bullet gives its state. Details are on the linked pages; the counts are in the [rating](../README.md#rating).

## 19 November 2026

- **Glossary.** The [glossary](GLOSSARY.md) gives a one-line meaning to each term on the front page, the start page and the cookbook. A word shared with the other two games has the same meaning there. The rating still counts the glossary as a page, but not its label words.
- **Link check.** `doc_links.py` resolves every relative link and anchor in the README and the docs, and `check_all.py` runs it.
- **Files read to the last byte.** `lol2_loose.py` walks `AUTOPLAY.WAV` and `SETUP.EXE`, the two `DAT` files that are not MIX archives. The 41,584-byte DOS part of `SETUP.EXE` is counted by its length, not read ([loose files](formats/loose.md)).
- **Counted rating.** The README and [STATUS](STATUS.md) show four counted lines instead of a percentage; [how we rate](HOW_WE_RATE.md) explains them.
- **Interface shapes (Q2, answered).** The `LOCAL.MIX` entry once read as room data is `options.shp`, the options-screen pictures ([shape format](formats/room-sections.md)).
- **Credits music (Q15, answered).** The last unnamed music key is `MUSIC\CREDITS.HMI`.
- **Compression (Q1, mostly answered).** Every place the program unpacks LZ77 data is identified, with its buffers ([compression](formats/compression.md)). The original file names for the generic loaders remain open.
- **Scripts and levels (Q4, Q5, Q6, Q18, all mostly answered).** Every level exit and its condition is listed, and every script group now has a known way in. Open: Q6 plot branches outside the 72 exits, the Q18 input gesture (not yet confirmed in play), and some Q4 receivers and Q5 callers.
- **Items and spells (Q8, Q9, both mostly answered).** The items that become "burnt" or "empty" after use are named through the program's own label table, and each kind of thrown or fired object's hit is traced ([items](lol2-item-handlers.md), [spells](lol2-spell-dispatch.md)). Open: what instance +5 means in play (Q8) and what starts timed message 0x26 (Q9).
- **Timers and saves (Q7, Q11, both mostly answered).** How a save restores the game clock and how the menu pauses it; a table of every save section's reader and writer. The first countdown after resume (Q7) and some save header fields (Q11) remain open.
- **Textures, walls and movies (Q12, Q14, Q16, Q20, all mostly answered).** Texture rows, wall spans with a replay of the original routine, movie pointer streams, and the shipped cache seed file. Open: two exceptional movie frames (Q12), the live `0x02AC` wall branch (Q14), the Huline Temple quads on screen (Q16) and which build supplied the 12 differing seed sizes (Q20).
- **Level-8 controls (Q17, partly answered).** The two controls are joined to their geometry and the input path. Which surfaces the player sees and clicks remains open.
- **Pictures.** Two unreadable example images were removed; the level map is regenerated and compared by its check.
- **New checks:** `rating.py`, `example_images.py`, `lol2_item_labels.py`, `lol2_save_native.py`, `lol2_cache_seed.py`, and a Huline wall replay check.

## 18 November 2026

- **Running-game results.** The game clock's writer, a creature distance branch, the save rows after a pickup and the level-8 control objects were looked at in the original game; the clock writer and the pickup's save rows answer their probes, and the creature branch and the level-8 controls are partial runs (Q10, Q17 partly answered) ([NEEDS_A_RUNNING_GAME](NEEDS_A_RUNNING_GAME.md)).
- **Guides.** [Start here](START_HERE.md), [how the game works](HOW_THE_GAME_WORKS.md), a [quick reference](QUICK_REFERENCE.md) and a [worked example](tutorial-one-event.md).
- **All 108 item-use handlers**, the spell payloads, spoken-line selection, texture flags and the CDCACHE files as run-time state.
