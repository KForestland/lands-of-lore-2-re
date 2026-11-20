# Patches

Small checked edits for a reader's own copy of the original game. A patch records the replacement bytes and a hash of the span it replaces. A patch must not remove or bypass a disc check, a serial check or any other copy protection, and none here does. The format and its limits are on the [patch format page](../docs/formats/patch.md). This folder has the list. It does not yet hold a patch file: the faults below are not a few proven bytes that these pages could show before and after in the running DOS 1.30 game.

The format is `lol-patch-3`. Each change lists its file, entry, offset, old span length and SHA-256, and new bytes. Keep `undo.json` private. It holds original game bytes from your copy.

These pages read DOS 1.30 (`LOLG.DAT` version string at file `+0x1C4714`, date `Dec 03 1997` at `+0x1C4749`). That build is already the patched retail DOS release. The open-question list does not name the scene faults below. Those questions are unread fields and producers. These pages did not find another retail fault, with a file and an offset, on the level pages.

How to start the game on a current machine is [Running](RUNNING.md).

## Already claimed by the 1.30 notes

The 1.06-to-1.30 notes name two gameplay fixes. Both are already claimed for this build. They are not repeated as new patches.

- Huline Temple altar. The note says that using more than one aloe and poison paint no longer locks out the lightning strike on the corpse. The Lands of Lore wiki Bugs page still says that selecting the bowl can create aloe and then block the caretaker action, and that an earlier save is the remedy. No further byte is isolated here. To see it, use the altar bowls in the Huline Temple.
- Cemetery barrel. The same note says the barrel in the Dracoid Cemetery can be pushed over and rolled down to the lower room in all circumstances. The wiki still says it sometimes will not tip, and gives human form, the top of the barrel, a clear path, or leaving and reloading. That is placement, not a located byte. No further byte change is isolated here.

## Quest-order reports

No few-byte script edit is isolated for these. The remedy the reports give is to keep the item, or to reload to before the choice.

- Daniel's blade. Walkthroughs say he drops the blade and the settlement gate wants it back. That is the order of the scene. No published byte edit was found.
- Silver leaf after the bracers. A GOG forum report (January 2023, "Dracoid cemetery bug") says the cemetery ghost is absent, and the silver leaf never appears, if the bracers were given to Dawn first. No byte is isolated here. To see the report, finish the ruins, give the bracers to Dawn, and return to the ghost's house.
- Belial's statue. The same report says the statue stuck in its courtyard, and that turning variable frame rate off let it move. The program stores the key `Video_Variable_Frame_Rate` at `LOLG.DAT+0x1C28BA`. No published byte edit of the program was found. The key is a setting in `options.ini`, not a patch.

## Tavern crash while Baccata speaks

The Lands of Lore wiki Bugs page and GOG support ("Lands of Lore 2 - crash while entering the Tavern") describe a memory failure when Luther enters the Huline village cantina and Baccata starts to speak. The failure text in this program is at `LOLG.DAT+0x1C5416` and begins `Memory allocation of`. These pages did not launch the game, so it did not see that line.

Two published remedies, re-read from this copy:

- Launch once with `-LOWMEM`, then save and start again without it. GOG support describes that switch. It is not a patch file. The characters `-LOWMEM` sit at `LOLG.DAT+0x1C53CD`. Startup code at analysis address `0x14EBDD` pushes that string and calls `0x15C5CC`. That routine calls `0x153C5C`, which walks the command text for those bytes. A nonzero result is stored in the three bytes at object-5 cells `0xB861`, `0xB862` and `0xB86C` (file `+0x1CC885`, `+0x1CC886` and `+0x1CC890`), which are zero in the stored program. A later test of `-8MB` (cell `0x1140`, file `+0x1C2164`) or `-16MB` (cell `0x1145`) also stores 1 at cell `0xB861`. At `0x9F1D8` a nonzero `0xB861` skips the following block. The same startup compares cell `0xB861` with zero and stores the opposite in the video-default byte at cell `0xBB5C`: the switch present leaves that byte 0.
- Change two bytes in `LOLG.EXE`. That file is the 2,847-byte DOS/4GW stub, not `LOLG.DAT`. One string begins at file `0x481`: `DOS4GVM=VirtualMemory:ON,VirtualSize:24M,SwapFileName:lolgswap.swp,SwapMin:20M,SwapInc:0`. The digits `24` are the bytes `32 34` at file `0x4A6` (decimal 1190) and `0x4A7`. The published edit stores `33 32` there, so the text reads `32M`. The length does not change. Those two bytes are characters in that string. They are not an instruction, so there is no instruction listing before and after: the stub reads the sentence. `LOLG.DAT+0x1E34E` is a different word, the option name `VirtualSize` beside `VirtualMemory` and `DeleteSwapFile`. It is not the number 24, and it is not part of this edit. `SETUPG.EXE` (2,262 bytes) carries its own copy of the same sentence, with `32 34` at file `0x466`. That file names `_SETUP.EXE` and `LOLG.DAT`. It is the setup stub. The tavern edit is only `LOLG.EXE`.

A patch file for this edit (one program change of two bytes, with the SHA-256 of this 2,847-byte `LOLG.EXE`) was made and applied and undone on a copy. It is not shipped yet: every patch here is tried in the running game first, and the crash has not been seen on this copy. Until then the two bytes above are the whole edit.

