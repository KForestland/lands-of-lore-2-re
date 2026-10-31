#!/usr/bin/env python3
"""Verify original edge-facing arithmetic with synthetic runtime coordinates."""
import argparse
import itertools
import json
import random
import struct
from pathlib import Path
import capstone
from lol2_native_height_lookup import recover
from lol2_verify_flat_wall_spans import WallReplay


def signed(v):
    return (v + 2**31) % 2**32 - 2**31


def facing(a, b, p):
    # Each subtraction wraps before signed multiplication. Each product is
    # independently truncated to its high half, before the final subtraction.
    first = (signed(p[0]-a[0]) * signed(b[1]-a[1])) // 2**32
    second = (signed(p[1]-a[1]) * signed(b[0]-a[0])) // 2**32
    return signed(first-second)


def replay(m, points, edge, p):
    m.regs.update(ebx=0x600000, esp=0x700000)
    for k, (x, y) in enumerate(points):
        m.writemem(0x600000+k*12, 4, x & 0xffffffff)
        m.writemem(0x600008+k*12, 4, y & 0xffffffff)
    for offset, value in [(0x540, edge*4), (0x524, p[0]), (0x520, p[1])]:
        m.writemem(0x700000+offset, 4, value & 0xffffffff)
    pc = 0xf5e03
    while pc < 0xf5e82:
        i = m.instructions[pc]
        o = i.operands
        if i.mnemonic == 'mov':
            m.put(i, o[0], m.get(i, o[1]))
        elif i.mnemonic == 'sub':
            m.put(i, o[0], (m.get(i, o[0])-m.get(i, o[1])) & 0xffffffff)
        elif i.mnemonic == 'shl':
            m.put(i, o[0], (m.get(i, o[0]) << m.get(i, o[1])) & 0xffffffff)
        elif i.mnemonic == 'imul' and len(o) == 1:
            product = signed(m.regs['eax']) * signed(m.get(i, o[0]))
            m.regs['eax'] = product & 0xffffffff
            m.regs['edx'] = (product >> 32) & 0xffffffff
        else:
            raise ValueError((hex(pc), i.mnemonic))
        pc += i.size
    return signed(m.readmem(0x700530, 4))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    exe = (args.game_root/'LOLG.DAT').read_bytes()
    _, proof = recover(exe)  # Pins executable and resolves LE data pages.
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    m = WallReplay({i.address:i for i in md.disasm(exe[0xf5e03+0x37000:0xf5e82+0x37000], 0xf5e03)}, b'')
    tables = []
    for address in (0xeb24, 0xeb34):
        offset = proof['pages'][address//4096]['file_offset'] + address%4096
        data = exe[offset:offset+16]
        m.mem[address:address+16] = data
        tables.append(struct.unpack('<4I', data))
    assert tables == [(3,6,9,0), (0,3,6,9)]
    rng = random.Random(20260911)
    values = [-2**31, -65536, -1, 0, 1, 65536, 2**31-1]
    fixtures = [((x,y),(z,x),(y,z)) for x,y,z in itertools.product(values, repeat=3)]
    fixtures += [tuple(tuple(rng.randrange(-2**31,2**31) for _ in range(2)) for _ in range(3)) for _ in range(4096)]
    count = 0
    for a,b,p in fixtures:
        for edge in range(4):
            points = [(0,0)]*4
            points[tables[0][edge]//3] = a
            points[tables[1][edge]//3] = b
            actual = replay(m, points, edge, p)
            assert actual == facing(a,b,p), (a,b,p,edge,actual)
            count += 1
    report = dict(cases=count, mismatches=0, endpoint_indices=[[x//3 for x in t] for t in tables],
        scope='Original F5E03..F5E7B replayed with original endpoint tables and synthetic runtime coordinates. Signed wrapping and independent product high halves preserved. Observer comes from object at global B8668 offsets19/1D by disassembly; camera equivalence, helper1338B0 and live visibility remain open.')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'wall_facing.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
