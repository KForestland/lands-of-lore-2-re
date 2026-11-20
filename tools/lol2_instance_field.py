#!/usr/bin/env python3
"""Read instance byte +5 and the remaining script subcommand handlers.

The placed-item record is six bytes at allocation +0x2C. Byte +5 is one
field of that record. The same scan lists the selector handlers of opcodes
2, 6, 9 and 15, and the opcode 1 and opcode 3 results of seven +0xAC slots.

  lol2_instance_field.py --data DAT
  lol2_instance_field.py --check --data DAT
"""
from cli_errors import run_cli, game_path
import os
import struct
import sys
from collections import Counter
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import (
    X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
    X86_REG_EBP, X86_REG_ESP, X86_REG_INVALID,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lol2_cli  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ITEM_PAGE = ROOT / "docs" / "lol2-item-handlers.md"
OPCODE_PAGE = ROOT / "docs" / "lol2-script-opcodes.md"
ITEM_BEGIN = "<!-- instance-plus5:begin -->"
ITEM_END = "<!-- instance-plus5:end -->"
OP_BEGIN = "<!-- script-arms:begin -->"
OP_END = "<!-- script-arms:end -->"
ANALYSIS = 0x59024
FILE_BIAS = 0x37000
CODE_FILE = 0x90024
CODE_SIZE = 0x130000
DATA_FILE = 0x1C1024
IMAGE_SIZE = 0x1E2AAF
CODE_LO, CODE_HI = ANALYSIS, ANALYSIS + CODE_SIZE
SEEDS = [
    0x95804, 0x95824, 0x95840, 0x95894, 0x94041, 0x9B5B5, 0x7788C,
    0xB50C0, 0xB5BAC, 0xB3EC8, 0xB5937, 0xD7890, 0xB6B8D, 0x64770,
    0x64A8C, 0x65518, 0xD259C, 0x94100, 0x5D904, 0x95328, 0xA62F4,
    0xF22B4, 0x1502EB, 0xED6D0, ANALYSIS + 0xF7B0C,
]
WINDOWS = (
    (0x64800, 0x64C80, "shared or row"),
    (0x65500, 0x65840, "opcode 208"),
    (0x65954, 0x65C00, "opcode 210"),
    (0xA6200, 0xA6800, "creature command"),
    (0xACA00, 0xAE200, "other record"),
    (0xAE800, 0xAEE00, "other near table"),
    (0xB3500, 0xB4200, "opcode 6"),
    (0xB4300, 0xB4FFF, "timer"),
    (0xB5000, 0xB6C00, "script command"),
    (0xB8000, 0xB9000, "other one"),
    (0xD4700, 0xD4800, "paired object"),
    (0xD7890, 0xD8A40, "opcode 2 or object"),
    (0x110800, 0x111000, "other record"),
    (0x114000, 0x116000, "region row"),
    (0x14E000, 0x15C000, "other record"),
    (0x162000, 0x185000, "other record"),
)
EXPECTED_GROUPS = {
    "instance": 15,
    "shared or row": 21,
    "opcode 208": 5,
    "opcode 210": 12,
    "creature command": 9,
    "other record": 12,
    "other near table": 3,
    "opcode 6": 14,
    "timer": 15,
    "script command": 12,
    "other one": 1,
    "paired object": 3,
    "opcode 2 or object": 22,
    "region row": 18,
}
INSTANCE = {
    0x77A73: ("read", "mov bl, byte ptr [ebx + 5]", "`[esi+0x90F]`",
              "when nonzero, stores the result of `0x95894` at `[0x2260F]` and 0 at `[0x2260B]`"),
    0x7E47F: ("read", "mov dl, byte ptr [esi + 5]", "`[0x23C57]`",
              "when nonzero and bit 0 of `[0x269C4]` is clear, calls `0xE3924`"),
    0x8CA4B: ("read", "mov al, byte ptr [eax + 5]", "`[0x23C57]`",
              "when nonzero and bit 0 of `[0x269C4]` is clear, calls `0xE3924`"),
    0x94060: ("write", "mov byte ptr [eax + 5], 0", "allocation + 0x2C",
              "constructor stores 0"),
    0x9581B: ("read", "mov dl, byte ptr [ebx + 5]", "second argument",
              "copy reads the source byte"),
    0x9581E: ("write", "mov byte ptr [eax + 5], dl", "first argument",
              "copy writes the source byte"),
    0x95830: ("write", "mov byte ptr [eax + 5], 0", "first argument",
              "initializer stores 0"),
    0x9B5C2: ("read", "mov dl, byte ptr [eax + 5]", "`[0x23C57]`",
              "handler 102 goes on only when it is zero"),
    0x9B5E9: ("write", "mov byte ptr [eax + 5], 5", "`[0x23C57]`",
              "handler 102 stores 5, then the pointer at `[0x2260B]`"),
    0xD25F6: ("read", "mov al, byte ptr [ebx + 5]", "return of `0x77ACC` (old `[0x23348+0x90F]`)",
              "when nonzero, stores the pointer at `[0x2260B]`"),
    0xD79A4: ("write", "mov byte ptr [edi + 5], al", "`[ebx+0x97]`, that is `[0x2260B]`",
              "opcode 2 selector 0 stores 0 (al cleared at `0xD79A2`), then 0 at `[0x2260B]`"),
    0xD7AD0: ("write", "mov byte ptr [esi + 5], al", "`[ebx+0x97]`, that is `[0x2260B]`",
              "opcode 2 selector 38 stores 0 (al cleared at `0xD7ACE`), then edi at `[0x2260B]`"),
    0xD7B07: ("write", "mov byte ptr [eax + 5], 0", "`[ebx+0x9B]` + 0x2C, that is `[0x2260F]` + 0x2C",
              "opcode 2 selector 38 stores 0, then 0 at `[0x2260F]`"),
    0xDD593: ("write", "mov byte ptr [edx + 5], 0", "`[eax+0x97]`, that is `[0x2260B]`",
              "`0xDD584`, called with 0x22574 at `0xED80C`, stores 0, then 0 at `[0x2260B]`"),
    0xDD5CB: ("write", "mov byte ptr [edx + 5], 0", "`[ebx+0x9B]` + 0x2C, that is `[0x2260F]` + 0x2C",
              "`0xDD584` stores 0, then 0 at `[0x2260F]`"),
}
ALIAS_31 = {
    0xD79DC: ("write", "mov byte ptr [eax + 0x31], 0", "`[ebx+0x9B]`, that is `[0x2260F]`",
              "opcode 2 selector 0 stores 0 at object +0x31 (record +5), then 0 at `[0x2260F]`"),
}
INNER_ANCHORS = {4: 0xD7F58, 5: 0xD89F6, 6: 0xD89F6, 19: 0xD7FB7, 28: 0xD8797, 60: 0xD7F5D}
DISPATCH_5_6 = {5: 0xB5ACE, 6: 0xB5B05}
PAGE_ARMS = {
    9: {2: 0xB50E6, 3: 0xB5117, 10: 0xB5393, 16: 0xB5401, 17: 0xB50FB, 18: 0xB5109, 19: 0xB5420, 21: 0xB5448},
}
PLAYER = 0x22574
LINEAR_5 = 270
SLOTS = {6: (13, 0), 9: (31, 4), 15: (69, 42)}
BANNED = ("UNCONFIRMED", "UNKNOWN", "PROVEN", "CONFIRMED")


def load_image(data_dir):
    path = game_path(Path(data_dir).resolve().parent, "LOLG.DAT")
    image = path.read_bytes()
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"program length {len(image)}")
    return image


