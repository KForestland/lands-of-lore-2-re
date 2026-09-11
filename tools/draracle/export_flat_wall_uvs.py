#!/usr/bin/env python3
"""Export diagnostic UVs for verified rectangular, repeating, static-material walls."""
import argparse,collections,json,math,struct
from pathlib import Path
from PIL import Image
from lol2_extract_draracle_geometry import decode
from wall_uv_addressing import address_uv

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for flag in ['game-root','geometry-evidence','textures','out']:p.add_argument('--'+flag,type=Path,required=True)
 a=p.parse_args();_,_,raw,_,_,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
 mats=json.loads(a.textures.read_text());lookup={r['record']:m for m in mats['materials'] for r in m['records']}
 groups=['flat_wall_spans','upper_lower_walls','sloped_middle_walls','sloped_upper_lower_walls','connector_middle_walls','special_upper_lower_walls']
 results=[];deferred=collections.Counter();seen=set();a.out.mkdir(parents=True,exist_ok=True);images={};cards=[];shown=set()
 for group in groups:
  for row in json.loads(next(a.geometry_evidence.glob('*/'+group+'.json')).read_text())['results']:
   k=row['record'];assert k not in seen;seen.add(k);d=raw[30093+k*8:30101+k*8];mat=lookup.get(k)
   if not row['active']:deferred['inactive']+=1;continue
   if not mat or mat['variant_count']!=1:deferred['unsupported or multi-variant material']+=1;continue
   pts=[[v/65536 for v in p] for p in row['points_fixed']]
   if pts[0][1]!=pts[1][1] or pts[2][1]!=pts[3][1]:deferred['nonrectangular vertical span']+=1;continue
   length=math.dist(pts[0][::2],pts[1][::2]);height=pts[0][1]-pts[3][1]
   if length==0 or height<=0:deferred['degenerate span']+=1;continue
   mode=(d[6]>>5)&3;scale=[2.,1.,.5,.25][d[7]&3];anchor,other=[(0,1),(1,0),(3,2),(2,3)][mode];start,end=pts[anchor],pts[other];dx,dz=(end[0]-start[0])/length,(end[2]-start[2])/length;vertical=-1 if mode<2 else 1
   im=next(x for x in mat['images'] if x['level']==0 and x['variant']==0);w,h=im['width'],im['height']
   addressing=8 if d[6]&16 else (16 if d[6]&8 else 0)
   uscale=scale if addressing else w/length
   vscale=scale if addressing==8 else h/height
   uoffset=d[2] if addressing else 0;voffset=d[3] if addressing==8 else 0
   uv=[[((pt[0]-start[0])*dx+(pt[2]-start[2])*dz)*uscale,(pt[1]-start[1])*vertical*vscale] for pt in pts]
   assert all(math.isfinite(v) and v>=-1e-7 for pair in uv for v in pair)
   im=next(x for x in mat['images'] if x['level']==0 and x['variant']==0);w,h=im['width'],im['height']
   # Preserve pre-wrap values: wrapping vertex UVs would destroy interpolation.
   result=dict(record=k,region=row['region'],descriptor=mat['descriptor'],orientation=mode,addressing=addressing,texels_per_unit=[uscale,vscale],points_godot=[[p[0],p[1],-p[2]] for p in pts],uv_unwrapped=[[(max(u,0)+uoffset)/w,(max(v,0)+voffset)/h] for u,v in uv],dimensions=[w,h],offset_bytes=list(d[2:4]))
   results.append(result);key=(mat['descriptor'],mode)
   if key in shown or len(cards)>=16:continue
   shown.add(key)
   if mat['descriptor'] not in images:images[mat['descriptor']]=Image.open(a.textures.parent/im['png']).convert('RGB')
   image=images[mat['descriptor']];pw=256;ph=max(48,min(384,round(pw*height/length)));preview=Image.new('RGB',(pw,ph));px=preview.load()
   for y in range(ph):
    for x in range(pw):
     tx,ty=(x+.5)/pw,(y+.5)/ph
     values=[(uv[0][j]*(1-tx)+uv[1][j]*tx)*(1-ty)+(uv[3][j]*(1-tx)+uv[2][j]*tx)*ty for j in range(2)]
     u,v=address_uv(round(max(values[0],0)*65536),round(max(values[1],0)*65536),uoffset,voffset,0,w,h,addressing);px[x,y]=image.getpixel((u>>16,v>>16))
   filename=f'wall_{k}.png';preview.save(a.out/filename);cards.append(f'<article><h2>Wall {k} · material {mat["descriptor"]}</h2><p>Orientation {mode}, {scale:g} texels/unit{' · PHOTO/TEST MATERIAL — cave use unresolved' if mat['descriptor']==3 else ''}</p><img src="{filename}"></article>')
 report=dict(exported=len(results),verified_geometry_records=len(seen),geometry_unresolved=3052-len(seen),deferred=dict(deferred),walls=results,scope='Diagnostic inferred world UVs, limited to rectangular static-material spans with three addressing modes. Unwrapped normalized UVs preserve repeats. No collision, transparency, camera or live rendering parity claim; generated files only.')
 (a.out/'flat_wall_uvs.json').write_text(json.dumps(report,indent=2));(a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Diagnostic cave walls</title><style>body{background:#222;color:#eee;font:16px sans-serif}main{display:flex;flex-wrap:wrap;gap:20px}article{width:280px}h2{font-size:16px}img{image-rendering:pixelated}</style><h1>Diagnostic original wall textures</h1><p>Recovered pixels with inferred UVs. Static first-variant previews; live visual parity remains open. Tall/short panels have bounded display proportions.</p><main>'+''.join(cards)+'</main>');print({k:v for k,v in report.items() if k!='walls'})
if __name__=='__main__':main()
