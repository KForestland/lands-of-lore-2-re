#!/usr/bin/env python3
"""Join original wall helper stages from post-prologue to return decisions."""
import argparse
import itertools
import json
import random
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha, require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay
from verify_wall_facing import facing
from verify_wall_camera_clip import run, transform, clip
from verify_wall_screen_bounds import accepted


def model(a,b,camera,cosine,sine,shortcut,scale,left,right):
    a,b = transform(a,camera,cosine,sine),transform(b,camera,cosine,sine)
    if shortcut and facing(b,a,(0,0)) <= 0:
        return True
    clipped = clip(a,b)
    return clipped is not None and accepted(*clipped,scale,left,right)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args = p.parse_args()
    exe = (args.game_root/'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH,'Executable changed')
    md = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    md.detail = True
    m = WallReplay({i.address:i for i in md.disasm(exe[0x1338b7+0x37000:0x133bc4+0x37000],0x1338b7)},b'')
    rng = random.Random(20260911)
    fixtures = []
    values = [-65536,-1,0,1,65536]
    for x,z,u,v in itertools.product(values,repeat=4):
        fixtures.append(((x,z),(u,v),(0,0),65536,0,320,-160,160))
    rotations = [(65536,0),(0,65536),(-65536,0),(0,-65536),(46341,46341),(56756,-32768)]
    for _ in range(4096):
        a,b,camera = [tuple(rng.randrange(-1048576,1048577) for _ in range(2)) for _ in range(3)]
        cosine,sine = rng.choice(rotations)
        scale,left,right = rng.choice([(320,-160,160),(65536,-32768,32768),(65536,0,65536)])
        fixtures.append((a,b,camera,cosine,sine,scale,left,right))
    exits = {hex(s):0 for s in [0x133a8f,0x133bb5,0x133bbf,0x133bc4]}
    differences = cases = 0
    for a,b,camera,cosine,sine,scale,left,right in fixtures:
        results = []
        for shortcut in [0,1]:
            m.regs.update(esp=0x700000)
            # Deliberately vary the unused vertical scratch words, which the
            # original reads without initialization in this helper.
            for offset,value in [(48,a[0]),(52,a[1]),(56,b[0]),(60,b[1]),(64,shortcut),(16,rng.getrandbits(32)),(4,rng.getrandbits(32))]:
                m.writemem(0x700000+offset,4,value & 0xffffffff)
            for address,value in [(0xfe470,camera[0]),(0xfe478,camera[1]),(0xfe474,rng.getrandbits(32)),(0xfe4d8,cosine),(0xfe4d4,sine),(0xfe480,scale),(0xfe424,left),(0xfe428,right)]:
                m.writemem(address,4,value & 0xffffffff)
            stop = run(m,0x1338b7,{int(s,16) for s in exits})
            actual = stop == 0x133bbf
            expected = model(a,b,camera,cosine,sine,shortcut,scale,left,right)
            require(actual == expected,f'Joined helper mismatch: {a,b,camera,shortcut}')
            exits[hex(stop)] += 1
            results.append(actual)
            cases += 1
        differences += results[0] != results[1]
    require(all(exits.values()),'A helper return path was not exercised')
    report = dict(cases=cases,mismatches=0,exit_counts=exits,shortcut_changed_result=differences,
        scope='Continuous original 1338B7 post-prologue through return decisions; no intermediate values replaced. Independent composition includes optional signed high-product shortcut, camera transform, zero-depth clip and screen rejection. Bounded synthetic coordinates avoid division overflow; no guest/live capture, caller camera/window setup or runtime edge propagation claim. Prologue/epilogue not replayed.')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'wall_visibility_helper.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':main()
