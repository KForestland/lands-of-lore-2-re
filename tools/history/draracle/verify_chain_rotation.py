#!/usr/bin/env python3
"""Replay native rotation against the previously reproduced x87 table."""
import argparse
import itertools
import json
from pathlib import Path
import struct
import capstone
from lol2_cache_named_wall_fixture import require, sha
from lol2_verify_draracle_slopes import EXE_HASH
from verify_creature_states import CreatureReplay, signed


def rotate_native(m, point, origin, angle):
    stack, p, o = 0x700000, 0x500000, 0x600000
    m.regs['esp'] = stack
    for offset,value in [(0x10,p),(0x14,o),(0x18,angle)]: m.writemem(stack+offset,4,value)
    for base,values in [(p,point),(o,origin)]:
        for index,value in enumerate(values): m.writemem(base+index*4,4,value)
    pc,below=0x111d6b,False
    for _ in range(100):
        if pc==0x111e1d: return tuple(signed(m.readmem(p+i*4,4)) for i in range(2))
        i=m.instructions[pc];op,o=i.mnemonic,i.operands;nxt=pc+i.size
        if op=='mov': m.put(i,o[0],m.get(i,o[1]))
        elif op=='lea': m.put(i,o[0],m.addr(i,o[1]))
        elif op=='cmp': below=m.get(i,o[0])<m.get(i,o[1])
        elif op=='jae':
            if not below: nxt=m.get(i,o[0])
        elif op=='jmp': nxt=m.get(i,o[0])
        elif op=='neg': m.put(i,o[0],-m.get(i,o[0]))
        elif op in ('and','add','sub','shr'):
            a,b=m.get(i,o[0]),m.get(i,o[1])
            m.put(i,o[0],a&b if op=='and' else a+b if op=='add' else a-b if op=='sub' else a>>(b&31))
        elif op=='imul' and len(o)==1:
            value=signed(m.regs['eax'])*signed(m.get(i,o[0]))
            m.regs['eax'],m.regs['edx']=value&0xffffffff,(value>>32)&0xffffffff
        elif op=='shrd':
            a,b,n=(m.get(i,x) for x in o)
            m.put(i,o[0],((a|(b<<32))>>(n&31))&0xffffffff)
        else: raise ValueError(f'Unsupported {pc:x}: {op}')
        pc=nxt
    raise ValueError('Instruction limit')


def model(point,origin,angle,table):
    def sine(a):
        a&=65535
        return table[(a&32767)>>3]*(-1 if a&32768 else 1)
    s,c=sine(angle),sine(angle+16384)
    x,y=point
    mul=lambda a,b:signed((signed(a)*signed(b))>>16)
    return (signed(origin[0]+mul(x,c)+mul(y,s)),signed(origin[1]+mul(y,c)-mul(x,s)))


def verify(root,rotation_proof,hinge_proof,out):
    exe=(root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
    meta=json.loads((rotation_proof/'rotation_table.json').read_text())
    data=(rotation_proof/'rotation_table.bin').read_bytes()
    require(meta['executable_sha256']==EXE_HASH and sha(data)==meta['table_sha256'] and len(data)==16384,'Rotation fixture provenance')
    table=struct.unpack('<4096i',data)
    code=exe[0x111d68+0x37000:0x111e21+0x37000]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    rows=list(md.disasm(code,0x111d68));require(rows[-1].address+rows[-1].size==0x111e21,'Instruction boundary')
    m=CreatureReplay({i.address:i for i in rows},b'');m.mem[0xdb650:0xdf650]=data
    angles=sorted(set(range(0,65536,256))|{1,7,8,16383,16384,32767,32768,65535,43144,51153,10376,58800})
    points=[(0,0),(32<<16,4<<16),(-32<<16,4<<16),(1,-1),(0x7fffffff,-0x80000000)]
    checks=0
    for angle,point,origin in itertools.product(angles,points,[(0,0),(1200<<16,11500<<16),(-65536,65535)]):
        require(rotate_native(m,point,origin,angle)==model(point,origin,angle,table),'Native rotation mismatch')
        checks+=1
    hinges=json.loads(hinge_proof.read_text());require(hinges['executable_sha256']==EXE_HASH,'Hinge executable provenance')
    paths=[]
    for row in hinges['source']:
        raw=bytes.fromhex(row['placement_hex']);x,y=struct.unpack_from('<hh',raw)
        anchor=(x<<16,y<<16);half_x=(row['width']//2)<<16;half_y=(row['depth']//2)<<16
        require(row['mode'] in [1,4],'Source hinge mode')
        corner=(-half_x,half_y if row['mode']==1 else -half_y)
        opposite=tuple(-v for v in corner)
        pivot=rotate_native(m,corner,anchor,row['initial_heading'])
        samples=[]
        for progress in [0,row['full_travel']//2,row['full_travel']]:
            angle=(row['initial_heading']+(-progress if row['mode']&1 else progress))&65535
            position=rotate_native(m,opposite,pivot,angle)
            require(position==model(opposite,model(corner,anchor,row['initial_heading'],table),angle,table),'Composed native rotation')
            samples.append(dict(progress=progress,heading=angle,position_fixed=position,delta_from_anchor_fixed=[a-b for a,b in zip(position,anchor)]))
        paths.append(dict(index=row['index'],anchor_fixed=anchor,pivot_fixed=pivot,samples=samples))
    out.mkdir(parents=True,exist_ok=True)
    (out/'code_111d68.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in rows)+'\n')
    report=dict(executable_sha256=EXE_HASH,code_sha256=sha(code),rotation_table_sha256=sha(data),
                rotation_checks=checks,composed_source_checks=6,mismatches=0,paths=paths,
                scope='Original integer rotation body replay using previously reproduced host-x87 table; no guest-table equality claim. Two calls composed in source order. Deltas relative to initial anchor, not proven per-tick movement. Collision, primitive rendering and live doorway remain unverified.')
    (out/'rotation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='paths'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True);p.add_argument('--rotation-proof',type=Path,required=True)
    p.add_argument('--hinge-proof',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();verify(a.game_root,a.rotation_proof,a.hinge_proof,a.out)
