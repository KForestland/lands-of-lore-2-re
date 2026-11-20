# Patches

Small checked edits for a reader's own copy of the original game. A patch file holds the changed bytes and the expected old bytes, not a game file. A patch must not remove or bypass a disc check, a serial check or any other copy protection, and none here does. The format and its limits are on the [patch format page](../docs/formats/patch.md). This folder has the list. It does not yet hold a patch file: the faults below are not a few proven bytes that these pages could show before and after in the running DOS 1.30 game.

The file format, when a patch is added, is `lol-patch-2`. `kind` is `data` or `program`. Each change has `file`, `entry`, `offset`, `old` and `new`.

These pages read DOS 1.30 (`LOLG.DAT` version string at file `+0x1C4714`, date `Dec 03 1997`). That build is already the patched retail DOS release.

## Reports, and where each fault sits

- Cemetery barrel. The Lands of Lore wiki Bugs page says the barrel in the Dracoid Cemetery sometimes will not tip. The remedy given there is human form, the top of the barrel, a clear path, or leaving and reloading. That is level script and placement, not a located byte. The 1.30 notes say the barrel pushes. No further byte change is isolated here.
- Huline Temple bowl. The same page says selecting the bowl can create aloe and then block the caretaker action. The remedy given there is an earlier save. No byte is isolated here.
- Daniel's blade, the silver leaf after the bracers, and a key item that was never picked up. These are quest-order reports. The remedy is to keep the item available. No few-byte script edit is isolated here.
- Tavern crash while Baccata speaks. GOG support, "Lands of Lore 2 - crash while entering the Tavern", says to launch once with `-LOWMEM`. That is a launch switch, not a patch file. A GOG forum note, "Fix for Lands of Lore 2 Baccata Tavern Dialogue Crash", says to change two bytes in `LOLG.EXE`. On this DOS copy the extender stub is 2,847 bytes and the text `VirtualSize:24M` has `32 34` at file `0x4A6`. The published edit stores `33 32` there (`32M`). This pass did not reproduce the crash under DOSBox, so that program edit is not shipped here.
