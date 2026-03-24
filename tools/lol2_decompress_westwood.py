#!/usr/bin/env python3
"""Westwood LZ77 decompressor for Lands of Lore 2.
Reverse-engineered from LOLG.DAT disassembly.

Command format:
  0x00-0x7F: Short back-ref, length=(cmd>>4)+3, distance=((cmd&0x0F)<<8)|next_byte
  0x80:      End of stream
  0x81-0xBF: Literal copy, length=cmd&0x3F
  0xC0-0xFD: Long back-ref, length=(cmd&0x3F)+3, distance=u16_from_stream
  0xFE:      RLE fill, count=u16, value=next_byte
  0xFF:      Longest back-ref, length=u16, distance=u16

Mode byte at start:
  src[0] != 0: absolute back-ref mode (distance from dst_start)
  src[0] == 0: skip 1 more byte, relative back-ref mode (distance from current pos)

Usage:
  python lol2_decompress_westwood.py <mixfile> <entry_index> <output_file>

Environment variables:
  LOL2_DAT  - path to the LoL2 DAT/ directory (default: current directory)
"""
import os
import struct
import sys

from lol2_mix_parser import read_mix_entry, LOL2_DAT


def decompress_westwood(comp: bytes, max_out: int) -> tuple:
    """Decompress Westwood LZ77 compressed data.

    Args:
        comp: compressed byte stream (starting with mode byte)
        max_out: maximum output size in bytes

    Returns:
        (decompressed_bytes, error_count, bytes_consumed)
    """
    out = bytearray()
    pos = 0

    # Mode byte
    mode = comp[pos]; pos += 1
    if mode == 0:
        # Relative mode - skip one more byte
        pos += 1
        absolute_mode = False
    else:
        absolute_mode = True

    errors = 0
    while pos < len(comp) and len(out) < max_out:
        cmd = comp[pos]; pos += 1

        if cmd < 0x80:
            # 0x00-0x7F: Short back-reference
            if pos >= len(comp):
                break
            nb = comp[pos]; pos += 1
            length = (cmd >> 4) + 3
            distance = ((cmd & 0x0F) << 8) | nb

            if distance == 0:
                last = out[-1] if out else 0
                out.extend(bytes([last]) * min(length, max_out - len(out)))
            else:
                src_pos = len(out) - distance
                if src_pos < 0:
                    out.extend(b'\x00' * min(length, max_out - len(out)))
                    errors += 1
                else:
                    for i in range(min(length, max_out - len(out))):
                        out.append(out[src_pos + (i % distance) if distance < length else src_pos + i])

        elif cmd == 0x80:
            break

        elif cmd < 0xC0:
            # 0x81-0xBF: Literal copy
            length = cmd & 0x3F
            if pos + length > len(comp):
                break
            out.extend(comp[pos:pos + length])
            pos += length

        elif cmd == 0xFE:
            # RLE fill: count = u16, value = next byte
            if pos + 3 > len(comp):
                break
            count = struct.unpack_from('<H', comp, pos)[0]; pos += 2
            value = comp[pos]; pos += 1
            out.extend(bytes([value]) * min(count, max_out - len(out)))

        elif cmd == 0xFF:
            # Longest back-ref: length = u16, distance = u16
            if pos + 4 > len(comp):
                break
            length = struct.unpack_from('<H', comp, pos)[0]; pos += 2
            distance = struct.unpack_from('<H', comp, pos)[0]; pos += 2

            if absolute_mode:
                src_pos = distance
            else:
                src_pos = len(out) - distance

            if src_pos < 0 or src_pos >= len(out):
                out.extend(b'\x00' * min(length, max_out - len(out)))
                errors += 1
            else:
                for i in range(min(length, max_out - len(out))):
                    if src_pos + i < len(out):
                        out.append(out[src_pos + i])
                    else:
                        out.append(out[src_pos + (i % (len(out) - src_pos))])

        else:
            # 0xC0-0xFD: Long back-reference
            if pos + 2 > len(comp):
                break
            length = (cmd & 0x3F) + 3
            distance = struct.unpack_from('<H', comp, pos)[0]; pos += 2

            if absolute_mode:
                src_pos = distance
            else:
                src_pos = len(out) - distance

            if src_pos < 0 or src_pos >= len(out):
                out.extend(b'\x00' * min(length, max_out - len(out)))
                errors += 1
            else:
                for i in range(min(length, max_out - len(out))):
                    if src_pos + i < len(out):
                        out.append(out[src_pos + i])
                    else:
                        out.append(out[src_pos + (i % max(1, len(out) - src_pos))])

    return bytes(out), errors, pos


def decompress_mix_entry(mix_path: str, entry_index: int, header_size: int = 4) -> tuple:
    """Read a MIX entry and decompress it.

    The entry is expected to start with a u32 decompressed-size field,
    followed by the compressed stream.

    Args:
        mix_path: path to the MIX file
        entry_index: entry index within the MIX
        header_size: bytes to skip before the compressed stream (default 4)

    Returns:
        (decompressed_bytes, error_count, bytes_consumed)
    """
    raw = read_mix_entry(mix_path, entry_index)
    decomp_size = struct.unpack_from('<I', raw, 0)[0]
    comp = raw[header_size:]
    return decompress_westwood(comp, decomp_size)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: lol2_decompress_westwood.py <mixfile> <entry_index> <output_file>")
        print("  Decompresses a Westwood LZ77 entry from a MIX container.")
        print()
        print("  Options (via environment):")
        print(f"    LOL2_DAT = {LOL2_DAT}")
        print()
        print("  The entry must start with a u32 decompressed-size field.")
        sys.exit(1)

    mix_file = sys.argv[1]
    entry_idx = int(sys.argv[2])
    out_file = sys.argv[3]

    if not os.path.isabs(mix_file):
        mix_file = os.path.join(LOL2_DAT, mix_file)

    data, errors, consumed = decompress_mix_entry(mix_file, entry_idx)
    with open(out_file, "wb") as f:
        f.write(data)

    print(f"Decompressed {len(data):,d} bytes to {out_file}")
    if errors:
        print(f"  WARNING: {errors} back-reference errors (wrote zeroes)")
    print(f"  Compressed bytes consumed: {consumed:,d}")
