#!/usr/bin/env python3
"""Asset-policy guard: fail if the repository tracks game files or game media.

The repository may hold documentation, tools, small data tables and a few
images made by the tools in examples/ and docs/images/. This check lists the
files git tracks and fails on:

  - game file types: .MIX .VQA .AUD .TEX .TE_ .WOM .PCX .SMF .LST .TRR .DAT
    .EXE .DLL .BIN, and converted media .WAV .OGG .MP3 .MID .HMI .XMI
  - PNG files outside examples/ and docs/images/
  - any file larger than 1 MiB

It cannot tell whether a PNG in the allowed folders shows game pixels; that
stays a review point. Needs no game data (--data is accepted and ignored).

  repo_guard.py --check
"""
import argparse
import os
import subprocess
import sys

GAME = {".mix", ".vqa", ".aud", ".tex", ".te_", ".wom", ".pcx", ".smf", ".lst", ".trr", ".dat", ".exe",
        ".dll", ".bin", ".wav", ".ogg", ".mp3", ".mid", ".midi", ".hmi", ".xmi", ".flac"}
PNG_OK = ("examples/", "docs/images/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--data", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if not a.check:
        ap.print_help(); return 2
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    files = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split("\n")
    files = [f for f in files if f]
    bad = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        p = os.path.join(root, f)
        if ext in GAME:
            bad.append(f"{f} (game file type)")
        elif ext in (".png", ".jpg", ".gif", ".bmp") and not f.startswith(PNG_OK):
            bad.append(f"{f} (image outside examples/ and docs/images/)")
        elif os.path.isfile(p) and os.path.getsize(p) > 1 << 20:
            bad.append(f"{f} (larger than 1 MiB)")
    print(f"CHECK repo_guard: {len(files)} tracked files; game files, media, stray images or files over 1 MiB: "
          f"{bad[:5] or 'none'}{' ...' if len(bad) > 5 else ''} ({len(bad)})")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
