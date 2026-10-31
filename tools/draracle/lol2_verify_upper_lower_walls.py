#!/usr/bin/env python3
"""Verify native flat upper/lower walls and lower-wall UV-offset correction."""
import argparse,json,struct,hashlib
from pathlib import Path
from collections import Counter
import capstone
from lol2_extract_draracle_geometry import decode,s16
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_flat_wall_spans import WallReplay

def model(r,n,c,offset,mode):
 floor,ceiling=s16(r[10]),s16(r[11])
 if c&12==0:return max(floor,s16(n[11])),ceiling,offset
 top=s16(n[10]);difference=top-ceiling
 if r[17]&255 !=255 and difference>0:
  top=ceiling;offset=(offset+(difference>>((mode-1)&31)))&255
 return floor,top,offset

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 source=(a.game_root/'DAT/L1_DC.MIX').read_bytes();_,_,raw,verts,records,_=decode(source)
 exe=(a.game_root/'LOLG.DAT').read_bytes();assert hashlib.sha256(exe).hexdigest()==EXE_HASH
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 code=exe[0x114aa4+0x37000:0x115119+0x37000];ins={i.address:i for i in md.disasm(code,0x114aa4)}
 m=WallReplay(ins,raw[54509:54509+1954*44]);m.writemem(0x22d04,4,0x500000)
 m.mem[0x500000:0x500000+len(verts)*8]=b''.join(struct.pack('<2i',*v) for v in verts)
 def verify(rid,r,n,c,offset,mode,v):
  low,high,uv=model(r,n,c,offset,mode);edge=c&3;p0,p1=[v[r[6+k]] for k in [edge,(edge+1)%4]]
  expected=[[p0[0],high*65536,p0[1]],[p1[0],high*65536,p1[1]],[p1[0],low*65536,p1[1]],[p0[0],low*65536,p0[1]]]
  points,active=m.execute(rid,c,mode<<14,offset)
  actual_offset=m.readmem(0x600031,1)
  assert points==expected and active==(low<high) and actual_offset==uv,(rid,c,points,expected,actual_offset,uv)
  return points,active,actual_offset
 results=[];deferred=Counter()
 for rid,r in enumerate(records):
  for index in range(r[13],r[13]+(r[15]&255)):
   d=raw[30093+index*8:30101+index*8];c=d[5]&31;nid=r[2+(c&3)]
   if c&12 not in [0,8]:continue
   if nid==65535:deferred['absent neighbor']+=1;continue
   n=records[nid]
   if r[14]&0xfc or n[14]&0xfc:deferred['slope/subdivision/special']+=1;continue
   points,active,uv=verify(rid,r,n,c,d[3],d[7]&3,verts)
   results.append(dict(record=index,region=rid,neighbor=nid,edge=c&3,surface_code=c,points_fixed=points,active=active,vertical_offset_before=d[3],vertical_offset_after=uv,scale_mode=d[7]&3))
 synthetic=0
 square=[(0,0),(128*65536,0),(128*65536,128*65536),(0,128*65536)]
 m.mem[0x500000:0x500020]=b''.join(struct.pack('<2i',*v) for v in square)
 for edge in range(4):
  for span in [0,8]:
   for heights in [(-200,-150),(-80,80),(20,60),(120,160),(-100,100)]:
    for absent_ceiling in [False,True]:
     for mode in range(4):
      row=[0]*22;row[2:6]=[65535]*4;row[2+edge]=1;row[6:10]=[0,1,2,3];row[10]=(-100)&65535;row[11]=100;row[17]=255 if absent_ceiling else 0
      n=row.copy();n[10]=heights[0]&65535;n[11]=heights[1]&65535
      m.mem[0x400000:0x400058]=struct.pack('<44H',*(row+n))
      verify(0,row,n,edge|span,250,mode,square);synthetic+=1
 a.out.mkdir(parents=True,exist_ok=True)
 report=dict(cases=len(results),active=sum(r['active'] for r in results),offset_adjustments=sum(r['vertical_offset_before']!=r['vertical_offset_after'] for r in results),synthetic_cases=synthetic,deferred=dict(deferred),mismatches=0,results=results,scope='Call-free original routine replay for flat classes 0/8 compared to an independent height/byte-offset model. Source runtime pointers supplied. No slope, special-connector, loader/global or final UV proof.')
 (a.out/'upper_lower_walls.json').write_text(json.dumps(report,indent=2));(a.out/'native_wall_shape.bin').write_bytes(code)
 print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
