#!/usr/bin/env python3
"""Read a LoL2 DAT folder and write inventory, level and text reports."""
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from cli_errors import ReaderArgumentParser, run_cli, game_path
import lol2_loose
from lol2_mix_parser import read_mix_with_hashes
from lol2_text_tables import parse_trr
from lol2_westwood_hash import ww_hash_v1
from rating import mix_covered

LOCALIZED = ("automap.trr", "opttext.trr", "helptext.trr", "credits.trr")


def inventory(data):
    rows = []
    for path in sorted(data.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".mix":
            reader = "rating.mix_covered"
            complete = mix_covered(path)
        elif path.suffix.lower() in (".exe", ".wav"):
            reader = "lol2_loose.covered"
            complete = lol2_loose.covered(path)
        else:
            reader = ""
            complete = False
        rows.append((path.name, path.stat().st_size, reader, "complete" if complete else "open"))
    return rows


def text_counts(data):
    rows = []
    for path, names in ((game_path(data.parent, "LOCALLNG.MIX"), LOCALIZED),
                        (game_path(data, "MOVIES.MIX"), ("credits.trr",))):
        blob, entries, base = read_mix_with_hashes(path)
        for name in names:
            key = ww_hash_v1(name)
            matches = [(offset, size) for ident, offset, size in entries if ident == key]
            if len(matches) != 1:
                raise ValueError(f"{path.name}: expected one entry for {name}")
            offset, size = matches[0]
            count, _, _ = parse_trr(blob[base + offset:base + offset + size], name)
            rows.append((os.path.relpath(path, data), name, count))
    for name in ("ERRTEXT.TRR", "OPTTEXT.TRR", "CREDITS.TRR"):
        path = game_path(data.parent, name)
        count, _, _ = parse_trr(path.read_bytes(), name)
        rows.append((os.path.relpath(path, data), name, count))
    return rows


def write_tsv(path, headings, rows):
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(headings)
        writer.writerows(rows)


def main():
    parser = ReaderArgumentParser(description=__doc__)
    default_data = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, default=default_data, required=default_data is None,
                        help="the game's DAT folder (default: $LOL2_DAT)")
    parser.add_argument("--out", type=Path, required=True, help="report folder outside the game and repository")
    args = parser.parse_args()
    data = args.data.resolve()
    out = args.out.resolve()
    repository = Path(__file__).resolve().parents[1]
    if any(out == root or root in out.parents for root in (repository, data.parent)):
        parser.error("--out must be outside the game and repository")
    out.mkdir(parents=True, exist_ok=True)
    names = ("inventory.tsv", "text-counts.tsv", "levels")
    # Keep a failed level read from publishing a half-written report.
    with tempfile.TemporaryDirectory(dir=out, prefix=".report-") as staging:
        occupied = [name for name in names if (out / name).exists() or (out / name).is_symlink()]
        if occupied:
            raise ValueError(f"output already contains {', '.join(occupied)}")
        report = Path(staging)
        files = inventory(data)
        text = text_counts(data)
        level_reader = Path(__file__).with_name("lol2_level_report.py")
        result = subprocess.run([sys.executable, str(level_reader), "--data", str(data),
                                 "--out", str(report / "levels")], capture_output=True, text=True)
        if result.returncode:
            raise ValueError((result.stderr or result.stdout).strip() or "level reader failed")
        levels = len(list((report / "levels").glob("*.md"))) - 1  # Exclude the index.
        if levels < 1:
            raise ValueError("no level sheets were generated")
        write_tsv(report / names[0], ("file", "bytes", "reader", "result"), files)
        write_tsv(report / names[1], ("source", "table", "records"), text)
        for name in ("levels", *names[:2]):
            (report / name).rename(out / name)
    print(f"wrote {len(files)} inventory rows, {levels} level sheets and {len(text)} text counts to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
