#!/usr/bin/env python3
"""
Decode 0x2256 Westwood Cell sprites from LoL2 MIX archives (MCEL.MIX, TDOOR.MIX, etc.).
Merges cell format detection (0x2256 header, AFDE block parsing) with 8bpp and 4bpp
rendering into PNG images.

Requires: Pillow (PIL)

Environment variables:
  LOL2_DAT       - path to the LoL2 DAT directory (default: current directory)
  LOL2_OUT       - output directory (default: ./lol2_sprite_out)
  LOL2_PALETTE   - path to a PCX file to use as palette source (optional)
"""
import struct, os, sys, argparse
from pathlib import Path
from PIL import Image


# ---------------------------------------------------------------------------
# Decompression: Format80 (Westwood LCW)
# ---------------------------------------------------------------------------
def decompress_f80(src, pos=0, max_out=4*1024*1024):
    """Westwood Format80 / LCW decompressor."""
    out = bytearray()
    end = len(src)
    while pos < end and len(out) < max_out:
        cmd = src[pos]; pos += 1
        if cmd == 0:
            break
        elif cmd < 0x80:
            if pos >= end: break
            b2 = src[pos]; pos += 1
            count = ((cmd >> 4) & 0x0F) + 3
            src_p = len(out) - (((cmd & 0x0F) << 8) | b2)
            if src_p < 0: src_p = 0
            for _ in range(count):
                out.append(out[src_p] if 0 <= src_p < len(out) else 0)
                src_p += 1
        elif cmd == 0x80:
            count = struct.unpack_from('<H', src, pos)[0]; pos += 2
            if count == 0: break
            sp = struct.unpack_from('<H', src, pos)[0]; pos += 2
            out.extend(out[sp:sp+count])
        elif cmd < 0xC0:
            count = cmd & 0x3F
            if count == 0: break
            out.extend(src[pos:pos+count]); pos += count
        elif cmd < 0xFE:
            count = (cmd & 0x1F) + 3
            sp = struct.unpack_from('<H', src, pos)[0]; pos += 2
            out.extend(out[sp:sp+count])
        elif cmd == 0xFE:
            count = struct.unpack_from('<H', src, pos)[0]; pos += 2
            fill = src[pos]; pos += 1
            out.extend([fill]*count)
        else:  # 0xFF
            count = struct.unpack_from('<H', src, pos)[0]; pos += 2
            fill = src[pos]; pos += 1
            out.extend([fill]*count)
            break
    return bytes(out)


# ---------------------------------------------------------------------------
# Cell format constants
# ---------------------------------------------------------------------------
BLOCK_SIZE   = 520
BLOCK_HEADER = 4
OUTER_HEADER = 16


def get_raw_pixels(data):
    """Extract all raw pixel bytes from a 0x2256 chunk via AFDE block parsing."""
    if data[:2] != b'\x22\x56':
        return b''
    pixels = bytearray()
    pos = OUTER_HEADER
    while pos < len(data):
        if pos + BLOCK_HEADER > len(data):
            break
        if data[pos:pos+2] != b'\xAF\xDE':
            break
        comp_sz = struct.unpack_from('<H', data, pos+2)[0]
        block_end = min(pos + BLOCK_SIZE, len(data))
        raw_start = pos + BLOCK_HEADER
        if comp_sz == 0:
            pixels.extend(data[raw_start:block_end])
        else:
            pixels.extend(data[raw_start:raw_start+comp_sz])
        pos += BLOCK_SIZE
    return bytes(pixels)


# ---------------------------------------------------------------------------
# Image rendering (8bpp and 4bpp)
# ---------------------------------------------------------------------------
def save_image(raw, w, h, out_path, bpp=8, palette=None):
    """Save raw pixel data as a PNG. Returns True on success."""
    n_pixels = w * h
    if bpp == 8:
        if len(raw) < n_pixels:
            return False
        img = Image.frombytes('P', (w, h), raw[:n_pixels])
    elif bpp == 4:
        needed = (n_pixels + 1) // 2
        if len(raw) < needed:
            return False
        expanded = bytearray()
        for b in raw[:needed]:
            expanded.append((b >> 4) & 0xF)
            expanded.append(b & 0xF)
        img = Image.frombytes('P', (w, h), bytes(expanded[:n_pixels]))
        if not palette:
            img.putpalette([i*17 for i in range(16)] * 16 + [0]*(256-16)*3)
    else:
        return False

    if palette:
        img.putpalette(palette)
    img.convert('RGB').save(str(out_path))
    return True


