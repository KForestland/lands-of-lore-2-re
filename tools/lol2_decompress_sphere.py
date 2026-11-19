#!/usr/bin/env python3
"""Read options.shp from LoL2's LOCAL.MIX.

The tool's filename is historical. Native shape directory and header
readers are at LOLG.DAT analysis addresses 0x15A22D and 0x15A457.
"""
from cli_errors import run_cli
import struct
from pathlib import Path

from lol2_decompress_westwood import decompress_westwood


def decode_shape(decoded, width, height):
    """Expand the opaque bytes and zero/run pairs used at 0x151FC4."""
    pixels = bytearray()
    at = 0
    while at < len(decoded):
        value = decoded[at]
        at += 1
        if value:
            pixels.append(value)
        else:
            if at == len(decoded):
                raise ValueError("shape ends inside a transparent run")
            pixels.extend(bytes(decoded[at]))
            at += 1
        if len(pixels) > width * height:
            raise ValueError("shape exceeds its declared dimensions")
    if len(pixels) != width * height:
        raise ValueError("shape falls short of its declared dimensions")
    return [list(pixels[row:row + width]) for row in range(0, len(pixels), width)]


def parse_entry1(blob):
    """Read shape flags 0 and 2, both present in the original options.shp."""
    count, = struct.unpack_from("<H", blob)
    offsets = [offset + 2 for offset in struct.unpack_from(f"<{count}I", blob, 2)]
    if not offsets or offsets[0] < 2 + 4 * count:
        raise ValueError("invalid shape directory")
    sections = {}
    for index, (start, end) in enumerate(zip(offsets, offsets[1:] + [len(blob)])):
        if not 0 <= start < end or end > len(blob) or end - start <= 10:
            raise ValueError(f"invalid shape {index} span")
        flags, height, width, _, total_size, size = struct.unpack_from("<HBHBHH", blob, start)
        if total_size != end - start or flags not in (0, 2) or not width or not height:
            raise ValueError(f"invalid shape {index} header")
        payload = blob[start + 10:end]
        if flags == 2:
            decoded = payload
        else:
            decoded, errors, consumed = decompress_westwood(payload, size)
            if errors or payload[consumed:] != b"\x80":
                raise ValueError(f"invalid shape {index} compression framing")
        if len(decoded) != size:
            raise ValueError(f"shape {index} decoded size mismatch")
        sections[index] = {
            "index": index, "flags": flags, "w": width, "h": height,
            "total_size": total_size, "decoded_size": size, "data": decoded,
            "grid": decode_shape(decoded, width, height),
        }
    return sections


def load_entry1(data_dir):
    from lol2_cli import resolve_input
    from lol2_source_format import parse_mix
    from lol2_westwood_hash import ww_hash_v1

    blob = Path(resolve_input("LOCAL.MIX", data_dir)).read_bytes()
    key = ww_hash_v1("options.shp")
    entry = next((item for item in parse_mix(blob) if item["key"] == key), None)
    if entry is None:
        raise ValueError("options.shp is absent from LOCAL.MIX")
    start = entry["offset"]
    return blob[start:start + entry["size"]]


def main():
    import lol2_cli

    parser = lol2_cli.tool_args(__doc__, out_help="write an indexed shape preview PNG")
    parser.add_argument("section", nargs="?", type=int, help="shape index")
    parser.add_argument("--blob", help="a saved options.shp entry instead of LOCAL.MIX")
    parser.add_argument("--png", help="legacy alias for --out")
    args = parser.parse_args()
    try:
        blob = Path(args.blob).read_bytes() if args.blob else load_entry1(args.data)
        sections = parse_entry1(blob)
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"options.shp: {error}\n")
    if args.check:
        stored = sum(shape["flags"] == 2 for shape in sections.values())
        print(f"CHECK sphere: LOCAL.MIX options.shp: {len(sections)} shapes, {stored} stored, "
              f"{len(sections) - stored} compressed; all section spans and decoded pixel counts match")
        return 0
    output = args.out or args.png
    if output and args.section is None:
        parser.error("give a shape index when requesting a PNG")
    if args.section is None:
        for index, shape in sections.items():
            print(f"Shape {index:2d}: {shape['w']:3d}x{shape['h']:<3d} "
                  f"flags=0x{shape['flags']:04X} decoded={shape['decoded_size']} bytes")
        return 0
    shape = sections.get(args.section)
    if shape is None:
        parser.error(f"shape {args.section} is outside the directory")
    for row in shape["grid"]:
        print("".join(f"{value:2X} " if value else " . " for value in row))
    if output:
        from PIL import Image

        lol2_cli.refuse_repo_output(output)
        indices = bytes(value for row in shape["grid"] for value in row)
        Image.frombytes("L", (shape["w"], shape["h"]), indices).save(output)
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
