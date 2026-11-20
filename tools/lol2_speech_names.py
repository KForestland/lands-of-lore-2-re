#!/usr/bin/env python3
"""Read LoL2 cue tables, speech names and native switch code.

--data is the game DAT folder, or $LOL2_DAT. LOLG.DAT sits in the parent of
that folder. --check re-reads the format bytes, the switch, the eight arms,
the branch that skips the .aud probe, two MCEL.MIX keys, the MCEL module's
import of the category switch, the cue table loaded from LOCALLNG.MIX, and
the absolute indirect calls of the 47 room modules.
It writes nothing unless --out is set, and then only the check line.
"""

from cli_errors import run_cli
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
CUE_WITNESSES = {161: 298, 162: 317, 167: 276, 168: 291, 174: 286, 197: 323, 198: 314, 199: 327}


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
    return check_cue_pointer_uses(image)


def check_cue_pointer_uses(image):
    """Every direct use of the cue table is a player call, a cleanup call, a compare of the loaded word,
    the null test before shutdown, or the shutdown store. Returns the counts."""
    le = 0x3BCB4
    page_table, record_table = struct.unpack_from("<II", image, le + 0x68)
    page_size = struct.unpack_from("<I", image, le + 0x28)[0]
    first, count = struct.unpack_from("<II", image, 0x3BD90 + 0xC)
    record_lengths = {(2, 0): 5, (7, 0): 7, (7, 16): 9, (19, 0): 7}
    import capstone  # only the program census needs it
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    kinds = {"player": 0, "cleanup": 0, "compare": 0, "null test": 0, "store": 0}
    via_jump = 0
    for page in range(first, first + count):
        start, end = struct.unpack_from("<II", image, le + page_table + 4 * (page - 1))
        at = le + record_table + start
        stop = le + record_table + end
        while at < stop:
            length = record_lengths.get(tuple(image[at:at + 2]))
            if length is None or at + length > stop:
                raise ValueError("cue use relocation")
            record = image[at:at + length]
            at += length
            if len(record) < 7 or record[4] != 5 or int.from_bytes(record[5:], "little") != 0x269CC:
                continue
            file_at = CODE_BIAS + RELOC + page_size * (page - first)
            file_at += struct.unpack_from("<h", record, 2)[0]
            if image[file_at - 2:file_at] == b"\x89\x3d":
                kinds["store"] += 1
                continue
            opcode = image[file_at - 2:file_at]
            va = file_at - (1 if opcode[1] == 0xA1 else 2) - CODE_BIAS
            kind, jumped = _cue_use_kind(decoder, image, va)
            if kind not in kinds:
                raise ValueError("cue pointer use at %X is %s" % (va, kind))
            kinds[kind] += 1
            via_jump += jumped and kind == "player"
    expected = {"player": 499, "cleanup": 11, "compare": 21, "null test": 1, "store": 1}
    if kinds != expected or via_jump != 14:
        raise ValueError("cue pointer uses %s, %d player calls through a jmp" % (kinds, via_jump))
    for va, target in (
        (0xE39A3, 0xE529C), (0xE39DD, 0x605F0), (0xE39E7, 0x605F0),
        (0xE3A92, 0xE4F1C), (0xE4FBE, 0xB3B8C), (0xE50D7, 0xB7144),
    ):
        if image[va + CODE_BIAS] != 0xE8 or rel_target(image, va) != target:
            raise ValueError("cue player call at %X" % va)
    if image[0xE529C + CODE_BIAS:0xE52F6 + CODE_BIAS].find(b"\xE8") != -1:
        raise ValueError("0xE529C calls out")
    if image[0x605F0 + CODE_BIAS:0x6061C + CODE_BIAS].find(b"\xE8") != -1:
        raise ValueError("0x605F0 calls out")
    if _calls_until(decoder, image, 0xE3924, 0xE3AA6) != [
        (0xE39A3, 0xE529C), (0xE39DD, 0x605F0), (0xE39E7, 0x605F0), (0xE3A92, 0xE4F1C),
    ]:
        raise ValueError("cue player body")
    if _calls_until(decoder, image, 0xE4F1C, 0xE5299) != [
        (0xE4FBE, 0xB3B8C), (0xE50D7, 0xB7144),
    ]:
        raise ValueError("cue player helper body")
    return kinds


