#!/usr/bin/env python3
"""Extract wall textures from Lands of Lore 2 LOCAL.MIX.

Wall textures are stored as an atlas in LOCAL.MIX Entry 1.
Each texture is 8bpp palette-indexed.  Raw (uncompressed) textures
are extracted to PNG; compressed textures are reported but skipped.

Atlas layout (Entry 1)
----------------------
  u16  count         -- number of entries in the offset table
  u16  header_size   -- byte offset where texture data begins (= 4 + count*4)
  u32[count] offsets -- per-entry: u16 pad(0) + u16 offset

  Texture 0 starts implicitly at *header_size*.
  offset[i] for i in 0..count-2 gives the start of texture i+1.
  offset[count-1] is an end-of-data sentinel.

Per-texture sub-header (10 bytes)
---------------------------------
  u8   flags
  u8   format       -- 0x00 = raw 8bpp, 0x80 = compressed
  u16  reserved
  u8   width
  u8   height
  u8   pad           (always 0)
  u8   dimension     (usually == width)
  u16  total_size    (header + pixel data)

Palette
-------
  SETUP.MIX entry 54: 768 bytes, 256 RGB triplets, 6-bit VGA values (*4).
  LOCAL.MIX entry 94: 768 bytes, level-specific override palette.

Usage
-----
  python lol2_wall_texture_extract.py [-o OUTPUT_DIR] [-p setup|local]

  Environment:  LOL2_DAT  path to the LoL2 game root (parent of DAT/)
                          default: /media/bob/Arikv/REFERENCE/game_files/lol2/
"""

from __future__ import annotations

import argparse
import os
import struct
import sys

# ---------------------------------------------------------------------------
# Import the shared MIX parser from the same directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lol2_mix_parser import read_mix, read_mix_entry  # noqa: E402

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_LOL2_ROOT = "/media/bob/Arikv/REFERENCE/game_files/lol2/"
SETUP_PAL_ENTRY = 54       # SETUP.MIX palette entry index
LOCAL_PAL_ENTRY = 94       # LOCAL.MIX level palette entry index
ATLAS_ENTRY = 1            # LOCAL.MIX entry containing the wall atlas
SUB_HEADER_SIZE = 10

FMT_RAW = 0x00
FMT_COMPRESSED = 0x80


# ---------------------------------------------------------------------------
# Palette helpers
# ---------------------------------------------------------------------------

def load_vga_palette(raw_768: bytes) -> list[int]:
    """Convert 768-byte VGA 6-bit palette to flat [R,G,B,...] x 256."""
    pal: list[int] = []
    for i in range(256):
        r = min(255, raw_768[i * 3] * 4)
        g = min(255, raw_768[i * 3 + 1] * 4)
        b = min(255, raw_768[i * 3 + 2] * 4)
        pal.extend([r, g, b])
    return pal


def load_palette(lol2_root: str, source: str = "setup") -> list[int]:
    """Load a 256-colour palette from the game data.

    *source* is ``"setup"`` for SETUP.MIX entry 54 (global palette) or
    ``"local"`` for LOCAL.MIX entry 94 (level palette).
    """
    if source == "local":
        mix_path = os.path.join(lol2_root, "LOCAL.MIX")
        entry_idx = LOCAL_PAL_ENTRY
    else:
        mix_path = os.path.join(lol2_root, "SETUP.MIX")
        entry_idx = SETUP_PAL_ENTRY

    raw = read_mix_entry(mix_path, entry_idx)
    if len(raw) < 768:
        raise ValueError(
            f"Palette entry {entry_idx} in {mix_path} is only {len(raw)} bytes "
            f"(expected 768)"
        )
    return load_vga_palette(raw[:768])


# ---------------------------------------------------------------------------
# Atlas parser
# ---------------------------------------------------------------------------

