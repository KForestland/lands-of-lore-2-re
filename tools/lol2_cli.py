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
