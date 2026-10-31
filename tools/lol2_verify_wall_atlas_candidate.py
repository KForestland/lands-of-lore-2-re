#!/usr/bin/env python3
"""Verify the current LOCAL.MIX wall-atlas candidate model.

This is a repo-first verifier, not a new extraction theory.

It answers a narrow question:
  "What does the current public atlas model from LOCAL.MIX entry 1
   deterministically reproduce?"

Current checks:
  - parse LOCAL.MIX entry 1 as the candidate wall atlas
  - summarize raw vs compressed texture records
  - extract the first raw texture (texture 0)
  - render texture 0 with the setup and local palettes
  - compare the setup-palette render against the repo example

The script intentionally does not claim runtime provenance closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lol2_wall_texture_extract import (  # noqa: E402
    extract_raw_pixels,
    load_palette,
    parse_atlas,
    read_mix_entry,
)
from lol2_decompress_sphere import parse_entry1  # noqa: E402
from lol2_sprite_decode import decompress_f80  # noqa: E402


DEFAULT_LOL2_ROOT = "lol2_game/"
DEFAULT_EXAMPLE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "L1_wall_texture_000.png",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_indexed_png(
    pixels: bytes,
    width: int,
    height: int,
    palette: list[int],
    path: str,
) -> None:
    from PIL import Image  # type: ignore

    img = Image.new("P", (width, height))
    img.putpalette(palette)
    img.putdata(list(pixels))
    img.save(path)


def probe_skip_decode(
    payload: bytes,
    pixel_count: int,
    max_skip: int = 16,
) -> dict[str, object]:
    exact_hits: list[dict[str, int]] = []
    near_hits: list[dict[str, int]] = []
    for skip in range(0, min(max_skip, len(payload))):
        try:
            decoded = decompress_f80(payload[skip:])
        except Exception:
            continue
        info = {"skip": skip, "decoded_size": len(decoded)}
        if len(decoded) == pixel_count:
            exact_hits.append(info)
        elif abs(len(decoded) - pixel_count) <= 8:
            near_hits.append(info)
    return {
        "exact_hits": exact_hits,
        "near_hits": near_hits,
    }


def image_sha256(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def rgb_stats(path: str) -> dict[str, object]:
    from PIL import Image  # type: ignore

    img = Image.open(path).convert("RGB")
    colors = img.getcolors(maxcolors=10000000) or []
    colors.sort(reverse=True)
    top = [
        {"count": count, "rgb": list(rgb)}
        for count, rgb in colors[:10]
    ]
    return {
        "size": [img.width, img.height],
        "unique_rgb": len(colors),
        "top10": top,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the current LOCAL.MIX wall-atlas candidate model."
    )
    parser.add_argument(
        "--lol2-root",
        default=os.environ.get("LOL2_DAT", DEFAULT_LOL2_ROOT),
        help="Path to LoL2 game root directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="atlas_candidate_verify",
        help="Output directory for report and rendered textures",
    )
    parser.add_argument(
        "--example",
        default=DEFAULT_EXAMPLE,
        help="Repo example PNG to compare against",
    )
    args = parser.parse_args()

    lol2_root = args.lol2_root
    local_mix = os.path.join(lol2_root, "LOCAL.MIX")
    if not os.path.isfile(local_mix):
        raise SystemExit(f"ERROR: cannot find {local_mix}")

    os.makedirs(args.output, exist_ok=True)

    atlas_data = read_mix_entry(local_mix, 1)
    textures = parse_atlas(atlas_data)
    sphere_sections = parse_entry1(atlas_data)

    raw_textures = [tex for tex in textures if tex.is_raw]
    compressed_textures = [tex for tex in textures if tex.is_compressed]
    raw_sizes = Counter((tex.width, tex.height) for tex in raw_textures)
    cmp_sizes = Counter((tex.width, tex.height) for tex in compressed_textures)

    report: dict[str, object] = {
        "model": "LOCAL.MIX entry 1 atlas candidate",
        "status": "candidate-only; not runtime-proven",
        "inputs": {
            "lol2_root": lol2_root,
            "local_mix": local_mix,
            "entry_index": 1,
            "atlas_size": len(atlas_data),
        },
        "atlas_header": {
            "count": len(textures),
            "header_size": int.from_bytes(atlas_data[2:4], "little"),
        },
        "texture_counts": {
            "raw": len(raw_textures),
            "compressed": len(compressed_textures),
        },
        "raw_sizes": {f"{w}x{h}": n for (w, h), n in sorted(raw_sizes.items())},
        "compressed_sizes": {f"{w}x{h}": n for (w, h), n in sorted(cmp_sizes.items())},
    }

    sphere_equivalent_count = 0
    sphere_examples: list[dict[str, object]] = []
    for tex in textures:
        sec = sphere_sections.get(tex.index)
        if sec is None:
            continue
        if (
            tex.width == sec["w"]
            and tex.height == sec["h"]
            and tex.total_size == sec["total_size"]
        ):
            sphere_equivalent_count += 1
            if len(sphere_examples) < 10:
                sphere_examples.append(
                    {
                        "index": tex.index,
                        "atlas": {
                            "offset": tex.offset,
                            "width": tex.width,
                            "height": tex.height,
                            "flags": tex.flags,
                            "format_byte": tex.format,
                            "total_size": tex.total_size,
                        },
                        "sphere": {
                            "flags": sec["flags"],
                            "width": sec["w"],
                            "height": sec["h"],
                            "total_size": sec["total_size"],
                            "decoded_size": sec["decoded_size"],
                        },
                    }
                )

    report["sphere_cross_check"] = {
        "section_count": len(sphere_sections),
        "same_count_as_atlas": len(sphere_sections) == len(textures),
        "same_record_count": sphere_equivalent_count,
        "same_record_dimensions_and_sizes": sphere_equivalent_count == len(textures),
        "examples": sphere_examples,
        "interpretation": (
            "LOCAL.MIX entry 1 also parses cleanly as the repo's known "
            "Sphere room-section structure. Atlas-like dimensions/sizes "
            "alone do not prove these records are texture sub-images."
        ),
    }

    compressed_probe: list[dict[str, object]] = []
    f80_match_count = 0
    skip_match_count = 0
    exact_skip_hits: list[dict[str, object]] = []
    for tex in compressed_textures:
        start = tex.offset + 10
        payload = atlas_data[start : tex.offset + tex.total_size]
        entry: dict[str, object] = {
            "index": tex.index,
            "width": tex.width,
            "height": tex.height,
            "flags": tex.flags,
            "format_byte": tex.format,
            "payload_size": len(payload),
            "pixel_count": tex.pixel_count,
            "payload_prefix": payload[:8].hex(),
        }
        try:
            decoded = decompress_f80(payload)
            entry["f80_decoded_size"] = len(decoded)
            entry["f80_matches_pixel_count"] = len(decoded) == tex.pixel_count
            if len(decoded) == tex.pixel_count:
                f80_match_count += 1
        except Exception as exc:
            entry["f80_error"] = str(exc)
            entry["f80_matches_pixel_count"] = False
        skip_probe = probe_skip_decode(payload, tex.pixel_count)
        entry["skip_probe"] = skip_probe
        if skip_probe["exact_hits"]:
            skip_match_count += 1
            exact_skip_hits.append(
                {
                    "index": tex.index,
                    "width": tex.width,
                    "height": tex.height,
                    "exact_hits": skip_probe["exact_hits"],
                }
            )
        compressed_probe.append(entry)

    report["compressed_probe"] = {
        "decoder_tested": "lol2_sprite_decode.decompress_f80",
        "match_count": f80_match_count,
        "skip_match_count": skip_match_count,
        "skip_exact_hit_records": exact_skip_hits,
        "record_count": len(compressed_probe),
        "records": compressed_probe,
    }

    if not raw_textures:
        report["result"] = "no raw textures found"
    else:
        tex0 = raw_textures[0]
        pixels = extract_raw_pixels(atlas_data, tex0)
        if pixels is None:
            raise SystemExit("ERROR: failed to extract raw pixels for texture 0")

        setup_pal = load_palette(lol2_root, "setup")
        local_pal = load_palette(lol2_root, "local")

        out_setup = os.path.join(args.output, "tex0_setup.png")
        out_local = os.path.join(args.output, "tex0_local.png")
        save_indexed_png(pixels, tex0.width, tex0.height, setup_pal, out_setup)
        save_indexed_png(pixels, tex0.width, tex0.height, local_pal, out_local)

        tex_report: dict[str, object] = {
            "index": tex0.index,
            "offset": tex0.offset,
            "width": tex0.width,
            "height": tex0.height,
            "total_size": tex0.total_size,
            "flags": tex0.flags,
            "format_byte": tex0.format,
            "pixel_sha256": sha256_bytes(pixels),
            "setup_png": {
                "path": out_setup,
                "sha256": image_sha256(out_setup),
                "stats": rgb_stats(out_setup),
            },
            "local_png": {
                "path": out_local,
                "sha256": image_sha256(out_local),
                "stats": rgb_stats(out_local),
            },
        }

        if os.path.isfile(args.example):
            example_sha = image_sha256(args.example)
            tex_report["example_compare"] = {
                "example_path": args.example,
                "example_sha256": example_sha,
                "matches_setup_png": example_sha == tex_report["setup_png"]["sha256"],
            }
        else:
            tex_report["example_compare"] = {
                "example_path": args.example,
                "present": False,
            }

        report["texture0"] = tex_report

    report_path = os.path.join(args.output, "report.json")
    with open(report_path, "w", encoding="ascii") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")

    print("Atlas candidate verification")
    print(f"  atlas bytes: {len(atlas_data)}")
    print(f"  textures: {len(textures)}")
    print(f"  raw: {len(raw_textures)}  compressed: {len(compressed_textures)}")
    if raw_textures:
        tex0 = report["texture0"]
        print("  texture0:")
        print(f"    size: {tex0['width']}x{tex0['height']}")
        print(f"    pixel sha256: {tex0['pixel_sha256']}")
        cmp_info = tex0["example_compare"]
        if cmp_info.get("matches_setup_png") is True:
            print("    repo example: exact match to setup-palette render")
        elif cmp_info.get("present") is False:
            print("    repo example: not present")
        else:
            print("    repo example: does not match setup-palette render")
    print(
        "  compressed probe:"
        f" {report['compressed_probe']['match_count']}"
        f" / {report['compressed_probe']['record_count']}"
        " records match pixel_count with direct f80 decode"
    )
    print(
        "  skip probe:"
        f" {report['compressed_probe']['skip_match_count']}"
        f" / {report['compressed_probe']['record_count']}"
        " records match pixel_count after skipping a short prefix"
    )
    print(f"  report: {report_path}")


if __name__ == "__main__":
    main()
