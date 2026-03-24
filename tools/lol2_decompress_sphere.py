#!/usr/bin/env python3
"""Sphere engine LZ77 decompressor for Lands of Lore 2 room sub-sections.
Reverse-engineered from LOCAL.MIX Entry 1 (Draracle Caverns).

Algorithm (Gemini's analysis, confirmed working):
  0x80-0xBF: Literal copy — count = cmd & 0x3F
  0x00-0x7F: Short relative copy — count = (cmd>>4)+3, offset = ((cmd&0xF)<<8)|next_byte
  0xC0-0xFF: Long absolute copy — count = (cmd&0x3F)+3, abs_offset = next_2_bytes (LE)

IMPORTANT: Sections within a rotation group use CHAINED decoding — each section's
LZ77 reads from a buffer pre-filled with the previous section's output. This is how
the Sphere engine achieves high compression for rotated room variants.

12-byte section header:
  [0-1] uint16 flags
  [2-3] uint16 always 0
  [4]   uint8  width
  [5]   uint8  height
  [6]   uint8  always 0
  [7]   uint8  width (duplicate)
  [8-9] uint16 total_section_size
  [10-11] uint16 decoded_output_size

Void-skip RLE (applied to decoded buffer to produce W*H grid):
  Non-zero byte -> place as tile at current grid position, advance
  0x00 followed by next byte N -> skip N grid positions (void cells)

Room groups (chained within each group):
  Secs 1-2:   corridors (5x32, 32x5)
  Secs 3-6:   16x16 corner pieces (4 rotations)
  Secs 7-10:  17x17 cave boundaries (4 rotations)
  Secs 11-14: 29x29 large chambers (4 rotations)
  Secs 16-19: 8x8/8x6 small rooms (4 rotations)
  Secs 20-23: 10x10 medium rooms (4 rotations)
  Secs 24-38: 16x16 individual cave rooms (chained sequentially)

Usage:
  python lol2_decompress_sphere.py <entry1_blob> [section_index]

  If section_index is given, prints only that section.
  Otherwise prints a summary of all sections.

Environment variables:
  LOL2_DAT  - path to the LoL2 DAT/ directory (default: current directory)
"""
import os
import struct
import sys


# Room groups for chained decoding
ROOM_GROUPS = [
    [1, 2],
    [3, 4, 5, 6],
    [7, 8, 9, 10],
    [11, 12, 13, 14],
    [16, 17, 18, 19],
    [20, 21, 22, 23],
    list(range(24, 39)),
]

LOL2_DAT = os.environ.get("LOL2_DAT", ".")


def decompress(payload: bytes, decoded_size: int, ref_buf: bytes = None) -> bytes:
    """Decompress Sphere LZ77 payload into raw byte buffer.

    Args:
        payload: compressed data after 12-byte header
        decoded_size: expected output size (from header bytes 10-11)
        ref_buf: optional reference buffer from previous section (for chained decode)
    """
    out = bytearray(decoded_size)
    if ref_buf:
        copy_len = min(len(ref_buf), decoded_size)
        out[:copy_len] = ref_buf[:copy_len]

    write_pos = 0
    inp = 0

    while write_pos < decoded_size and inp < len(payload):
        cmd = payload[inp]; inp += 1

        if 0x80 <= cmd <= 0xBF:
            # Literal copy
            cnt = cmd & 0x3F
            if cnt == 0:
                cnt = 64
            take = min(cnt, len(payload) - inp, decoded_size - write_pos)
            out[write_pos:write_pos + take] = payload[inp:inp + take]
            write_pos += take; inp += take

        elif 0x00 <= cmd <= 0x7F:
            # Short relative copy
            cnt = (cmd >> 4) + 3
            if inp < len(payload):
                nb = payload[inp]; inp += 1
                offset = ((cmd & 0x0F) << 8) | nb
            else:
                offset = 1
            for _ in range(cnt):
                if write_pos >= decoded_size:
                    break
                if offset == 0:
                    out[write_pos] = 0
                else:
                    src = write_pos - offset
                    out[write_pos] = out[src] if src >= 0 else 0
                write_pos += 1

        elif 0xC0 <= cmd <= 0xFF:
            # Long absolute copy (reads from pre-allocated/pre-filled buffer)
            cnt = (cmd & 0x3F) + 3
            if inp + 1 < len(payload):
                abs_off = struct.unpack_from("<H", payload, inp)[0]; inp += 2
            elif inp < len(payload):
                abs_off = payload[inp]; inp += 1
            else:
                abs_off = 0
            for _ in range(cnt):
                if write_pos >= decoded_size:
                    break
                out[write_pos] = out[abs_off % decoded_size]
                write_pos += 1; abs_off += 1

    return bytes(out)