_FAMILIES = {r: f for f, regs in {
    "eax": ("eax", "ax", "al", "ah"), "ebx": ("ebx", "bx", "bl", "bh"), "ecx": ("ecx", "cx", "cl", "ch"),
    "edx": ("edx", "dx", "dl", "dh"), "esi": ("esi", "si"), "edi": ("edi", "di"), "ebp": ("ebp", "bp"),
}.items() for r in regs}


def _regs(text):
    return {_FAMILIES[w] for w in text.replace(",", " ").replace("[", " ").replace("]", " ").replace("*", " ").split()
            if w in _FAMILIES}


def _cue_use_kind(decoder, image, va):
    """Follow the register loaded from the cue pointer at va to its first use that decides.

    A call to 0xE3924 or 0xE4004 is a player or cleanup call; a cmp on a register that holds the
    pointer or a word read through it is a compare; test of the pointer register against itself is the
    null test. A conditional jump on an unrelated register falls through; an unconditional jmp is
    followed (at most two). Returns (kind, whether a jmp was followed)."""
    first = next(decoder.disasm(image[va + CODE_BIAS:va + CODE_BIAS + 16], va))
    pointer = _FAMILIES[first.op_str.split(",")[0].strip()]
    tracked = {pointer}
    cur = first.address + first.size
    jumps = 0
    decided = False
    for _ in range(40):
        insn = next(decoder.disasm(image[cur + CODE_BIAS:cur + CODE_BIAS + 16], cur), None)
        if insn is None:
            break
        m, ops = insn.mnemonic, insn.op_str
        if m == "call" and ops.startswith("0x"):
            return {0xE3924: "player", 0xE4004: "cleanup"}.get(int(ops, 16), ops), jumps > 0
        if m == "jmp" and ops.startswith("0x") and jumps < 2:
            cur = int(ops, 16)
            jumps += 1
            continue
        if m == "cmp" and _regs(ops) & tracked:
            decided = "compare"
        elif m == "test" and ops == "%s, %s" % (pointer, pointer) and pointer in tracked:
            decided = "null test"
        elif m.startswith("j") and decided:
            return decided, jumps > 0
        elif m.startswith("mov") and "," in ops:
            dest, src = ops.split(",", 1)
            dest_regs = _regs(dest) if "[" not in dest else set()
            if _regs(src) & tracked:
                tracked |= dest_regs
            else:
                tracked -= dest_regs
        cur = insn.address + insn.size
    return None, jumps > 0


def _calls_until(decoder, image, start, ret_at):
    """Call targets in one straight walk from start through the return at ret_at."""
    calls = []
    cur = start
    end = ret_at + 1
    while cur < end:
        insns = list(decoder.disasm(image[cur + CODE_BIAS:cur + CODE_BIAS + 16], cur))
        if not insns or insns[0].address != cur:
            raise ValueError("disassembly at %X" % cur)
        insn = insns[0]
        if insn.mnemonic == "call" and insn.op_str.startswith("0x"):
            calls.append((cur, int(insn.op_str, 16)))
        cur = insn.address + insn.size
    if cur != end:
        raise ValueError("walk ended at %X" % cur)
    return calls


def check_cue_table(dat_dir, image):
    for va, target in (
        (0xA01A0, 0xE3608), (0xE362E, 0x14FBE0),
        (0xE372D, 0x118BEC), (0xE3742, 0x118820),
    ):
        if image[va + CODE_BIAS] != 0xE8 or rel_target(image, va) != target:
            raise ValueError(f"cue table call at {va:#x}")
    for va, encoding in (
        (0xE34FB, "c780642d000000000000"),  # constructor clears object +0x2D64
        (0xA0196, "6892110000"), (0xA019B, "68683c0200"),  # name at data 0x1192, object 0x23C68
        (0xE3614, "8b7514"),  # esi = the object argument
        (0xE3629, "6828030000"),
        (0xE363C, "8986642d0000"), (0xE3725, "6a0268d8fcffff"),
        (0xE3735, "68280300008b9e642d00005357"),  # 0x328, buffer [esi+0x2D64], handle
    ):
        start = va + CODE_BIAS
        raw = bytes.fromhex(encoding)
        if image[start:start + len(raw)] != raw:
            raise ValueError(f"cue table argument at {va:#x}")
    name = b"global\\sounds.efx\x00"
    if image[0x1192 + DATA_BIAS:0x1192 + DATA_BIAS + len(name)] != name:
        raise ValueError("cue table name at data 0x1192")

    _, _, _, cues = cue_footer(dat_dir)
    if {index: cues[index] for index in CUE_WITNESSES} != CUE_WITNESSES:
        raise ValueError("category cue words")


