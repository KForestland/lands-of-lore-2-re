#!/usr/bin/env python3
"""Replay native horizontal camera transform and zero-depth edge clipping."""
import argparse
import itertools
import json
import random
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from verify_wall_facing import signed


def divide(a, b):
    if not b:
        raise ZeroDivisionError()
    return (abs(a)//abs(b)) * (-1 if (a < 0) != (b < 0) else 1)


def run(m, start, stops):
    pc = start
    relation = 0
    for _ in range(200):
        if pc in stops:
            return pc
        i = m.instructions[pc]
        o = i.operands
        op = i.mnemonic
        nxt = pc+i.size
        if op == 'mov':
            m.put(i,o[0],m.get(i,o[1]))
        elif op in ('add','sub','xor'):
            a,b = m.get(i,o[0]),m.get(i,o[1])
            v = a+b if op == 'add' else a-b if op == 'sub' else a^b
            m.put(i,o[0],v & 0xffffffff)
        elif op == 'neg':
            m.put(i,o[0],(-m.get(i,o[0])) & 0xffffffff)
        elif op == 'imul' and len(o) == 1:
            v = signed(m.regs['eax'])*signed(m.get(i,o[0]))
            m.regs['eax'],m.regs['edx'] = v & 0xffffffff,(v >> 32) & 0xffffffff
        elif op == 'shrd':
            a,b,n = (m.get(i,x) for x in o)
            m.put(i,o[0],((a | b << 32) >> n) & 0xffffffff)
        elif op == 'idiv':
            v = (m.regs['edx'] << 32) | m.regs['eax']
            if v & (1 << 63):
                v -= 1 << 64
            d = signed(m.get(i,o[0]))
            q = divide(v,d)
            if not -2**31 <= q < 2**31:
                raise OverflowError('Native divide overflow')
            m.regs['eax'],m.regs['edx'] = q & 0xffffffff,(v-q*d) & 0xffffffff
        elif op in ('cmp','test'):
            a,b = (m.get(i,x) for x in o)
            relation = signed(a)-signed(b) if op == 'cmp' else signed(a & b)
        elif op == 'jge':
            if relation >= 0:
                nxt = m.get(i,o[0])
        elif op == 'jmp':
            nxt = m.get(i,o[0])
        else:
            raise ValueError((hex(pc),op))
        pc = nxt
    raise ValueError('Instruction limit')


def transform(point, camera, cosine, sine):
    x,z = (signed(a-b) for a,b in zip(point,camera))
    mul = lambda a,b: signed((a*b)//65536)
    return signed(mul(x,cosine)-mul(z,sine)), signed(mul(z,cosine)+mul(x,sine))


def clip(a,b):
    x,z = a
    u,v = b
    if z < 0 and v < 0:
        return None
    if z < 0:
        x += divide(-z*(u-x),v-z)
        z = 0
    elif v < 0:
        u += divide(-v*(u-x),v-z)
        v = 0
    return (x,z),(u,v)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    exe = (args.game_root/'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH,'Executable changed')
    md = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    md.detail = True
    m = WallReplay({i.address:i for i in md.disasm(exe[0x1338b7+0x37000:0x133a49+0x37000],0x1338b7)},b'')
    stack = 0x700000
    def put(offset,value): m.writemem(stack+offset,4,value & 0xffffffff)
    def points(): return tuple(tuple(signed(m.readmem(stack+o,4)) for o in pair) for pair in [(12,20),(0,8)])
    rng = random.Random(20260911)
    rotations = [(65536,0),(0,65536),(-65536,0),(0,-65536),(46341,46341),(56756,-32768)]
    transform_cases = 0
    for cosine,sine in rotations:
        for _ in range(512):
            a,b,camera = [tuple(rng.randrange(-2**31,2**31) for _ in range(2)) for _ in range(3)]
            m.regs['esp'] = stack
            for offset,value in zip([48,52,56,60],a+b): put(offset,value)
            for address,value in [(0xfe470,camera[0]),(0xfe478,camera[1]),(0xfe4d8,cosine),(0xfe4d4,sine),(0xfe474,0)]:
                m.writemem(address,4,value & 0xffffffff)
            put(16,0);put(4,0)
            run(m,0x1338b7,{0x1339ae})
            # Last endpoint depth store occurs at 1339B2, after the stop.
            put(8,m.regs['esi'])
            assert points() == (transform(a,camera,cosine,sine),transform(b,camera,cosine,sine))
            transform_cases += 1
    clip_cases = rejected = 0
    values = [-131072,-65536,-1,0,1,65536,131072]
    for x,z,u,v in itertools.product(values,repeat=4):
        m.regs['esp'] = stack
        for offset,value in [(12,x),(20,z),(0,u),(8,v)]:put(offset,value)
        stop = run(m,0x1339e7,{0x133a49,0x133bc4})
        actual = None if stop == 0x133bc4 else points()
        assert actual == clip((x,z),(u,v)), (x,z,u,v,actual)
        rejected += actual is None
        clip_cases += 1
    report = dict(transform_cases=transform_cases,clip_cases=clip_cases,rejected_clip_cases=rejected,mismatches=0,
        scope='Original horizontal transform 1338B7..1339AC replayed; final ESI depth observed directly. Zero-depth clip 1339E7..133A45 replayed. Transform fixtures cover wrapping; clipping fixtures bounded to avoid subtraction/divide overflow. Vertical scratch values supplied as zero; not claimed as initialized by original. Optional facing shortcut, horizontal outcodes, later depth65536 projection, camera setup and live visibility remain open.')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'wall_camera_clip.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':main()