class TextureInfo:
    """Metadata for one texture inside the atlas."""

    __slots__ = (
        "index", "offset", "flags", "format", "reserved",
        "width", "height", "pad", "dimension", "total_size",
    )

    def __init__(self, index: int, offset: int, header_bytes: bytes):
        self.index = index
        self.offset = offset
        self.flags = header_bytes[0]
        self.format = header_bytes[1]
        self.reserved = struct.unpack_from("<H", header_bytes, 2)[0]
        self.width = header_bytes[4]
        self.height = header_bytes[5]
        self.pad = header_bytes[6]
        self.dimension = header_bytes[7]
        self.total_size = struct.unpack_from("<H", header_bytes, 8)[0]

    @property
    def pixel_count(self) -> int:
        return self.width * self.height

    @property
    def is_raw(self) -> bool:
        """A texture is raw if total_size == 10 + width*height."""
        return self.total_size == SUB_HEADER_SIZE + self.pixel_count

    @property
    def is_compressed(self) -> bool:
        return not self.is_raw

    @property
    def pixel_data_size(self) -> int:
        return self.total_size - SUB_HEADER_SIZE

    @property
    def format_str(self) -> str:
        if self.is_raw:
            return "RAW"
        return "CMP"

    def __repr__(self) -> str:
        return (
            f"Tex[{self.index:2d}] {self.width:3d}x{self.height:3d} "
            f"{self.format_str:3s}  flags=0x{self.flags:02X}  "
            f"total={self.total_size:5d}  @{self.offset}"
        )


def parse_atlas(atlas_data: bytes) -> list[TextureInfo]:
    """Parse the texture atlas header and return a list of TextureInfo."""
    if len(atlas_data) < 4:
        raise ValueError("Atlas too small")

    count = struct.unpack_from("<H", atlas_data, 0)[0]
    header_size = struct.unpack_from("<H", atlas_data, 2)[0]

    expected_hdr = 4 + count * 4
    if header_size != expected_hdr:
        print(
            f"WARNING: header_size={header_size} but expected "
            f"4+{count}*4={expected_hdr}",
            file=sys.stderr,
        )

    # Build offset list: texture 0 is implicit at header_size,
    # offset table entries point to textures 1 .. count-1.
    # The last entry (index count-1) is an end sentinel.
    tex_offsets = [header_size]
    for i in range(count):
        off = struct.unpack_from("<H", atlas_data, 4 + i * 4 + 2)[0]
        tex_offsets.append(off)

    # The actual number of textures is count (not count+1);
    # the last offset is a sentinel marking end-of-data.
    textures: list[TextureInfo] = []
    num_textures = count  # textures indexed 0 .. count-1

    for i in range(num_textures):
        off = tex_offsets[i]
        end = tex_offsets[i + 1] if (i + 1) < len(tex_offsets) else len(atlas_data)

        if off + SUB_HEADER_SIZE > len(atlas_data):
            print(
                f"WARNING: texture {i} header at offset {off} overflows atlas "
                f"({len(atlas_data)} bytes); stopping.",
                file=sys.stderr,
            )
            break

        hdr = atlas_data[off : off + SUB_HEADER_SIZE]
        tex = TextureInfo(i, off, hdr)

        # Sanity: total_size should not exceed the gap to the next texture
        gap = end - off
        if tex.total_size > gap + 2:  # allow 2-byte tolerance for sentinel
            print(
                f"WARNING: texture {i} total_size={tex.total_size} but gap "
                f"to next={gap}",
                file=sys.stderr,
            )

        textures.append(tex)

    return textures


def extract_raw_pixels(atlas_data: bytes, tex: TextureInfo) -> bytes | None:
    """Return raw pixel bytes for a raw (uncompressed) texture, or None."""
    if not tex.is_raw:
        return None
    start = tex.offset + SUB_HEADER_SIZE
    length = tex.width * tex.height
    if start + length > len(atlas_data):
        print(
            f"WARNING: texture {tex.index} pixel data overflows atlas",
            file=sys.stderr,
        )
        return None
    return atlas_data[start : start + length]


# ---------------------------------------------------------------------------
# PNG writer (Pillow-optional fallback via raw PPM)
# ---------------------------------------------------------------------------

def _save_png_pil(pixels: bytes, width: int, height: int,
                  palette: list[int], path: str) -> None:
    from PIL import Image  # type: ignore
    img = Image.new("P", (width, height))
    img.putpalette(palette)
    img.putdata(list(pixels))
    img.save(path)


def _save_ppm_fallback(pixels: bytes, width: int, height: int,
                       palette: list[int], path: str) -> None:
    """Write a PPM file (no external deps) when Pillow is unavailable."""
    ppm_path = path.rsplit(".", 1)[0] + ".ppm"
    with open(ppm_path, "wb") as f:
        f.write(f"P6\n{width} {height}\n255\n".encode())
        for idx in pixels:
            f.write(bytes(palette[idx * 3 : idx * 3 + 3]))
    print(f"  (Pillow unavailable -- wrote PPM instead: {ppm_path})")


