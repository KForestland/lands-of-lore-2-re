#!/usr/bin/env python3
"""Extract raw indexed wall mip/variant payloads; defer unsupported encodings."""
import argparse, collections, json, struct
from pathlib import Path
from lol2_cache_named_wall_fixture import load_named, require, sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_extract_draracle_geometry import decode
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette,colorize,png_rgb

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,blob,identity,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed')
 _,_,raw,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
 uses=collections.defaultdict(list)
 for rid,r in enumerate(regions):
  for index in range(r[13],r[13]+(r[15]&255)):
   k=struct.unpack_from('<h',raw,30093+index*8)[0];require(k>=0,'Animated reference requires separate binding')
   uses[k].append(dict(record=index,region=rid))
 s=sections(blob);end=min(x for x in s if x>s[3]);pal=struct.unpack_from('<I',blob,4)[0]
 rgb=rgb_palette(blob[pal:pal+768],6);a.out.mkdir(parents=True,exist_ok=True)
 results=[];deferred=[];cards=[]
 for k,records in sorted(uses.items()):
  v=struct.unpack_from('<6H11I',blob,s[2]+k*56);ident,w,h,flags,variants,field=v[:6];mips=field&255
  require(1<=mips<=5 and variants>0,'Invalid descriptor dimensions')
  images=[];reason=None
  for level in range(mips):
   width,height=max(1,w>>level),max(1,h>>level);offset,size=v[7+level],v[12+level]
   if size!=8+width*height:reason='Non-raw payload size';break
   start=s[3]+offset;require(s[3]<=start and start+variants*size<=end,'Payload extent')
   if level+1<mips:require(offset+variants*size==v[8+level],'Variant/mip boundary')
   for variant in range(variants):
    pos=start+variant*size
    require(struct.unpack_from('<4H',blob,pos)==(flags,width,height,(width*height)&65535),'Raw mip header')
    data=blob[pos+8:pos+size]
    images.append((dict(level=level,variant=variant,width=width,height=height,source_offset=pos,pixels_sha256=sha(data)),data))
  if reason:
   deferred.append(dict(descriptor=k,flags=flags,reason=reason,records=records));continue
  folder=a.out/f'material_{k:04d}';folder.mkdir(exist_ok=True);metadata=[]
  for im,data in images:
   stem=f'variant_{im["variant"]}_mip_{im["level"]}'
   (folder/(stem+'.indices')).write_bytes(data);(folder/(stem+'.png')).write_bytes(png_rgb(im['width'],im['height'],colorize(data,rgb)))
   im['png']=f'{folder.name}/{stem}.png';metadata.append(im)
   if im['level']==0 and im['variant']==0:cards.append(f'<article><h2>Descriptor {k}</h2><p>{len(records)} wall records; {variants} variant(s)</p><img src="{im["png"]}"></article>')
  results.append(dict(descriptor=k,flags=flags,variant_count=variants,records=records,images=metadata))
 report=dict(identity=identity,materials=results,deferred=deferred,image_count=sum(len(x['images']) for x in results),scope='Original indexed pixels with file palette; descriptor ordinals from wall first words. Transparency, playback, native UVs, shading and runtime pointer provenance remain unresolved.')
 (a.out/'wall_textures.json').write_text(json.dumps(report,indent=2))
 (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Cave wall texture review</title><style>body{background:#222;color:#eee;font:16px sans-serif}main{display:flex;flex-wrap:wrap;gap:24px}article{width:300px}img{max-width:280px;image-rendering:pixelated}</style><h1>Original cave wall texture payloads</h1><p>First variants shown. File palette only; transparency, playback and placement unresolved.</p><main>'+''.join(cards)+'</main>')
 print(dict(materials=len(results),images=report['image_count'],records=sum(len(x['records']) for x in results),deferred=[x['descriptor'] for x in deferred]))
if __name__=='__main__':main()
