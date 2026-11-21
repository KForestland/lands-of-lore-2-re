#!/usr/bin/env python3
"""Compare your original LoL2 install with the measured edition fingerprints."""
from hashlib import sha256
import os
from pathlib import Path

from cli_errors import ReaderArgumentParser, game_path, run_cli


WITNESSES = {'English GOG release, DOS 1.30': {'LOLG.DAT': (1977007, 'b27a35341c6e877e40b1540b6482748e7a750c605fefe6452431b18a5d766775'),
                      'LOLG.EXE': (2847, 'cbd225cebc81cfbf06272456492686340d95c0148b5db9a0acca3c58653902f6'),
                      'GLOBAL.MIX': (7407657, '1e3e2a46340d714aaf4d583e5aff7e58dc11005bac6c694fac49c07d13e01edd'),
                      'LOCAL.MIX': (27594554, 'd0783146cad8823b3cbc540373fc85cd80482dff4375eaab7bc2a352e97fa278'),
                      'DAT/GLOBAL.MIX': (7407657, '1e3e2a46340d714aaf4d583e5aff7e58dc11005bac6c694fac49c07d13e01edd'),
                      'DAT/L1_DC.MIX': (7424548, '6384ec4d4d78f1aadfc1f154d924e1e20636af037cf5af68fe35af8478854345')}}
SUBFOLDER = "DAT"
DATA_ENV = "LOL2_DAT"


def locate(root, name):
    path = game_path(root, name)
    return path if path.is_file() else None


def identify(root):
    names = dict.fromkeys(name for rows in WITNESSES.values() for name in rows)
    if SUBFOLDER == "DATA":
        child = game_path(root, SUBFOLDER)
        root = child if child.is_dir() else root
    elif SUBFOLDER == "DAT" and root.name.upper() == "DAT":
        root = root.parent
    found = {}
    for name in names:
        path = locate(root, name)
        if path is not None:
            with path.open("rb") as stream:
                found[name] = (path.stat().st_size, sha256_stream(stream))
    return root, found


def sha256_stream(stream):
    digest = sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def status(expected, observed):
    if observed is None:
        return "missing"
    return "matches" if observed == expected else "differs"


def main(argv=None):
    parser = ReaderArgumentParser(description=__doc__)
    default = os.environ.get(DATA_ENV)
    parser.add_argument("--data", type=Path, default=default, required=default is None,
                        help=f"your game folder or its {SUBFOLDER} folder (default: ${DATA_ENV})")
    parser.add_argument("--check", action="store_true",
                        help="verify that all fingerprint files match a measured edition")
    args = parser.parse_args(argv)
    root, found = identify(args.data.resolve())
    if not found:
        parser.error(f"No edition files found in {root}. Give --data your original game installation or its data folder.")

    def score(edition):
        _, rows = edition
        return (all(found.get(name) == value for name, value in rows.items()),
                sum(found.get(name) == value for name, value in rows.items()),
                sum(name in found for name in rows))

    label, rows = max(WITNESSES.items(), key=score)
    statuses = {name: status(value, found.get(name)) for name, value in rows.items()}
    differences = [f"{name} {value}" for name, value in statuses.items() if value != "matches"]
    summary = f"{label}: all {len(rows)} fingerprint files match in {root}."
    if args.check:
        if differences:
            raise ValueError(f"The {label} fingerprint does not match in {root} ({', '.join(differences)}). "
                             "Check an unmodified copy or run without --check for sizes and checksums.")
        print(f"CHECK edition: {summary}")
        return 0

    print("File | Bytes | SHA-256 | Status")
    for name, result in statuses.items():
        size, checksum = found.get(name, ("—", "—"))
        print(f"{name} | {size} | {checksum} | {result}")
    if differences:
        print(f"No complete edition fingerprint matches in {root}. The table compares with {label}.")
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
