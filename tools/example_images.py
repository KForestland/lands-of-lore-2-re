#!/usr/bin/env python3
"""Check that every image the repository shows is exactly what today's tools make from the game files.

  example_images.py --data DAT --check            # regenerate each image in a temporary folder and compare pixels
  example_images.py --data DAT --out-dir new/     # write today's versions (to replace stale images)

Each image is listed in IMAGES with the tool command that makes it. Pixels are compared after
conversion to RGBA, so PNG compression settings do not matter. Every PNG under examples/ and
docs/images/ must be listed.
"""
import os
import subprocess
import sys
import tempfile

import lol2_cli

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# repository path -> (tool, arguments; the tool writes the file named by --out)
IMAGES = {
    "docs/images/l1_dc_regions.png": ("lol2_level_map.py", ["--level", "1", "--size", "900"]),
}


def make(data_dir, path):
    tool, args = IMAGES[path]
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, os.path.basename(path))
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", tool), "--data", data_dir, *args, "--out", out],
                           capture_output=True, text=True)
        if p.returncode:
            raise ValueError(f"{path}: {tool} failed: {(p.stderr or p.stdout).strip()[-200:]}")
        with open(out, "rb") as f:
            return f.read()


def pixels(blob):
    import io
    from PIL import Image
    image = Image.open(io.BytesIO(blob)).convert("RGBA")
    return image.size, image.tobytes()


def main():
    ap = lol2_cli.tool_args(__doc__, out_help=argparse_suppressed())
    ap.add_argument("--out-dir", help="write today's versions here")
    a = ap.parse_args()
    if not (a.check or a.out_dir):
        ap.print_help(); return 2
    shown = sorted(os.path.relpath(os.path.join(d, n), ROOT)
                   for top in ("examples", "docs/images") for d, _, fs in os.walk(os.path.join(ROOT, top))
                   for n in fs if n.lower().endswith(".png"))
    stale = []
    for path in sorted(IMAGES):
        today = make(a.data, path)
        if a.out_dir:
            os.makedirs(a.out_dir, exist_ok=True)
            with open(os.path.join(a.out_dir, os.path.basename(path)), "wb") as f:
                f.write(today)
        full = os.path.join(ROOT, path)
        if a.check and (not os.path.exists(full) or pixels(open(full, "rb").read()) != pixels(today)):
            stale.append(path)
    unlisted = [p for p in shown if p not in IMAGES]
    if a.check:
        if stale or unlisted:
            print(f"CHECK example_images: FAIL stale {stale or 'none'}, not made by a listed command {unlisted or 'none'}")
            return 1
        print(f"CHECK example_images: {len(IMAGES)} shown image equals today's tool output pixel for pixel")
    return 0


def argparse_suppressed():
    return "not used"


if __name__ == "__main__":
    sys.exit(main())