def cue_footer(dat_dir):
    bank, entries, base = read_mix_with_hashes(parent_file(dat_dir, "LOCALLNG.MIX"))
    key = ww_hash_v1("global\\sounds.efx")
    [(offset, length)] = [(offset, size) for number, offset, size in entries if number == key]
    start = base + offset
    count, directory = struct.unpack_from("<II", bank, start + 0x258)
    footer = start + length - 0x328
    if (count, start, footer) != (1179, 0x33D488, 0x1B17198) or footer != start + directory + 60 * count:
        raise ValueError("cue table and row directory boundaries")
    cues = struct.unpack_from("<404H", bank, footer)
    if max(cues) >= count or len(set(cues)) != 361:
        raise ValueError("cue index outside the sound bank or changed cue census")
    return bank, start + directory, footer, cues


def _host_load(body, at):
    """mov reg, [eax+disp] whose displacement is a host-table offset. Returns (reg, offset, next)."""
    if at + 2 > len(body) or body[at] != 0x8B:
        return None
    modrm = body[at + 1]
    reg = (modrm >> 3) & 7
    mode = modrm & 0xC7
    if mode == 0x80 and at + 6 <= len(body):
        return reg, struct.unpack_from("<I", body, at + 2)[0], at + 6
    if mode == 0x40 and at + 3 <= len(body) and body[at + 2] < 0x80:
        return reg, body[at + 2], at + 3
    if mode == 0x00:
        return reg, 0, at + 2
    return None


def _slot_copies(body, sites):
    """Relocated slot (body offset) to the host-table offset copied into it.

    The last copy of a run loads through eax and stores with A3, because that load
    overwrites the table pointer. Earlier copies are mov reg, [eax+disp]; mov [slot], reg.
    """
    slots = {}
    limit = len(body)
    for at in range(limit):
        loaded = _host_load(body, at)
        if loaded is None:
            continue
        reg, host_off, nxt = loaded
        slot = disp_at = None
        if reg == 0 and nxt + 5 <= limit and body[nxt] == 0xA3:
            slot = struct.unpack_from("<I", body, nxt + 1)[0]
            disp_at = nxt + 1
        elif nxt + 6 <= limit and body[nxt] == 0x89 and body[nxt + 1] == ((reg << 3) | 5):
            slot = struct.unpack_from("<I", body, nxt + 2)[0]
            disp_at = nxt + 2
        if slot is None or disp_at not in sites or host_off % 4 or host_off > 0x13C:  # 80 slots, 0xE92C..0xEA6B
            continue
        previous = slots.get(slot)
        if previous is not None and previous != host_off:
            raise ValueError("room slot %X filled twice" % slot)
        slots[slot] = host_off
    return slots


def _function_calls(image, va):
    """Direct call targets of the function at va, following its branches to every ret.

    Returns (targets, extent): extent is the end of the last reached instruction minus va.
    """
    import capstone  # only the room-import census needs it
    from capstone.x86 import X86_OP_IMM

    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    seen, targets, work, end = set(), set(), [va], va
    while work:
        at = work.pop()
        while at not in seen:
            insn = next(decoder.disasm(image[at + CODE_BIAS:at + CODE_BIAS + 16], at), None)
            if insn is None:
                raise ValueError("host function decode at 0x%X" % at)
            seen.add(at)
            end = max(end, insn.address + insn.size)
            name = insn.mnemonic
            if name == "ret":
                break
            operand = insn.operands[0] if insn.operands else None
            if name == "call" and operand.type == X86_OP_IMM:
                targets.add(operand.imm)
            elif name == "jmp":
                if operand.type != X86_OP_IMM:
                    break
                at = operand.imm
                continue
            elif name.startswith("j") and operand.type == X86_OP_IMM:
                work.append(operand.imm)
            at = insn.address + insn.size
    return targets, end - va


