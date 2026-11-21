# Patches

Small checked edits for a reader's own copy of the original game. A patch records the replacement bytes and a hash of the span it replaces. A patch must not remove or bypass a disc check, a serial check or any other copy protection, and none here does. The format and its limits are on the [patch format page](../docs/formats/patch.md). This folder has the list. The fault notes below are not a patch file. The optional intro skip is a separate comfort patch.

The format is `lol-patch-3`. Each change lists its file, entry, offset, old span length and SHA-256, and new bytes. Keep `undo.json` private. It holds original game bytes from your copy.

These pages read DOS 1.30 (`LOLG.DAT` version string at file `+0x1C4714`, date `Dec 03 1997` at `+0x1C4749`). That build is already the patched retail DOS release. The open-question list does not name the scene faults below. Those questions are unread fields and producers. These pages did not find another retail fault, with a file and an offset, on the level pages.

How to start the game on a current machine is [Running](RUNNING.md).

## Where each reported fault sits

One line per report. Script means a quest or scene order. State means a flag, a form, or where the player stands. Program means bytes in the executable or its stub. A few-byte patch is a short edit of those files. A setting and a reload are not that patch. The notes under the later headings are the same reports, written out.

- Cantina crash while Baccata speaks (wiki Bugs; GOG support). Program: `LOLG.EXE` digits `32 34` at file `0x4A6`, the `24` in `VirtualSize:24`. A few-byte patch can exist: those two digits become `33 32`. It was applied and undone on a copy and is not shipped. Folders 0035 and 0036 walked the same way before and after that edit, stayed outside, and showed no memory message. On 20 November 2026 the owner entered the tavern on the unpatched game (DOSBox 0.74-3, `memsize=30`) and it did not crash.
- Cemetery barrel will not tip (wiki Bugs). State: human form, the top of the barrel, a clear path, or leaving and reloading. No file offset. No few-byte patch.
- Temple bowl creates aloe and can block the caretaker (wiki Bugs). Script. The 1.30 notes already claim this fix. No further byte is isolated. No few-byte patch is attempted.
- Daniel's blade and the settlement gate (walkthroughs). Script: the order of that scene. No byte is isolated. No few-byte patch.
- Silver leaf missing after the bracers were given to Dawn (GOG forum, January 2023). State: that gift comes first. No byte is isolated. No few-byte patch.
- Belial's statue stuck in its courtyard (same GOG report). Program setting: `options.ini` key `Video_Variable_Frame_Rate` at `LOLG.DAT+0x1C28BA`. The reported remedy is turning that setting off. No program byte edit was found. No few-byte patch is attempted.

## Already claimed by the 1.30 notes

The 1.06-to-1.30 notes name two gameplay fixes. Both are already claimed for this build. They are not repeated as new patches.

- Huline Temple altar. The note says that using more than one aloe and poison paint no longer locks out the lightning strike on the corpse. The Lands of Lore wiki Bugs page still says that selecting the bowl can create aloe and then block the caretaker action, and that an earlier save is the remedy. No further byte is isolated here. To see it, use the altar bowls in the Huline Temple.
- Cemetery barrel. The same note says the barrel in the Dracoid Cemetery can be pushed over and rolled down to the lower room in all circumstances. The wiki still says it sometimes will not tip, and gives human form, the top of the barrel, a clear path, or leaving and reloading. That is placement, not a located byte. No further byte change is isolated here.

## Quest-order reports

No few-byte script edit is isolated for these. The remedy the reports give is to keep the item, or to reload to before the choice.

- Daniel's blade. Walkthroughs say he drops the blade and the settlement gate wants it back. That is the order of the scene. No published byte edit was found.
- Silver leaf after the bracers. A GOG forum report (January 2023, "Dracoid cemetery bug") says the cemetery ghost is absent, and the silver leaf never appears, if the bracers were given to Dawn first. No byte is isolated here. To see the report, finish the ruins, give the bracers to Dawn, and return to the ghost's house.
- Belial's statue. The same report says the statue stuck in its courtyard, and that turning variable frame rate off let it move. The program stores the key `Video_Variable_Frame_Rate` at `LOLG.DAT+0x1C28BA`. No published byte edit of the program was found. The key is a setting in `options.ini`, not a patch.

### Retail script checks

