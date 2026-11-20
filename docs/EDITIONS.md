# Identify your edition

Run this from the downloaded tools folder. Replace the example with the path to your own installation or its data folder. The command reads names, sizes and checksums and reports whether they match a measured copy. Each file is marked `matches`, `differs` or `missing`.

```sh
python3 tools/edition.py --data "/path/to/your/LoL2"
```

In Windows PowerShell, use `py -3` in place of `python3`, for example `py -3 tools/edition.py --data "C:\Games\LoL2"`. Requires Python 3.10 or later and the standard library.

Set `$LOL2_DAT` to the same folder to omit `--data`. Add `--check` to verify the complete fingerprint in one line.

## Measured files

**CONFIRMED.** Byte counts and SHA-256 cover every byte from file offset `+0x00` to EOF. File names start in the installation folder. `DAT/` marks files inside that subfolder.

### English GOG release, DOS 1.30

| File | Bytes | SHA-256 |
|---|---:|---|
| `LOLG.DAT` | 1,977,007 | `b27a35341c6e877e40b1540b6482748e7a750c605fefe6452431b18a5d766775` |
| `LOLG.EXE` | 2,847 | `cbd225cebc81cfbf06272456492686340d95c0148b5db9a0acca3c58653902f6` |
| `GLOBAL.MIX` | 7,407,657 | `1e3e2a46340d714aaf4d583e5aff7e58dc11005bac6c694fac49c07d13e01edd` |
| `LOCAL.MIX` | 27,594,554 | `d0783146cad8823b3cbc540373fc85cd80482dff4375eaab7bc2a352e97fa278` |
| `DAT/GLOBAL.MIX` | 7,407,657 | `1e3e2a46340d714aaf4d583e5aff7e58dc11005bac6c694fac49c07d13e01edd` |
| `DAT/L1_DC.MIX` | 7,424,548 | `6384ec4d4d78f1aadfc1f154d924e1e20636af037cf5af68fe35af8478854345` |

## Build strings and comparison

- **CONFIRMED.** `LOLG.DAT+0x1C4714` holds `DOS 1.30`. `+0x1C4749` and `+0x1C4755` hold `Dec 03 1997` and `17:51:02`. The program reaches those strings through data pointers `0xEE54`, `0xEE5C` and `0xEE60`. The LE header has no timestamp. [Executable build strings](lol2-cache-initializer.md)
- **CONFIRMED.** `LOLG.DAT+0x33364` holds the extender component date `Apr 03 1996 15:01:07`. `+0x1C5AC8` holds a VQA component string with date `Sep 05 1997 13:11:59`. The separate `LOLG.EXE+0x4DB` identifies its DOS/4GW runtime as `2.01a`.
- Releases other than this English GOG release (DOS 1.30) have **not been measured here**. The two `GLOBAL.MIX` paths in this installation have the same size and full SHA-256. `DAT/GLOBAL.MIX` names the copy inside the data folder. [MIX archives](formats/mix.md)
