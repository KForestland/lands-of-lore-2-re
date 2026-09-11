#!/usr/bin/env python3
"""Replay original prop region-height selection, clamp and byte store."""
import argparse,json,struct,itertools
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import require,sha
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_extract_draracle_geometry import decode,u32
from lol2_verify_flat_wall_spans import WallReplay


def selected_height(flags,region_present,floor,ceiling,state_height):
    return (min(255,ceiling-floor) if flags&2 and region_present else state_height)&255


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
    _,_,raw,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    ins={i.address:i for i in md.disasm(exe[0xf1dd2+0x37000:0xf1e15+0x37000],0xf1dd2)};m=WallReplay(ins,b'')
    def check(flags,present,floor,ceil,h):
        m.regs.update(ebp=0x700000,edx=0x610000,ebx=0x620000)
        m.writemem(0x610032,1,flags);m.writemem(0x700024,4,0x400000 if present else 0);m.writemem(0x62000f,1,h)
        m.writemem(0x400014,2,floor&65535);m.writemem(0x400016,2,ceil&65535)
        pc=0xf1dd2;relation=0
        while pc<0xf1e15:
            i=ins[pc];o=i.operands;op=i.mnemonic;nxt=pc+i.size
            if op=='mov':m.put(i,o[0],m.get(i,o[1]))
            elif op in ['xor','and','sub']:
                x,y=m.get(i,o[0]),m.get(i,o[1]);v=x^y if op=='xor' else x&y if op=='and' else x-y;m.put(i,o[0],v&0xffffffff);relation=v
            elif op=='sar':
                v=m.get(i,o[0]);v=v-2**32 if v&2**31 else v;m.put(i,o[0],(v>>m.get(i,o[1]))&0xffffffff)
            elif op in ['test','cmp']:
                x,y=m.get(i,o[0]),m.get(i,o[1]);signed=lambda v:v-2**32 if v&2**31 else v;relation=x&y if op=='test' else signed(x)-signed(y)
            elif op in ['je','jle']:
                if relation==0 if op=='je' else relation<=0:nxt=m.get(i,o[0])
            elif op=='jmp':nxt=m.get(i,o[0])
            else:raise ValueError(op)
            pc=nxt
        require(m.readmem(0x700000-0x37,1)==selected_height(flags,present,floor,ceil,h),'Height mismatch')
    source=[]
    for k in range(u32(raw,0x60)):
        d=raw[u32(raw,0x14)+k*37:u32(raw,0x14)+(k+1)*37]
        if struct.unpack_from('<H',d,32)[0]!=28:continue
        rid=struct.unpack_from('<H',d,10)[0];r=regions[rid];floor,ceil=struct.unpack('<hh',struct.pack('<HH',r[10],r[11]));check(2,True,floor,ceil,128)
        source.append(dict(record=k,region=rid,height=selected_height(2,True,floor,ceil,128)))
    synthetic=0
    for flags,present,(floor,ceil),h in itertools.product([0,2],[False,True],[(-32768,32767),(0,0),(0,254),(0,255),(0,256),(1,0)],[0,128,255]):
        check(flags,present,floor,ceil,h);synthetic+=1
    report=dict(source_cases=len(source),synthetic_cases=synthetic,mismatches=0,results=source,scope='F1DD2..F1E12 replayed: template bit2 and nonnull supplied region select signed ceiling-floor capped255 then byte-stored; otherwise state height. Source region association supplied, not live captured. No lower clamp; negative synthetic differences wrap at byte store. Original prop anchors preserved.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'prop_region_height.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='results'})


if __name__=='__main__':main()