def save_texture(pixels: bytes, width: int, height: int,
                 palette: list[int], path: str) -> None:
    """Save an 8bpp indexed image as PNG (or PPM fallback)."""
    try:
        _save_png_pil(pixels, width, height, palette, path)
    except ImportError:
        _save_ppm_fallback(pixels, width, height, palette, path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract wall textures from LoL2 LOCAL.MIX"
    )
    parser.add_argument(
        "-o", "--output", default="lol2_wall_textures",
        help="Output directory (default: lol2_wall_textures)",
    )
    parser.add_argument(
        "-p", "--palette", choices=["setup", "local"], default="setup",
        help="Palette source: setup (SETUP.MIX entry 54) or local "
             "(LOCAL.MIX entry 94). Default: setup",
    )
    parser.add_argument(
        "--lol2-root",
        default=os.environ.get("LOL2_DAT", DEFAULT_LOL2_ROOT),
        help="Path to LoL2 game root directory (or set LOL2_DAT env var)",
    )
    parser.add_argument(
        "--list-only", action="store_true",
        help="Only list textures; do not extract",
    )
    args = parser.parse_args()

    lol2_root: str = args.lol2_root
    local_mix = os.path.join(lol2_root, "LOCAL.MIX")

    if not os.path.isfile(local_mix):
        print(f"ERROR: cannot find {local_mix}", file=sys.stderr)
        sys.exit(1)

    # ---- Load atlas data ---------------------------------------------------
    print(f"Loading atlas from {local_mix} entry {ATLAS_ENTRY} ...")
    atlas_data = read_mix_entry(local_mix, ATLAS_ENTRY)
    print(f"  Atlas size: {len(atlas_data):,d} bytes")

    count = struct.unpack_from("<H", atlas_data, 0)[0]
    header_size = struct.unpack_from("<H", atlas_data, 2)[0]
    print(f"  Count: {count}  Header size: {header_size}")

    # ---- Parse textures ----------------------------------------------------
    textures = parse_atlas(atlas_data)
    print(f"  Parsed {len(textures)} texture(s)\n")

    # ---- Summary table -----------------------------------------------------
    raw_count = 0
    cmp_count = 0
    other_count = 0
    size_set: set[tuple[int, int]] = set()

    print(f"{'Idx':>3s}  {'W':>4s} {'H':>4s}  {'Fmt':>3s}  "
          f"{'Flags':>5s}  {'Total':>6s}  {'Pixels':>6s}")
    print("-" * 48)
    for tex in textures:
        size_set.add((tex.width, tex.height))
        if tex.is_raw:
            raw_count += 1
        elif tex.is_compressed:
            cmp_count += 1
        else:
            other_count += 1
        print(
            f"{tex.index:3d}  {tex.width:4d} {tex.height:4d}  "
            f"{tex.format_str:>3s}  0x{tex.flags:02X}  "
            f"{tex.total_size:6d}  {tex.pixel_count:6d}"
        )

    print(f"\nSummary: {len(textures)} textures total")
    print(f"  Raw (extractable): {raw_count}")
    print(f"  Compressed:        {cmp_count}")
    if other_count:
        print(f"  Other format:      {other_count}")
    print(f"  Unique sizes:      {sorted(size_set)}")

    if args.list_only:
        return

    # ---- Load palette ------------------------------------------------------
    print(f"\nLoading palette ({args.palette}) ...")
    palette = load_palette(lol2_root, args.palette)

    # Show a few sample palette entries
    for idx in [0, 77, 90, 91, 92, 93, 255]:
        r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
        print(f"  pal[{idx:3d}] = ({r:3d}, {g:3d}, {b:3d})")

    # ---- Extract -----------------------------------------------------------
    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)
    extracted = 0

    for tex in textures:
        pixels = extract_raw_pixels(atlas_data, tex)
        if pixels is None:
            # Skip compressed / invalid
            continue

        fname = f"tex_{tex.index:03d}_{tex.width}x{tex.height}.png"
        path = os.path.join(out_dir, fname)
        save_texture(pixels, tex.width, tex.height, palette, path)
        extracted += 1
        print(f"  Extracted: {fname}")

    print(f"\nDone: {extracted} raw texture(s) extracted to {out_dir}/")
    if cmp_count:
        print(f"  ({cmp_count} compressed texture(s) skipped -- "
              f"decompressor not yet implemented)")


if __name__ == "__main__":
    main()
