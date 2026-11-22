# DOS 1.30 setup files and tested settings

Read this against your own copy. **Tried here** identifies a recorded run. **From files** identifies a setting read from the installed files. **Reported elsewhere** identifies a setting described in the supplied notes or by another player.

The retail build in that tree is DOS 1.30. `LOLG.DAT` is 1,977,007 bytes. The version string `DOS 1.30` is at file `+0x1C4714` and the date `Dec 03 1997` is at `+0x1C4749`.

## Setup tried here

- **Tried here, folders 0042 and 0043.** DOSBox used `memsize=30`, `cycles=fixed 140000` and `LOLG.EXE -CD ..` from the installed game layout. Both copies reached the menu and played the opening movie after New Game and Normal. Audio output was disabled with `nosound=true` and `mididevice=none` for these runs. See the [run notes](README.md).
- **Tried here, folders 0033 and 0034.** The original DOS program loaded the Huline village save. Left and Up turned and moved the party outside the tavern. The owner also entered the tavern on an unpatched DOSBox 0.74-3 copy with `memsize=30` on 20 November 2026. The no-crash result applies to that setup.

## Which programs are which

**From files.** These are the program formats and the files they name.

| File | What it is | Role |
| --- | --- | --- |
| `LOLG.EXE` | 2,847-byte DOS MZ stub | Starts the DOS game. It is the DOS/4GW loader, not the game code. |
| `LOLG.DAT` | DOS LE image, DOS/4GW embedded | The DOS game program. |
| `SETUPG.EXE` | 2,262-byte DOS MZ stub | Names `_SETUP.EXE` and `LOLG.DAT`. Setup, not the cantina edit. |
| `_SETUP.EXE` | DOS LE, DOS/4GW | DOS setup. It names `SETUP.MIX` and `LOLSETUP.INI`. |
| `SETUP.EXE`, `INSTALL.EXE` | 16-bit Windows (NE) | The Windows setup program. `_SETUPDX.EXE` tells you to run `Setup.exe` from Windows when memory is short. |
| `RUNGAME.EXE` | 16-bit Windows (NE) | Names the setup program. It is not a second copy of `LOLG.DAT`. |
| `_SETUPDX.EXE` | 32-bit Windows (PE) | CD setup helper. Its text says it is a Windows 95 executable. |

The 1.30 notes also describe a Windows Direct3D build. The playable program in this tree is the DOS pair `LOLG.EXE` plus `LOLG.DAT`. The Windows files here are setup and the 16-bit launcher.

## What the DOS program asks for at startup

**From files.** The `-CD` and `-LOWMEM` strings are in `LOLG.DAT`.

- `-CD` is at file `+0x1C5285`, in the same list as `-NOMIX` and `-PATH`. Two earlier copies of the letters `-CD` sit at `+0x1C49DC` and `+0x1C4A84`. Beside the first of those, the program stores `\DAT`, `\CD2`, `\CD3` and `\CD4`. The installed configuration uses `lolg.exe -CD ..`, which points the switch at the parent of the mounted folder. **Tried here:** this setting reached the menu in folders 0042 and 0043.
- `-LOWMEM` is at file `+0x1C53CD`. What it sets is on the [fault page](README.md). **Reported elsewhere:** GOG support suggests using it for the cantina, saving, then starting again without it. Returning the in-game video controls to their previous values is part of that advice.
- `-PATH` is at file `+0x1C527F`. Two other copies of the letters are at `+0x1C1C19` and `+0x1C548C`. It is the prefix the program joins to data names. Changing that prefix remains untested here.

**From files.** Sound setup is `lolsetup.ini`, named at `LOLG.DAT+0x1C4A9C`. The copy read here stores Sound Blaster ASP/16 for digital audio (port `0x220`, IRQ 5, DMA 5) and the same card for MIDI (port `0x388`). **Reported elsewhere:** the 1.30 notes attribute some DOS hardware acceleration failures to the 3Dfx driver. Audible Sound Blaster output and 3Dfx acceleration remain untested here.

## Video and audio keys

**From files and the supplied 1.30 notes.** `options.ini` is named at `LOLG.DAT+0x1C2714`. The recorded runs kept their settings. Changing the individual keys below remains untested here.

