#!/usr/bin/env python3
"""Replay native connector middle walls against independent endpoint and height rules."""
import argparse,json,struct,hashlib
from pathlib import Path
import capstone
from lol2_extract_draracle_geometry import decode,s16,slope_corners
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,_,raw,verts,records,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes());exe=(a.game_root/'LOLG.DAT').read_bytes();assert hashlib.sha256(exe).hexdigest()==EXE_HASH
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={};a.out.mkdir(parents=True,exist_ok=True)
 for start,end in [(0x114aa4,0x115119),(0xf4504,0xf458d),(0xf4590,0xf4614),(0xf49fc,0xf4a3c)]:
  code=exe[start+0x37000:end+0x37000];ins.update({i.address:i for i in md.disasm(code,start)});(a.out/f'code_{start:x}.bin').write_bytes(code)
 m=WallReplay(ins,raw[54509:54509+1954*44]);m.writemem(0x22d04,4,0x500000);m.mem[0x500000:0x500000+len(verts)*8]=b''.join(struct.pack('<2i',*v) for v in verts)
 results=[]
 for rid,r in enumerate(records):
  for index in range(r[13],r[13]+(r[15]&255)):
   d=raw[30093+index*8:30101+index*8];c=d[5]&31;edge=c&3;nid=r[2+edge];nr=records[nid] if nid!=65535 else None
   if c&12 not in [4,12] or not ((r[14]|(nr[14] if nr else 0))&16):continue
   assert not (r[14]|(nr[14] if nr else 0))&0xec
   j=(edge+1)%4;p0,p1=[verts[r[6+k]] for k in [edge,j]]
   low=[s16(r[10])]*4;high=[s16(r[11])]*4
   if nr and nr[14]&16:
    k=0 if nr[2]==rid else 2
    if d[6]&128:low=[s16(nr[10])]*4;high=[s16(nr[11])]*4
    if c&12==4:p1=verts[nr[6+k+1]]
    else:p0=verts[nr[6+k]]
   elif nr:
    low=[max(s16(r[10]),s16(nr[10]))]*4;high=[min(s16(r[11]),s16(nr[11]))]*4
   expected=[[p0[0],high[edge]*65536,p0[1]],[p1[0],high[j]*65536,p1[1]],[p1[0],low[j]*65536,p1[1]],[p0[0],low[edge]*65536,p0[1]]]
   points,active=m.execute(rid,c,source_flags=d[6])
   assert points==expected and active==(p0!=p1 and (low[edge]<high[edge] or low[j]<high[j])),(rid,index,points,expected)
   results.append(dict(record=index,region=rid,edge=edge,surface_code=c,source_flags=d[6],points_fixed=points,active=active))
 report=dict(cases=len(results),active=sum(r['active'] for r in results),mismatches=0,results=results,scope='Original wall routine instructions replayed against an independent endpoint and height model. Only connector-associated class4/12 records without slopes/subdivision; source byte6 bit7 selects the height region. Other classes and special links deferred; no loader/UV/collision parity claim.')
 (a.out/'connector_middle_walls.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
