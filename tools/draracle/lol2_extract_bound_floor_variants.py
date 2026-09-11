#!/usr/bin/env python3
"""Extract structurally validated bound floor variants without assigning playback semantics."""
import argparse,json,struct
from pathlib import Path
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_pixel_layout import column_major_to_rows
from lol2_palette_png import rgb_palette,colorize,png_rgb
TARGETS={16:(0x80a9,1),156:(0xe1,5),161:(0xe1,5),285:(0xe1,5)}
def extract(blob,index):
 s=sections(blob);v=struct.unpack_from('<6H11I',blob,s[2]+index*56);ident,w,h,flags,variants,field10=v[:6]
 require((flags,variants)==TARGETS[index],'Unexpected bound descriptor layout')
 require(field10&255==5,'Unexpected mip count');end=min(x for x in s if x>s[3]);images=[]
 for level,(offset,size) in enumerate(zip(v[7:12],v[12:17])):
  width,height=max(1,w>>level),max(1,h>>level);require(size==8+width*height,'Mip size mismatch')
  start=s[3]+offset;require(s[3]<=start and start+variants*size<=end,'Variant span outside payload')
  if level<4:require(offset+variants*size==v[8+level],'Variants do not end at next mip')
  for variant in range(variants):
   pos=start+variant*size;require(struct.unpack_from('<4H',blob,pos)==(flags,width,height,(width*height)&65535),'Variant header mismatch')
   data=blob[pos+8:pos+size];images.append(dict(level=level,variant=variant,width=width,height=height,source_offset=pos,pixels_sha256=sha(data),pixels=data))
 return dict(descriptor_index=index,identifier=ident,flags=flags,variant_count=variants,descriptor_hex=blob[s[2]+index*56:s[2]+(index+1)*56].hex(),images=images)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,b,identity,_=load_named(a.game_root,ASSET);require(sha(b)==HASH,'Cave source changed');s=sections(b);pal=struct.unpack_from('<I',b,4)[0];require(pal+768==s[4],'Palette boundary');rgb=rgb_palette(b[pal:pal+768],6);a.out.mkdir(parents=True,exist_ok=True);results=[];cards=[]
 for k in TARGETS:
  result=extract(b,k);folder=a.out/f'material_{k:04d}';folder.mkdir(exist_ok=True)
  for im in result['images']:
   data=im.pop('pixels');im['preview_layout']='column-major corrected' if result['flags']==0x80a9 else 'row-major unverified';stem=f'variant_{im["variant"]}_mip_{im["level"]}';(folder/f'{stem}.indices').write_bytes(data);(folder/f'{stem}.png').write_bytes(png_rgb(im['width'],im['height'],colorize(column_major_to_rows(data,im['width'],im['height']) if result['flags']==0x80a9 else data,rgb)))
   if im['level']==0:cards.append(f'<article><h2>Descriptor {k}, variant {im["variant"]}</h2><img src="material_{k:04d}/{stem}.png"></article>')
  results.append(result)
 report=dict(identity=identity,materials=results,image_count=sum(len(r['images']) for r in results),scope='Variant boundaries, headers, dimensions and original indexed pixels validated. Flag semantics, playback order/timing, UVs and live shading not established.')
 (a.out/'variants.json').write_text(json.dumps(report,indent=2)+'\n');(a.out/'palette_rgb.bin').write_bytes(rgb)
 (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Bound cave floor variants</title><style>body{background:#222;color:#eee;font:16px sans-serif;margin:24px}main{display:flex;flex-wrap:wrap;gap:20px}h2{font-size:16px}img{image-rendering:pixelated;max-width:256px}</style><h1>Original bound floor variants</h1><p>File-palette previews. Variant order, timing and special effects remain unverified.</p><main>'+''.join(cards)+'</main>')
 print(report['image_count'],'variant/mip images extracted')
if __name__=='__main__':main()
