#!/usr/bin/env python3
"""Recover per-region eight-byte wall records with native address/setup replay."""
import json,struct,hashlib,argparse
from pathlib import Path
from collections import Counter
import capstone
from lol2_extract_draracle_geometry import decode,u32
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_spatial_constructor import ConstructorReplay
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    ROOT=args.game_root
    OUT=args.out
    exe=(ROOT/'LOLG.DAT').read_bytes();assert hashlib.sha256(exe).hexdigest()==EXE_HASH
    source=(ROOT/'DAT/L1_DC.MIX').read_bytes();entries,entry,raw,verts,records,regions=decode(source)
    start,count=u32(raw,8),u32(raw,0x54)
    assert start+count*8==u32(raw,12)
    table=raw[start:start+count*8]
    OUT.mkdir(parents=True,exist_ok=True)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    ins={}
    for a,z in [(0xf4370,0xf43b2),(0x114632,0x114643),(0x114681,0x114693),(0x114aa4,0x114ad0),(0x114b45,0x114b60)]:
     code=exe[a+0x37000:z+0x37000];ii=list(md.disasm(code,a));ins.update({i.address:i for i in ii});(OUT/f'code_{a:x}.bin').write_bytes(code);(OUT/f'code_{a:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ii)+'\n')
    m=ConstructorReplay(ins,b'');m.writemem(0x22d08,4,0x500000);m.mem[0x500000:0x500000+len(table)]=table
    owners={};assignments=[];ordinary=0
    for rid,r in enumerate(records):
     d=bytes.fromhex(regions[rid]['raw_hex']);first=r[13];n=d[30]
     if not n:
      assert first==65535
      continue
     assert first+n<=count
     m.mem[0x600000:0x60002c]=d;m.regs.update(eax=0x600000,edx=0)
     m.span(0xf4375,0xf438e)
     assert m.regs['eax']==0x500000+first*8 and m.regs['edx']==n
     for index in range(first,first+n):
      assert index not in owners;owners[index]=rid
      wall=table[index*8:index*8+8];code=wall[5]&31
      m.regs.update(ebx=0x500000+index*8,esi=0x610000);m.span(0x114632,0x11463a)
      assert m.readmem(0x610042,1)==code
      setup=None
      if not code&16:
       m.span(0x114681,0x114693);setup=[m.readmem(0x610000+x,1) for x in [0x30,0x31,0x40]]
       assert setup==list(wall[2:5]);ordinary+=1
      assignments.append(dict(index=index,region=rid,source_offset=entry['offset']+start+index*8,raw_hex=wall.hex(),surface_code=code,edge_candidate=code&3,span_class_bits=code&12,special=bool(code&16),resource_word_candidate=struct.unpack_from('<h',wall)[0],ordinary_object_bytes_30_31_40=setup))
    assert set(owners)==set(range(count))
    report=dict(source_sha256=hashlib.sha256(source).hexdigest(),exe_sha256=EXE_HASH,table_start=start,record_count=count,nonempty_regions=sum(bool(r[15]&255) for r in records),native_region_index_cases=sum(bool(r[15]&255) for r in records),native_surface_code_cases=count,native_ordinary_setup_cases=ordinary,surface_codes=dict(Counter(w['surface_code'] for w in assignments)),resource_candidates=dict(Counter(w['resource_word_candidate'] for w in assignments)),records=assignments,scope='Original instruction spans replayed on source bytes; table partitions exactly. Resource first-word meaning/binding, surface class geometry and native UVs remain unverified; no scene wall texture assignments made.')
    (OUT/'wall_records.json').write_text(json.dumps(report,indent=2));(OUT/'wall_table.bin').write_bytes(table)
    print({k:v for k,v in report.items() if k not in ['records','resource_candidates']})

if __name__=='__main__':main()
