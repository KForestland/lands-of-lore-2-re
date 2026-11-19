#!/usr/bin/env python3
"""Recheck four wall quads from the Huline Temple with the DOS constructor.

Uses the original LOLG.DAT and L14_HT.MIX, and requires Capstone. The replay
supplies the level-table pointers, starts at 0x114AA4 and ends before drawing.
Writes nothing.
"""
import argparse
import hashlib
import os
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lol2_export_scripts import section
from lol2_source_format import level_geometry

CODE_BIAS = 0x37000
ROUTINES = (
    (0x114AA4, 0x115119),
    (0xF4504, 0xF458D),
    (0xF4590, 0xF4614),
    (0xF49FC, 0xF4A3C),
)
EXPECTED = (
    (75, 80, (214302720, 227475456), (204800000, 217382912)),
    (0, 80, (214302720, 227475456), (212074496, 225050624)),
    (0, 55, (214302720, 227475456), (204800000, 217382912)),
    (0, 80, (207834407, 220581341), (204800000, 217382912)),
)


def check(data_dir):
    try:
        import capstone  # noqa: F401
    except ImportError:
        raise ValueError("requires Capstone (pip install capstone)")
    from lol2_verify_draracle_slopes import EXE_HASH
    from lol2_verify_flat_wall_spans import WallReplay

    executable = (data_dir.parent / "LOLG.DAT").read_bytes()
    if hashlib.sha256(executable).hexdigest() != EXE_HASH:
        raise ValueError("expected the documented DOS 1.30 executable")
    disasm = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    disasm.detail = True
    instructions = {}
    for start, end in ROUTINES:
        code = executable[start + CODE_BIAS:end + CODE_BIAS]
        instructions.update((ins.address, ins) for ins in disasm.disasm(code, start))

    _, geometry = level_geometry((data_dir / "L14_HT.MIX").read_bytes())
    _, _, vertices = section(geometry, 0x04, 0x50, 8)
    _, _, walls = section(geometry, 0x08, 0x54, 8)
    _, _, regions = section(geometry, 0x0C, 0x58, 44)
    first = struct.unpack_from("<H", regions, 0x1A)[0]
    if first != 7448 or regions[0x1E] != len(EXPECTED):
        raise ValueError("region zero wall run changed")
    replay = WallReplay(instructions, regions)
    vertices_address = 0x500000
    replay.writemem(0x22D04, 4, vertices_address)
    replay.mem[vertices_address:vertices_address + len(vertices)] = vertices
    for delta, (bottom, top, a, b) in enumerate(EXPECTED):
        index = first + delta
        material = walls[index * 8:(index + 1) * 8]
        points, active = replay.execute(0, material[5] & 0x1F, (material[7] & 3) << 14,
                                        material[3], material[6])
        expected = [[x, y << 16, z] for (x, z), y in ((a, top), (b, top),
                                                    (b, bottom), (a, bottom))]
        if points != expected or not active:
            raise ValueError(f"wall row {index} geometry or active flag changed")
    return "CHECK Huline wall quads: L14_HT region 0, rows 7448–7451, 4 active spans"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    data = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, default=data, required=data is None)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        print(check(args.data.resolve()))
    except (ImportError, OSError, ValueError, struct.error) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
