#!/usr/bin/env python3
"""Extract and verify pinned cave geometry and wall records from a local installation."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from cli_errors import ReaderArgumentParser, run_cli


def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.game_root.resolve()
    if not (root / "DAT/L1_DC.MIX").is_file() or not (root / "LOLG.DAT").is_file():
        parser.error("game-root must contain DAT/L1_DC.MIX and LOLG.DAT")
    steps = [
        ("lol2_draracle_openings.py", "geometry"),
        ("lol2_verify_draracle_slopes.py", "slopes"),
        ("lol2_verify_draracle_connectors.py", "connectors"),
        ("lol2_extract_wall_records.py", "walls"),
        ("lol2_verify_flat_wall_spans.py", "flat_walls"),
        ("lol2_verify_upper_lower_walls.py", "upper_lower_walls"),
        ("lol2_verify_sloped_middle_walls.py", "sloped_middle_walls"),
        ("lol2_verify_sloped_upper_lower_walls.py", "sloped_upper_lower_walls"),
        ("lol2_verify_connector_middle_walls.py", "connector_middle_walls"),
        ("lol2_verify_special_upper_lower_walls.py", "special_upper_lower_walls"),
        ("audit_wall_coverage.py", "coverage"),
    ]
    for script, folder in steps:
        result = subprocess.run([sys.executable, str(Path(__file__).with_name(script)),
                                 "--game-root", str(root), "--out", str((args.out / folder).resolve())],
                                capture_output=True, text=True)
        if result.returncode:
            lines = (result.stderr or result.stdout).strip().splitlines()
            detail = lines[-1] if lines else f"exit status {result.returncode}"
            raise ValueError(f"{script}: {detail}")
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
    print("Geometry and wall-record checks complete.")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
