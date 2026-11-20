"""Command-line diagnostics shared by the file readers."""
import argparse
import os
import shlex
import struct
import sys
from pathlib import Path


def one_line(message):
    return " ".join(str(message).splitlines()).strip()


REPOSITORY = Path(__file__).resolve().parents[1]
# Options through which a tool writes a file or a folder of files.
OUTPUT_OPTIONS = ("out", "output", "output_dir", "summary", "png")
# Options that name the game's DAT folder or the game folder above it.
DATA_OPTIONS = ("data", "game_dat", "game_root", "lol2_root")


def is_game_file(name):
    """A game archive (MIX) or the game program (LOLG.DAT)."""
    name = name.upper()
    return name.endswith(".MIX") or name == "LOLG.DAT"


def holds_game_data(folder):
    """True when folder or a folder above it holds a game archive (MIX) or the game program (LOLG.DAT)."""
    for place in (folder, *folder.parents):
        try:
            if any(is_game_file(entry.name) for entry in place.iterdir()):
                return True
        except OSError:
            continue
    return False


def output_refusal(path, data=None, repository=False):
    """Why a tool may not write path (a file or a folder), or None. Refused: the
    --data folder (one path or several) and anything below it, any folder holding a
    MIX archive or LOLG.DAT or lying below one, and, with repository=True, this repository."""
    target = Path(path).resolve()
    roots = [REPOSITORY] if repository else []
    for folder in (data if isinstance(data, (list, tuple)) else [data]):
        if isinstance(folder, (str, os.PathLike)) and str(folder):
            roots.append(Path(folder).resolve())
    if any(root == target or root in target.parents for root in roots) or holds_game_data(target):
        where = "the game data and repository" if repository else "the game data"
        return f"give an output path outside {where}: {path}"
    return None


class ReaderArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, output_options=(), **kwargs):
        """output_options: further option names through which this tool writes."""
        super().__init__(*args, **kwargs)
        self.output_options = OUTPUT_OPTIONS + tuple(output_options)

    def parse_args(self, args=None, namespace=None):
        options = super().parse_args(args, namespace)
        for name in ("data", "game_dat"):
            folder = getattr(options, name, None)
            if isinstance(folder, (str, os.PathLike)) and not Path(folder).is_dir():
                self.error(f"game data folder does not exist: {folder}")
        # A data folder that is only the built-in default "." is a guess, not a game folder;
        # the archive check below still refuses it when it holds game files.
        data = [getattr(options, name, None) for name in DATA_OPTIONS
                if not getattr(options, name, None) == self.get_default(name) == "."]
        for name in self.output_options:
            path = getattr(options, name, None)
            if isinstance(path, (str, os.PathLike)) and str(path):
                refusal = output_refusal(path, data)
                if refusal:
                    self.error(refusal)
        return options

    def error(self, message):
        self.exit(2, message)

    def exit(self, status=0, message=None):
        if message:
            message = one_line(message)
            print(f"{self.prog}: {message}", file=sys.stderr)
        super().exit(status)


def run_cli(main, *args):
    try:
        result = main(*args)
        sys.stdout.flush()
        return result
    except BrokenPipeError:
        # Flush can fail again during interpreter shutdown after a pipe closes.
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        return 0
    except (OSError, EOFError, ImportError, ValueError, struct.error, IndexError, KeyError) as error:
        module = (error.name or "").partition(".")[0] if isinstance(error, ImportError) else ""
        package = {"PIL": "Pillow", "numpy": "numpy", "capstone": "capstone"}.get(module)
        if package:
            python = f'& "{sys.executable}"' if os.name == "nt" else shlex.quote(sys.executable)
            message = f"This job needs {package}: run {python} -m pip install {package}."
        else:
            message = one_line(error) or type(error).__name__
        print(f"{Path(sys.argv[0]).name}: {message}", file=sys.stderr)
        return 1
