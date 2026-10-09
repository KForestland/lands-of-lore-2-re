#!/usr/bin/env python3
"""Verify the native four-byte action-table selector, without assigning AI meanings."""
import argparse
import json
from pathlib import Path
import capstone
from extract_creature_states import load_states
from lol2_cache_named_wall_fixture import require, sha
from lol2_verify_draracle_slopes import EXE_HASH
from verify_creature_states import CreatureReplay, signed


def select(entries, action, mask, tag, roll=0):
    first = eligible = -1
    for index, (key, flags, value, unused) in enumerate(entries):
        if key != action:
            continue
        if first < 0:
            first = index
        if not flags & mask:
            continue
        if tag == -1:
            roll -= value
            if roll < 0:
                return index
        elif value == tag:
            return index
        if eligible < 0:
            eligible = index
    return eligible if eligible >= 0 else first


def verify(game_root, out):
    exe = (game_root/'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH, 'Executable changed')
    source = load_states(game_root)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    start, end = 0xa1e44, 0xa1f2a
    code = exe[start+0x37000:end+0x37000]
    ins = list(md.disasm(code,start))
    m = CreatureReplay({i.address:i for i in ins},b'')
    (out/'action_lookup.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ins)+'\n')
    cases = 0
    bindings = []
    for entity in source['entities']:
        entries = entity['entries_bytes']
        data = bytes(value for entry in entries for value in entry)
        m.mem[0x600000:0x600000+len(data)] = data
        m.writemem(0x500037,4,0x600000)
        m.writemem(0x50002e,1,len(entries))
        keys = sorted({e[0] for e in entries} | {127})
        for action in keys:
            for mask in [0,1,2,4,7,8]:
                for tag, roll in [(t,0) for t in [0,2,10,50,90,127]] + [(-1,r) for r in range(101)]:
                    m.regs.update(esp=0x700000, esi=0x500000, ebx=0xffffffff, eax=roll)
                    for offset,value in [(0,-1),(0x18,0x500000),(0x1c,action),(0x20,mask),(0x24,tag)]:
                        m.writemem(0x700000+offset,4,value)
                    # Weighted entry starts after RNG call; the supplied roll is not RNG parity.
                    m.execute(0xa1e72 if tag == -1 else 0xa1e4b,0xa1f22)
                    expected = select(entries,action,mask,tag,roll)
                    require(signed(m.regs['eax']) == expected, 'Action selector mismatch')
                    cases += 1
            if action != 127:
                selectors = sorted({select(entries,action,7,-1,r) for r in range(101)})
                bindings.append(dict(entity=entity['record'],name=entity['name'],action_key=action,
                    selectors=selectors, resources={str(i):[v['resource_reference'] for v in entity['states'][i]['views']] for i in selectors if i>=0}))
    result = dict(executable_sha256=EXE_HASH, code_sha256=sha(code), replay_cases=cases,
        mismatches=0, bindings=bindings,
        scope='A1E44 four-byte table lookup verified with original entries. Byte0 is action key, byte1 eligibility mask, byte2 exact tag or subtractive weight. Byte3 not consumed here. First eligible/first-key fallbacks retained. RNG output supplied, native RNG and AI action meanings/timing unverified.')
    (out/'action_lookup.json').write_text(json.dumps(result,indent=2)+'\n')
    print(dict(replay_cases=cases,mismatches=0,bindings=len(bindings)))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    verify(a.game_root,a.out)
