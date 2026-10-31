#!/usr/bin/env python3
"""Separate sprite colours from destination-remapping pixels; not a final composite."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from extract_prop_sprite_previews import decode_rows
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    _,b,_,_=load_named(a.game_root,ASSET);require(sha(b)==HASH,'Cache changed');s=sections(b);po=struct.unpack_from('<I',b,4)[0];pal=rgb_palette(b[po:po+768],6);a.out.mkdir(parents=True,exist_ok=True);rows=[]
    for d in [193,194,474,475,476]:
        v=struct.unpack_from('<6H11I',b,s[2]+d*56);require(v[3]==0x28e and v[4]==1,'Unsupported descriptor')
        for level in range(v[5]&255):
            data=b[s[3]+v[7+level]:s[3]+v[7+level]+v[12+level]];w,h,pix,_=decode_rows(data,allow_special=True)
            require((w,h)==(max(1,v[1]>>level),max(1,v[2]>>level)),'Mip dimensions')
            stem=f'{d}_mip_{level}'
            Image.frombytes('RGBA',(w,h),bytes(c for x in pix for c in [*pal[x*3:x*3+3],255 if x>1 else 0])).save(a.out/f'{stem}_colour.png')
            Image.frombytes('L',(w,h),bytes(255 if x==1 else 0 for x in pix)).save(a.out/f'{stem}_remap_mask.png')
            rows.append(dict(descriptor=d,level=level,width=w,height=h,special_pixels=pix.count(1),source_sha256=sha(data),stem=stem))
    (a.out/'masks.json').write_text(json.dumps(dict(results=rows,scope='White mask pixels remap the destination in the native renderer; colour PNG omits those pixels. Separate diagnostic layers, not final appearance. No Godot integration.'),indent=2)+'\n')
    cards=''.join(f'<article><h2>Resource {r["descriptor"]}</h2><img src="{r["stem"]}_colour.png"><img src="{r["stem"]}_remap_mask.png"></article>' for r in rows if r['level']==0)
    (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Sprite remap masks</title><style>body{background:#333;color:white;font:18px sans-serif}img{background:#555;image-rendering:pixelated;max-width:400px}article{margin:24px}</style><h1>Sprite colour and background-remap masks</h1><p>Left: colour pixels only. Right: white marks pixels that transform the background. This is not the final composite.</p>'+cards)
    print(dict(mips=len(rows),special_pixels=sum(r['special_pixels'] for r in rows)))


if __name__=='__main__':main()
