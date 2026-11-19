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

First byte, as the function at VA 0x158D58 does it:
  src[0] == 0: consume it, then relative long back-refs (distance from current pos)
  src[0] != 0: do not consume it; it is the first command, and long back-refs
               are absolute (distance from the start of the output)
Short back-refs are relative in both paths.

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

    # VA 0x158D6C. A zero byte selects the relative loop and is consumed.
    # Any other byte is the first command of the absolute loop.
    if comp[pos] == 0:
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
                # VA 0x158DAE and 0x158E62: mov esi, edi; sub esi, eax; rep movsb.
                # Distance 0 leaves the source on the destination, so those bytes
                # stay as they are. A zeroed buffer gains zeros, not a copy of the
                # previous byte.
                out.extend(b'\x00' * min(length, max_out - len(out)))
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


USAGE = """
  lol2_decompress_westwood.py MIXFILE INDEX --out out.bin   # entry must start with a u32 size
  lol2_decompress_westwood.py --check   # try every MIX entry whose first u32 looks like an
                                        # uncompressed size; report how many decode cleanly
"""


def main():
    import lol2_cli
    ap = lol2_cli.tool_args((__doc__ or "") + USAGE)
    ap.add_argument("mix", nargs="?")
    ap.add_argument("index", nargs="?", type=int)
    a = ap.parse_args()
    if a.check:
        from lol2_mix_parser import read_mix_with_hashes
        tried = clean = 0
        for f in lol2_cli.mix_files(a.data):
            data, entries, base = read_mix_with_hashes(os.path.join(a.data, f))
            for h, o, s in entries:
                raw = data[base + o:base + o + s]
                if s < 8:
                    continue
                size = struct.unpack_from("<I", raw, 0)[0]
                if not (s < size <= 16 * s and size < 1 << 24):
                    continue
                tried += 1
                try:
                    out, err, used = decompress_westwood(raw[4:], size)
                    clean += (err == 0 and len(out) == size)
                except Exception:
                    pass
        # Relative mode (leading 00): literal, short relative copy, fill, end.
        # Absolute mode (no leading 00): a long back-reference is a distance from
        # the start of the output. Distance 0 on a short copy writes zeros.
        cases = (
            (bytes.fromhex("00" "8140" "0001" "823b3e" "1006" "fe030007" "80"),
             bytes.fromhex("40404040" "3b3e" "40404040" "070707")),
            (bytes.fromhex("84" "11223344" "c10000" "80"),
             bytes.fromhex("11223344" "11223344")),
            (bytes.fromhex("00" "82abcd" "0000" "80"),
             bytes.fromhex("abcd" "000000")),
        )
        ok = True
        for stream, want in cases:
            got, err, _ = decompress_westwood(stream, 64)
            ok = ok and got == want and err == 0
        print(f"CHECK westwood: decoder self-test {'passed' if ok else 'FAILED'}; data scan: {tried} MIX entries "
              f"whose first u32 exceeds the entry size, {clean} of them decode to that size with this decoder. "
              f"The options.shp shapes in LOCAL.MIX use it; other source files are open (docs/OPEN_QUESTIONS.md Q1).")
        return 0 if ok else 1
    if not (a.mix and a.index is not None and a.out):
        ap.print_help(); return 2
    lol2_cli.refuse_repo_output(a.out)
    path = a.mix if os.path.isabs(a.mix) else os.path.join(a.data, a.mix)
    data, errors, consumed = decompress_mix_entry(path, a.index)
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"Decompressed {len(data):,d} bytes to {a.out}; compressed bytes used {consumed:,d}"
          + (f"; WARNING {errors} bad back-references" if errors else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
