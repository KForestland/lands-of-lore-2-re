#!/usr/bin/env python3
"""Compare the shipped LoL2 cache seed lengths with the 15 original texture banks."""
import ctypes
from cli_errors import ReaderArgumentParser, run_cli
import os
import re
import struct
from pathlib import Path

from draracle.lol2_cache_named_wall_fixture import parse_records
from lol2_texture_container import _lzo_decompress_fn, find_texture_entry

# Art folder and leved folder named in each bank's first decoded block.
BANK_FOLDERS = (
    ("L1_DC", "SPHERE1\\L1_DC", "sphere1\\l1_dc"),
    ("L3_DH", "SPHERE1\\L2&3", "sphere1\\l3_dh"),
    ("L4_HJ", "SPHERE1\\L4_HJ", "sphere1\\l4_hj"),
    ("L5_HC", "SPHERE1\\L5_HC", "sphere1\\l5_hc"),
    ("L7_DH", "SPHERE1\\L7_DH", "sphere1\\l7_dh"),
    ("L8_SJ", "SPHERE2\\L8_SJ", "sphere2\\l8_sj"),
    ("L9_DR", "SPHERE2\\L9_DR", "sphere2\\l9_dr"),
    ("L10_DC", "SPHERE2\\L10_DC", "sphere2\\l10_dc"),
    ("L12_CM", "SPHERE2\\L12_CM", "sphere2\\l12_cm"),
    ("L13_RC", "SPHERE2\\L13_RC", "sphere2\\l13_rc"),
    ("L14_HT", "SPHERE2\\L14_HT", "sphere2\\l14_ht"),
    ("L16_CA", "SPHERE3\\L16_CA", "sphere3\\l16_ca"),
    ("L17_HC", "SPHERE3\\L17_HC", "sphere3\\l17_hc"),
    ("L19_BC", "SPHERE3\\L19_BC", "sphere3\\l19_bc"),
    ("L20_BB", "SPHERE3\\L20_BB", "sphere3\\l20_bb"),
)


def first_block(raw):
    """Decode the first LZO block of a texture entry."""
    fn = _lzo_decompress_fn()
    size, = struct.unpack_from("<I", raw, 4)
    if not 0 < size <= len(raw) - 8:
        raise ValueError("texture block size")
    src = ctypes.create_string_buffer(raw[8:8 + size])
    dst = ctypes.create_string_buffer(1 << 20)
    decoded = ctypes.c_size_t(len(dst))
    code = fn(src, size, dst, ctypes.byref(decoded), None)
    if code != 0 or decoded.value < 256:
        raise ValueError("texture block decode")
    return dst.raw[:decoded.value]


