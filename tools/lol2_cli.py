"""Shared command line for the LoL2 tools: --data (or $LOL2_DAT), --out, --check.

The game's DAT folder is never assumed; tools that read game files need
--data /path/to/DAT or the LOL2_DAT environment variable. Nothing is written
unless an output path is given.
"""
from cli_errors import ReaderArgumentParser, command_name, data_folder, game_path, input_path, output_refusal
import argparse
import os

DEFAULT_DATA = os.environ.get("LOL2_DAT")


def tool_args(doc, data=True, out_help="write the result here (default: print only)",
              *, out_aliases=(), writes=True):
    ap = ReaderArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    if data:
        ap.add_argument("--data", default=DEFAULT_DATA, required=DEFAULT_DATA is None,
                        help="the game's DAT folder (default: $LOL2_DAT)")
    if writes:
        ap.add_argument("--out", *out_aliases, help=out_help)
    ap.add_argument("--check", action="store_true", help="run the tool's check and print one CHECK line; exit 1 on failure")
    return ap


def mix_files(data_dir):
    return sorted(f for f in os.listdir(data_dir) if f.upper().endswith(".MIX"))


def refuse_repo_output(path, data=None):
    """Exit 2 with a message if an output path lies in this repository, in the --data folder,
    or in or below a folder that holds a MIX archive or LOLG.DAT (game data must not land in them)."""
    import sys
    refusal = output_refusal(path, data, repository=True)
    if refusal:
        print(f"{command_name()}: {refusal}", file=sys.stderr)
        sys.exit(2)
    return path


def resolve_input(name, data_dir=None):
    """Find a game file given as a path or a bare name: as given, then in the DAT folder
    (--data or $LOL2_DAT), then in the game folder above it (LOCAL, LOCALLNG, DMUSIC, SETUP, GLOBAL)."""
    path = input_path(name)
    if path.is_file():
        return str(path)
    data_dir = data_dir or os.environ.get("LOL2_DAT")
    if data_dir:
        data = data_folder(input_path(data_dir))
        for folder in (data, data.resolve().parent):
            path = game_path(folder, name)
            if path.is_file():
                return str(path)
    return str(name)
