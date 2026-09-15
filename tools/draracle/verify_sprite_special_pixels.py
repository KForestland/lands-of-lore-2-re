#!/usr/bin/env python3
"""Replay the native first-pixel paths for special sprite rows."""
import argparse,json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import require,sha
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    cases=0
    for start,end,stops in [(0x12b44a,0x12b64b,{0x12b462,0x12b560,0x12b641}),(0x12b767,0x12b968,{0x12b77f,0x12b87d,0x12b95e})]:
        ins={i.address:i for i in md.disasm(exe[start+0x37000:end+0x37000],start)};m=WallReplay(ins,b'')
        for i in range(256):
            m.writemem(0x500000+i,1,(i*3+11)&255)
            m.writemem(0x4000+i,1,(i*5+7)&255)
        for source in range(256):
            for background in range(256):
                m.regs.update(eax=0,ebp=0x600000,esi=0,edi=0x610000,ecx=0x4000,edx=0x500000,ebx=0)
                m.writemem(0x600000,1,source);m.writemem(0x610000,1,background)
                pc=start;relation=0
                for _ in range(30):
                    if pc in stops:break
                    i=ins[pc];o=i.operands;nxt=pc+i.size
                    if i.mnemonic=='mov':m.put(i,o[0],m.get(i,o[1]))
                    elif i.mnemonic=='cmp':relation=m.get(i,o[0])-m.get(i,o[1])
                    elif i.mnemonic=='dec':m.put(i,o[0],(m.get(i,o[0])-1)&0xffffffff)
                    elif i.mnemonic in ['jbe','jae','jne']:
                        if {'jbe':relation<=0,'jae':relation>=0,'jne':relation!=0}[i.mnemonic]:nxt=m.get(i,o[0])
                    else:raise ValueError(i.mnemonic)
                    pc=nxt
                else:raise ValueError('Instruction budget')
                expected=background if source==0 else (background*5+7)&255 if source==1 else (source*3+11)&255
                require(m.readmem(0x610000,1)==expected,'Special pixel mismatch');cases+=1
    report=dict(cases=cases,mismatches=0,scope='Both native first-pixel orientations replayed for all256 source and256 destination indices with supplied distinct synthetic lookup tables. Index0 preserves destination; index1 remaps destination via table4000; other indices use source shade table. Does not recover runtime table contents, full clipping or Godot framebuffer parity.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'special_pixels.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
