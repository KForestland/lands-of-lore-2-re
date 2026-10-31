#!/usr/bin/env python3
"""Audit disjoint wall evidence and reproduce deferred absent-neighbor failures."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import capstone
from lol2_extract_draracle_geometry import decode
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay

GROUPS = [('flat_walls','flat_wall_spans'), ('upper_lower_walls','upper_lower_walls'),
          ('sloped_middle_walls','sloped_middle_walls'),
          ('sloped_upper_lower_walls','sloped_upper_lower_walls'),
          ('connector_middle_walls','connector_middle_walls'),
          ('special_upper_lower_walls','special_upper_lower_walls')]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    evidence=args.out.parent
    seen=set()
    for folder,name in GROUPS:
        report=json.loads((evidence/folder/(name+'.json')).read_text())
        ids=[row['record'] for row in report['results']]
        assert len(ids)==len(set(ids)) and not seen.intersection(ids), name
        assert report['mismatches']==0 and report['cases']==len(ids), name
        seen.update(ids)
    _,_,raw,vertices,regions,_=decode((args.game_root/'DAT/L1_DC.MIX').read_bytes())
    executable=(args.game_root/'LOLG.DAT').read_bytes()
    assert hashlib.sha256(executable).hexdigest()==EXE_HASH
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    start,end=0x114aa4,0x115119
    instructions={i.address:i for i in md.disasm(executable[start+0x37000:end+0x37000],start)}
    machine=WallReplay(instructions,raw[54509:54509+len(regions)*44])
    machine.writemem(0x22d04,4,0x500000)
    machine.mem[0x500000:0x500000+len(vertices)*8]=b''.join(struct.pack('<2i',*v) for v in vertices)
    deferred=[];all_ids=set()
    for rid,r in enumerate(regions):
        for index in range(r[13],r[13]+(r[15]&255)):
            assert index not in all_ids
            all_ids.add(index)
            if index in seen:continue
            data=raw[30093+index*8:30101+index*8];code=data[5]&31
            assert r[2+(code&3)]==65535 and code&12 in [0,8]
            try:
                machine.execute(rid,code,(data[7]&3)<<14,data[3],data[6])
            except ValueError as error:
                if str(error)!='Absent-neighbor region dereference':raise
            else:
                raise AssertionError('Deferred case did not reach expected invalid dereference')
            deferred.append(dict(record=index,region=rid,surface_code=code,
                                 reason='Serialized absent neighbor dereferenced by ordinary wall routine'))
    assert all_ids==set(range(3052)) and seen<=all_ids
    assert all_ids-seen==set(range(245,253))
    incoming=[dict(region=rid,edge=edge) for rid,r in enumerate(regions)
              for edge,n in enumerate(r[2:6]) if n==1851]
    report=dict(verified_records=len(seen),deferred_records=len(deferred),
                deferred=deferred,region1851_incoming_links=incoming,
                scope='Static host audit: invalid serialized inputs rejected. Does not prove a live game fault or resolve runtime region preparation.')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'wall_coverage.json').write_text(json.dumps(report,indent=2))
    print({k:v for k,v in report.items() if k not in ['deferred','region1851_incoming_links']})
if __name__=='__main__':main()
