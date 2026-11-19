#!/usr/bin/env python3
"""Spoken-line name format and the category switch.

--data is the game DAT folder, or $LOL2_DAT. LOLG.DAT sits in the parent of
that folder. --check re-reads the format bytes, the switch, the eight arms,
the branch that skips the .aud probe, two MCEL.MIX keys, and the MCEL
module's import of the category switch (host +0xFC). It writes nothing
unless --out is set, and then only the check line. It is not one of the
checks in check_all.py.
"""

import os
import struct
import sys

import lol2_cli
from lol2_mix_parser import read_mix_with_hashes
from lol2_westwood_hash import ww_hash_v1

CODE_BIAS = 0x37000
DATA_BIAS = 0x1C1024
RELOC = 0x59024
FORMAT_VA = 0x3256
SUFFIX_VA = 0x326D
SLOT_VA = 0xF131C
# Each arm is a tail of the switch at 0xF133C: push 0x18, push category,
# push 2, call 0xEE784, OR one bit into the byte at data 0xDB500, return.
ARMS = (
    (0xF13C6, "6a186a386a02e8b3d3ffffa000b50d000c0183c40ca200b50d005f5e5bc3"),
    (0xF13E4, "6a186a156a02e895d3ffff8a2d00b50d0080cd0283c40c882d00b50d005f5e5bc3"),
    (0xF1405, "6a186a1b6a02e874d3ffff8a0d00b50d0080c90483c40c880d00b50d005f5e5bc3"),
    (0xF1426, "6a186a3a6a02e853d3ffff8a3d00b50d0080cf0883c40c883d00b50d005f5e5bc3"),
    (0xF1447, "6a186a1a6a02e832d3ffff8a1d00b50d0080cb1083c40c881d00b50d005f5e5bc3"),
    (0xF1468, "6a186a216a02e811d3ffff8a3500b50d0080ce2083c40c883500b50d005f5e5bc3"),
    (0xF1489, "6a186a396a02e8f0d2ffff8a1500b50d0080ca4083c40c881500b50d005f5e5bc3"),
    (0xF14AA, "6a186a146a02e8cfd2ffff8a2500b50d0080cc8083c40c882500b50d005f5e5bc3"),
)
# name, directory index, byte length. A colliding alias of the first name is checked too.
KEYS = (
    ("WOMS\\MCEL\\0202024E.aud", 5, 17564),
    ("WOMS\\MCEL\\0202624E.aud", 7, 21668),
)
ALIAS = "WOMS\\MCEL\\0312002E.aud"


def parent_file(dat_dir, name):
    path = os.path.join(os.path.dirname(os.path.abspath(dat_dir)), name)
    if not os.path.isfile(path):
        raise FileNotFoundError("%s is not in the parent of the DAT folder" % name)
    return path


def rel_target(image, va):
    rel = struct.unpack_from("<i", image, va + CODE_BIAS + 1)[0]
    return (va + 5 + rel) & 0xFFFFFFFF


def check_cue_pointer_references(image):
    """Classify relocations in the retail LE code object targeting data 0x269CC."""
    le = 0x3BCB4
    page_table, record_table = struct.unpack_from("<II", image, le + 0x68)
    page_size = struct.unpack_from("<I", image, le + 0x28)[0]
    first, count = struct.unpack_from("<II", image, 0x3BD90 + 0xC)
    # Internal-reference records: source type 2 (16-bit selector), 7 (32-bit offset, word or dword
    # target) and 0x13 (16:16 pointer with the alias flag).
    record_lengths = {(2, 0): 5, (7, 0): 7, (7, 16): 9, (19, 0): 7}
    loads = 0
    stores = []
    for page in range(first, first + count):
        start, end = struct.unpack_from("<II", image, le + page_table + 4 * (page - 1))
        at = le + record_table + start
        stop = le + record_table + end
        while at < stop:
            length = record_lengths.get(tuple(image[at:at + 2]))
            if length is None or at + length > stop:
                raise ValueError(f"unsupported LE relocation at file 0x{at:X}")
            record = image[at:at + length]
            at += length
            if record[4] != 5 or int.from_bytes(record[5:], "little") != 0x269CC:
                continue
            site = CODE_BIAS + RELOC + page_size * (page - first)
            site += struct.unpack_from("<h", record, 2)[0]
            if record[:2] != bytes((7, 16)) or image[site:site + 4] != b"\xCC\x69\x02\x00":
                raise ValueError(f"cue relocation at file 0x{site:X}")
            if image[site - 1] == 0xA1 or image[site - 2:site] in (
                b"\x8B\x0D", b"\x8B\x15", b"\x8B\x1D", b"\x8B\x35"
            ):
                loads += 1
            elif image[site - 2:site] == b"\x89\x3D":
                stores.append(site - CODE_BIAS - 2)
            else:
                raise ValueError(f"cue pointer instruction at file 0x{site:X}")
    if loads != 532 or stores != [0x14EA9C]:
        raise ValueError("cue pointer reference census")


