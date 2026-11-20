#!/usr/bin/env python3
"""Read game files and compare the published LoL2 example images.

  example_images.py --data DAT --check            # regenerate each image in a temporary folder and compare pixels
  example_images.py --data DAT --out-dir new/     # write today's versions (to replace stale images)

Each image is listed in IMAGES with the tool command that makes it. Pixels are compared after
conversion to RGBA, so PNG compression settings do not matter. Pillow versions draw a few edge
pixels differently, so a regenerated image must either equal the published one or be one of the
measured renderings in RASTER_VARIANTS. Every PNG under examples/ and docs/images/ must be listed.
"""
from cli_errors import run_cli
from hashlib import sha256
import os
import subprocess
import sys
import tempfile

import lol2_cli

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# repository path -> (tool, arguments; the tool writes the file named by --out)
IMAGES = {
    "docs/images/l1_dc_regions.png": ("lol2_level_map.py", ["--level", "1", "--size", "900"]),
    "examples/l5_hc_schematic.png": ("lol2_level_schematic.py", [
        "--level", "5", "--focus", "792", "--radius", "360", "--size", "660",
    ]),
}


# RGBA digests of each image as drawn by the Pillow versions that requirements.txt allows,
# measured on Pillow 10.1.0 through 13.0.0. The published images are the 10.2 renderings.
RASTER_VARIANTS = {
    "docs/images/l1_dc_regions.png": {
        "07cd714d52a909a788e5838609d5260352cca98306ad5424ff362d481a343ccc",  # Pillow 11.1.0
        "09a44c6ca58b261e613aa629f42bdabf01257955878af560885e4b47bf107363",  # Pillow 11.2.1 to 13.0.0
    },
    "examples/l5_hc_schematic.png": {
        "2404e948425f370b7f6e92b8291f4b33b9b507032e547fddd59a793066cf1651",  # Pillow 12.0.0 to 13.0.0
        "bdf7f29717efc3d241b99f83617f6b2dc9f7cea3afea66b33fb49a52e961f454",  # Pillow 10.1.0
    },
}


def matches(path, published, generated):
    if published == generated:
        return True
    return (published[0] == generated[0]
            and sha256(generated[1]).hexdigest() in RASTER_VARIANTS.get(path, set()))


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
    ap = lol2_cli.tool_args(__doc__, out_help="write today's versions to this directory",
                            out_aliases=("--out-dir",))
    a = ap.parse_args()
    if not (a.check or a.out):
        ap.print_help(); return 2
    shown = sorted(os.path.relpath(os.path.join(d, n), ROOT)
                   for top in ("examples", "docs/images") for d, _, fs in os.walk(os.path.join(ROOT, top))
                   for n in fs if n.lower().endswith(".png"))
    stale = []
    for path in sorted(IMAGES):
        today = make(a.data, path)
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            with open(os.path.join(a.out, os.path.basename(path)), "wb") as f:
                f.write(today)
        full = os.path.join(ROOT, path)
        if a.check and (not os.path.exists(full) or not matches(path, pixels(open(full, "rb").read()), pixels(today))):
            stale.append(path)
    unlisted = [p for p in shown if p not in IMAGES]
    if a.check:
        if stale or unlisted:
            print(f"CHECK example_images: FAIL stale {stale or 'none'}, not made by a listed command {unlisted or 'none'}")
            return 1
        print(f"CHECK example_images: all {len(IMAGES)} shown images match a measured rendering of today's tool output")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