A geometry patch can edit the five-byte rows in the existing predicate
table. Keep the table offset, row count and entry length. Edited rows must
use the documented operators and operand types. Recursive references must
stay in the table and terminate. Test the original and the edited script in
their matching game states before releasing a patch.
[Predicate fields](../docs/lol2-script-events.md#predicates-and-shared-bytes)

| Report | DOS 1.30 records | What would settle the report |
|---|---|---|
| Cemetery barrel | `L10_DC.MIX+0xD15B4C` names `Barrel_in_ready_position`. The level's predicate rows and framed commands have no direct reference to that indexed local byte. | Record the barrel object, player form and positions just before a failed push and a successful push in 1.30. |
| Temple bowl | Empty-hand actions on prop 82 at `L14_HT.MIX+0xB31894` and `+0xB318A2` advance its state 1 → 2 → 3 and each grant aloe. Separate props 285 and 370 increment local bytes 9 and 8, with continuation predicates at `+0xB487AD` and `+0xB487A3` that test for exactly 2. Prop 285 also changes its own state, which gates repeat use. | Record which prop is used, the two counters and the corpse scene when repeating aloe and paint in a 1.30 save. |
| Daniel's blade | The placed item at `L8_SJ.MIX+0xCEB6E4` uses the War blade identity. Separate scene groups store `GV_DANIEL_KILLED` at `+0xCD51E8` or `GV_DANIEL_SPARED` at `+0xCD51AC`. | Use a save in which the correct blade is still present and the intended handover fails. |
| Silverleaf after giving away the bracers | Bracer removal clears shared byte 37. Region 3754 at `L10_DC.MIX+0xC8E432` uses that byte to admit the urn and ashes scene. The separate bush path at `+0xC8E45C` and `+0xC8E46A` checks shared byte 16 and local byte 10. | Compare the priest scene and the bush on a save made before entering region 3754, with the urn and ashes already obtained and the bracers given away. |

## Tavern crash while Baccata speaks

The Lands of Lore wiki Bugs page and GOG support ("Lands of Lore 2 - crash while entering the Tavern") describe a memory failure when Luther enters the Huline village cantina and Baccata starts to speak. The failure text in this program is at `LOLG.DAT+0x1C5416` and begins `Memory allocation of`. These pages did not launch the game, so it did not see that line.

Two published remedies, re-read from this copy:

- Launch once with `-LOWMEM`, then save and start again without it. GOG support describes that switch. It is not a patch file. The characters `-LOWMEM` sit at `LOLG.DAT+0x1C53CD`. Startup code at analysis address `0x14EBDD` pushes that string and calls `0x15C5CC`. That routine calls `0x153C5C`, which walks the command text for those bytes. A nonzero result is stored in the three bytes at object-5 cells `0xB861`, `0xB862` and `0xB86C` (file `+0x1CC885`, `+0x1CC886` and `+0x1CC890`), which are zero in the stored program. A later test of `-8MB` (cell `0x1140`, file `+0x1C2164`) or `-16MB` (cell `0x1145`) also stores 1 at cell `0xB861`. At `0x9F1D8` a nonzero `0xB861` skips the following block. The same startup compares cell `0xB861` with zero and stores the opposite in the video-default byte at cell `0xBB5C`: the switch present leaves that byte 0.
- Change two bytes in `LOLG.EXE`. That file is the 2,847-byte DOS/4GW stub, not `LOLG.DAT`. One string begins at file `0x481`: `DOS4GVM=VirtualMemory:ON,VirtualSize:24M,SwapFileName:lolgswap.swp,SwapMin:20M,SwapInc:0`. The digits `24` are the bytes `32 34` at file `0x4A6` (decimal 1190) and `0x4A7`. The published edit stores `33 32` there, so the text reads `32M`. The length does not change. Those two bytes are characters in that string. They are not an instruction, so there is no instruction listing before and after: the stub reads the sentence. `LOLG.DAT+0x1E34E` is a different word, the option name `VirtualSize` beside `VirtualMemory` and `DeleteSwapFile`. It is not the number 24, and it is not part of this edit. `SETUPG.EXE` (2,262 bytes) carries its own copy of the same sentence, with `32 34` at file `0x466`. That file names `_SETUP.EXE` and `LOLG.DAT`. It is the setup stub. The tavern edit is only `LOLG.EXE`.

A patch file for this edit (one program change of two bytes, with the SHA-256 of this 2,847-byte `LOLG.EXE`) was made, and applied and undone on a copy. It is not shipped. On 20 November 2026 the owner of this copy loaded a game-written save in the Huline village and walked into the tavern on the unpatched game (DOSBox 0.74-3, `memsize=30`): the scene played, with no crash and no memory message. So on that setup the fault does not occur, and the patch has nothing to fix there. What could still show it: a DOSBox setup with less memory than `memsize=30`, or a real DOS machine with less extended memory, or the Windows version of the game, which this page does not cover. If you see the memory message in the cantina, the two bytes above are the published edit; please report the setup.

## Comfort

Optional changes of this program. They are not mixed with the tavern note, and they are not mixed with each other. A patch is written only where one small edit has a single on or off result. A speed or a time with no chosen new number is described and left unpatched.

### Intro movies

Startup plays the opening Westwood card, the title clip, and the game intro, then goes on. The patch [intro-skip.json](intro-skip.json) is two jumps, so those are skipped even when `Run_Intro` is `On` and even when `-INTRO` is present.

The title clip is `OUTTAKES\TITLE_E.VQA` at file `+0x1C5499`. Analysis `0x14F014` tests that name, and `0x14F02C` calls the opener `0xCF3C0`. The command `-MIJAS` at file `+0x1C5492` is tested at `0x14F003`. A hit jumps to `0x14F034` and the title is not opened. The patch takes that same jump.

Title test at `0x14F012`, file `+0x186012` (decimal 1597458). Only the first byte changes. The `20` that follows is already the distance, so the patch file stores that one byte.

| | Bytes | Instruction |
| --- | --- | --- |
| before | `75 20` | `jne 0x14F034` |
| after | `eb 20` | `jmp 0x14F034` |

The game intro is scene 0, `outtakes\lolg.vqa`. The calls are `0x14F08F` and `0x14F0C6`, both to `0xCF2B4`. That block runs when `-INTRO` (file `+0x1C54BA`) is on the command, tested at `0x14F034`. If the switch is absent, byte `0x22399` still sends it there when the byte is not zero (`0x14F045`). That byte is set at `0xCBACB` from options.ini `Run_Intro`. When the switch is absent and the byte is zero, `0x14F04C` jumps to `0x14F0E1` and neither intro call runs. The second change is that jump.

Intro test at `0x14F041`, file `+0x186041` (decimal 1597505). The five new bytes replace `85 C0 75 0D 80`. The rest of the old compare is not reached. `0x14F0E1` is `mov ebx, 1`, the skip tail this program already uses.

| | Bytes | Instruction |
| --- | --- | --- |
| before | `85 C0` / `75 0D` / `80` | `test eax, eax` / `jne 0x14F052` / start of `cmp` |
| after | `E9 9B 00 00 00` | `jmp 0x14F0E1` |

The patch was applied and undone on a copy of this `LOLG.DAT`. The restored file matched the original. Two later launches watched it, each on its own fresh copy. The unpatched copy showed the Westwood card, then the title card, then the main menu. The patched copy showed the DOSBox card and then the main menu. The Westwood card, the title card, and the intro are not in that set.

On 20 November 2026 folder 0042 was unpatched and folder 0043 had only this patch. After New Game and Normal, the opening movie played the same way on both copies: the same three scenes, and the end mean difference is 5.5 because the frame timing differs. The patch does not stop a new game or its opening movie. Player control was not reached in two minutes, so this run does not test walking. Folders 0039, 0040 and 0041 stopped before that movie and are not this pair.

```sh
python3 tools/patch.py apply --data "GAME" --out "../lol2-intro-patched" patches/intro-skip.json
python3 tools/patch.py apply --data "GAME COPY" --out "../lol2-intro-restored" "../lol2-intro-patched/undo.json"
```

Copy the patched `LOLG.DAT` into a copy of the game. Keep `undo.json` with that copy.

### Text and message display time

No options key sets how long a message stays. The script opcode that multiplies its own byte by 60 is not a checked message-time edit, and the countdown that clears the message line is not one immediate. No patch.

### Mouse turn speed

`Mouse_Sensitivity` is at file `+0x1C2A7F`. The reader clamps it to 0 through 10. The turn path indexes eleven immediates, one per step: `0x460000`, `0x500000`, `0x5A0000`, `0x6E0000`, `0x780000`, `0x820000`, `0x8C0000`, `0x960000`, `0xA00000`, `0xAA0000`, `0xB40000`, stored from analysis `0x5FB38`. The setting already picks the step. No new speed was chosen, so no patch.

### Frame-rate cap

The frame update compares the sample count with `0x1E0` at file `+0x117C11` and the elapsed step with `0x80000` at file `+0x117C62`, and stores the same immediate when the compare clamps. A small edit would replace both copies of one immediate. No new cap was chosen, so no patch. `-SPEED` is a debug gate later in that function. It is not this cap.

