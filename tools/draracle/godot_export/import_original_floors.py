#!/usr/bin/env python3
"""Build an original-floor review asset; UV projection is explicitly provisional."""
import argparse,json,math,struct
from pathlib import Path
from PIL import Image
from interior_spans import build

def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();b=a.evidence_root;a.out.mkdir(parents=True,exist_ok=True)
 g=json.loads((b/'draracle_openings_2026-09-11/geometry_v2.json').read_text());bindings=json.loads((b/'draracle_floor_bindings_2026-09-11/bindings.json').read_text());setup=json.loads((b/'draracle_floor_setup_2026-09-11/setup_replay.json').read_text());states={r['preset']:r for r in setup['results'] if r['initial_flags']==0};byregion={r['region']:r for r in bindings['regions']};table=struct.unpack('<4096i',(b/'draracle_rotation_table_2026-09-11/rotation_table.bin').read_bytes())
 def trig(a):
  a&=65535;return table[(a&32767)>>3]*(-1 if a>=32768 else 1)
 materials={};faces=[];textured=0
 for r in g['regions']:
  if r.get('floor_subdivisions'):continue
  binding=byregion.get(r['id']);descriptor=binding.get('descriptor_index') if binding else None
  if descriptor is not None and str(descriptor) not in materials:
   regular=b/f'draracle_materials_2026-09-11/material_{descriptor:04d}/mip_0_palette.png';variant=b/f'draracle_floor_variants_2026-09-11/material_{descriptor:04d}/variant_0_mip_0.png';path=regular if regular.exists() else variant
   if path.exists():
    src=Image.open(path).convert('RGB');w,h=src.size
    # Preserve byte order but show native candidate address U*height+V.
    dst=Image.frombytes('RGB',(h,w),src.tobytes());name=f'material_{descriptor}.png';dst.save(a.out/name);materials[str(descriptor)]=dict(path=name,width=w,height=h)
  points=[];uv=[]
  for v,z in zip(r['vertex_indices'],r['floor_corners']):
   x,y=g['vertices_fixed'][v];points.append([x/65536/64,z/64,-y/65536/64])
   if descriptor is not None and str(descriptor) in materials:
    st=states[binding['preset']];xx=x-st['offset_x_fixed'];yy=y-st['offset_y_fixed'];aa=trig(st['angle_word']);bb=trig(st['angle_word']+16384);u=((yy*bb)>>16)+((xx*aa)>>16);vv=((xx*bb)>>16)-((yy*aa)>>16);mode=st['object_flags_3e']&0xc000;scale={0:2,0x4000:1,0x8000:.5,0xc000:.25}[mode];u=u*scale/65536+st['object_bytes_30_31'][0];vv=vv*scale/65536+st['object_bytes_30_31'][1];m=materials[str(descriptor)];uv.append([vv/m['height'],u/m['width']])
   else:uv.append([0,0])
  available=descriptor is not None and str(descriptor) in materials;textured+=available;faces.append(dict(region=r['id'],material=str(descriptor) if available else 'unresolved',points=points,uv=uv))
 shell=[]
 def point(vertex,height):
  x,y=g['vertices_fixed'][vertex];return [x/65536/64,height/64,-y/65536/64]
 for r in g['regions']:
  if r.get('standalone_ceiling'):
   shell.append(dict(kind='ceiling',region=r['id'],points=[point(v,h) for v,h in zip(r['vertex_indices'],r['ceiling_corners'])]))
  if not r.get('standalone_walls'):continue
  for edge,neighbor in enumerate(r['neighbors']):
   if neighbor is not None:continue
   j=(edge+1)%4;v0,v1=r['vertex_indices'][edge],r['vertex_indices'][j]
   shell.append(dict(kind='boundary',region=r['id'],edge=edge,points=[point(v0,r['floor_corners'][edge]),point(v1,r['floor_corners'][j]),point(v1,r['ceiling_corners'][j]),point(v0,r['ceiling_corners'][edge])]))
 interior,audit=build(g);shell.extend(interior)
 (a.out/"interior_audit.json").write_text(json.dumps(audit,indent=2)+"\n")
 result=dict(interior_audit=audit,shell=shell,faces=faces,materials=materials,summary=dict(floor_quads=len(faces),with_texture_candidates=textured,unresolved=len(faces)-textured,ceilings=sum(x["kind"]=="ceiling" for x in shell),boundary_quads=sum(x["kind"]=="boundary" for x in shell),interior_candidates=len(interior)),scope='Original geometry and static material identities. Diagnostic planar UVs, storage-axis interpretation, first variant and 1/64 display scale are provisional. Neutral primary ceilings and absent-neighbor boundary spans only. Interior steps/jambs unresolved. No collision completeness or guest-render parity.')
 (a.out/'floors.json').write_text(json.dumps(result)+'\n');print(result['summary'])
if __name__=='__main__':main()
