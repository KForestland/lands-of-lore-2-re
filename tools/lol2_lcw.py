#!/usr/bin/env python3
"""LCW-like decompressor kept for lol2_verify_wall_atlas_candidate.py, which recorded its result.

It is the function from the retired lol2_sprite_decode.py, unchanged. It is NOT classic
Westwood LCW ("format 80"): it reads 0x80 as a u16 count + u16 absolute copy (classic:
end of stream), masks 0xC0-0xFD counts with 0x1F (classic: 0x3F) and treats 0xFF as a
fill that ends the stream (classic: long absolute copy). Do not use it for new work; the
LOCAL.MIX room sections use lol2_decompress_sphere.py.
"""
import struct


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
