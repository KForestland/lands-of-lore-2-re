#!/usr/bin/env python3
"""Build an indexed Godot compositor fixture; row64 has verified static loader provenance."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette
from extract_prop_sprite_previews import decode_rows
from verify_special_pixel_table_binding import verify


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    _,b,_,_=load_named(a.game_root,ASSET);require(sha(b)==HASH,'Cache changed');s=sections(b);po=struct.unpack_from('<I',b,4)[0];pal=rgb_palette(b[po:po+768],6)
    remap,binding=verify((a.game_root/'LOLG.DAT').read_bytes(),b)
    a.out.mkdir(parents=True,exist_ok=True)
    w,h=640,400;background=bytes((x//20+y//20*32)%256 for y in range(h) for x in range(w));sprite=bytearray(w*h)
    v=struct.unpack_from('<6H11I',b,s[2]+474*56);data=b[s[3]+v[7]:s[3]+v[7]+v[12]];sw,sh,pix,_=decode_rows(data,allow_special=True)
    for y in range(sh):
        for x in range(sw):
            for dy in range(3):
                for dx in range(3):sprite[(60+y*3+dy)*w+110+x*3+dx]=pix[y*sw+x]
    # Bottom strips exhaustively exercise all background indices for source0/1/2.
    for source in [0,1,2]:
        for index in range(256):
            for y in range(340+source*16,356+source*16):
                for x in range(index*2,index*2+2):sprite[y*w+x]=source
    # Give each two-pixel strip the exact input index, including duplicate RGB entries.
    bg=bytearray(background)
    for y in range(340,388):
        for x in range(512):bg[y*w+x]=x//2
    for name,indices in [('background',bg),('sprite',sprite)]:
        Image.frombytes('RGB',(w,h),bytes(c for i in indices for c in [i,i,i])).save(a.out/f'{name}.png')
    Image.frombytes('RGB',(256,1),pal).save(a.out/'palette.png')
    Image.frombytes('RGB',(256,1),bytes(c for i in remap for c in [i,i,i])).save(a.out/'remap.png')
    expected=bytes(c for src,dst in zip(sprite,bg) for c in pal[(remap[dst] if src==1 else src if src else dst)*3:(remap[dst] if src==1 else src if src else dst)*3+3])
    Image.frombytes('RGB',(w,h),expected).save(a.out/'expected.png')
    (a.out/'fixture.json').write_text(json.dumps(dict(initial_remap_row=64,binding=binding,remap_sha256=sha(remap),expected_sha256=sha(expected),scope='Static loader binds initial special-pixel table to file shade64; later runtime changes unverified. Indexed background preserves exact destination index. Ordinary source colours use file palette without runtime shading.'),indent=2)+'\n')
    print('Built640x400 indexed compositor fixture; initial shade64 loader binding verified')


if __name__=='__main__':main()