| Key | File offset | What the 1.30 notes say |
| --- | --- | --- |
| `Audio_Channels` | `0x1C278F` | Channel count. |
| `Audio_Reverse` | `0x1C27A8` | Stereo swap. |
| `Audio_Music_Type` | `0x1C27C7` | Digital or MIDI. |
| `Video_Game_Resolution` | `0x1C27EC` | High or low game resolution. |
| `Video_Movie_Resolution` | `0x1C2811` | Movie resolution. |
| `Video_Viewport_Size` | `0x1C2832` | How large the view is. |
| `Video_Texture_Resolution` | `0x1C2851` | High or low. Low leaves movies, monsters and items alone and uses coarser floor, wall and tree textures. |
| `Video_Texture_Cache` | `0x1C287A` | Large when the machine has more than 16 MB; small, with low texture resolution, at 16 MB or below. |
| `Video_Gamma_Correction` | `0x1C289A` | Brightness. |
| `Video_Variable_Frame_Rate` | `0x1C28BA` | The installed file uses No for the fixed-rate option. One report used Off when a statue stuck. |

Each offset is the first byte of that name in this `LOLG.DAT`. The bytes just before several of the video names are the stored default word (`High`, `Large`, `Small`), not part of the key.

**Reported elsewhere.** One community note for the cantina raises `memsize` to 64 and points the extender at a small `DOS4GVM` file. **From files.** The stub contains `DOS4GVM=VirtualMemory:ON,VirtualSize:24M,...` at `LOLG.EXE+0x481`. See the [fault page](README.md) for the result of testing the two-digit edit.

## Movement keys

**Tried here:** Up and Left in the village, folders 0033 and 0034. **From files:** all four arrow keys are bound for walking or turning. `LOLG.DAT` stores each key name three times (English, then French, then German). The English arrow names are `LEFT` at `+0x1C317C`, `UP` at `+0x1C31C5`, `DOWN` at `+0x1C31D3` and `RIGHT` at `+0x1C3232`. The keypad names are in the same table: `*LEFT` at `+0x1C325B`, `*UP` at `+0x1C328F`, `*DOWN` at `+0x1C32AF` and `*RIGHT` at `+0x1C32F5`.

The setting names begin at `Key_Move_Forward_1`, file `+0x1C3465`. This `options.ini` sets them once, in `[Keyboard]`:

| Setting | Name offset | Value |
| --- | --- | --- |
| `Key_Move_Forward_1` | `0x1C3465` | `UP` |
| `Key_Move_Forward_2` | `0x1C3478` | `*UP` |
| `Key_Move_Backward_1` | `0x1C348B` | `*DOWN` |
| `Key_Move_Backward_2` | `0x1C349F` | `DOWN` |
| `Key_Turn_Left_1` | `0x1C34F5` | `LEFT` |
| `Key_Turn_Left_2` | `0x1C3505` | `*HOME` |
| `Key_Turn_Right_1` | `0x1C3515` | `RIGHT` |
| `Key_Turn_Right_2` | `0x1C3526` | `*PGUP` |
| `Key_Move_Left_1` | `0x1C34B3` | `*LEFT` |
| `Key_Move_Right_1` | `0x1C34D3` | `*RIGHT` |

`Key_Move_Left_2` and `Key_Move_Right_2` are blank here. The letters `W`, `A`, `S` and `D` are other actions. Their first values in the same section are `Key_Use_Mouse_Item_1=W` (name at `+0x1C3C1D`), `Key_Pitch_Reset_1=A` (`+0x1C3577`), `Key_Cast_Spell_1=S` (`+0x1C364F`) and `Key_Jump_1=D` (`+0x1C35FD`). Later lines in that section repeat some keys and leave many blank, including an empty `Key_Use_Mouse_Item_1`. They do not assign forward, backward or turn again, so both bindings remain in effect. The keypad Down key is the first Backward binding. The arrow Down key is the second.

## Cache and install

**From files.** The installer ships `CACHEBAK.MIX` (131 bytes) and `CDCACHE.LS_` (4,008 bytes, 15 records, every state -1). The game writes `CDCACHE.MIX` and `CDCACHE.LST` when it runs. On a reset it copies the shipped list onto `CDCACHE.LST` and the 131-byte seed onto the cache archive, then extends it. The recorded runs used an existing cache. The [cache reader notes](../docs/lol2-cache-initializer.md) describe the reset from code and files.

`INSTALL.EXE` and `SETUP.EXE` are the 16-bit Windows setup programs. `_SETUPDX.EXE` is the 32-bit helper and it looks for `SETUP.MIX` and `LOLSETUP.INI`. A short memory message in that helper says to run `Setup.exe` from Windows. None of these is the DOS game.
