#!/usr/bin/env python3
"""Replay native upper/lower wall slopes including original corner helper instructions."""
import argparse,json,struct,hashlib
from collections import Counter
from lol2_verify_upper_lower_walls import model
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
 results=[];deferred=Counter()
 for rid,r in enumerate(records):
  for index in range(r[13],r[13]+(r[15]&255)):
   d=raw[30093+index*8:30101+index*8];c=d[5]&31;edge=c&3;nid=r[2+edge]
   if c&12 not in [0,8]:continue
   if nid==65535:deferred['absent neighbor']+=1;continue
   nr=records[nid]
   if r[14]&0xf0 or nr[14]&0xf0:deferred['subdivision/special']+=1;continue
   if not (r[14]|nr[14])&12:continue
   j=(edge+1)%4;indices=[edge,j];offset=d[3];mode=d[7]&3
   low,high,uv=model(r,nr,c,offset,mode)
   if c&12==0:
    high=[slope_corners(records,rid,True)[k] for k in indices];low=[low]*2
    neighbor_slope=bool(nr[14]&8)
   else:
    low=[slope_corners(records,rid)[k] for k in indices];high=[high]*2
    neighbor_slope=bool(nr[14]&4)
   if neighbor_slope:
    matches=[k for k,v in enumerate(nr[6:10]) if v==r[6+edge]]
    if len(matches)!=1 or nr[6+(matches[0]+3)%4]!=r[6+j]:
     deferred['nonreciprocal or ambiguous edge']+=1;continue
    k=matches[0];corners=slope_corners(records,nid,c&12==0)
    heights=[corners[k],corners[(k+3)%4]]
    if c&12==0:low=heights
    else:high=heights;uv=offset
   p0,p1=[verts[r[6+k]] for k in indices]
   expected=[[p0[0],high[0]*65536,p0[1]],[p1[0],high[1]*65536,p1[1]],[p1[0],low[1]*65536,p1[1]],[p0[0],low[0]*65536,p0[1]]]
   points,active=m.execute(rid,c,mode<<14,offset)
   actual_offset=m.readmem(0x600031,1)
   assert points==expected and active==(low[0]<high[0] or low[1]<high[1]) and actual_offset==uv,(rid,index,points,expected,actual_offset,uv)
   results.append(dict(record=index,region=rid,neighbor=nid,edge=edge,surface_code=c,points_fixed=points,active=active,vertical_offset_before=offset,vertical_offset_after=actual_offset,neighbor_slope=neighbor_slope))
 report=dict(cases=len(results),active=sum(r['active'] for r in results),neighbor_slope_cases=sum(r['neighbor_slope'] for r in results),offset_adjustments=sum(r['vertical_offset_before']!=r['vertical_offset_after'] for r in results),deferred=dict(deferred),mismatches=0,results=results,scope='Original wall routine and native slope/corner helper instructions replayed against an independent height and offset model. Ordinary sloped classes 0/8 with reciprocal indexed edges. Host supplies runtime pointers; no loader, rendering, UV or collision parity claim.')
 (a.out/'sloped_upper_lower_walls.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
