#!/usr/bin/env python3
"""Check native horizontal edge rejection after zero-depth clipping."""
import argparse
import itertools
import json
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from verify_wall_camera_clip import run, divide


def outcode(x,z):
    return (1 if -x > z else 0) | (16 if x > z else 0)


def accepted(a,b,scale,left,right):
    x,z = a
    u,v = b
    c,d = outcode(x,z),outcode(u,v)
    if c & d:
        return False
    if c | d == 17:
        return True
    if not c:
        if z < 65536:
            if v < 65536:
                return True
            x += divide((65536-z)*(u-x),v-z)
            z = 65536
        x = divide(x*scale,z)
        c = (1 if x < left else 0) | (16 if x > right else 0)
    if not d:
        if v < 65536:
            if z < 65536:
                return True
            # Preserve original ordering: x may already be projected above.
            u += divide((65536-v)*(u-x),v-z)
            v = 65536
        u = divide(u*scale,v)
        d = (1 if u < left else 0) | (16 if u > right else 0)
    return not c & d


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    exe = (args.game_root/'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH,'Executable changed')
    md = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    md.detail = True
    m = WallReplay({i.address:i for i in md.disasm(exe[0x133a49+0x37000:0x133bbf+0x37000],0x133a49)},b'')
    cases = rejected = 0
    stops = {0x133a8f,0x133bb5,0x133bbf}
    xs = [-131072,-65536,-1,0,1,65536,131072]
    zs = [0,1,65535,65536,65537,131072]
    windows = [(65536,-32768,32768),(320,-160,160),(65536,0,65536)]
    outcomes = {hex(s):0 for s in stops}
    for (x,z,u,v),(scale,left,right) in itertools.product(itertools.product(xs,zs,xs,zs),windows):
        m.regs.update(esp=0x700000,ebx=0)
        for offset,value in [(12,x),(20,z),(0,u),(8,v),(24,0)]:
            m.writemem(0x700000+offset,4,value & 0xffffffff)
        for address,value in [(0xfe480,scale),(0xfe424,left),(0xfe428,right)]:
            m.writemem(address,4,value & 0xffffffff)
        stop = run(m,0x133a49,stops)
        actual = stop == 0x133bbf
        assert actual == accepted((x,z),(u,v),scale,left,right),(x,z,u,v,scale,left,right)
        outcomes[hex(stop)] += 1
        rejected += not actual
        cases += 1
    report = dict(cases=cases,rejected=rejected,mismatches=0,exit_counts=outcomes,
        scope='Original 133A49..133BBD horizontal outcodes, depth65536 guard and window rejection replayed with bounded synthetic post-clip coordinates and three supplied projection/windows. Early acceptance is conservative and does not prove an edge draws. Optional facing shortcut, runtime camera/window setup and whole-helper/live parity remain open.')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'wall_screen_bounds.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':main()
