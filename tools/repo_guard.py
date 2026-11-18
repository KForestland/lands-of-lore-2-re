#!/usr/bin/env python3
"""Asset-policy guard: fail if the repository tracks game files or game media.

The repository may hold documentation, tools, small data tables and a few
images made by the tools in examples/ and docs/images/. This check lists the
files git tracks and fails on:

  - game file types: .MIX .VQA .AUD .TEX .TE_ .WOM .PCX .SMF .LST .TRR .DAT
    .EXE .DLL .BIN, and converted media .WAV .OGG .MP3 .MID .HMI .XMI
  - PNG files outside examples/ and docs/images/
  - full script listings (*.groups.jsonl, *.events.jsonl, *.group-notes*.md) written by
    tools/lol2_level_notes.py --out: they are tool output for the user's own copy
  - any file larger than 300 KB, except the existing data tables in SIZE_ALLOWED
    (generated listings of game content are tool output, not tracked files)
  - with --release only: in the git history, any author or committer address not in ALLOWED_AUTHORS
    (committers may also be GitHub's noreply@github.com); the address is not printed
  - in text files: machine paths (/home/, /media/, /mnt/, C:\\Users\\) and
    private or assistant names (kept only as salted hashes in NAME_HASHES)

It cannot tell whether a PNG in the allowed folders shows game pixels; that
stays a review point. Needs no game data (--data is accepted and ignored).

  repo_guard.py --check
"""
import argparse
import os
import re
import subprocess
import sys

GAME = {".mix", ".vqa", ".aud", ".tex", ".te_", ".wom", ".pcx", ".smf", ".lst", ".trr", ".dat", ".exe",
        ".dll", ".bin", ".wav", ".ogg", ".mp3", ".mid", ".midi", ".hmi", ".xmi", ".flac"}
PNG_OK = ("examples/", "docs/images/")


# Text rules: no machine paths and no lane, agent or private names in tracked files.
# This file is exempt because it holds the lists.
MACHINE_PATH = re.compile(r"/home/[a-z]|/media/[a-z]|/mnt/[a-z]|[A-Za-z]:\\Users\\")
# Names are stored only as salted SHA-256 prefixes, so this file does not publish them.
NAME_SALT = "lol-re-guard-v1:"
NAME_HASHES = {'23338abd2a2d97eb', '29e9c7594cdb5db0', '726ed7fd32fdaaf1', '81fa922e71ac7a9d', '8ecf3cb164791cae', 'a28fcab3720b19a2', 'c92dda7cee70420c', 'debf9dcbb9908f16', 'e3470cbd354e28f8'}
WORD = re.compile(r"[A-Za-z]+")


def name_hit(word):
    import hashlib
    return hashlib.sha256((NAME_SALT + word).encode()).hexdigest()[:16] in NAME_HASHES



def text_findings(root, f):
    if f.endswith("tools/repo_guard.py") or f == "tools/repo_guard.py":
        return []
    try:
        with open(os.path.join(root, f), encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except (UnicodeDecodeError, OSError):
        return []
    out = []
    for n, line in enumerate(lines, 1):
        if MACHINE_PATH.search(line):
            out.append(f"{f}:{n} (machine path)")
        for m in WORD.finditer(line):
            if not name_hit(m.group(0)):
                continue
            if line[m.start() - 1:m.start()] == '"' and line[m.end():m.end() + 1] == '"':
                continue  # a quoted name is game text, e.g. a bow named like an assistant
            out.append(f"{f}:{n} (private or assistant name)")
            break
    return out


# Commit identity: every author and committer address in the history of the checked-out branch (HEAD,
# what gets published) must be one of these.
# GitHub's own web merges commit as noreply@github.com (committer only).
ALLOWED_AUTHORS = {'261564562+KForestland@users.noreply.github.com'}
ALLOWED_COMMITTERS = ALLOWED_AUTHORS | {"noreply@github.com"}


def identity_findings(root):
    """Authors and committers in the git history that are not on the allowed lists."""
    try:
        out = subprocess.run(["git", "-C", root, "log", "HEAD", "--format=%h %ae %ce"],
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []  # not a git checkout (for example a downloaded archive): nothing to check
    bad = []
    for line in out.splitlines():
        h, author, committer = line.split(" ")
        if author not in ALLOWED_AUTHORS:
            bad.append(f"commit {h} (author address not allowed)")
        if committer not in ALLOWED_COMMITTERS:
            bad.append(f"commit {h} (committer address not allowed)")
    return bad


# Full script listings written by tools/lol2_level_notes.py --out are tool output, never tracked.
LISTING_SUFFIXES = (".groups.jsonl", ".events.jsonl", ".group-notes.md")

# No tracked file over 300 KB, except these existing data tables (listed by name).
SIZE_LIMIT = 300_000
SIZE_ALLOWED = set()  # none

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--release", action="store_true",
                    help="also require the project noreply identity on every commit (release procedure)")
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
        elif f.endswith(LISTING_SUFFIXES) or ".group-notes-" in f or (".events-" in f and f.endswith(".jsonl")) or (".groups-" in f and f.endswith(".jsonl")):
            bad.append(f"{f} (full script listing: tool output, not tracked)")
        elif os.path.isfile(p) and os.path.getsize(p) > SIZE_LIMIT and f not in SIZE_ALLOWED:
            bad.append(f"{f} (larger than 300 KB)")
        if os.path.isfile(p):
            bad.extend(text_findings(root, f))
    if getattr(a, 'release', False):
        bad.extend(identity_findings(root))
    print(f"CHECK repo_guard: {len(files)} tracked files; game files, media, stray images, files over 300 KB, machine paths, private or assistant names, or commit identities: "
          f"{bad[:5] or 'none'}{' ...' if len(bad) > 5 else ''} ({len(bad)})")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
