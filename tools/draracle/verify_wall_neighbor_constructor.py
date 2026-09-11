#!/usr/bin/env python3
"""Replay native neighbor construction using original cave region records."""
import argparse
import json
import struct
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from lol2_extract_draracle_geometry import decode
from verify_wall_camera_clip import run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    exe = (args.game_root/'LOLG.DAT').read_bytes()
    require(sha(exe)==EXE_HASH,'Executable changed')
    _,_,_,_,regions,_ = decode((args.game_root/'DAT/L1_DC.MIX').read_bytes())
    md = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    m = WallReplay({i.address:i for i in md.disasm(exe[0xf59d4+0x37000:0xf5ab0+0x37000],0xf59d4)},b'')
    region_base,object_base,stack = 0x400000,0x500000,0x700000
    for k,r in enumerate(regions):
        m.mem[region_base+k*44:region_base+(k+1)*44] = struct.pack('<22H',*r)
    m.writemem(0x22d0c,4,region_base)
    rows = []
    for mode in [0,64]:
        for k,r in enumerate(regions):
            obj = object_base+k*160
            m.regs.update(ebx=obj,edi=region_base+k*44,esp=stack)
            m.writemem(obj+0x9e,1,mode)
            m.writemem(obj+0x9f,1,255)
            for offset,value in [(0,object_base),(8,region_base+k*44),(0x28,0)]:m.writemem(stack+offset,4,value)
            run(m,0xf59d4,{0xf5ab0})
            expected=[];absent=0
            for edge,n in enumerate(r[2:6]):
                if n == 65535:
                    expected.append(None);absent |= 1 << edge
                else:
                    require(n<len(regions),'Neighbor outside source region table')
                    keep = bool(regions[n][14]&128) if mode else regions[n][12]==r[12]
                    expected.append(n if keep else None)
            actual=[]
            for edge in range(4):
                pointer=m.readmem(obj+0x8c+edge*4,4)
                actual.append((pointer-object_base)//160 if pointer else None)
                require(pointer==(object_base+expected[edge]*160 if expected[edge] is not None else 0),'Pointer mismatch')
            require(m.readmem(obj+0x9d,1)==absent,'Sentinel mask mismatch')
            require(m.readmem(obj+0x9f,1)==251,'Traversal flag clear mismatch')
            rows.append(dict(region=k,mode=mode,neighbors=actual,absent_mask=absent))
    report=dict(cases=len(rows),regions=len(regions),mismatches=0,
        retained_links={str(mode):sum(n is not None for r in rows if r['mode']==mode for n in r['neighbors']) for mode in [0,64]},
        scope='Original F59D4..F5AAE replayed against cave region bytes with synthetic contiguous runtime object allocation and base-region index0. Both supplied object flag40 modes checked. Actual allocation range and flag40 selection remain open; this does not establish live neighbor graph or camera/visibility parity.',results=rows)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'wall_neighbor_constructor.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))


if __name__=='__main__':main()
