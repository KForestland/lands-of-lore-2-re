#!/usr/bin/env python3
"""Replay EXEC damage splitting and stat adjustments from a user-owned game.
No game payloads, decoded assets or machine-specific extraction outputs required.
"""
import argparse,csv,hashlib,io,json
from pathlib import Path
import capstone
from extract_creature_states import parse_states
from lol2_extract_draracle_geometry import parse_mix
from lol2_verify_draracle_slopes import EXE_HASH
from verify_creature_states import CreatureReplay,signed

GLOBAL_HASH='1e3e2a46340d714aaf4d583e5aff7e58dc11005bac6c694fac49c07d13e01edd'
HIVE_HASH='a1979e60d401ae308e430f69a7163ff07a7f704aeb233769add85e7cc0960bf8'


def verify(game):
    exe=(game/'LOLG.DAT').read_bytes();hive=(game/'DAT/L5_HC.MIX').read_bytes();global_mix=(game/'GLOBAL.MIX').read_bytes()
    for blob,wanted in [(exe,EXE_HASH),(hive,HIVE_HASH),(global_mix,GLOBAL_HASH)]:
        if hashlib.sha256(blob).hexdigest()!=wanted: raise ValueError('Unsupported input hash; no replay performed')
    def payload(blob,key):
        entry=next(e for e in parse_mix(blob) if e['key']==key)
        return blob[entry['offset']:entry['offset']+entry['size']]
    definition=next(e for e in parse_states(payload(hive,3776335874))['entities'] if e['name']=='EXEC')
    body=bytes.fromhex(definition['raw_hex'])[:135]
    # Keys belong to global\ai\EXEC\stat.csv and effector.csv in this pinned archive.
    stat_csv=payload(global_mix,3427340867);effect_csv=payload(global_mix,3634660276)
    stats=bytes((int(r[1]) if r[1] else 0)&255 for r in list(csv.reader(io.StringIO(stat_csv.decode('ascii'))))[1:])
    effect=bytes((int(v) if v else 0)&255 for r in list(csv.reader(io.StringIO(effect_csv.decode('ascii'))))[1:] for v in r[1:31])
    assert len(stats)==32 and len(effect)==1740
    md=capstone.Cs(3,4);md.detail=True;ins={};spans=[]
    for a,z in [(0xa1d28,0xa1d4d),(0xa1f2c,0xa1f7f),(0x5a19b,0x5a19e),(0x5a1a0,0x5a1f4)]:
        raw=exe[a+0x37000:z+0x37000];decoded=list(md.disasm(raw,a))
        assert decoded[-1].address+decoded[-1].size==z
        ins.update({i.address:i for i in decoded});spans.append(dict(start=a,end=z,sha256=hashlib.sha256(raw).hexdigest()))
    m=CreatureReplay(ins,b'');base,table,dest,stack=0x400000,0x410000,0x420000,0x430000
    m.mem[base:base+135]=body;m.regs['ebx']=base;m.execute(0xa1d28,0xa1d4d)
    total,minimum=m.readmem(base+0x81,1),m.readmem(base+0x82,1)
    assert (total,minimum)==(30,3)
    splits=0
    for first in range(256):
        for second in range(256):
            m.regs['esp']=stack
            for i,v in enumerate([base,first,second]):m.writemem(stack+4+i*4,4,v)
            m.execute(0xa1f2c,{0xa1f57,0xa1f7e})
            expected=total if first and not second else max(minimum,1 if not first else total*first//(first+second))
            assert m.regs['eax']==expected and m.regs['esp']==stack
            splits+=1
    def adjust(row,values,op):
        ptr=table+0x55e+30*op;m.mem[ptr:ptr+30]=bytes(v&255 for v in row)
        m.mem[dest-1:dest+31]=b'\xab'+bytes(values)+b'\xcd'
        m.regs['esp']=stack
        for i,v in enumerate([table,op,dest]):m.writemem(stack+4+i*4,4,v)
        pc=0x5a1a0
        while True:
            stop=m.execute(pc,{0x5a1e0,0x5a19d})
            if stop==0x5a19d:break
            i=ins[stop];m.put(i,i.operands[0],signed(m.get(i,i.operands[1]),8));pc=0x5a1e3
        actual=list(m.mem[dest:dest+30])
        assert actual==[max(0,min(255,v+d)) for v,d in zip(values,row)]
        assert m.regs['esp']==stack and m.mem[dest-1]==0xab and m.mem[dest+30]==0xcd
        return actual
    pairs=0
    for start in range(0,65536,30):
        indexes=list(range(start,min(start+30,65536)));pairs+=len(indexes)
        indexes+=[128]*(30-len(indexes))
        adjust([i%256-128 for i in indexes],[i//256 for i in indexes],7+(start//30)%2)
    for op in [7,8]:
        row=[signed(v,8) for v in effect[30*op:30*(op+1)]]
        for value in range(256):adjust(row,[value]*30,op)
    return dict(executable_sha256=EXE_HASH,hive_sha256=HIVE_HASH,global_sha256=GLOBAL_HASH,
        code_spans=spans,damage_split_cases=splits,stat_delta_pairs=pairs,source_adjustment_cases=512,
        source_stat_bytes_2_3=list(stats[2:4]),definition_total=total,definition_minimum=minimum,
        scope='Bounded original-instruction replay. CSV parsing, table allocation and inputs supplied; MOVSX explicitly modeled. No live AI, native clock, target health or constructor A3 producer claim.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path)
    args=p.parse_args();report=verify(args.game_root)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
