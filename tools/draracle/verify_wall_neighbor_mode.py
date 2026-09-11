#!/usr/bin/env python3
"""Verify runtime neighbor mode selection from original region flags."""
import argparse
import json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from lol2_extract_draracle_geometry import decode
from verify_wall_camera_clip import run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();exe=(a.game_root/'LOLG.DAT').read_bytes()
    require(sha(exe)==EXE_HASH,'Executable changed')
    _,_,_,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    m=WallReplay({i.address:i for i in md.disasm(exe[0xf58d9+0x37000:0xf5901+0x37000],0xf58d9)},b'')
    fixtures=[(r[14],k%256) for k,r in enumerate(regions)]
    fixtures += [(flags,old) for flags in [0,128] for old in range(256)]
    for flags,old in fixtures:
        m.regs['esp']=0x700000
        m.writemem(0x700008,4,0x400000);m.writemem(0x700018,4,0x60009e)
        m.writemem(0x40001c,2,flags);m.writemem(0x60009e,1,old)
        run(m,0xf58d9,{0xf5901})
        require(m.readmem(0x60009e,1)==(old&~64)|(64 if flags&128 else 0),'Mode mismatch')
    report=dict(cases=len(fixtures),regions=len(regions),source_mode64=sum(bool(r[14]&128) for r in regions),mismatches=0,
        scope='Original F58D9..F58FF replayed. Region flag80 maps to object flag40, preserving other bits. Source region selection verified; live allocation descriptor and allocator execution remain outside scope.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_neighbor_mode.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