def decoder():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    return md


def one(image, md, va):
    if not (CODE_LO <= va < CODE_HI):
        return None
    found = list(md.disasm(image[va + FILE_BIAS:va + FILE_BIAS + 16], va))
    return found[0] if found and found[0].address == va else None


def text_of(insn):
    return f"{insn.mnemonic} {insn.op_str}".strip()


def cell(text):
    if any(word in text for word in BANNED) or "|" in text or "\n" in text:
        raise ValueError(f"table cell is not plain: {text!r}")
    return text


def expect(image, md, va, text):
    insn = one(image, md, va)
    got = text_of(insn) if insn else None
    if got != text:
        raise ValueError(f"0x{va:X} is {got!r}, wanted {text!r}")
    return insn


def returns_eax(image, md, va, imm):
    """True when va sets eax to imm and a ret follows with no further call."""
    insn = one(image, md, va)
    if imm is None:
        if insn is None or text_of(insn) != "xor eax, eax":
            return False
    elif insn is None or text_of(insn) != f"mov eax, {imm}":
        return False
    saw_call = False
    cursor = va
    for _ in range(8):
        insn = one(image, md, cursor)
        if insn is None:
            return False
        if insn.mnemonic == "call":
            saw_call = True
        if insn.mnemonic == "ret":
            return not saw_call
        cursor += insn.size
    return False


