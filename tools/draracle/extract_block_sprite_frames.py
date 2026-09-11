#!/usr/bin/env python3
"""Decode native 1246 block sprites with explicitly selected cached codebooks."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette


def lcw(src):
    out=bytearray();pos=0
    def take(n):
        nonlocal pos
        require(pos+n<=len(src),'Truncated LCW command')
        data=src[pos:pos+n];pos+=n;return data
    while pos<len(src):
        cmd=take(1)[0]
        if cmd==0x80:
            require(pos==len(src),'LCW trailing bytes')
            return bytes(out)
        if cmd&0xc0==0x80:out.extend(take(cmd&63))
        elif cmd==0xfe:
            n=struct.unpack('<H',take(2))[0];out.extend(take(1)*n)
        else:
            if cmd<0x80:
                n=(cmd>>4)+3;ref=len(out)-(((cmd&15)<<8)|take(1)[0])
            else:
                n=struct.unpack('<H',take(2))[0] if cmd==0xff else (cmd&63)+3
                ref=struct.unpack('<H',take(2))[0]
            require(0<=ref<len(out),'Invalid LCW reference')
            for j in range(n):out.append(out[ref+j])
        require(len(out)<=1048576,'LCW output limit')
    raise ValueError('Missing LCW terminator')


def decode_blocks(data,codebook):
    require(len(data)>=24 and len(codebook)%16==0,'Block header/codebook extent')
    flags,w,h,size=struct.unpack_from('<4H',data)
    require(flags==0x1246 and size==len(data)-22,'1246 size convention')
    require(w%4==0 and h%4==0 and 0<w//4<256,'Block dimensions')
    first,last=data[22:24]
    require(first<=last<h//4,'Block row range')
    table_end=24+2*(last-first+1)
    require(table_end<=len(data),'Row table extent')
    pixels=bytearray(w*h);used=set();ends=[]
    for row in range(first,last+1):
        rel=struct.unpack_from('<H',data,24+2*(row-first))[0]
        if rel==0:continue
        pos=24+rel;require(table_end<=pos<len(data),'Row pointer')
        start=pos;x=0
        while x<w//4:
            require(pos+2<=len(data),'Row command extent')
            op,n=data[pos:pos+2];pos+=2
            require(n>0 and x+n<=w//4,'Block run extent')
            if op:
                require(pos+2*n<=len(data),'Block indices extent')
                for j in range(n):
                    index=struct.unpack_from('<H',data,pos)[0];pos+=2
                    require(index*16+16<=len(codebook),'Codebook index')
                    used.add(index)
                    for y in range(4):
                        offset=(row*4+y)*w+(x+j)*4
                        pixels[offset:offset+4]=codebook[index*16+y*4:index*16+y*4+4]
            x+=n
        ends.append((start,pos))
    # Referenced row streams must be contiguous; report unused record tails.
    cursor=table_end
    for start,end in sorted(set(ends)):
        require(start==cursor,'Row stream gap/overlap');cursor=end
    require(cursor<=len(data),'Frame stream extent')
    return w,h,bytes(pixels),len(used),len(data)-cursor


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    _,blob,_,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');s=sections(blob)
    paloff=struct.unpack_from('<I',blob,4)[0];pal=rgb_palette(blob[paloff:paloff+768],6)
    codebooks={};results=[];a.out.mkdir(parents=True,exist_ok=True)
    for descriptor in range((s[3]-s[2])//56):
        v=struct.unpack_from('<6H11I',blob,s[2]+descriptor*56)
        if v[3]!=0x1246:continue
        pos=s[3]+v[7];data=blob[pos:pos+v[12]];ci=struct.unpack_from('<I',data,8)[0]
        require(ci<17,'Unsupported codebook table index')
        if ci not in codebooks:
            off,allocation,packed=struct.unpack_from('<3I',blob,s[9]+ci*12)
            require(s[8]<=off and off+allocation<=s[9] and packed<=allocation,'Codebook storage extent')
            codebooks[ci]=lcw(blob[off:off+packed])
        w,h,pixels,used,tail=decode_blocks(data,codebooks[ci]);require((w,h)==v[1:3],'Descriptor dimensions')
        name=f'frame_{descriptor}.png';rgba=bytes(c for x in pixels for c in [*pal[x*3:x*3+3],255 if x else 0]);Image.frombytes('RGBA',(w,h),rgba).save(a.out/name)
        results.append(dict(descriptor=descriptor,codebook=ci,width=w,height=h,used_blocks=used,unread_tail_bytes=tail,png=name,payload_sha256=sha(data)))
    report=dict(frames=len(results),codebooks={str(k):dict(bytes=len(v),sha256=sha(v)) for k,v in codebooks.items()},results=results,scope='Native12607C row algorithm translated to Python; cache section9 codebook association supported structurally and visually, not replayed loader. Full row extents and codebook indices checked. Identity, playback, spawn, alpha and shading not established.')
    (a.out/'frames.json').write_text(json.dumps(report,indent=2)+'\n')
    page='''<!doctype html><meta charset="utf-8"><title>Cave block sprite frames</title><style>body{background:#333;color:white;font:18px sans-serif}img{background:#555;image-rendering:pixelated;max-width:100%}input{width:90%}</style><h1>Recovered block sprite frames</h1><p>Stored resource order; creature identity, animation timing and spawn are not assigned.</p><p id="label"></p><input aria-label="Frame" id="slider" type="range" min="0" value="0"><p><img id="frame"></p><script>const frames=DATA;const slider=document.getElementById('slider');slider.max=frames.length-1;function show(){const f=frames[slider.value];document.getElementById('label').textContent='Resource '+f.descriptor+' · block table '+f.codebook;document.getElementById('frame').src=f.png}slider.oninput=show;show()</script>'''
    (a.out/'review.html').write_text(page.replace('DATA',json.dumps(results)))
    print(dict(frames=len(results),codebooks=len(codebooks)))


if __name__=='__main__':main()
