#!/usr/bin/env python3
"""Verify region allocation request arithmetic; descriptor loading remains open."""
import argparse,json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha,require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    ins=list(md.disasm(exe[0xf5853+0x37000:0xf588c+0x37000],0xf5853));m=WallReplay({i.address:i for i in ins},b'')
    cases=0
    for first in [0,1,29,1938,1953,65535]:
        for count in range(256):
            m.regs['esp']=0x700000;m.writemem(0x700040,4,0x610000);m.writemem(0x610000,2,first);m.writemem(0x610017,1,count);m.writemem(0x22d0c,4,0x400000)
            for i in ins:
                o=i.operands;op=i.mnemonic
                if op=='mov':m.put(i,o[0],m.get(i,o[1]))
                elif op=='lea':
                    x=o[1].mem
                    value=x.disp+(m.regs[i.reg_name(x.base)] if x.base else 0)+(m.regs[i.reg_name(x.index)]*x.scale if x.index else 0)
                    m.put(i,o[0],value & 0xffffffff)
                elif op in ['xor','add','sub','shl']:
                    x,y=m.get(i,o[0]),m.get(i,o[1]);v=x^y if op=='xor' else x+y if op=='add' else x-y if op=='sub' else x<<y;m.put(i,o[0],v & 0xffffffff)
                else:raise ValueError(op)
            require(m.readmem(0x700008,4)==0x400000+first*44,'Region address mismatch')
            require(m.readmem(0x700024,4)==count and m.regs['eax']==count*160,'Allocation size mismatch');cases+=1
    report=dict(cases=cases,mismatches=0,scope='Original F5853..F5889 replayed with synthetic descriptor first-word and byte17 values. All256 counts tested, including zero. Computes region_base+first*44 and count*160 allocation size. No range check in this block. Caller E18BE..E18D9 indexes descriptors relative22D10 at stride42, and E1962/E1963 passes descriptor to F584C by disassembly. Source descriptor loading, allocator behavior and actual cave allocation ranges remain open.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_allocation_request.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
