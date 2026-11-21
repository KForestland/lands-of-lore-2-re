# First ten minutes

Draw a level from your own installed copy of Lands of Lore II.
You need Python 3.10 or later, the Pillow package and a web browser.

## Find your game files

Open the folder for the copy you play. Find `LOLG.DAT` in that folder and
open the `DAT` folder next to it. Look for `L9_DR.MIX` and `L1_DC.MIX`
directly inside `DAT`. Lowercase names such as `l9_dr.mix` also work.

If you have several installations or test copies, start with the installation
you normally launch. Copy the full path to its `DAT` folder, with both
marker files inside and `LOLG.DAT` one folder up.

## Download the tools

On the [repository page](https://github.com/KForestland/lands-of-lore-2-re),
choose **Code**, then **Download ZIP**. Extract the whole ZIP to your
Downloads folder. The tools folder should be inside the extracted
repository folder alongside `README.md`. The commands below assume the
extracted folder is `lands-of-lore-2-re-main`. Use the folder name you see
if it differs.

## Windows

Open **Windows PowerShell** from the Start menu. Run `py -3 --version`.
If the command is missing or the version is below 3.10, install a
current Python 3 release with the Python launcher, then reopen PowerShell.
[Python for Windows](https://www.python.org/downloads/windows/)

Run this line, then paste the folder path when PowerShell asks for it.

```powershell
$data = (Read-Host 'Paste the path to your game folder').Trim('"')
```

Then paste these lines.

```powershell
Set-Location "$HOME\Downloads\lands-of-lore-2-re-main"
$out = "$HOME\Downloads\LoL2 output"
New-Item -ItemType Directory -Force "$out" | Out-Null
```

Prepare a Python environment and install Pillow once.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install Pillow
```

Draw the level and open the picture.

```powershell
.\.venv\Scripts\python.exe tools/lol2_level_schematic.py --data "$data" --level L1_DC --out "$out\first-level.png"
Start-Process "$out\first-level.png"
```

## Linux

Open a terminal. If `python3 --version` reports a version below 3.10,
install a newer Python with your distribution's package manager. On Ubuntu or Debian, `sudo apt install python3-venv` installs the venv module.
Run this line, paste the folder path and press Enter again.

```sh
IFS= read -r data
```

Then paste these lines.

```sh
cd "$HOME/Downloads/lands-of-lore-2-re-main"
out="$HOME/Downloads/LoL2 output"
mkdir -p "$out"
python3 -m venv .venv
.venv/bin/python -m pip install Pillow
.venv/bin/python tools/lol2_level_schematic.py --data "$data" --level L1_DC --out "$out/first-level.png"
xdg-open "$out/first-level.png"
```

You should see an overhead plan with numbered item and actor placements.
If the tool cannot find a game file, check the markers in
[Find your game files](#find-your-game-files). If no window opens, open
`first-level.png` from the output folder in a browser on your desktop.

To draw the picture again, choose a new picture file name in both lines.

[More recipes](COOKBOOK.md) · [Terms used in the guides](GLOSSARY.md)

## Open an interactive level plan

Use a new subfolder of the output folder you created above.

Windows PowerShell

```powershell
.\.venv\Scripts\python.exe tools/lol.py level --data "$data" --out "$out\plans"
Start-Process "$out\plans\L1_DC.html"
```

Linux

```sh
.venv/bin/python tools/lol.py level --data "$data" --out "$out/plans"
xdg-open "$out/plans/L1_DC.html"
```

Click a region or placement to see its details. Choose **Props** under **Show** to see prop dots. Turn on **Map numbers**
to show the placement numbers. To repeat the command, choose a new
subfolder such as `plans-2` in both lines.

## Convert a movie or sound

For the movie, install FFmpeg and check that `ffmpeg -version` and
`ffprobe -version` both work in the same terminal. The NumPy install
line is needed for the movie. Sound conversion uses the Python you
set up above.

Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m pip install numpy
.\.venv\Scripts\python.exe tools/lol.py movie --data "$data" --file CAN.MIX --entry 22 --out "$out\movie"
.\.venv\Scripts\python.exe tools/lol.py sound --data "$data" --file GLOBAL.MIX --entry 342 --out "$out\sound"
```

Linux

```sh
.venv/bin/python -m pip install numpy
.venv/bin/python tools/lol.py movie --data "$data" --file CAN.MIX --entry 22 --out "$out/movie"
.venv/bin/python tools/lol.py sound --data "$data" --file GLOBAL.MIX --entry 342 --out "$out/sound"
```

Open the files named in the tool output from the `movie` or `sound` folder.
The filenames keep the archive names' letter case. A lowercase installation
produces `can-22.mkv` and `global-342.wav`. The movie has 20 frames. The sound
has 22,050 samples. [How to choose a different entry](COOKBOOK.md#convert-a-movie-or-sound)

## Find another job

Use the same Python command with `tools/lol.py` to list the jobs.
Add a job name and `--help` for its options.
[Interactive plans](COOKBOOK.md#open-an-interactive-level-plan)