def dword(image, file_at):
    return struct.unpack_from("<I", image, file_at)[0]


def table_targets(image, disp, count):
    if not (0 <= disp < CODE_SIZE):
        raise ValueError(f"table disp 0x{disp:X}")
    base = CODE_FILE + disp
    out = []
    for index in range(count):
        va = dword(image, base + 4 * index) + ANALYSIS
        if not (CODE_LO <= va < CODE_HI):
            raise ValueError(f"table 0x{disp:X} index {index} is 0x{va:X}")
        out.append(va)
    return out


def reach(image, md):
    """Follow direct branches and sized jump tables. One pass, as the census was counted."""
    reached = {}
    work, queued = [], set()

    def add(va):
        if CODE_LO <= va < CODE_HI and va not in queued:
            queued.add(va)
            work.append(va)

    for seed in SEEDS:
        add(seed)

    def prev_insn(va):
        for size in range(1, 16):
            insn = reached.get(va - size)
            if insn is not None and insn.size == size:
                return insn
        return None

    def bound_before(jmp_va):
        cur = prev_insn(jmp_va)
        jcc = None
        steps = 0
        while cur is not None and steps < 6:
            if cur.mnemonic in ("ja", "jae") and cur.operands and cur.operands[0].type == X86_OP_IMM:
                jcc = cur
            if cur.mnemonic == "cmp" and len(cur.operands) == 2 and cur.operands[1].type == X86_OP_IMM:
                imm = cur.operands[1].imm & 0xFFFFFFFF
                if jcc is not None and imm <= 0x80:
                    if jcc.mnemonic == "ja":
                        return imm + 1
                    if jcc.mnemonic == "jae":
                        return imm
                return None
            cur = prev_insn(cur.address)
            steps += 1
        return None

    tables = []
    while work:
        va = work.pop()
        if va in reached:
            continue
        insn = one(image, md, va)
        if insn is None:
            continue
        if any((va - off) in reached and reached[va - off].size > off for off in range(1, insn.size)):
            continue
        reached[va] = insn
        if insn.id == X86_INS_RET:
            continue
        if insn.operands and insn.operands[0].type == X86_OP_IMM and (
            insn.id in (X86_INS_JMP, X86_INS_CALL) or insn.mnemonic.startswith("j")
        ):
            add(insn.operands[0].imm & 0xFFFFFFFF)
            if insn.id != X86_INS_JMP:
                add(va + insn.size)
            continue
        if insn.id == X86_INS_JMP and insn.operands and insn.operands[0].type == X86_OP_MEM:
            op = insn.operands[0]
            if op.mem.scale == 4 and op.mem.base == X86_REG_INVALID and op.mem.index != X86_REG_INVALID:
                count = bound_before(va)
                if count is None and op.mem.disp == 0x5C878:
                    count = 24
                if count:
                    try:
                        entries = table_targets(image, op.mem.disp, count)
                    except ValueError:
                        entries = None
                    if entries:
                        tables.append((va, op.mem.disp, count))
                        for entry in entries:
                            add(entry)
            continue
        if insn.id != X86_INS_JMP:
            add(va + insn.size)

    hits, hits31 = [], []
    for va, insn in reached.items():
        for op in insn.operands:
            if (op.type == X86_OP_MEM and op.size == 1 and op.mem.disp == 0x31
                    and op.mem.index == X86_REG_INVALID
                    and op.mem.base not in (X86_REG_ESP, X86_REG_EBP, X86_REG_INVALID)):
                prev = [reached.get(va - size) for size in range(1, 64)]
                base = insn.reg_name(op.mem.base)
                for back in sorted((p for p in prev if p is not None), key=lambda p: -p.address)[:8]:
                    if text_of(back).startswith(f"mov {base}, ") and "0x9b]" in text_of(back):
                        hits31.append((va, text_of(insn)))
                        break
        for op in insn.operands:
            if (op.type == X86_OP_MEM and op.size == 1 and op.mem.disp == 5
                    and op.mem.index == X86_REG_INVALID
                    and op.mem.base not in (X86_REG_ESP, X86_REG_EBP, X86_REG_INVALID)):
                hits.append((va, text_of(insn)))
    hits.sort()
    hits31.sort()
    return hits, hits31


