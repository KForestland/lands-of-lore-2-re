#!/usr/bin/env python3
"""Verify save and clock instruction witnesses against retail DOS LOLG.DAT."""
import argparse
import os
import struct
from pathlib import Path

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
    ):
        expected = bytes.fromhex(sequence)
        start = address + CODE_BIAS
        if image[start:start + len(expected)] != expected:
            raise ValueError(f"save or clock instruction at 0x{address:X}")
    # Adjustment arms are stored object-relative; adding 0x59024 gives the analysis address.
    table = 0x1205D8
    for section, target in ((62, 0xEA077), (64, 0xEA0C5), (67, 0xE97AC)):
        if struct.unpack_from("<I", image, table + section * 4)[0] + 0x59024 != target:
            raise ValueError(f"section {section} adjust arm")
    for table, selectors in (
        (0x11F64C, {4: 0xE8723, 7: 0xE878D, 9: 0xE87C3, 10: 0xE87E2}),
        (0x11F800, {7: 0xE8A34, 9: 0xE8A74, 36: 0xE8E2F, 60: 0xE90BC}),
    ):
        for section, target in selectors.items():
            if struct.unpack_from("<I", image, table + section * 4)[0] + 0x59024 != target:
                raise ValueError(f"section {section} data selector")
    return ("CHECK native save: header, global and level payload paths, "
            "timer restore and menu clock restart, actor links and automap markers")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    data = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, default=data, required=data is None)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        print(check(args.data.resolve().parent / "LOLG.DAT"))
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"CHECK native save: {error}\n")


if __name__ == "__main__":
    main()