def decode_room(decoded: bytes, w: int, h: int) -> list:
    """Apply void-skip RLE to decoded buffer, producing W*H tile grid.

    Returns list of lists: grid[y][x] = tile_value (0 = void)
    """
    grid = [[0] * w for _ in range(h)]
    pos = 0
    i = 0
    while i < len(decoded) and pos < w * h:
        b = decoded[i]
        if b != 0:
            y, x = divmod(pos, w)
            grid[y][x] = b
            pos += 1
            i += 1
        else:
            if i + 1 < len(decoded):
                pos += decoded[i + 1]
                i += 2
            else:
                break
    return grid


def parse_entry1(blob: bytes) -> dict:
    """Parse Entry 1 sub-section directory and decompress all sections with chaining.

    Args:
        blob: raw bytes of Entry 1 from a LOCAL.MIX file

    Returns:
        dict mapping section index to section info dict with keys:
            index, flags, w, h, total_size, decoded_size, data, grid
    """
    count = struct.unpack_from("<H", blob, 0)[0]
    offsets = [struct.unpack_from("<I", blob, 2 + i * 4)[0] for i in range(count)]
    offsets_with_end = offsets + [len(blob)]

    # Build group membership lookup
    sec_to_group = {}
    for group in ROOM_GROUPS:
        for idx, sec in enumerate(group):
            sec_to_group[sec] = (group, idx)

    # First pass: parse headers
    raw_sections = {}
    for i in range(count):
        start = offsets[i]
        end = offsets_with_end[i + 1] if i + 1 < count else len(blob)
        raw = blob[start:end]
        if len(raw) < 12:
            continue
        raw_sections[i] = raw

    # Second pass: decompress with chaining
    sections = {}
    decoded_cache = {}

    for i in sorted(raw_sections.keys()):
        raw = raw_sections[i]
        flags = struct.unpack_from("<H", raw, 0)[0]
        w, h = raw[4], raw[5]
        total_size = struct.unpack_from("<H", raw, 8)[0]
        decoded_size = struct.unpack_from("<H", raw, 10)[0]
        payload = raw[12:]

        if i in (0, 15):
            decoded = bytes(payload[:decoded_size])
        else:
            # Find reference buffer from previous section in same group
            ref_buf = None
            if i in sec_to_group:
                group, idx = sec_to_group[i]
                if idx > 0:
                    prev_sec = group[idx - 1]
                    if prev_sec in decoded_cache:
                        ref_buf = decoded_cache[prev_sec]

            decoded = decompress(payload, decoded_size, ref_buf)

        decoded_cache[i] = decoded

        grid = None
        if i not in (0, 15):
            grid = decode_room(decoded, w, h)

        sections[i] = {
            'index': i, 'flags': flags, 'w': w, 'h': h,
            'total_size': total_size, 'decoded_size': decoded_size,
            'data': decoded, 'grid': grid,
        }

    return sections


def print_grid(grid: list):
    """Print a tile grid as ASCII art."""
    for row in grid:
        print(''.join(f'{c:2X}' if c != 0 else ' .' for c in row))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lol2_decompress_sphere.py <entry1_blob> [section_index]")
        print()
        print("  Decompresses Sphere engine room sections from a LOCAL.MIX Entry 1 blob.")
        print("  If section_index is given, prints that section's grid.")
        print("  Otherwise prints a summary of all sections.")
        print()
        print(f"  LOL2_DAT = {LOL2_DAT}")
        sys.exit(1)

    blob_path = sys.argv[1]
    if not os.path.isabs(blob_path):
        blob_path = os.path.join(LOL2_DAT, blob_path)

    with open(blob_path, "rb") as f:
        blob = f.read()

    sections = parse_entry1(blob)

    if len(sys.argv) >= 3:
        idx = int(sys.argv[2])
        if idx not in sections:
            print(f"Section {idx} not found. Available: {sorted(sections.keys())}")
            sys.exit(1)
        s = sections[idx]
        print(f"Section {idx}: {s['w']}x{s['h']} flags=0x{s['flags']:04X} "
              f"decoded={s['decoded_size']} bytes")
        if s['grid']:
            print_grid(s['grid'])
        else:
            print(f"  Raw data: {len(s['data'])} bytes (no grid for this section)")
    else:
        for i in sorted(sections.keys()):
            s = sections[i]
            if s['grid']:
                placed = sum(1 for row in s['grid'] for c in row if c != 0)
                void = s['w'] * s['h'] - placed
                print(f"Section {i:2d}: {s['w']:3d}x{s['h']:<3d} "
                      f"flags=0x{s['flags']:04X} placed={placed:3d} void={void:3d}")
            else:
                print(f"Section {i:2d}: {s['w']:3d}x{s['h']:<3d} "
                      f"flags=0x{s['flags']:04X} raw={len(s['data'])} bytes")
