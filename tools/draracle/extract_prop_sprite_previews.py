#!/usr/bin/env python3
"""Decode bounded 28E row-span previews; alpha semantics remain provisional."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette


def decode_rows(data, expected_flags=0x28e):
    flags,w,h,size=struct.unpack_from('<4H',data)
    require(flags==expected_flags and size==len(data)-8,'Unexpected sprite header')
    pixels=bytearray(w*h);pos=8;marked=0
    for y in range(h):
        require(pos+4<=len(data),'Truncated row header')
        control,n=struct.unpack_from('<HH',data,pos);pos+=4
        require(not control&0x8000,'Unsupported row flag')
        x=control&0x3fff
        require(x+n<=w and pos+n<=len(data),'Row extent')
        row=data[pos:pos+n];pos+=n
        require(bool(control&0x4000)==(0 in row),'Transparency hint mismatch')
        marked+=bool(control&0x4000);pixels[y*w+x:y*w+x+n]=row
    require(pos==len(data),'Trailing sprite bytes')
    return w,h,bytes(pixels),marked


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    _,blob,_,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');s=sections(blob)
    paloff=struct.unpack_from('<I',blob,4)[0];pal=rgb_palette(blob[paloff:paloff+768],6)
    a.out.mkdir(parents=True,exist_ok=True);results=[]
    for descriptor in [192,195,273,274,275,276,278,295,296,297,298,299,300,301,302,306,417,469,473]:
        v=struct.unpack_from('<6H11I',blob,s[2]+descriptor*56)
        require(v[3]==0x28e and v[4]==1,'Unsupported descriptor')
        for level in range(v[5]&255):
            start=s[3]+v[7+level];size=v[12+level];data=blob[start:start+size]
            w,h,indices,marked=decode_rows(data)
            require((w,h)==(max(1,v[1]>>level),max(1,v[2]>>level)),'Mip dimensions')
            rgba=bytes(c for index in indices for c in [*pal[index*3:index*3+3],255 if index else 0])
            name=f'prop_{descriptor}_mip_{level}.png';Image.frombytes('RGBA',(w,h),rgba).save(a.out/name)
            results.append(dict(descriptor=descriptor,level=level,width=w,height=h,marked_rows=marked,payload_sha256=sha(data),png=name))
    cards=''.join(f'<article><h2>Resource {r["descriptor"]}</h2><img src="{r["png"]}"></article>' for r in results if r['level']==0)
    (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Cave prop sprite previews</title><style>body{background:#333;color:white;font:18px sans-serif}article{display:inline-block;vertical-align:top;margin:20px}img{image-rendering:pixelated;min-width:200px;background:#777}</style><h1>Candidate sprite decodes</h1><p>Row spans checked; index-zero alpha provisional. Identity, scale and native rendering remain unverified.</p>'+cards)
    report=dict(images=len(results),rows=sum(r['height'] for r in results),results=results,scope='All row extents, mip dimensions and payload ends checked. Row4000 matches presence of index0 for these fixtures. Index0 and omitted row extents shown transparent provisionally; no native sampler/alpha replay. Do not infer object identity, UV orientation or placement scale from preview alone.')
    (a.out/'prop_previews.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='results'})


if __name__=='__main__':main()
