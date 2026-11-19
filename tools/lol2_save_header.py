#!/usr/bin/env python3
"""Read the native LoL2 DOS slot header of a player save (game-written, not shipped). Prints offsets and sizes to stdout."""
from cli_errors import ReaderArgumentParser, run_cli
import json
import struct
from pathlib import Path

HEADER_SIZE = 0x25A


def parse_header(header, file_size):
    """Read preview, global and level ranges from the 1.30 slot directory."""
    if len(header) < HEADER_SIZE:
        raise ValueError("short LoL2 slot header")
    size, version, layout = struct.unpack_from("<3I", header, 0x2C)
    if size != file_size or (version, layout) != (0x12, 0x66):
        raise ValueError("LoL2 slot size or version mismatch")
    width, height, preview = struct.unpack_from("<3I", header, 0x9C)
    offsets = (preview, *struct.unpack_from("<31I", header, 0x18E), size)
    if preview < HEADER_SIZE or any(start > end for start, end in zip(offsets, offsets[1:])):
        raise ValueError("invalid LoL2 slot section directory")
    spans = [(start, end - start) for start, end in zip(offsets, offsets[1:])]
    return dict(size=size, preview=spans[0], width=width, height=height,
                sections=spans[1:12], levels=spans[12:],
                stored_level_lengths=struct.unpack_from("<20I", header, 0x20A))


def main():
    parser = ReaderArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--check", action="store_true", help="compare stored and derived level lengths")
    args = parser.parse_args()
    try:
        with args.file.open("rb") as source:
            header = source.read(HEADER_SIZE)
            size = source.seek(0, 2)
        result = parse_header(header, size)
        if args.check:
            if result["stored_level_lengths"] != tuple(length for _, length in result["levels"]):
                raise ValueError("stored level lengths disagree with the directory")
            print("CHECK save header: 20 stored level lengths match the directory")
        else:
            print(json.dumps(result, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"save header: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
