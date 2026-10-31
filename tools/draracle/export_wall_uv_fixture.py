#!/usr/bin/env python3
"""Export one diagnostic wall UV fixture and original-pixel preview; no scene mutation."""
import argparse,json,math
from pathlib import Path
from PIL import Image
from lol2_extract_draracle_geometry import decode
from wall_uv_addressing import address_uv

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--geometry-evidence',type=Path,required=True);p.add_argument('--textures',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,_,raw,_,_,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
 textures=json.loads(a.textures.read_text());mat=next(m for m in textures['materials'] if m['descriptor']==134);ids={r['record'] for r in mat['records']}
 rows=json.loads((a.geometry_evidence/'flat_walls/flat_wall_spans.json').read_text())['results']
 candidates=[]
 for r in rows:
  d=raw[30093+r['record']*8:30101+r['record']*8]
  if r['record'] in ids and r['active'] and d[6]&16:
   pts=[[v/65536 for v in p] for p in r['points_fixed']];length=math.dist(pts[0][::2],pts[1][::2]);height=pts[0][1]-pts[3][1]
   if length>0 and height>0:candidates.append((r,d,pts,length,height))
 assert candidates
 r,d,pts,length,height=candidates[0];mode=(d[6]>>5)&3;scale=[2.,1.,.5,.25][d[7]&3]
 anchor,other=[(0,1),(1,0),(3,2),(2,3)][mode];start=pts[anchor];end=pts[other]
 horizontal=[(end[0]-start[0])/length,(end[2]-start[2])/length];vertical=-1 if mode<2 else 1
 # This geometric construction is an algebraic inference, not live renderer parity.
 def uv(point):return ((point[0]-start[0])*horizontal[0]+(point[2]-start[2])*horizontal[1])*scale,(point[1]-start[1])*vertical*scale
 texels=[uv(p) for p in pts]
 im=next(im for im in mat['images'] if im['level']==0 and im['variant']==0);image=Image.open(a.textures.parent/im['png']).convert('RGB');w,h=image.size
 # Independent perspective-ratio check in a synthetic camera frame.
 cases=0
 X,Z=7.,23.;U,V=-horizontal[0]/scale,-horizontal[1]/scale;Y=5.;W=vertical/scale
 for t in [.1,.25,.5,.75,.9]:
  for v in [.1,.5,.9]:
   distance=t*length;qx=X+horizontal[0]*distance;qz=Z+horizontal[1]*distance
   if abs(qz)<1e-9:continue
   qy=Y+v*height*vertical;x=qx/qz;y=qy/qz;den=-U*W+x*V*W
   if abs(den)<1e-9:continue
   pu=(-W*X+x*W*Z)/den;pv=(U*Y-x*V*Y+y*(V*X-U*Z))/den
   assert math.isclose(pu,distance*scale,abs_tol=1e-8) and math.isclose(pv,v*height*scale,abs_tol=1e-8);cases+=1
 assert cases==15
 preview=Image.new('RGB',(512,256));pixels=preview.load()
 for y in range(256):
  for x in range(512):
   tx=(x+.5)/512;ty=(y+.5)/256
   top=[texels[0][j]*(1-tx)+texels[1][j]*tx for j in range(2)];bottom=[texels[3][j]*(1-tx)+texels[2][j]*tx for j in range(2)]
   u,v=[top[j]*(1-ty)+bottom[j]*ty for j in range(2)]
   ui,vi=address_uv(round(u*65536),round(v*65536),d[2],d[3],0,w,h,8);pixels[x,y]=image.getpixel((ui>>16,vi>>16))
 a.out.mkdir(parents=True,exist_ok=True);preview.save(a.out/'wall_preview.png')
 report=dict(record=r['record'],region=r['region'],descriptor=134,orientation=mode,texels_per_unit=scale,points_original=pts,uv_texels_before_offsets=texels,offset_bytes=list(d[2:4]),synthetic_projection_checks=cases,scope='Diagnostic geometric UV inference checked against recovered projection coefficient algebra in a synthetic camera frame. Original file-palette pixels, first variant, nearest sampling. Not live camera/shading/transparency parity; do not replace scene walls automatically.')
 (a.out/'wall_fixture.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
