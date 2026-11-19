#!/usr/bin/env python3
"""Replay native sprite orientation setup with bounded screen rectangles."""
import argparse,json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import require,sha
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    ins={i.address:i for i in md.disasm(exe[0x129ac8+0x37000:0x129d14+0x37000],0x129ac8)};m=WallReplay(ins,b'');cases=0
    for flags in range(256):
        for left,right,top,bottom in [(10,90,20,60),(0,319,0,199)]:
            stack=0x700000;m.regs.update(esp=stack,ebp=left,edi=right,esi=top)
            for o,v in [(0x60,flags),(0x70,65536),(0x74,65536),(0xe0,right),(0xf0,left),(0xec,top),(0xdc,bottom),(0xf8,bottom)]:m.writemem(stack+o,4,v)
            for addr,v in [(0xfe438,0),(0xfe420,0),(0xfe434,0x100000),(0xfda18,320)]:m.writemem(addr,4,v)
            pc=0x129ac8;relation=0
            for _ in range(100):
                if pc==0x129bf0:break
                i=ins[pc];o=i.operands;op=i.mnemonic;nxt=pc+i.size
                if op=='mov':m.put(i,o[0],m.get(i,o[1]))
                elif op in ['add','sub','and','imul']:
                    x,y=m.get(i,o[0]),m.get(i,o[1]);v=x+y if op=='add' else x-y if op=='sub' else x&y if op=='and' else x*y;m.put(i,o[0],v&0xffffffff)
                elif op=='neg':m.put(i,o[0],(-m.get(i,o[0]))&0xffffffff)
                elif op=='cmp':relation=m.get(i,o[0])-m.get(i,o[1])
                elif op in ['jb','jbe','je']:
                    if {'jb':relation<0,'jbe':relation<=0,'je':relation==0}[op]:nxt=m.get(i,o[0])
                elif op=='jmp':nxt=m.get(i,o[0])
                else:raise ValueError((hex(pc),op))
                pc=nxt
            else:raise ValueError('Instruction limit')
            x=right if flags&64 else left;y=bottom if flags&128 else top
            require(m.readmem(stack+0x80,4)==0x100000+y*320+x,'Destination origin mismatch')
            require(m.readmem(stack+0x84,4)==((-320 if flags&128 else 320)&0xffffffff),'Row direction mismatch')
            cases+=1
    report=dict(cases=cases,mismatches=0,scope='Original129AC8 through orientation branches to129BF0 replayed for all256 flags and two bounded unclipped rectangles. Bit40 starts at right edge; bit80 starts at bottom and negates pitch. Horizontal row walkers add/subtract destination offsets (12AA5C/12ABE5,12AD61/12B0C0) by disassembly. No complete clipping, scaling, shading or framebuffer replay.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'prop_flip_setup.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
