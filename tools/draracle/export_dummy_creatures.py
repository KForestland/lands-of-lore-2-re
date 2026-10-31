#!/usr/bin/env python3
"""Export two original indexed creature poses for explicitly provisional dummies."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from extract_block_sprite_frames import lcw,decode_blocks

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();_,b,_,_=load_named(a.game_root,ASSET);require(sha(b)==HASH,'Cache changed');s=sections(b);a.out.mkdir(parents=True,exist_ok=True);rows=[]
 for k,label,height in [(408,'Normal guard stand-in',56),(733,'Roach-like stand-in',12)]:
  v=struct.unpack_from('<6H11I',b,s[2]+k*56);require(v[3]==0x1246,'Unexpected frame type');payload=b[s[3]+v[7]:s[3]+v[7]+v[12]];ci=struct.unpack_from('<I',payload,8)[0];require(ci<17,'Unsupported codebook');off,allocation,packed=struct.unpack_from('<3I',b,s[9]+ci*12);require(s[8]<=off and off+allocation<=s[9] and packed<=allocation,'Codebook extent')
  w,h,pixels,_,tail=decode_blocks(payload,lcw(b[off:off+packed]));require((w,h)==v[1:3] and 1 not in pixels,'Special pixel needs separate semantics')
  im=Image.frombytes('L',(w,h),pixels);bbox=im.getbbox();require(bbox is not None,'Empty frame');crop=im.crop(bbox);crop.save(a.out/f'creature_{k}.png');rows.append(dict(descriptor=k,label=label,original_size=[w,h],crop_box=bbox,texture_size=crop.size,indices_sha256=sha(crop.tobytes()),unread_tail=tail,preview_height=height,preview_width=height*crop.width/crop.height,identity_scope='Visual identification, not original filename/state binding'))
 placements=[dict(id='guard_a',descriptor=408,region=353),dict(id='roach_a',descriptor=733,region=354),dict(id='guard_b',descriptor=408,region=1813),dict(id='roach_b',descriptor=733,region=1813,vertex=2,fraction=0.4)]
 (a.out/'creatures.json').write_text(json.dumps(dict(cache_sha256=HASH,frames=rows,placements=placements,scope='Static dummy poses. Original decoded pixels, cropped transparent bounds. Provisional display heights and floor-region centroid placements; not original spawns, direction/timing, AI, collision or gameplay. Kevin314-407 excluded.'),indent=2)+'\n');print(rows)
if __name__=='__main__':main()
