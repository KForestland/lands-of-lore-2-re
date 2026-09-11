#!/usr/bin/env python3
"""Replay native edge-mask update with supplied helper result and facing score."""
import argparse
import itertools
import json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay


def replay(m, mask, edge, helper, score):
    m.regs.update(ebx=0x600000, esp=0x700000, eax=helper)
    m.writemem(0x60009c, 1, mask)
    m.writemem(0x70053c, 4, 1 << edge)
    m.writemem(0x700534, 4, 16 << edge)
    m.writemem(0x700544, 4, 0)
    pc = 0xf5dfb
    zero = negative = False
    for _ in range(30):
        if pc == 0xf5eaf:
            return m.readmem(0x60009c, 1)
        # The facing arithmetic is an input boundary in this bounded replay.
        if pc == 0xf5e03:
            m.regs['eax'] = score & 0xffffffff
            pc = 0xf5e82
        i = m.instructions[pc]
        o = i.operands
        nxt = pc + i.size
        if i.mnemonic == 'mov':
            m.put(i, o[0], m.get(i, o[1]))
        elif i.mnemonic == 'test':
            value = m.get(i, o[0]) & m.get(i, o[1])
            zero, negative = value == 0, bool(value & 0x80000000)
        elif i.mnemonic in ('je', 'jle'):
            if zero or (i.mnemonic == 'jle' and negative):
                nxt = m.get(i, o[0])
        elif i.mnemonic == 'or':
            m.put(i, o[0], m.get(i, o[0]) | m.get(i, o[1]))
        else:
            raise ValueError((hex(pc), i.mnemonic))
        pc = nxt
    raise ValueError('Instruction limit')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    exe = (a.game_root / 'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH, 'Executable changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    instructions = {i.address: i for i in md.disasm(exe[0xf5dfb+0x37000:0xf5eaf+0x37000], 0xf5dfb)}
    m = WallReplay(instructions, b'')
    cases = 0
    for mask, edge, helper, score in itertools.product(range(256), range(4), [0, 1, 0xffffffff], [-2147483648, -1, 0, 1, 2147483647]):
        expected = mask | (16 << edge)
        if helper == 0 or score > 0:
            expected |= 1 << edge
        actual = replay(m, mask, edge, helper, score)
        require(actual == expected, f'Mask mismatch: {mask, edge, helper, score}')
        cases += 1
    report = dict(cases=cases, mismatches=0, executable_sha256=sha(exe),
        rule='Always set bit edge+4; also set bit edge when helper result is zero or supplied signed facing score is positive. Preserve other bits.',
        scope='Original F5DFB/F5DFD and F5E82..F5EA9 instructions replayed. F5E03..F5E7B arithmetic bypassed with supplied score. Helper 1338B0, camera inputs, edge lookup tables, reciprocal neighbor propagation and live visibility remain unverified.')
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'wall_edge_mask.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