def decode_cell(data, label, out_dir, palette=None):
    """Decode a single 0x2256 cell and render at all plausible dimensions."""
    if data[:2] != b'\x22\x56':
        return []

    unk67 = struct.unpack_from('<H', data, 6)[0]
    raw = get_raw_pixels(data)
    n = len(raw)
    saved = []

    if n == 0:
        return saved

    candidate_widths = [16, 24, 32, 40, 48, 56, 64, 80, 96, 100, 112, 128, 160, 192, 200, 256]

    # Strategy 1: unk67 = total pixel count
    if unk67 > 0:
        for w in candidate_widths:
            if unk67 % w == 0:
                h = unk67 // w
                if 8 <= h <= 512:
                    for bpp in [8, 4]:
                        name = f"{label}_u67_{bpp}bpp_{w}x{h}.png"
                        path = out_dir / name
                        if save_image(raw, w, h, path, bpp, palette):
                            saved.append(str(path))

    # Strategy 2: raw byte count = w*h (8bpp direct fit)
    for w in candidate_widths:
        if n >= w and n % w == 0:
            h = n // w
            if 8 <= h <= 512:
                name = f"{label}_raw_{w}x{h}.png"
                path = out_dir / name
                if save_image(raw, w, h, path, 8, palette):
                    saved.append(str(path))

    # Strategy 3: one AFDE block per row
    nblocks = (len(data) - OUTER_HEADER + BLOCK_SIZE - 1) // BLOCK_SIZE
    if nblocks > 0 and n > 0:
        bytes_per_block = n // nblocks
        if 8 <= bytes_per_block <= 512:
            for bpp, mult in [(8, 1), (4, 2)]:
                w = bytes_per_block * mult
                name = f"{label}_row{bpp}_{w}x{nblocks}.png"
                path = out_dir / name
                if save_image(raw, w, nblocks, path, bpp, palette):
                    saved.append(str(path))

    return saved


# ---------------------------------------------------------------------------
# MIX file reading
# ---------------------------------------------------------------------------
def read_mix(path):
    """Read a Westwood MIX archive."""
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack_from("<H", data, 0)[0]
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, o, s = struct.unpack_from("<III", data, off)
        entries.append((h, o, s))
    return data, entries, 6 + count * 12


def process_mix(mix_path, out_dir, palette=None, max_entries=None):
    """Process all 0x2256 cell entries in a MIX file."""
    data, entries, base = read_mix(mix_path)
    label = Path(mix_path).stem
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"{label} ({len(entries)} entries)")
    print(f"{'='*60}")

    total_saved = 0
    count = 0
    for i, (h, o, s) in enumerate(entries):
        chunk = data[base+o:base+o+s]

        if chunk[:2] == b'\x22\x56':
            unk67 = struct.unpack_from('<H', chunk, 6)[0]
            raw = get_raw_pixels(chunk)
            print(f"\n  Entry {i}: size={s} magic=2256 raw_bytes={len(raw)} unk67={unk67}")

            saved = decode_cell(chunk, f"{label}_e{i:03d}", out_dir, palette)
            for p in saved:
                print(f"    Saved: {os.path.basename(p)}")
            total_saved += len(saved)

            count += 1
            if max_entries and count >= max_entries:
                break

        elif chunk[:4] == b'FORM':
            print(f"  Entry {i}: VQA/IFF (skipped)")

    print(f"\n  Total PNGs saved: {total_saved}")
    return total_saved


def load_palette(palette_path):
    """Load a palette from a PCX or palette image file."""
    if palette_path and os.path.isfile(palette_path):
        try:
            img = Image.open(palette_path)
            pal = img.getpalette()
            if pal:
                print(f"Palette loaded from {palette_path}")
                return pal
        except Exception:
            pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Decode 0x2256 cell sprites from a LoL2 MIX archive into PNGs.")
    parser.add_argument("mix_path",
                        help="Path to a MIX file (e.g. MCEL.MIX or TDOOR.MIX)")
    parser.add_argument("-o", "--output", default=None,
                        help="Output directory (default: LOL2_OUT or ./lol2_sprite_out)")
    parser.add_argument("-p", "--palette", default=None,
                        help="Path to a PCX file to use as palette (default: LOL2_PALETTE env)")
    parser.add_argument("-n", "--max-entries", type=int, default=None,
                        help="Maximum number of cell entries to decode")
    args = parser.parse_args()

    out_dir = args.output or os.environ.get("LOL2_OUT", "./lol2_sprite_out")
    palette_path = args.palette or os.environ.get("LOL2_PALETTE")
    palette = load_palette(palette_path)

    if not os.path.isfile(args.mix_path):
        print(f"Error: file not found: {args.mix_path}", file=sys.stderr)
        sys.exit(1)

    process_mix(args.mix_path, out_dir, palette, args.max_entries)


if __name__ == "__main__":
    main()
