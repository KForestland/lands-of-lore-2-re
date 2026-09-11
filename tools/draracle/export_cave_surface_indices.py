#!/usr/bin/env python3
"""Export floor and ordinary prop indices, checking existing preview parity."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_pixel_layout import column_major_to_rows
from lol2_palette_png import rgb_palette
from extract_prop_sprite_previews import decode_rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--godot-project',type=Path,required=True);a=p.parse_args()
 _,blob,_,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');s=sections(blob);po=struct.unpack_from('<I',blob,4)[0];pal=rgb_palette(blob[po:po+768],6)
 generated=a.godot_project/'assets/lol2/generated';out=generated/'surface_indices';out.mkdir(parents=True,exist_ok=True);rows=[]
 floors=json.loads((generated/'original_floors/floors.json').read_text());props=json.loads((generated/'prop_review/props.json').read_text())
 for kind,ids in [('floor',sorted(map(int,floors['materials']))),('prop',sorted({p['descriptor'] for p in props['props']}))]:
  for k in ids:
   v=struct.unpack_from('<6H11I',blob,s[2]+k*56);start=s[3]+v[7];payload=blob[start:start+v[12]];w,h=v[1:3]
   if kind=='prop':
    require(v[3]==0x28e and v[4]==1,'Unsupported sprite');dw,dh,indices,_=decode_rows(payload);require((dw,dh)==(w,h),'Sprite dimensions');require(1 not in indices,'Special pixel needs separate compositor')
    rgba=bytes(c for i in indices for c in [*pal[i*3:i*3+3],255 if i else 0]);reference=Image.open(generated/f'prop_review/prop_{k}.png').convert('RGBA');expected=rgba;layout='verified row spans'
   else:
    require(len(payload)==8+w*h and struct.unpack_from('<4H',payload)==(v[3],w,h,w*h&65535),'Unsupported floor payload')
    raw=payload[8:];reference=Image.open(generated/'original_floors'/floors['materials'][str(k)]['path']).convert('RGB')
    candidates=[('raw source bytes',raw),('column-to-row source bytes',column_major_to_rows(raw,w,h))]
    matches=[(name,buf) for name,buf in candidates if bytes(c for i in buf for c in pal[i*3:i*3+3])==reference.tobytes()]
    require(bool(matches),f'No source layout matches floor{k}');layout,indices=matches[0];w,h=reference.size
    expected=bytes(c for i in indices for c in pal[i*3:i*3+3]);layout+='; preserves existing floor import, not new native orientation proof'
   require(reference.size==(w,h) and reference.tobytes()==expected,f'Preview parity failed: {kind}{k}')
   Image.frombytes('L',(w,h),indices).save(out/f'{kind}_{k}.png');rows.append(dict(kind=kind,descriptor=k,width=w,height=h,indices_sha256=sha(indices),layout=layout,preview_parity=True))
 (out/'manifest.json').write_text(json.dumps(dict(cache_sha256=HASH,materials=rows,scope='Original first mip and variant, exact preview RGB/RGBA parity; no invented index values or new layout claims.'),indent=2)+'\n');print('Exported',len(floors['materials']),'floor and',len({p['descriptor'] for p in props['props']}),'prop index textures; parity exact')
if __name__=='__main__':main()