def linear_count(image):
    """Byte accesses at displacement 5 in a linear pass over the code section."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    count = 0
    for insn in md.disasm(image[CODE_LO + FILE_BIAS:CODE_HI + FILE_BIAS], CODE_LO):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if (op.type == X86_OP_MEM and op.size == 1 and op.mem.disp == 5
                    and op.mem.index == X86_REG_INVALID
                    and op.mem.base not in (X86_REG_ESP, X86_REG_EBP, X86_REG_INVALID)):
                count += 1
    return count


def classify(va):
    if va in INSTANCE:
        return "instance"
    for lo, hi, name in WINDOWS:
        if lo <= va <= hi:
            return name
    return "UNCLASSIFIED"


def require_hits(hits, hits31):
    if [va for va, _text in hits31] != sorted(ALIAS_31):
        raise ValueError(f"displacement-0x31 stores through +0x9B: {[hex(va) for va, _t in hits31]}")
    for va, text in hits31:
        if text != ALIAS_31[va][1]:
            raise ValueError(f"0x{va:X} text {text!r}")
    groups = Counter(classify(va) for va, _text in hits)
    if groups.get("UNCLASSIFIED") or dict(groups) != EXPECTED_GROUPS:
        sample = [(hex(va), classify(va), text) for va, text in hits if classify(va) == "UNCLASSIFIED"][:8]
        raise ValueError(f"displacement-5 census {dict(groups)} sample {sample}")
    found = {}
    for va, text in hits:
        if va in INSTANCE:
            found[va] = text
    if set(found) != set(INSTANCE):
        raise ValueError("instance byte +5 sites changed")
    for va, (_access, want, _pointer, _role) in INSTANCE.items():
        if found[va] != want:
            raise ValueError(f"0x{va:X} text {found[va]!r}")
    return len(hits)


def arm_inner(image, md, value):
    """First instruction after the byte-+4 search at 0xD84D6."""
    va = 0xD84D6
    jumped = False
    for _ in range(80):
        insn = one(image, md, va)
        if insn is None:
            return None
        if (insn.mnemonic == "cmp" and insn.operands and insn.operands[0].type == X86_OP_REG
                and insn.reg_name(insn.operands[0].reg) == "ah" and insn.operands[1].type == X86_OP_IMM):
            imm = insn.operands[1].imm & 0xFF
            nxt = one(image, md, insn.address + insn.size)
            if nxt is None:
                return None
            nxt2 = one(image, md, nxt.address + nxt.size)
            if nxt.mnemonic == "jb" and nxt.operands[0].type == X86_OP_IMM:
                if value < imm:
                    va = nxt.operands[0].imm & 0xFFFFFFFF
                elif nxt2 and nxt2.mnemonic == "jbe" and nxt2.operands[0].type == X86_OP_IMM:
                    va = nxt2.operands[0].imm if value == imm else nxt2.address + nxt2.size
                else:
                    va = nxt.address + nxt.size
                jumped = True
                continue
            if nxt.mnemonic == "jbe" and nxt.operands[0].type == X86_OP_IMM:
                va = nxt.operands[0].imm if value <= imm else nxt.address + nxt.size
                jumped = True
                continue
            if nxt.mnemonic == "ja" and nxt.operands[0].type == X86_OP_IMM:
                va = nxt.operands[0].imm if value > imm else nxt.address + nxt.size
                jumped = True
                continue
            if nxt.mnemonic == "je" and nxt.operands[0].type == X86_OP_IMM:
                va = nxt.operands[0].imm if value == imm else nxt.address + nxt.size
                jumped = True
                continue
            return None
        if insn.mnemonic == "jmp" and insn.operands and insn.operands[0].type == X86_OP_IMM:
            va = insn.operands[0].imm & 0xFFFFFFFF
            continue
        if not jumped:
            va = insn.address + insn.size
            continue
        return va
    return None


def opcode2_rows(image, md):
    expect(image, md, 0xD84D6, "mov ah, byte ptr [edx + 4]")
    expect(image, md, 0xB5BB3, "cmp dh, 5")
    expect(image, md, 0xB5BB6, "jb 0xb5bc7")
    expect(image, md, 0xB5BB8, "jbe 0xb5ace")
    expect(image, md, 0xB5BC1, "je 0xb5b05")
    expect(image, md, 0xB5BCD, "call 0xd7890")
    expect(image, md, 0xB5AE4, "call 0x5fbc8")
    expect(image, md, 0xB5AF8, "call 0xdd5dc")
    expect(image, md, 0xB5B12, "call 0x5fbc8")
    for value, want in INNER_ANCHORS.items():
        got = arm_inner(image, md, value)
        if got != want:
            raise ValueError(f"selector {value} lands at 0x{got:X}")
    default = {arm_inner(image, md, value) for value in range(67, 256)}
    if default != {0xD8527}:
        raise ValueError(f"opcode 2 default {sorted(default)}")
    rows = []
    for value in range(67):
        handler = DISPATCH_5_6[value] if value in DISPATCH_5_6 else arm_inner(image, md, value)
        if handler is None:
            raise ValueError(f"selector {value} has no landing")
        rows.append(("opcode 2", str(value), handler))
    rows.append(("opcode 2", "67-255", 0xD8527))
    return rows


def switch_rows(image, md):
    specs = (
        ("opcode 6", 0xB4119, "cmp al, 0xc", "ja 0xb3f50", 0xB4126, 0x5AE70, 13, 0xB3F50),
        ("opcode 9", 0xB50CF, "cmp dl, 0x22", "ja 0xb56be", 0xB50DE, 0x5C010, 35, 0xB56BE),
        ("opcode 15", 0xB5CE4, "cmp al, 0x70", "ja 0xb5947", 0xB5CF1, 0x5C6B4, 0x71, 0xB5947),
    )
    rows = []
    for name, cmp_at, cmp_text, ja_text, jmp_at, disp, count, above in specs:
        expect(image, md, cmp_at, cmp_text)
        expect(image, md, cmp_at + one(image, md, cmp_at).size, ja_text)
        insn = one(image, md, jmp_at)
        if insn is None or insn.mnemonic != "jmp" or insn.operands[0].mem.disp != disp:
            raise ValueError(f"{name} jump at 0x{jmp_at:X}")
        targets = table_targets(image, disp, count)
        number = int(name.split()[1])
        if (len(set(targets)), targets.count(above)) != SLOTS[number]:
            raise ValueError(f"{name} distinct targets {len(set(targets))}, past-the-end {targets.count(above)}")
        pinned = PAGE_ARMS.get(9 if name == "opcode 9" else 0, {})
        for index, handler in enumerate(targets):
            if index in pinned and handler != pinned[index]:
                raise ValueError(f"{name} index {index} is 0x{handler:X}")
            rows.append((name, str(index), handler))
        if name == "opcode 6" and not returns_eax(image, md, above, "1"):
            raise ValueError("opcode 6 above-range arm")
        if name == "opcode 6" and targets[1] != 0xB3F5C:
            raise ValueError("opcode 6 arm 1")
        expect(image, md, 0xB3F5D, "call 0x9f584")
    return rows


def slot_rows(image, md):
    slots = (
        ("controls", 0x5484, 0x5D904),
        ("placed item", 0x573C, 0x95328),
        ("creature", 0x58D0, 0xA62F4),
        ("pure virtual", 0x59C8, 0x1502EB),
        ("pure virtual", 0x5AD8, 0x1502EB),
        ("props", 0xA848, 0xF22B4),
        ("player", 0x5C20, 0xD7890),
    )
    rows = []
    for name, cell_at, handler in slots:
        raw = dword(image, DATA_FILE + cell_at + 0xAC)
        if raw + ANALYSIS != handler:
            raise ValueError(f"{name} +0xAC is 0x{raw + ANALYSIS:X}")
        rows.append((name, cell_at, handler))
    expect(image, md, 0x5D90F, "cmp al, 8")
    expect(image, md, 0x95334, "cmp al, 9")
    expect(image, md, 0xF22BF, "cmp al, 8")
    if not all(returns_eax(image, md, va, "1") for va in (0x5D913, 0x9533C, 0xF22C3, 0xA6359)):
        raise ValueError("opcode 1 or 3 fallthrough")
    expect(image, md, 0xA6305, "sub al, 3")
    expect(image, md, 0xA6307, "cmp al, 0xa")
    expect(image, md, 0xA6309, "ja 0xa6359")
    if table_targets(image, 0x4D2A4, 11)[0] != 0xA631C:
        raise ValueError("creature opcode 3 arm")
    expect(image, md, 0xA6334, "call 0x95b68")
    if not returns_eax(image, md, 0xA6339, "1"):
        raise ValueError("creature opcode 3 result")
    expect(image, md, 0xD78A1, "cmp al, 2")
    expect(image, md, 0xD78A3, "jb 0xd78af")
    expect(image, md, 0xD78AD, "je 0xd78b8")
    if not returns_eax(image, md, 0xD78AF, None):
        raise ValueError("player opcode 1 result")
    expect(image, md, 0xD78B8, "cmp byte ptr [0x223d4], 0")
    expect(image, md, 0xD78BF, "jne 0xd78af")
    expect(image, md, 0xD78D9, "call 0x95b68")
    expect(image, md, 0xD78E3, "je 0xd78b1")
    expect(image, md, 0xD78E5, "test byte ptr [ebx + 0x228], 0x80")
    expect(image, md, 0xD78EE, "test byte ptr [ebx + 0x227], 0x40")
    expect(image, md, 0xD78FC, "call 0x95600")
    if not returns_eax(image, md, 0xD7904, "1"):
        raise ValueError("player opcode 3 result")
    expect(image, md, 0x1502EB, "cmp word ptr [0x197b0], 0")
    expect(image, md, 0x15030D, "ret")
    return rows


def require_sites(image, md):
    expect(image, md, 0x94059, "add eax, 0x2c")
    expect(image, md, 0x9406D, "mov dword ptr [eax - 4], 0x573c")
    expect(image, md, 0x95811, "mov dl, byte ptr [ebx + 4]")
    expect(image, md, 0x95830, "mov byte ptr [eax + 5], 0")
    expect(image, md, 0x77A6D, "mov ebx, dword ptr [esi + 0x90f]")
    expect(image, md, 0xD25BA, "call 0x77acc")
    expect(image, md, 0xD25BF, "mov ebx, eax")
    expect(image, md, 0xD7B04, "lea eax, [edi + 0x2c]")
    expect(image, md, 0xDD5C8, "lea edx, [ebx + 0x2c]")
    # The player object is 0x22574, so its +0x97 is [0x2260B] and its +0x9B is [0x2260F].
    if PLAYER + 0x97 != 0x2260B or PLAYER + 0x9B != 0x2260F:
        raise ValueError("player offsets")
    expect(image, md, 0xB5BC8, "push 0x22574")
    expect(image, md, 0xB5BCD, "call 0xd7890")
    expect(image, md, 0xD7899, "mov ebx, dword ptr [ebp + 0x14]")
    expect(image, md, 0xED807, "push 0x22574")
    expect(image, md, 0xED80C, "call 0xdd584")
    expect(image, md, 0xDD585, "mov eax, dword ptr [esp + 8]")
    expect(image, md, 0x9B5ED, "mov dword ptr [0x2260b], eax")
    expect(image, md, 0xD25FD, "mov dword ptr [0x2260b], ebx")
    expect(image, md, 0x77A7C, "mov dword ptr [0x2260f], eax")
    expect(image, md, 0x77A81, "mov dword ptr [0x2260b], ebx")
    expect(image, md, 0xD89F0, "je 0xd7910")
    expect(image, md, 0xD7910, "test byte ptr [ebx + 0x227], 0x40")
    expect(image, md, 0xD7917, "je 0xd89f6")
    expect(image, md, 0xD7995, "mov edi, dword ptr [ebx + 0x97]")
    expect(image, md, 0xD79A2, "xor al, al")
    expect(image, md, 0xD79A7, "mov dword ptr [ebx + 0x97], 0")
    expect(image, md, 0xD79C8, "mov eax, dword ptr [ebx + 0x9b]")
    expect(image, md, 0xD79E3, "mov dword ptr [ebx + 0x9b], 0")
    expect(image, md, 0xD7AC1, "mov esi, dword ptr [ebx + 0x97]")
    expect(image, md, 0xD7ACE, "xor al, al")
    expect(image, md, 0xD7AD3, "mov dword ptr [ebx + 0x97], edi")
    expect(image, md, 0xD7AF0, "mov edi, dword ptr [ebx + 0x9b]")
    expect(image, md, 0xD7B0B, "mov dword ptr [ebx + 0x9b], 0")
    expect(image, md, 0xDD589, "mov edx, dword ptr [eax + 0x97]")
    expect(image, md, 0xDD597, "mov dword ptr [eax + 0x97], 0")
    expect(image, md, 0xDD5B8, "mov ebx, dword ptr [eax + 0x9b]")
    expect(image, md, 0xDD5CF, "mov dword ptr [eax + 0x9b], 0")
    expect(image, md, 0x7E48A, "test byte ptr [0x269c4], 1")
    expect(image, md, 0x7E4AC, "call 0xe3924")
    expect(image, md, 0x8CA52, "test byte ptr [0x269c4], 1")
    expect(image, md, 0x8CA78, "call 0xe3924")
    window = image[0x960EA + FILE_BIAS:0x96112 + FILE_BIAS]
    if window[:12] != bytes.fromhex("A1046909008B000588000000"):
        raise ValueError("handler 2 window")
    va = 0x960EA
    while va < 0x96112:
        insn = one(image, md, va)
        if insn is None:
            raise ValueError(f"handler 2 window at 0x{va:X}")
        for op in insn.operands:
            if op.type == X86_OP_MEM and op.mem.disp == 5 and op.size == 1:
                raise ValueError(f"displacement 5 at 0x{va:X}")
        va += insn.size


def instance_body():
    lines = [
        "**CONFIRMED.** Sixteen instructions read or write byte +5 of the 6-byte record at allocation +0x2C "
        "(a dword at +0, a byte at +4 and a byte at +5). `tools/lol2_instance_field.py --check` follows the code from 25 entry points "
        "and finds 162 byte accesses at displacement 5. Fifteen of them use a register that holds a record pointer, and one more "
        "writes the same byte as displacement 0x31 from the object start. "
        "The constructor at `0x94044` adds 0x2C at `0x94059`, stores 0 in both bytes and the dword, and stores vtable `0x573C` at `[eax-4]`. "
        "The copy at `0x95804` copies byte +4, the dword and byte +5. The initializer at `0x95824` stores 0 in byte +5. "
        "The player object is `0x22574` (the opcode 2 dispatcher passes it to `0xD7890` at `0xB5BC8`, and `0xED807` passes it to `0xDD584`), "
        "so its +0x97 is `[0x2260B]` and its +0x9B is `[0x2260F]`. "
        "Handler 102 is the only site that stores a nonzero constant: 5 in the held record, whose pointer it then keeps at `[0x2260B]`. "
        "When the byte is nonzero, the read at `0xD25F6` keeps the record pointer at `[0x2260B]`, and the read at `0x77A73` keeps the object that `0x95894` returns at `[0x2260F]` and clears `[0x2260B]`. "
        "Opcode 2 selector 0 (when player byte +0x227 has bit 0x40), selector 38 and `0xDD584` store 0 in the byte again and clear `[0x2260B]` and `[0x2260F]`. "
        "The other 147 accesses lie in the command, object, timer and region-row code windows listed in the tool. "
        f"A linear pass over the whole code section finds {LINEAR_5} such accesses; the {LINEAR_5 - 162} the census does not reach are not classified here.",
        "",
        "| Address | Access | Instruction | Record pointer | Effect |",
        "|---|---|---|---|---|",
    ]
    rows = dict(INSTANCE)
    rows.update(ALIAS_31)
    for va in sorted(rows):
        access, instruction, pointer, role = rows[va]
        lines.append(f"| `0x{va:X}` | {cell(access)} | `{cell(instruction)}` | {cell(pointer)} | {cell(role)} |")
    return "\n".join(lines)


def script_body(image, md, op_rows, ac_rows):
    lines = [
        "**CONFIRMED.** `tools/lol2_instance_field.py --check` lists every selector handler. "
        "Opcode 2 at `0xB5BAC` takes selector 5 at `0xB5ACE` and selector 6 at `0xB5B05`; both call `0x5FBC8`, and selector 5 then calls `0xDD5DC`. "
        "Every other selector calls `0xD7890`, whose search on byte +4 is the opcode 2 row below. "
        "That search lands at `0xD89F6` for values 5 and 6, which this dispatcher does not pass in, and a value above 66 lands at `0xD8527`. "
        "Opcode 6 (`0xB4126`, table at `0xB3E94`, indexes 0 through 12), opcode 9 (`0xB50DE`, table at `0xB5034`, indexes 0 through 34) "
        "and opcode 15 (`0xB5CF1`, table at `0xB56D8`, indexes 0 through 112) follow. "
        "A selector past the last index lands at `0xB3F50`, `0xB56BE` or `0xB5947`. "
        f"The tables hold {SLOTS[6][0]}, {SLOTS[9][0]} and {SLOTS[15][0]} different targets. "
        f"In opcode 9, {SLOTS[9][1]} indexes go to the past-the-end landing `0xB56BE`; in opcode 15, {SLOTS[15][1]} go to `0xB5947`, the common low-table epilogue that every out-of-range selector also reaches. "
        "On opcodes 1 and 3, controls, the placed-item vtable and props return 1. "
        "The player returns 0 for opcode 1. For opcode 3 it returns 0 when `[0x223D4]` is nonzero; otherwise it calls `0x95B68`, returns 0 when that returns 0, and else returns 1, calling `0x95600` first when player byte +0x228 bit 0x80 is clear and +0x227 bit 0x40 is set. "
        "A creature returns 1 for opcode 1 and calls `0x95B68` for opcode 3. "
        "Both pure-virtual cells enter `0x1502EB` and do not read the opcode.",
        "",
        "| Switch | Selector | Handler | First instruction |",
        "|---|---:|---|---|",
    ]
    for name, selector, handler in op_rows:
        insn = one(image, md, handler)
        if insn is None:
            raise ValueError(f"{name} selector {selector} at 0x{handler:X}")
        lines.append(f"| {cell(name)} | {cell(selector)} | `0x{handler:X}` | `{cell(text_of(insn))}` |")
    lines.extend([
        "",
        "| Slot | Cell | Handler | Opcode 1 | Opcode 3 |",
        "|---|---|---|---|---|",
        "| controls | `0x5484` | `0x5D904` | returns 1 | returns 1 |",
        "| placed item | `0x573C` | `0x95328` | returns 1 | returns 1 |",
        "| creature | `0x58D0` | `0xA62F4` | returns 1 | calls `0x95B68`, then returns 1 |",
        "| pure virtual | `0x59C8` | `0x1502EB` | does not read the opcode | does not read the opcode |",
        "| pure virtual | `0x5AD8` | `0x1502EB` | does not read the opcode | does not read the opcode |",
        "| props | `0xA848` | `0xF22B4` | returns 1 | returns 1 |",
        "| player | `0x5C20` | `0xD7890` | returns 0 | 0 when `[0x223D4]` is nonzero or `0x95B68` returns 0, else 1 |",
    ])
    if [row[2] for row in ac_rows] != [0x5D904, 0x95328, 0xA62F4, 0x1502EB, 0x1502EB, 0xF22B4, 0xD7890]:
        raise ValueError("slot handlers changed")
    for line in lines:
        if any(word in line for word in ("UNCONFIRMED", "UNKNOWN", "PROVEN")):
            raise ValueError("script text uses a rating label")
    return "\n".join(lines)


def marked(text, begin, end):
    if begin not in text or end not in text:
        raise ValueError("markers are missing")
    body = text.split(begin, 1)[1].split(end, 1)[0]
    if body.startswith("\n"):
        body = body[1:]
    if body.endswith("\n"):
        body = body[:-1]
    return body


def build(data_dir):
    image = load_image(data_dir)
    md = decoder()
    hits, hits31 = reach(image, md)
    count = require_hits(hits, hits31)
    require_sites(image, md)
    linear = linear_count(image)
    if linear != LINEAR_5:
        raise ValueError(f"linear displacement-5 count {linear}")
    op_rows = opcode2_rows(image, md) + switch_rows(image, md)
    ac_rows = slot_rows(image, md)
    if count != 162 or len(op_rows) != 67 + 1 + 13 + 35 + 113:
        raise ValueError(f"census {count} rows {len(op_rows)}")
    return instance_body(), script_body(image, md, op_rows, ac_rows)


def main():
    parser = lol2_cli.tool_args(__doc__, out_help="write both generated sections to this file")
    args = parser.parse_args()
    try:
        item, script = build(args.data)
    except (OSError, ValueError, KeyError, struct.error) as error:
        parser.exit(1, f"CHECK instance_field: {error}\n")
    if args.check:
        try:
            item_body = marked(ITEM_PAGE.read_text(encoding="utf-8"), ITEM_BEGIN, ITEM_END)
            script_body_stored = marked(OPCODE_PAGE.read_text(encoding="utf-8"), OP_BEGIN, OP_END)
        except (OSError, ValueError) as error:
            parser.exit(1, f"CHECK instance_field: {error}\n")
        if item_body != item or script_body_stored != script:
            parser.exit(1, "CHECK instance_field: docs differ from the tables\n")
        print("CHECK instance_field: 16 instance byte +5 sites (15 of 162 displacement-5 accesses, 1 at +0x31); "
              "opcode 2 has 67 selectors; opcode 6, 9 and 15 tables have 13, 35 and 113 slots, 13, 31 and 69 targets; docs match")
        return 0
    text = f"{ITEM_BEGIN}\n{item}\n{ITEM_END}\n\n{OP_BEGIN}\n{script}\n{OP_END}\n"
    if args.out:
        lol2_cli.refuse_repo_output(args.out)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote instance byte +5 and script arms to {args.out}")
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