def check(dat_dir):
    image = open(parent_file(dat_dir, "LOLG.DAT"), "rb").read()
    if len(image) != 1977007:
        raise ValueError("LOLG.DAT length %s" % len(image))
    check_cue_pointer_references(image)
    format_at = FORMAT_VA + DATA_BIAS
    suffix_at = SUFFIX_VA + DATA_BIAS
    if image[format_at:format_at + 23] != b"WOMS\\%s\\%02d%03d%02d%c\x00":
        raise ValueError("name format")
    if image[suffix_at:suffix_at + 5] != b".aud\x00":
        raise ValueError("aud suffix")
    # sprintf arguments, the argument-2 joins, the cue-id load, and the switch
    expect = (
        (0xEE7BC, "6a455357566804b50d00"),
        (0xEE7D0, "e883190600"),
        (0xEE7E1, "83fe020f84c2000000"),
        (0xEE8B3, "83fe640f85b1010000"),
        (0xEEA6D, "83fe020f85bf010000"),
        (0xEEA76, "83fb140f8eb6010000"),
        (0xEEA7F, "89fb"),
        (0xEEAA3, "81c38d000000"),
        (0xEEABE, "a801"),
        (0xEEAC5, "8b15cc69020001c001d031d2668b10"),
        (0xEEAF9, "e8264effff"),
        (0xF0B98, "8b8690000000668b9694000000"),
        (0xF0BFE, "668b044325ffff0000505268683c0200"),
        (0xF0C16, "66c786940000000000c78690000000ffffffff"),
        (0xEEC35, "833dc8b40d00000f85fb000000"),
        (0xEEC42, "be6d320000"),
        (0xF133C, "535657"),
        (0xF1380, "6a076a0068d8210200"),
        (0xF139B, "f6c20175e0"),
        (0xF13BE, "2eff2485f8820900"),
    )
    for va, hex_bytes in expect:
        raw = bytes.fromhex(hex_bytes)
        if image[va + CODE_BIAS:va + CODE_BIAS + len(raw)] != raw:
            raise ValueError("bytes at %X" % va)
    if (rel_target(image, 0xEE7D0) != 0x150158 or rel_target(image, 0xEEAF9) != 0xE3924
            or rel_target(image, 0xF0C0E) != 0xE4004 or rel_target(image, 0xF1389) != 0x12415C):
        raise ValueError("call target")
    arms = []
    for va, hex_bytes in ARMS:
        raw = bytes.fromhex(hex_bytes)
        if image[va + CODE_BIAS:va + CODE_BIAS + len(raw)] != raw:
            raise ValueError("arm %X" % va)
        if rel_target(image, va + 6) != 0xEE784:
            raise ValueError("arm %X target" % va)
        arms.append(va)
    slot_at = SLOT_VA + CODE_BIAS
    stored = struct.unpack_from("<%dI" % len(arms), image, slot_at)
    if stored != tuple(va - RELOC for va in arms):
        raise ValueError("switch slots")

    path = os.path.join(dat_dir, "MCEL.MIX")
    raw, entries, base = read_mix_with_hashes(path)
    by_hash = {}
    for index, (key, offset, size) in enumerate(entries):
        by_hash.setdefault(key, []).append((index, offset, size))
    [(_, module, _)] = by_hash[ww_hash_v1("WOMS\\MCEL_.WOM")]
    module += base
    if module != 0x156:
        raise ValueError("MCEL room module offset")
    body_at = module + 0x30
    body_length, _, count = struct.unpack_from("<III", raw, module + 0x24)
    fixups_at = body_at + body_length
    sites = struct.unpack_from(f"<{count}I", raw, fixups_at)
    if (raw[0x530:0x53C] != bytes.fromhex("8b90fc00000089154c0a0000")
            or raw[0x777:0x779] != b"\xFF\x15"
            or 0x779 - body_at not in sites
            or struct.unpack_from("<I", raw, 0x779)[0] != 0xA4C
            or struct.unpack_from("<I", image, 0x1CFA4C)[0] + RELOC != 0xF133C):
        raise ValueError("MCEL category switch import")
    first_hash = None
    for name, index, size in KEYS:
        key = ww_hash_v1(name)
        hits = by_hash.get(key, [])
        if len(hits) != 1 or hits[0][0] != index or hits[0][2] != size:
            raise ValueError("key %s" % name)
        blob = raw[base + hits[0][1]:base + hits[0][1] + size]
        rate, comp, _out, flags, codec = struct.unpack_from("<HIIBB", blob)
        if rate != 44100 or flags != 2 or codec != 99 or comp != size - 12:
            raise ValueError("header %s" % name)
        if first_hash is None:
            first_hash = key
    if ww_hash_v1(ALIAS) != first_hash:
        raise ValueError("alias hash")
    return ("CHECK speech: format at file 0x1C427A; switch at 0xF133C enters "
            "eight arms through slots at 0xF131C; cue id from table 0x269CC "
            "calls 0xE3924; 532 direct pointer loads and one shutdown store; .aud probe is the other branch; "
            "MCEL entries 5 and 7 are 44100 Hz codec 99 (17564 and 21668 bytes); MCEL import +0xFC reaches 0xF133C")


def main(argv):
    parser = lol2_cli.tool_args(__doc__)
    args = parser.parse_args(argv)
    if args.out and not args.check:
        parser.error("--out is only the one-line check, with --check")
    if not args.check:
        parser.print_help()
        return 2
    if args.out:
        lol2_cli.refuse_repo_output(args.out)
    try:
        line = check(args.data)
    except (OSError, ValueError, struct.error) as error:
        print("CHECK speech: FAIL %s" % error)
        return 1
    if args.out:
        with open(args.out, "w", encoding="ascii") as handle:
            handle.write(line + "\n")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
