#!/usr/bin/env python3
"""Check whether LOCAL.MIX entry 1 record 0 appears directly in runtime wall buffers.

This is a narrow verifier for the surviving Entry 1 witness:

- load LOCAL.MIX entry 1
- extract record 0 raw pixels (128x128)
- compare them against a few preserved runtime wall/renderer buffers

The goal is not to prove total non-use. It only answers a smaller,
repo-safe question:

  "Do the currently preserved runtime buffer captures contain direct raw
   reuse of Entry 1 record 0 under straightforward layout assumptions?"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lol2_wall_texture_extract import extract_raw_pixels, parse_atlas, read_mix_entry  # noqa: E402


DEFAULT_LOL2_ROOT = "/media/bob/Arikv/REFERENCE/game_files/lol2/"
DEFAULT_OUTPUT = "atlas_candidate_verify/entry1_runtime_witness_check.json"

RUNTIME_TARGETS = [
    {
        "name": "l1cap_wall_lane",
        "path": "/home/bob/lol2_out/l1cap_wall_lane.bin",
        "width": 128,
        "height": 128,
    },
    {
        "name": "bigdump_wall_lane",
        "path": "/home/bob/lol2_out/bigdump_wall_lane.bin",
        "width": 128,
        "height": 128,
    },
    {
        "name": "l1cap_renderer_texture",
        "path": "/home/bob/lol2_out/l1cap_renderer_texture.bin",
        "width": 256,
        "height": 256,
    },
    {
        "name": "bigdump_renderer_src",
        "path": "/home/bob/lol2_out/bigdump_renderer_src.bin",
        "width": 128,
        "height": 64,
    },
]


def rows(data: bytes, width: int, height: int) -> list[bytes]:
    return [data[i * width:(i + 1) * width] for i in range(height)]


def patch_map(data: bytes, width: int, height: int, patch_size: int) -> dict[bytes, tuple[int, int]]:
    result: dict[bytes, tuple[int, int]] = {}
    data_rows = rows(data, width, height)
    for y in range(height - patch_size + 1):
        for x in range(width - patch_size + 1):
            block = b"".join(r[x:x + patch_size] for r in data_rows[y:y + patch_size])
            result.setdefault(block, (x, y))
    return result


def best_row_match(lhs_rows: list[bytes], rhs_rows: list[bytes]) -> dict[str, int]:
    best_eq = -1
    best_lhs = -1
    best_rhs = -1
    for i, lhs in enumerate(lhs_rows):
        for j, rhs in enumerate(rhs_rows):
            eq = sum(a == b for a, b in zip(lhs, rhs))
            if eq > best_eq:
                best_eq = eq
                best_lhs = i
                best_rhs = j
    return {
        "equal_bytes": best_eq,
        "row_width": len(lhs_rows[0]) if lhs_rows else 0,
        "lhs_row": best_lhs,
        "rhs_row": best_rhs,
    }


def variant_rows(data: bytes, width: int, height: int) -> dict[str, list[bytes]]:
    mat = [list(data[i * width:(i + 1) * width]) for i in range(height)]
    return {
        "orig": [bytes(r) for r in mat],
        "flipx": [bytes(reversed(r)) for r in mat],
        "flipy": [bytes(r) for r in reversed(mat)],
        "transpose": [bytes(mat[y][x] for y in range(height)) for x in range(width)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Entry 1 record 0 against preserved runtime wall buffers."
    )
    parser.add_argument(
        "--lol2-root",
        default=os.environ.get("LOL2_DAT", DEFAULT_LOL2_ROOT),
        help="Path to LoL2 game root directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help="JSON output path",
    )
    args = parser.parse_args()

    local_mix = os.path.join(args.lol2_root, "LOCAL.MIX")
    atlas_data = read_mix_entry(local_mix, 1)
    textures = parse_atlas(atlas_data)
    tex0 = textures[0]
    pixels = extract_raw_pixels(atlas_data, tex0)
    if pixels is None:
        raise SystemExit("ERROR: failed to extract LOCAL.MIX entry 1 record 0")

    tex_rows = rows(pixels, tex0.width, tex0.height)
    tex_patch_maps = {
        8: patch_map(pixels, tex0.width, tex0.height, 8),
        16: patch_map(pixels, tex0.width, tex0.height, 16),
    }
    tex_variants = variant_rows(pixels, tex0.width, tex0.height)

    report: dict[str, object] = {
        "model": "LOCAL.MIX entry 1 record 0 runtime witness check",
        "status": "narrow direct-reuse check only",
        "entry1_record0": {
            "index": tex0.index,
            "width": tex0.width,
            "height": tex0.height,
            "total_size": tex0.total_size,
        },
        "targets": [],
    }

    for target in RUNTIME_TARGETS:
        data = Path(target["path"]).read_bytes()
        width = int(target["width"])
        height = int(target["height"])
        target_rows = rows(data, width, height)
        target_report: dict[str, object] = {
            "name": target["name"],
            "path": target["path"],
            "width": width,
            "height": height,
            "byte_length": len(data),
            "exact_full_match": data == pixels,
            "exact_substring_match": pixels in data,
            "best_row_match": best_row_match(tex_rows, target_rows),
            "variant_best_row_match": {},
            "exact_patch_match": {},
        }

        for variant_name, variant in tex_variants.items():
            target_report["variant_best_row_match"][variant_name] = best_row_match(variant, target_rows)

        for patch_size in (8, 16):
            found = None
            for y in range(height - patch_size + 1):
                for x in range(width - patch_size + 1):
                    block = b"".join(r[x:x + patch_size] for r in target_rows[y:y + patch_size])
                    if block in tex_patch_maps[patch_size]:
                        found = {
                            "entry1_xy": list(tex_patch_maps[patch_size][block]),
                            "target_xy": [x, y],
                        }
                        break
                if found is not None:
                    break
            target_report["exact_patch_match"][str(patch_size)] = found

        report["targets"].append(target_report)

    report["interpretation"] = (
        "These checks only test direct raw reuse under straightforward "
        "layout assumptions. Negative results do not prove Entry 1 record 0 "
        "is unrelated to runtime wall rendering, but they do argue against "
        "the simplest 'captured wall buffer == raw tex0' story."
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="ascii") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("Entry 1 runtime witness check")
    for target in report["targets"]:
        best = target["best_row_match"]
        print(
            f"  {target['name']}: full={target['exact_full_match']} "
            f"substring={target['exact_substring_match']} "
            f"best_row={best['equal_bytes']}/{best['row_width']} "
            f"patch8={target['exact_patch_match']['8'] is not None} "
            f"patch16={target['exact_patch_match']['16'] is not None}"
        )
    print(f"  report: {out_path}")


if __name__ == "__main__":
    main()
