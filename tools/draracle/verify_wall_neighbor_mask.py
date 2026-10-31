#!/usr/bin/env python3
"""Replay reciprocal runtime edge-mask propagation, including missing links."""
import argparse
import itertools
import json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from verify_wall_camera_clip import run


def propagate(mask, links, helper, score):
    if links is None:
        return mask
    edge = next((k for k in range(3) if links[k]), 3)
    bits = 16 if score > 0 and helper != 0 else 17
    return mask | (bits << edge)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    exe = (args.game_root/'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH,'Executable changed')
    md = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    md.detail = True
    m = WallReplay({i.address:i for i in md.disasm(exe[0xf5eaf+0x37000:0xf5ef5+0x37000],0xf5eaf)},b'')
    topologies = [None,(True,False,False,False),(False,True,False,False),
        (False,False,True,False),(False,False,False,True),
        (False,False,False,False),(False,True,True,True)]
    cases = 0
    for mask,links,helper,score in itertools.product(range(256),topologies,[0,1,0xffffffff],[-2**31,0,2**31-1]):
        source,neighbor,stack = 0x600000,0x610000,0x700000
        pointer = 0 if links is None else neighbor
        m.regs.update(ebx=source,edx=pointer,esp=stack)
        m.writemem(neighbor+0x9c,1,mask)
        for k,match in enumerate(links or [False]*4):
            m.writemem(neighbor+0x8c+k*4,4,source if match else 0)
        for offset,value in [(0x530,score),(0x528,helper),(0x544,pointer)]:
            m.writemem(stack+offset,4,value & 0xffffffff)
        run(m,0xf5eaf,{0xf5ef5})
        actual = m.readmem(neighbor+0x9c,1)
        require(actual == propagate(mask,links,helper,score),f'Neighbor mask mismatch: {mask,links,helper,score}')
        cases += 1
    report = dict(cases=cases,mismatches=0,topologies=len(topologies),
        scope='Original F5EAF..F5EEF replayed with synthetic runtime neighbor pointers. Null neighbor skips write. First matching slot0..2 selected; slot3 used without comparison if none match. Set checked bit; rejection bit set when helper is zero or supplied signed score is nonpositive. Other bits preserved. Runtime link construction, stale-score provenance, traversal scheduling, camera setup and live draw parity remain open.')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'wall_neighbor_mask.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':main()
