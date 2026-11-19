#!/usr/bin/env python3
"""Draw a top-down schematic map of a LoL2 level from its region polygons.

Reads the vertex and region tables of the level data entry (docs/formats/geometry.md)
and draws every region as a polygon shaded by floor height (darker = higher),
wall sides as dark lines and portal sides as light lines. The picture holds no
game pixels: it is a plot of the geometry numbers.

  lol2_level_map.py --data DAT --level 1 --out map.png [--size 1600]
  lol2_level_map.py --check --data DAT      # one line: every region polygon of the
                                            # 15 levels has 4 distinct in-range corners
Needs Pillow for --out.
"""
from cli_errors import run_cli
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lol2_cli  # noqa: E402
import lol2_source_format as S  # noqa: E402
from lol2_level_report import level_files  # noqa: E402


def load(data_dir, stem):
    b = (Path(data_dir) / f"{stem}.MIX").read_bytes()
    _, raw = S.level_geometry(b)
    nv, nr = struct.unpack_from("<I", raw, 0x50)[0], struct.unpack_from("<I", raw, 0x58)[0]
    vo, ro = struct.unpack_from("<I", raw, 0x04)[0], struct.unpack_from("<I", raw, 0x0C)[0]
    verts = [struct.unpack_from("<ii", raw, vo + 8 * i) for i in range(nv)]
    regs = [struct.unpack_from("<22H", raw, ro + 44 * i) for i in range(nr)]
    return verts, regs


def s16(n):
    return n - 65536 if n & 0x8000 else n


def draw(verts, regs, out, size):
    from PIL import Image, ImageDraw
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    scale = (size - 20) / max(x1 - x0, y1 - y0, 1)
    width, height = int((x1 - x0) * scale) + 20, int((y1 - y0) * scale) + 20
    pt = lambda v: (10 + (verts[v][0] - x0) * scale, 10 + (y1 - verts[v][1]) * scale)  # north up
    floors = [s16(r[10]) for r in regs]
    lo, hi = min(floors), max(floors)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for r, f in sorted(zip(regs, floors), key=lambda t: t[1]):  # lower floors first, higher drawn on top
        g = 200 - int(140 * (f - lo) / max(hi - lo, 1))
        d.polygon([pt(v) for v in r[6:10]], fill=(g, g, 255 - (200 - g) // 2))
    for r in regs:
        for s in range(4):
            a, b = pt(r[6 + s]), pt(r[6 + (s + 1) % 4])
            if r[2 + s] == 0xFFFF:
                d.line([a, b], fill=(20, 20, 20), width=2)
            else:
                d.line([a, b], fill=(235, 235, 235), width=1)
    img.save(out)
    return lo, hi


def main():
    ap = lol2_cli.tool_args(__doc__ or "")
    ap.add_argument("--level", type=int)
    ap.add_argument("--size", type=int, default=1600)
    a = ap.parse_args()
    stems = level_files(a.data)
    if a.check:
        regions = degenerate = 0
        for stem in stems:
            verts, regs = load(a.data, stem)
            regions += len(regs)
            degenerate += sum(1 for r in regs if len(set(r[6:10])) != 4 or any(v >= len(verts) for v in r[6:10]))
        print(f"CHECK level_map: {len(stems)} levels, {regions:,} region polygons; with repeated or out-of-range "
              f"corners: {degenerate}")
        return 0
    if a.level is None or not a.out:
        ap.print_help(); return 2
    stem = [s for s in stems if int(s.split("_")[0][1:]) == a.level]
    if not stem:
        ap.error(f"no level archive L{a.level}_*.MIX")
    verts, regs = load(a.data, stem[0])
    lo, hi = draw(verts, regs, a.out, a.size)
    print(f"{stem[0]}: {len(regs)} regions drawn to {a.out} (floor heights {lo} to {hi}; darker = higher)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
