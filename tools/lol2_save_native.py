#!/usr/bin/env python3
"""Verify save and clock instruction witnesses and level animation rows."""
import argparse
from collections import Counter
import os
import struct
from pathlib import Path

from lol2_entity_field_analyzer import LEVEL_FILES, locate_entity_table
from lol2_source_format import u32
from lol2_texture_container import load_blob

CODE_BIAS = 0x37000


def check(executable):
    image = executable.read_bytes()
    for address, target in (
        (0xE7931, 0xE867C), (0xE69D1, 0xE867C),
        (0xE687E, 0x118820), (0xE6CFC, 0x118820),
        (0xE7A3E, 0xEB6A0), (0xE7A5B, 0x118864),
        (0xE749C, 0xEB600), (0xE8338, 0x118864),
        (0xE7418, 0xE8914), (0xE8125, 0xE8914),
        (0xE74B7, 0x118820), (0xE765B, 0x118820),
        (0xEA09C, 0xEB2C8), (0xEA0E6, 0xEB2C8),
        (0xB9321, 0xA0200), (0xB96A7, 0xA02F8),
        (0xA023E, 0x14FAA1), (0xA031A, 0x14FABD),
        (0xA033D, 0x14FADB), (0xA034A, 0x14FABD),
        (0xE95B4, 0xEB2C8), (0xD36FE, 0x115D6C),
        (0x64DBE, 0x66664), (0xE8020, 0x145F2C), (0x7CF23, 0xFA5C4),
        (0xE7C47, 0x118864), (0xE68BB, 0xEB82C),
        (0xA053E, 0x67460), (0xA0553, 0x110754),
        (0x9E053, 0x67424), (0x9DCD1, 0x110724),
    ):
        opcode, displacement = struct.unpack_from("<Bi", image, address + CODE_BIAS)
        if opcode != 0xE8 or address + 5 + displacement != target:
            raise ValueError(f"call at 0x{address:X}")
    for address, sequence in (
        (0xE9123, "c700402c0200b8912c02002d402c020089028903c70103000000"),
        (0xE751D, "3343fc418946fc"),
        (0xE7552, "8a61ff4630e0438842ff"),
        (0xE0A5A, "8bb312050000468a2d9823020089b312050000"),
        (0x14FAB3, "c70200000000"),
        (0x14FAC8, "8b50088b12428910"),
        (0xB8CE4, "66294308"),
        (0xEB30D, "c780d000000001000000"),
        (0x115D6C, "31c0c3"),
        (0xA7245, "891da4690900"),
        (0xAA5E9, "3b05a46909000f94c3"),
        (0xAAF10, "893289763c"),
        (0x64DCE, "c6400901"),
        (0xE7B79, "8d45cc"), (0xE7BA5, "c70000000000"),
        (0xE7C53, "8b556e0102"),
        (0xEB8D0, "8b8a060200008d34850000000085c974ce8b4a40"),
        (0x5DE52, "8b15e82c02008d04950000000029d08b15782d0200c1e00201d0"),
        (0x9E037, "6a008b6c24085557e8a8ab070083c40c8b44243c505789838c000000"),
        (0x9DC9D, "6a008b5c2424538b8c24bc06000051e83baf070083c40c8b44245cc1e803"),
        (0x67486, "8a4610a8010f851a010000"), (0x676E7, "66895e04"),
        (0x11077A, "8a4706a8010f8509010000"), (0x1109C2, "885f07"),
    ):
        expected = bytes.fromhex(sequence)
        start = address + CODE_BIAS
        if image[start:start + len(expected)] != expected:
            raise ValueError(f"save or clock instruction at 0x{address:X}")
    # Adjustment arms are stored object-relative; adding 0x59024 gives the analysis address.
    table = 0x1205D8
    for section, target in ((26, 0xE97AC), (27, 0xE97AC),
                            (62, 0xEA077), (64, 0xEA0C5), (67, 0xE97AC)):
        if struct.unpack_from("<I", image, table + section * 4)[0] + 0x59024 != target:
            raise ValueError(f"section {section} adjust arm")
    for table, selectors in (
        (0x11F64C, {4: 0xE8723, 7: 0xE878D, 9: 0xE87C3, 10: 0xE87E2}),
        (0x11F800, {7: 0xE8A34, 9: 0xE8A74, 26: 0xE8CF2, 27: 0xE8D1F,
                    36: 0xE8E2F, 60: 0xE90BC}),
    ):
        for section, target in selectors.items():
            if struct.unpack_from("<I", image, table + section * 4)[0] + 0x59024 != target:
                raise ValueError(f"section {section} data selector")
    return ("CHECK native save: header, global and level payload paths, "
            "timer restore and menu clock restart, actor links and automap markers")


def check_surface_tables(data_dir):
    surfaces = animations = 0
    surface_modes, animation_modes = Counter(), Counter()
    for filename in LEVEL_FILES:
        path = data_dir / filename
        archive = path.read_bytes()
        entry, _, _ = locate_entity_table(archive, path.stem)
        base = entry["offset"]
        offset, count = u32(archive, base + 4), u32(archive, base + 0x3C)
        next_table = u32(archive, base + 8)
        if not 0x204 <= offset <= next_table <= entry["size"] or offset + 46 * count != next_table:
            raise ValueError(f"{filename}: section 26 source bounds")
        surfaces += count
        for at in range(base + offset, base + offset + 24 * count, 24):
            if archive[at + 0x10] & 1:
                surface_modes[archive[at + 0x0F]] += 1
        del archive

        texture, _ = load_blob(path)
        offset, length = u32(texture, 0x20), u32(texture, 0x5C)
        if length % 8 or not 0x6A2 <= offset <= offset + length <= len(texture):
            raise ValueError(f"{filename}: section 27 source bounds")
        animations += length // 8
        for at in range(offset, offset + length, 8):
            if texture[at + 6] & 1:
                animation_modes[texture[at + 5]] += 1

    if surfaces != 428 or surface_modes != {0x01: 2, 0x11: 1, 0x20: 12, 0x21: 74,
                                           0x23: 3, 0x30: 1, 0x33: 1, 0xF1: 1}:
        raise ValueError("section 26 source row census changed")
    if animations != 36 or animation_modes != {0x01: 3, 0x11: 2, 0x21: 14}:
        raise ValueError("section 27 source row census changed")
    return (f"CHECK native save: {surfaces} ODF surface rows and {animations} texture animation rows "
            f"in {len(LEVEL_FILES)} levels, with {sum(surface_modes.values())} and "
            f"{sum(animation_modes.values())} enabled")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    data = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, default=data, required=data is None)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        data_dir = args.data.resolve()
        print(check(data_dir.parent / "LOLG.DAT"))
        print(check_surface_tables(data_dir))
    except (OSError, RuntimeError, ValueError, struct.error) as error:
        parser.exit(1, f"CHECK native save: {error}\n")


if __name__ == "__main__":
    main()
