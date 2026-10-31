#!/usr/bin/env python3
"""Replay the native wall draw eligibility gate, not complete visibility or collision."""
import argparse,json,itertools
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha,require
from lol2_extract_draracle_geometry import decode
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay

def eligible(active,source_code,descriptor,edge,mask):
 return active and not source_code&32 and descriptor!=0 and not mask&(1<<(edge&3))

def replay(m,active,raw,mask):
 m.regs.update(ebx=0x600000,esi=0x610000,esp=0x700000)
 m.writemem(0x600044,1,int(active));m.writemem(0x600042,1,raw[5]&31);m.mem[0x610000:0x610008]=raw;m.writemem(0x700008,1,mask)
 pc=0x114806;zero=False
 for _ in range(60):
  if pc in [0x114850,0x114973]:return pc==0x114850
  i=m.instructions[pc];o=i.operands;op=i.mnemonic;nxt=pc+i.size
  if op=='mov':m.put(i,o[0],m.get(i,o[1]))
  elif op in ['cmp','test']:
   a,b=m.get(i,o[0]),m.get(i,o[1]);zero=(a==b) if op=='cmp' else (a&b)==0
  elif op=='setne':m.put(i,o[0],int(not zero))
  elif op in ['je','jne']:
   if zero==(op=='je'):nxt=m.get(i,o[0])
  elif op in ['xor','and','shl']:
   a,b=m.get(i,o[0]),m.get(i,o[1]);v=a^b if op=='xor' else a&b if op=='and' else a<<(b&31);m.put(i,o[0],v);zero=(v&((1<<(8*o[0].size))-1))==0
  else:raise ValueError((pc,op))
  pc=nxt
 raise ValueError('Instruction limit')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--geometry-evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed');_,_,raw,_,_,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;m=WallReplay({i.address:i for i in md.disasm(exe[0x114806+0x37000:0x114850+0x37000],0x114806)},b'')
 groups=['flat_wall_spans','upper_lower_walls','sloped_middle_walls','sloped_upper_lower_walls','connector_middle_walls','special_upper_lower_walls'];rows=[];seen=set();cases=0
 for group in groups:
  for r in json.loads(next(a.geometry_evidence.glob('*/'+group+'.json')).read_text())['results']:
   k=r['record'];assert k not in seen;seen.add(k);d=raw[30093+k*8:30101+k*8];descriptor=int.from_bytes(d[:2],'little');passed=[]
   for mask in range(16):
    result=replay(m,r['active'],d,mask);assert result==eligible(r['active'],d[5],descriptor,d[5]&3,mask);cases+=1
    if result:passed.append(mask)
   rows.append(dict(record=k,eligible_masks=passed,active=r['active'],source_hidden=bool(d[5]&32)))
 synthetic=0
 for active,hidden,descriptor,edge,mask in itertools.product([False,True],[0,32],[0,1,65535],range(4),range(16)):
  d=descriptor.to_bytes(2,'little')+bytes([0,0,0,4|edge|hidden,0,0])
  assert replay(m,active,d,mask)==eligible(active,d[5],descriptor,edge,mask);synthetic+=1
 report=dict(source_cases=cases,synthetic_cases=synthetic,records=len(rows),active=sum(r['active'] for r in rows),eligible_with_zero_mask=sum(0 in r['eligible_masks'] for r in rows),source_hidden=sum(r['source_hidden'] for r in rows),mismatches=0,results=rows,scope='Original 114806..11484A eligibility gate replayed. Runtime edge mask and active state supplied. Passing this gate does not prove draw submission, transparency, occlusion, collision or live mask generation.')
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_visibility.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
