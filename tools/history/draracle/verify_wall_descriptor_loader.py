#!/usr/bin/env python3
"""Replay descriptor post-read initialization; file read and memset are boundaries."""
import argparse,json,struct
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha,require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from lol2_extract_draracle_geometry import decode


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
    _,_,raw,_,_,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    off,count=(struct.unpack_from('<I',raw,k)[0] for k in [0xa4,0xac])
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    ins=list(md.disasm(exe[0xe2516+0x37000:0xe252b+0x37000],0xe2516));m=WallReplay({i.address:i for i in ins},b'')
    records=[raw[off+k*26:off+(k+1)*26] for k in range(count)]
    records += [bytes([v])*26 for v in range(256)]
    for record in records:
        base=0x600000;m.mem[base:base+42]=record+b'\xff'*16;m.regs.update(ebx=base,esi=base+26,esp=0x700000)
        for i in ins:
            o=i.operands
            if i.mnemonic=='mov':m.put(i,o[0],m.get(i,o[1]))
            elif i.mnemonic=='add':m.put(i,o[0],m.get(i,o[0])+m.get(i,o[1]))
            elif i.mnemonic=='and':m.put(i,o[0],m.get(i,o[0])&m.get(i,o[1]))
            elif i.mnemonic=='push':
                value=m.get(i,o[0]);m.regs['esp']-=4;m.writemem(m.regs['esp'],4,value)
            else:raise ValueError(i.mnemonic)
        stack=m.regs['esp'];args=[m.readmem(stack+k*4,4) for k in range(3)]
        require(args==[base+26,0,16],'Unexpected memset arguments')
        # Model the external memset only after checking its original arguments.
        m.mem[args[0]:args[0]+args[2]]=bytes([args[1]])*args[2]
        expected=bytearray(record+b'\0'*16);expected[16]=0;expected[25]&=15
        require(m.mem[base:base+42]==expected,'Descriptor initialization mismatch')
        require(m.mem[base:base+2]==record[:2] and m.mem[base+23]==record[23],'Allocation fields changed')
    report=dict(source_cases=count,synthetic_cases=256,mismatches=0,
        scope='Original E2516..E2528 replayed with supplied 26-byte source reads; checked memset arguments, modeled zero-fill. 42-byte initialized records preserve allocation first-word/byte17; clear byte10, mask byte19 low nibble, zero16-byte tail. File IO, allocation, global22D10 handoff and live loader execution not replayed.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_descriptor_loader.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