def compare(data):
    seed = (data.parent / "CDCACHE.LS_").read_bytes()
    backup = (data.parent / "CACHEBAK.MIX").read_bytes()
    count, size = struct.unpack_from("<HI", backup)
    body = 6 + 12 * count
    if (len(backup), count, size, body) != (131, 5, 65, 66):
        raise ValueError("shipped backup MIX dimensions")
    spans = sorted(struct.unpack_from("<II", backup, 10 + 12 * i) for i in range(count))
    if spans != [(13 * i, 13) for i in range(count)]:
        raise ValueError("shipped backup MIX spans")

    rows = []
    for record in parse_records(seed):
        name = record["canonical_name"]
        level = name.rsplit("\\", 1)[-1].removesuffix(".tex").upper()
        image, entry, bank_name = find_texture_entry(data / f"{level}.MIX")
        if name != bank_name.lower().removesuffix(".te_") + ".tex":
            raise ValueError(f"{level} seed and bank name differ")
        length, = struct.unpack_from("<I", image, entry["offset"])
        rows.append((level, record["record_offset"], record["length"], length, record["pointer"]))
        if record["state"] != 0xFFFFFFFF:
            raise ValueError(f"{level} active record in shipped seed")
    texts = re.findall(rb"[\x20-\x7e]{4,}", seed)
    names = (
        b"sphere1\\l1_dc\\l1_dc.tex", b"sphere1\\l3_dh\\l3_dh.tex",
        b"sphere1\\l4_hj\\l4_hj.tex", b"sphere1\\l5_hc\\l5_hc.tex",
        b"sphere1\\l7_dh\\l7_dh.tex", b"sphere2\\l8_sj\\l8_sj.tex",
        b"sphere2\\l9_dr\\l9_dr.tex", b"sphere2\\l10_dc\\l10_dc.tex",
        b"sphere2\\l12_cm\\l12_cm.tex", b"sphere2\\l13_rc\\l13_rc.tex",
        b"sphere2\\l14_ht\\l14_ht.tex", b"sphere3\\l16_ca\\l16_ca.tex",
        b"sphere3\\l17_hc\\l17_hc.tex", b"sphere3\\l19_bc\\l19_bc.tex",
        b"sphere3\\l20_bb\\l20_bb.tex",
    )
    if tuple(texts) != names:
        raise ValueError("seed strings are not the 15 level names")
    program = (data.parent / "LOLG.DAT").read_bytes()
    if program[0x1C4714:0x1C471C] != b"DOS 1.30":
        raise ValueError("executable version string")
    if program[0x1C4749:0x1C475D] != b"Dec 03 1997\x0017:51:02":
        raise ValueError("executable date string")
    # Data pointers to the three strings and the code that reads them.
    pointers = tuple(struct.unpack_from("<I", program, 0x1C1024 + cell)[0] for cell in (0xEE54, 0xEE5C, 0xEE60))
    if pointers != (0x36F0, 0x3725, 0x3731):
        raise ValueError("version and date string pointers")
    readers = ((0xB9BD0, "a154ee0000"), (0x60AD5, "8b355cee0000"), (0x60B80, "8b3560ee0000"))
    for va, code in readers:
        want = bytes.fromhex(code)
        if program[va + 0x37000:va + 0x37000 + len(want)] != want:
            raise ValueError("version and date string reader at %X" % va)
    if program[0x100:0x110] != bytes.fromhex("bd01680cdf07910fdf07950fdf078910"):
        raise ValueError("LOLG.DAT+0x100 differs")
    if program[0x25C:0x26D] != b"DOS/4G  Copyright":
        raise ValueError("LOLG.DAT+0x25C differs")
    if program[0x3BCBC:0x3BCC0] != bytes.fromhex("02000100"):
        raise ValueError("LOLG.DAT+0x3BCBC differs")
    for level, art, leved in BANK_FOLDERS:
        image, entry, _bank = find_texture_entry(data / f"{level}.MIX")
        raw = image[entry["offset"]:]
        head = first_block(raw).lower()
        art_name = art.lower().encode("ascii")
        leved_name = leved.lower().encode("ascii")
        if b"projects\\lol_2\\art\\wallsets\\" + art_name not in head:
            raise ValueError(f"{level} art folder")
        if b"projects\\lol_2\\leved\\" + leved_name not in head:
            raise ValueError(f"{level} leved folder")
    return rows


def main():
    parser = ReaderArgumentParser(description=__doc__)
    data = os.environ.get("LOL2_DAT")
    parser.add_argument("--data", type=Path, default=data, required=data is None)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        rows = compare(args.data.resolve())
        matches = [level for level, _, seed, current, _ in rows if seed == current]
        offsets = [(level, pointer) for level, _, _, _, pointer in rows if pointer != 0xFFFFFFFF]
        if len(rows) != 15 or matches != ["L1_DC", "L9_DR", "L14_HT"] or offsets != [("L1_DC", 5066)]:
            raise ValueError("shipped seed comparison changed")
        print("CHECK cache seed: 15 original banks, 3 decoded lengths match, 12 differ; "
              "only L1_DC has a finite old position (5066); backup holds five 13-byte members")
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"CHECK cache seed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
