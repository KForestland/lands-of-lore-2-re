#!/usr/bin/env python3
"""Check a wall's preview RGB against pinned source indices and its file palette."""
import argparse,json,struct,collections
from pathlib import Path
from PIL import Image
from lol2_extract_draracle_geometry import decode
from lol2_extract_cave_materials import ASSET,HASH
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_wall_material_checkpoint import sections
from lol2_pixel_layout import column_major_to_rows
from lol2_palette_png import rgb_palette,colorize

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--textures',type=Path,required=True);p.add_argument('--record',type=int,default=2702);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,_,raw,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes());require(0<=a.record<3052,'Record outside table')
 record=raw[30093+a.record*8:30101+a.record*8];descriptor=struct.unpack_from('<h',record)[0]
 owner=next(i for i,r in enumerate(regions) if r[13]<=a.record<r[13]+(r[15]&255))
 _,blob,identity,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');s=sections(blob)
 v=struct.unpack_from('<6H11I',blob,s[2]+descriptor*56);_,w,h,flags,variants,_=v[:6];require(flags in [0xa9,0x80a9] and variants==1,'Unsupported layout')
 pos=s[3]+v[7];require(v[12]==w*h+8,'Unexpected payload size');require(struct.unpack_from('<4H',blob,pos)==(flags,w,h,w*h&65535),'Header mismatch')
 source=blob[pos+8:pos+8+w*h];indices=column_major_to_rows(source,w,h);paloff=struct.unpack_from('<I',blob,4)[0];palette=rgb_palette(blob[paloff:paloff+768],6)
 expected=colorize(indices,palette);path=a.textures/f'material_{descriptor:04d}/variant_0_mip_0.png';im=Image.open(path).convert('RGB');require(im.size==(w,h),'Preview dimensions')
 actual=im.tobytes();require(actual==expected,'Preview differs from original file palette')
 common=[dict(index=k,pixels=n,rgb=list(palette[k*3:k*3+3])) for k,n in collections.Counter(indices).most_common(8)]
 report=dict(record=a.record,region=owner,descriptor=descriptor,flags=flags,variants=variants,pixels=w*h,rgb_mismatches=0,source_pixels_sha256=sha(source),preview_rgb_sha256=sha(actual),common_colors=common,identity=identity,scope='Preview exactly matches original indexed payload with its file palette. No blue tint added by this export. Does not establish live shade-bank choice, transparency, lighting, renderer palette changes or semantic use of this material.')
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_palette_audit.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['identity','common_colors']})
if __name__=='__main__':main()
