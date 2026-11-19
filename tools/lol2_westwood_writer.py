#!/usr/bin/env python3
"""Read LoL2 options shapes, WSA panels and texture books and re-encode LZ77."""
from pathlib import Path
import re
import struct

from cli_errors import run_cli
import lol2_cli
from lol2_decompress_sphere import load_entry1, parse_entry1
from lol2_decompress_westwood import decompress_westwood
from lol2_media_check import mix_dir, panel_names, wsa_frames
from lol2_westwood_hash import ww_hash_v1

RUN = re.compile(rb"(.)\1{5,}", re.DOTALL)


def encode_westwood(decoded, relative=False):
    """Write literals, fills and a prefix reference in either offset mode."""
    output = bytearray(b"\0" if relative else b"")
    offset = decoded.find(decoded[:16], 1, 0x10000 + 15) if len(decoded) >= 17 else -1
    if offset > 0:
        length = 16
        limit = min(len(decoded) - offset, 0xFFFF)
        while length < limit and decoded[length] == decoded[offset + length]:
            length += 1
        put_runs(output, decoded[:offset])
        output.extend(long_copy(offset, 0, length, relative))
        put_runs(output, decoded[offset + length:])
    else:
        put_runs(output, decoded)
    output.append(0x80)
    return bytes(output)


def put_runs(output, decoded):
    at = 0
    for match in RUN.finditer(decoded):
        put_literals(output, decoded, at, match.start())
        remaining = len(match[0])
        while remaining:
            count = min(remaining, 0xFFFF)
            output.extend(struct.pack("<BHB", 0xFE, count, match[0][0]))
            remaining -= count
        at = match.end()
    put_literals(output, decoded, at, len(decoded))


def put_literals(output, data, start, end):
    for offset in range(start, end, 63):
        part = data[offset:min(offset + 63, end)]
        output.append(0x80 | len(part))
        output.extend(part)


def long_copy(output_at, source_at, length, relative):
    """Generate a long command in the selected offset mode."""
    offset = output_at - source_at if relative else source_at
    if not (0 <= source_at < output_at and 0 <= offset <= 0xFFFF and 3 <= length <= 0xFFFF):
        raise ValueError("invalid long-copy range")
    if length <= 64:
        return struct.pack("<BH", 0xC0 | (length - 3), offset)
    return struct.pack("<BHH", 0xFF, length, offset)


def repack(payload, decoded):
    relative = payload[0] == 0
    rebuilt = encode_westwood(decoded, relative)
    data, errors, consumed = decompress_westwood(rebuilt, len(decoded) + 1)
    if data != decoded or errors or consumed != len(rebuilt):
        raise ValueError("rebuilt LZ77 stream was read differently")
    return rebuilt


def write_options(original):
    shapes = parse_entry1(original)
    count = len(shapes)
    offsets = struct.unpack_from(f"<{count}I", original, 2)
    prefix = 2 + count * 4
    data = bytearray(original[prefix:offsets[0] + 2])
    rows = []
    for shape, offset in zip(shapes.values(), offsets):
        rows.append(prefix + len(data) - 2)
        at = offset + 2
        payload = original[at + 10:at + shape["total_size"]]
        if shape["flags"] == 0:
            payload = repack(payload, shape["data"])
        flags, h, w, h2, _, size = struct.unpack_from("<HBHBHH", original, at)
        data.extend(struct.pack("<HBHBHH", flags, h, w, h2, 10 + len(payload), size))
        data.extend(payload)
    rebuilt = struct.pack("<H", count) + struct.pack(f"<{count}I", *rows) + data
    actual = parse_entry1(rebuilt)
    if any(any(new[key] != old[key] for key in ("flags", "w", "h", "decoded_size", "data", "grid"))
           for new, old in zip(actual.values(), shapes.values())):
        raise ValueError("rebuilt options shapes differ through the reader")
    return rebuilt, sum(shape["flags"] == 0 for shape in shapes.values())


def write_panel(original):
    count, _, _, spans = wsa_frames(original)
    capacity = struct.unpack_from("<H", original, 10)[0]
    payload = bytearray()
    start = 14 + 4 * (count + 2)
    offsets = [start]
    decoded = []
    for offset, size, expected in spans:
        source = original[offset:offset + size]
        part, errors, consumed = decompress_westwood(source, capacity)
        if (len(part), errors, consumed) != (expected, 0, size):
            raise ValueError("original WSA span changed during read-back")
        decoded.append(part)
        payload.extend(repack(source, part))
        offsets.append(start + len(payload))
    rebuilt = original[:14] + struct.pack(f"<{count + 2}I", *offsets) + payload
    _, _, _, updated = wsa_frames(rebuilt)
    for part, (offset, size, _) in zip(decoded, updated):
        if decompress_westwood(rebuilt[offset:offset + size], capacity) != (part, 0, size):
            raise ValueError("rebuilt WSA delta differs through the reader")
    return rebuilt, len(spans)


def check(data_dir):
    root = Path(data_dir).resolve()
    local = Path(lol2_cli.resolve_input("LOCAL.MIX", root))
    image = (root.parent / "LOLG.DAT").read_bytes()
    rows = {row["key"]: row for row in mix_dir(local)[-1]}

    def member(name):
        row = rows[ww_hash_v1(name)]
        with local.open("rb") as source:
            source.seek(row["offset"])
            return source.read(row["size"])

    _, shapes = write_options(load_entry1(root))
    names = panel_names(image)
    deltas = sum(write_panel(member(name))[1] for name in names)
    texture = member("global\\global.tex")
    base = struct.unpack_from("<I", texture, 0x298)[0]
    table = base + struct.unpack_from("<I", texture, base + 0x2C)[0]
    books = struct.unpack_from("<I", texture, base + 0x2A4)[0]
    for i in range(books):
        relative, capacity, length = struct.unpack_from("<III", texture, table + 12 * i)
        start = base + relative
        source = texture[start:start + length]
        decoded, errors, used = decompress_westwood(source, capacity)
        if errors or used != length:
            raise ValueError("global texture LZ77 extent")
        repack(source, decoded)
    if (shapes, len(names), deltas, books) != (37, 21, 640, 15):
        raise ValueError("mode-byte writer corpus changed")
    print(f"CHECK Westwood write: {shapes} options shapes, {deltas} WSA deltas in {len(names)} panels, "
          f"{books} global texture streams; decoded bytes identical, compressed bytes not")


def main():
    parser = lol2_cli.tool_args(__doc__, writes=False)
    args = parser.parse_args()
    if not args.check:
        parser.error("give --check to encode and re-read in memory")
    check(args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