def check_room_imports(dat_dir, image):
    """The 47 room modules' absolute indirect calls, resolved through the host-table copy."""
    from lol2_media_check import BANNER, cstr, mix_dir, read_at, room_module_layout

    host_file = DATA_BIAS + 0xE92C
    modules = []
    for index in range(46):
        ptr = struct.unpack_from("<I", image, DATA_BIAS + 0xEA6C + 4 * index)[0]
        prefix = cstr(image, DATA_BIAS + ptr)
        cut = prefix.find("_")
        path = os.path.join(dat_dir, prefix[:cut].upper() + ".MIX")
        _size, _body, entries = mix_dir(path)
        hits = []
        for entry in entries:
            if entry["size"] < 0x68:
                continue
            raw = read_at(path, entry["offset"], entry["size"])
            if raw[:len(BANNER)] == BANNER:
                hits.append(raw)
        if len(hits) != 1:
            raise ValueError("%s code entries %s" % (prefix, len(hits)))
        modules.append((hits[0], 0x34))
    arena = os.path.join(dat_dir, "ARENA.MIX")
    _size, _body, entries = mix_dir(arena)
    modules.append((read_at(arena, entries[1]["offset"], entries[1]["size"]), 0x2C))
    if len(modules) != 47:
        raise ValueError("room module count")

    counts = {}
    callers = {}
    total = 0
    for raw, dispatch in modules:
        body_length, _offset, sites = room_module_layout(raw, dispatch)
        body = raw[len(BANNER) + 16:len(BANNER) + 16 + body_length]
        sites = set(sites)
        slots = _slot_copies(body, sites)
        for at in range(len(body) - 6):
            if body[at:at + 2] != b"\xFF\x15" or at + 2 not in sites:
                continue
            total += 1
            slot = struct.unpack_from("<I", body, at + 2)[0]
            host_off = slots.get(slot)
            if host_off is None:
                raise ValueError("unresolved room call")
            stored = struct.unpack_from("<I", image, host_file + host_off)[0]
            va = (stored + RELOC) & 0xFFFFFFFF
            counts[va] = counts.get(va, 0) + 1
            callers.setdefault(va, set()).add(id(raw))
    if total != 3134 or len(counts) != 63 or counts.get(0xEE784) != 763 or counts.get(0xF16D8) != 31:
        raise ValueError("room import census %s %s" % (total, len(counts)))
    if len(callers[0xEE784]) != 37 or len(callers[0xF16D8]) != 28:
        raise ValueError("room import callers")
    # Each host function is walked through its branches to every ret: none calls the text
    # loader directly, and the longest (0xEE784) ends 0x5DF bytes after its entry.
    extents = {}
    for va in counts:
        targets, extents[va] = _function_calls(image, va)
        if 0xCF014 in targets:
            raise ValueError("room import calls the text loader")
    if max(extents.values()) != 0x5DF or extents[0xEE784] != 0x5DF:
        raise ValueError("room import extents")
    # Indirectly, host +0xC4 (0xEE540) reaches the loader through the menu 0xB9204.
    for site, target in ((0xEE692, 0x7555C), (0x7559B, 0x74ECC), (0x74F99, 0xB9204), (0xB93CF, 0xCF014)):
        if image[site + CODE_BIAS] != 0xE8 or rel_target(image, site) != target:
            raise ValueError("menu route to the text loader")
    if (struct.unpack_from("<I", image, host_file + 0xC4)[0] + RELOC) & 0xFFFFFFFF != 0xEE540:
        raise ValueError("host slot +0xC4")
    window = bytes.fromhex(
        "8b4424068b15cc690200c1f8106a00668b044225ffff0000508b54240c5268683c0200e80429ffff83c410c3"
    )
    if image[0xF16D8 + CODE_BIAS:0xF16D8 + CODE_BIAS + len(window)] != window:
        raise ValueError("cue index import")
    if rel_target(image, 0xF16FB) != 0xE4004:
        raise ValueError("cue index import calls cleanup")
    if struct.unpack_from("<I", image, host_file + 0x13C)[0] + RELOC != 0xF16D8:
        raise ValueError("host slot +0x13C")


def check(dat_dir):
    image = open(parent_file(dat_dir, "LOLG.DAT"), "rb").read()
    if len(image) != 1977007:
        raise ValueError("LOLG.DAT length %s" % len(image))
    uses = check_cue_pointer_references(image)
    check_cue_table(dat_dir, image)
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
    check_room_imports(dat_dir, image)
    return ("CHECK speech: format at file 0x1C427A; switch at 0xF133C enters "
            "eight arms through slots at 0xF131C; cue id from table 0x269CC "
            "calls 0xE3924; the reader loads 404 footer words from the EFX bank; "
            "533 direct cue-pointer uses: %(player)d player calls (14 after a jmp), %(cleanup)d cleanup calls, "
            "%(compare)d word compares, %(null test)d null test, %(store)d shutdown store; .aud probe is the other branch; "
            "MCEL entries 5 and 7 are 44100 Hz codec 99 (17564 and 21668 bytes); MCEL import +0xFC reaches 0xF133C" % uses)


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
    raise SystemExit(run_cli(main, sys.argv[1:]))
