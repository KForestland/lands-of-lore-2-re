"""Shared command line for the LoL2 tools: --data (or $LOL2_DAT), --out, --check.

The game's DAT folder is never assumed; tools that read game files need
--data /path/to/DAT or the LOL2_DAT environment variable. Nothing is written
unless an output path is given.
"""
import argparse
import os

DEFAULT_DATA = os.environ.get("LOL2_DAT")


def tool_args(doc, data=True, out_help="write the result here (default: print only)"):
    ap = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    if data:
        ap.add_argument("--data", default=DEFAULT_DATA, required=DEFAULT_DATA is None,
                        help="the game's DAT folder (default: $LOL2_DAT)")
    ap.add_argument("--out", help=out_help)
    ap.add_argument("--check", action="store_true", help="run the tool's check and print one CHECK line; exit 1 on failure")
    return ap


def mix_files(data_dir):
    return sorted(f for f in os.listdir(data_dir) if f.upper().endswith(".MIX"))


def refuse_repo_output(path):
    """Exit with a message if an output path lies inside this repository (game data must not land in it)."""
    import sys
    repo = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    target = os.path.realpath(path)
    if target == repo or target.startswith(repo + os.sep):
        sys.exit(f"refusing to write inside the repository ({path}); give an output path outside it")
    return path


def resolve_input(name, data_dir=None):
    """Find a game file given as a path or a bare name: as given, then in the DAT folder
    (--data or $LOL2_DAT), then in the game folder above it (LOCAL, LOCALLNG, DMUSIC, SETUP, GLOBAL)."""
    name = str(name)
    if os.path.isfile(name):
        return name
    data_dir = data_dir or os.environ.get("LOL2_DAT")
    if data_dir:
        for folder in (data_dir, os.path.dirname(os.path.abspath(str(data_dir)))):
            for cand in (name, name.upper(), name.lower()):
                p = os.path.join(folder, cand)
                if os.path.isfile(p):
                    return p
    return name
