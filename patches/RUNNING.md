# Running the DOS 1.30 game on a current machine

Read this against your own copy. The notes below come from the programs and the setup files in one English GOG tree, and from the strings those programs store. No game was launched for this page, so a setting is listed because the program names it, not because a play session scored it.

The retail build in that tree is DOS 1.30. `LOLG.DAT` is 1,977,007 bytes. The version string `DOS 1.30` is at file `+0x1C4714` and the date `Dec 03 1997` is at `+0x1C4749`.

## Which programs are which

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

`LOLG.EXE` does not contain `-CD` or `-LOWMEM`. Those switches are in `LOLG.DAT`.

- `-CD` is at file `+0x1C5285`, in the same list as `-NOMIX` and `-PATH`. Two earlier copies of the letters `-CD` sit at `+0x1C49DC` and `+0x1C4A84`. Beside the first of those, the program stores `\DAT`, `\CD2`, `\CD3` and `\CD4`. The single-player DOSBox configuration that ships with this tree runs `lolg.exe -CD ..`, which points the switch at the parent of the mounted folder. Omit it only when the data already sits where the program looks without the switch.
- `-LOWMEM` is at file `+0x1C53CD`. What it sets is on the [fault page](README.md). Use it for the cantina section, save, and start again without it. GOG support also says the video options can stay on the low settings afterwards, and that you put them back from the in-game video controls.
- `-PATH` sits in that same list at file `+0x1C527F`. Two other copies of the letters are at `+0x1C1C19` and `+0x1C548C`. It is the prefix the program joins to data names.

Sound setup is `lolsetup.ini`, named at `LOLG.DAT+0x1C4A9C`. The copy read here stores Sound Blaster ASP/16 for digital audio (port `0x220`, IRQ 5, DMA 5) and the same card for MIDI (port `0x388`). The 1.30 notes say a wrong or old 3Dfx driver is the usual reason DOS hardware acceleration fails. This page did not try a 3Dfx card.

## Video and audio keys

`options.ini` is named at `LOLG.DAT+0x1C2714`. These keys are in the program, with the file offset of each name:

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
| `Video_Variable_Frame_Rate` | `0x1C28BA` | On keeps the rate variable. Off holds it steadier. One report used Off when a statue stuck. |

Each offset is the first byte of that name in this `LOLG.DAT`. The bytes just before several of the video names are the stored default word (`High`, `Large`, `Small`), not part of the key.

The DOSBox configuration that ships with this tree sets `memsize=30`. One community note for the cantina, instead of `-LOWMEM`, raises that to 64 and points the extender at a small `DOS4GVM` file. The stub already contains its own sentence, `DOS4GVM=VirtualMemory:ON,VirtualSize:24M,...`, at `LOLG.EXE+0x481`. The two-digit edit of that sentence is the patch on the [fault page](README.md). It is not required to start the game.

## Cache and install

The installer ships `CACHEBAK.MIX` (131 bytes) and `CDCACHE.LS_` (4,008 bytes, 15 records, every state -1). The game writes `CDCACHE.MIX` and `CDCACHE.LST` when it runs. Those two are one run's cache, not a file to copy between machines. On a reset the program copies the shipped list onto `CDCACHE.LST` and the 131-byte seed onto the cache archive, then extends it. The byte-level account is [Native texture cache initialization](../docs/lol2-cache-initializer.md). If a run asks to rebuild the cache, that is this reset, not a patch.

`INSTALL.EXE` and `SETUP.EXE` are the 16-bit Windows setup programs. `_SETUPDX.EXE` is the 32-bit helper and it looks for `SETUP.MIX` and `LOLSETUP.INI`. A short memory message in that helper says to run `Setup.exe` from Windows. None of these is the DOS game.
