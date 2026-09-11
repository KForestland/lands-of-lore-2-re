"""Palette and PNG helpers; no runtime capture or scene-rendering claims."""
import struct,zlib
import lol2_cache_named_wall_fixture as cache

def rgb_palette(dac: bytes, bits: int) -> bytes:
    cache.require(len(dac) == 768 and bits in (6, 8), "unsupported palette")
    maximum = (1 << bits) - 1
    cache.require(max(dac) <= maximum, "palette exceeds DAC range")
    return bytes((value * 255 + maximum // 2) // maximum for value in dac)

def colorize(indices: bytes, rgb: bytes) -> bytes:
    cache.require(len(rgb) == 768, "RGB palette must have 256 entries")
    return b"".join(rgb[value * 3:value * 3 + 3] for value in indices)

def png_rgb(width: int, height: int, pixels: bytes) -> bytes:
    cache.require(width > 0 and height > 0 and len(pixels) == width * height * 3,
                  "invalid RGB image extent")
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content))
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))

