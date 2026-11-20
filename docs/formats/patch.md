# Lands of Lore patch format

A patch is a small file that describes a few changed bytes in your own copy
of the game: what the bytes were and what they become. `tools/patch.py`
makes a patch from a folder of changed files, applies it to a game folder,
and writes an undo patch beside the result. The same tool and the same
format are used in the three repositories (LoL1, LoL2 and LoL3); a patch
names the game it is for, and the tool of another game refuses it.

The tool only reads your game folder. Every result goes into a new folder
that you name, outside the game folder and outside this repository. You copy
the changed files into a **copy** of your game yourself, and the undo patch
gives you back the exact original bytes.

## Rules

- Patches must not remove or bypass copy protection (disc checks, serial
  or manual look-ups). Program patches never touch copy-protection code.
  The tool cannot tell what program bytes do, so this rule rests on the
  person making the patch; this project neither makes nor accepts such
  patches.
- Share only your own edits. A patch carries the bytes it replaces as
  `old`, so the sizes are capped (below) to keep original game text and
  code out of shared patches. Complete game files, archive members, text,
  scripts, pictures and sounds are not shared.
- Native ports and engine work are outside the scope of this project.

## Make, apply and undo

These commands are typed in this repository's folder. Put quotes around
any path that contains spaces; on Windows type `py -3` instead of
`python3`. `--data` names the game folder, as in the other tools; it can
also be given as the first path.

```sh
python3 tools/patch.py make --data "GAME" "CHANGED" --title "My edit" --out "my edit.json"
python3 tools/patch.py apply --data "GAME" "my edit.json" --out "patched files"
python3 tools/patch.py apply --data "GAME COPY" "patched files/undo.json" --out "restored files"
```

- `make` compares `CHANGED` with the game folder. `CHANGED` holds changed
  game files at the same paths as in the game folder; the output folder of
  `modkit.py build` works as it is. Unchanged copies of other game files
  there are ignored. It finds the kind (data or program) from the changed
  files; `--kind` sets it, and data and program changes need two patches.
  `--description` is optional.
- `apply` checks every old byte, the program's SHA-256 for a program
  patch, and that the undo restores the source exactly, before it writes
  anything. It then writes the patched files and `undo.json` into the new
  `--out` folder and prints which files it wrote.
- To try the result, copy the patched files, with their folders, into a
  copy of your game (not `undo.json`). To undo, apply `undo.json` to that
  copy and copy the restored files back in the same way.
- Applying a patch twice is refused, because the old bytes are no longer
  there. Each command prints one summary line, or one sentence saying what
  is wrong and what to do.

## The file

A patch is UTF-8 JSON:

```json
{
  "format": "lol-patch-2",
  "game": "lol2",
  "kind": "data",
  "title": "Adjust a test number",
  "description": "Change one value in a synthetic fixture.",
  "changes": [
    {"file": "DAT/TEST.MIX", "entry": 0, "offset": 16, "old": "05", "new": "09"}
  ]
}
```

- `game` is `lol1`, `lol2` or `lol3`.
- `kind` is `data` for the game's archives and loose tables, or `program`
  for the game's own program files. A program patch also has `"sha256"`,
  the SHA-256 of each whole program file before the change
  (`{"FILE": "64 hex digits"}`). `apply` refuses a program file with
  another hash: a few matching bytes do not prove the same edition and
  version.
- `file` is the path below the folder named in the section for this game
  below, with forward slashes and the spelling on disk. A patch made from
  the installation folder and one made from its `DAT` or `DATA` folder
  name the same file in the same way, so a file that ships twice is never
  confused with its copy.
- `entry` is the zero-based index of the archive member in the archive's
  directory order; 0 for a loose table or a program.
- `offset` counts bytes from the start of the member (for a program, from
  the start of the file), as a decimal number.
- `old` and `new` are lowercase hexadecimal byte pairs. The old bytes must
  match exactly. Two changes to one member need at least one unchanged
  byte between them. A data change may insert or remove bytes (an empty
  value) where the member's format allows it; a program change replaces
  bytes with the same number of bytes and keeps the file length.

A data change must stay inside the tables and text the mod kit edits: the
changed member is read with the game's format reader, rebuilt and
compared, in both directions. A program change can be any bytes, so keep
it to bytes you understand, such as one letter in a message.

## Size limits

| | Bytes per change (`old` and `new` each) | Bytes per patch (`old` and `new` each) | Changes per patch |
| --- | --- | --- | --- |
| Data patch | 256 | 4,096 | 1,024 |
| Program patch | 16 | 256 | 1,024 |

`make` compares members whose length changed up to 65,536 bytes each. A
bigger edit needs more than one patch, or a mod kit build shared as steps
instead of bytes.

## LoL2

**File names** start at the game folder holding `LOLG.DAT` and `DAT`. If
you give the `DAT` folder, the tool uses the folder above it. `GLOBAL.MIX`
ships twice, byte for byte the same: `GLOBAL.MIX` in the game folder and
`DAT/GLOBAL.MIX`. A patch names the one you changed. Which of the two the
game opens has not been shown (**UNCONFIRMED**), so change both in the
same way.

**Program files** are `LOLG.EXE` and `LOLG.DAT` in the game folder.
`LOLG.EXE+0x438` names `LOLG.DAT`. Most gameplay offsets in these pages
belong to that second image, whose embedded LE header starts at file
`+0x3BCB4`. Convert analysis addresses to file offsets before making a
patch.

**CONFIRMED.** The target is the original DOS game under DOSBox. Data
patches change files read by the DOS program, including MIX archives and
loose TRR tables.
[MIX and TRR readers](../ROUND_TRIP.md) ·
[Executable addresses](../lol2-executable-tables.md)
