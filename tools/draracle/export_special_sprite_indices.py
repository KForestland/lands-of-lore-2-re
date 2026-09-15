#!/usr/bin/env python3
"""Export resource474 source indices for a controlled in-cave compositor test."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from extract_prop_sprite_previews import decode_rows
from verify_special_pixel_table_binding import verify

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,blob,_,_=load_named(a.game_root,ASSET);s=sections(blob);require(sha(blob)==HASH,'Cache changed');v=struct.unpack_from('<6H11I',blob,s[2]+474*56)
 require(v[3]==0x28e and v[4]==1,'Descriptor changed');w,h,indices,_=decode_rows(blob[s[3]+v[7]:s[3]+v[7]+v[12]],allow_special=True);remap,binding=verify((a.game_root/'LOLG.DAT').read_bytes(),blob)
 a.out.mkdir(parents=True,exist_ok=True);Image.frombytes('L',(w,h),indices).save(a.out/'sprite_474.png');Image.frombytes('L',(256,1),remap).save(a.out/'remap.png')
 (a.out/'manifest.json').write_text(json.dumps(dict(descriptor=474,width=w,height=h,special_pixels=indices.count(1),indices_sha256=sha(indices),binding=binding,scope='Original pixels and initial remap; diagnostic placement, scale and overlap are not native placement evidence.'),indent=2)+'\n');print(w,h,indices.count(1),'special pixels')
if __name__=='__main__':main()
