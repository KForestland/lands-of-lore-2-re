#!/usr/bin/env python3
"""Recover three single-state special-pixel props from native placement tables."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_extract_draracle_geometry import decode,parse_mix,u32
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from extract_prop_sprite_previews import decode_rows
from verify_special_pixel_table_binding import verify

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 mix=(a.game_root/'DAT/L1_DC.MIX').read_bytes();_,_,geo,_,_,_=decode(mix);entry=next(e for e in parse_mix(mix) if e['key']==2971019266);raw=mix[entry['offset']:entry['offset']+entry['size']]
 off,count=u32(raw,8),u32(raw,0x40);so=off+count*55+4;fo=so+u32(raw,so-4)*16+4;state=frame=0;states={};chosen={50:474,51:475,52:476}
 for t in range(count):
  template=raw[off+t*55:off+(t+1)*55];n=template[46]+template[47]
  for selector in range(n):
   s=raw[so+state*16:so+(state+1)*16];c=struct.unpack_from('<b',s,13)[0]
   if t in chosen:
    f=raw[fo+frame*12:fo+(frame+1)*12];require(n==1 and c==1 and template[50]==0 and struct.unpack_from('<h',f)[0]==chosen[t],'State binding changed')
    states[t]=dict(descriptor=chosen[t],left=-s[14]/2+f[5],right=s[14]/2-f[7],bottom=f[8],top=s[15]-f[6],frame_flags=f[2],template_source_offset=off+t*55,state_source_offset=so+state*16,frame_source_offset=fo+frame*12,state_hex=s.hex(),frame_hex=f.hex())
   state+=1;frame+=1 if c<0 else c
 props=[]
 for k in range(u32(geo,0x60)):
  pos=u32(geo,0x14)+k*37;d=geo[pos:pos+37];t=struct.unpack_from('<H',d,32)[0]
  if t not in chosen:continue
  require(d[35]==0,'Nonzero placement selector');x,y,z=(struct.unpack_from('<h',d,o)[0] for o in (0,2,6))
  props.append(dict(record=k,template=t,region=struct.unpack_from('<H',d,10)[0],position_native=[x,z,-y],placement_source_offset=pos,placement_hex=d.hex(),**states[t]))
 require({v['record'] for v in props}=={1051,1057,1058},'Placement set changed')
 _,blob,_,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');sections_=sections(blob);remap,binding=verify((a.game_root/'LOLG.DAT').read_bytes(),blob);a.out.mkdir(parents=True,exist_ok=True)
 for k in chosen.values():
  v=struct.unpack_from('<6H11I',blob,sections_[2]+k*56);require(v[3]==0x28e and v[4]==1,'Unexpected sprite descriptor');w,h,pixels,_=decode_rows(blob[sections_[3]+v[7]:sections_[3]+v[7]+v[12]],allow_special=True)
  Image.frombytes('L',(w,h),pixels).save(a.out/f'sprite_{k}.png')
 Image.frombytes('L',(256,1),remap).save(a.out/'remap.png')
 report=dict(props=props,count=len(props),mix_sha256=sha(mix),cache_sha256=HASH,binding=binding,scope='Single-state/frame static table bindings and original positions/bounds. Fixed-Y billboard remains preview convention; no spawn, interaction, native lighting or draw-order parity. Templates82/86/87 deliberately outside this three-prop export.')
 (a.out/'props.json').write_text(json.dumps(report,indent=2)+'\n');print([(v['record'],v['descriptor'],v['left'],v['right'],v['top']) for v in props])
if __name__=='__main__':main()
