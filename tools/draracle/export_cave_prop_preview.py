#!/usr/bin/env python3
"""Export a limited static-prop preview from original placement and state fields."""
import argparse,json,struct,shutil
from pathlib import Path
from lol2_extract_draracle_geometry import decode,parse_mix,u32


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--sprites',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    mix=(a.game_root/'DAT/L1_DC.MIX').read_bytes();_,_,geo,_,_,_=decode(mix);entry=next(e for e in parse_mix(mix) if e['key']==2971019266);raw=mix[entry['offset']:entry['offset']+entry['size']]
    off,count=u32(raw,8),u32(raw,0x40);so=off+count*55+4;ns=u32(raw,so-4);fo=so+ns*16+4
    chosen={16:302,21:417,23:278,24:278};states={};state=0;frame=0
    for t in range(count):
        template=raw[off+t*55:off+(t+1)*55];n=template[46]+template[47]
        for selector in range(n):
            s=raw[so+state*16:so+(state+1)*16];c=struct.unpack_from('<b',s,13)[0]
            if t in chosen:
                f=raw[fo+frame*12:fo+(frame+1)*12]
                assert n==1 and c==1 and template[50]==0 and struct.unpack_from('<h',f)[0]==chosen[t]
                # Renderer129300..129377: width/2 with left/right trims,
                # top=anchor+height-top_trim; bottom=anchor+bottom_trim.
                states[t]=dict(descriptor=chosen[t],left=-s[14]/2+f[5],right=s[14]/2-f[7],bottom=f[8],top=s[15]-f[6],frame_flags=f[2])
            frame+=1 if c<0 else c;state+=1
    props=[]
    for k in range(u32(geo,0x60)):
        d=geo[u32(geo,0x14)+k*37:u32(geo,0x14)+(k+1)*37];t=struct.unpack_from('<H',d,32)[0]
        if t not in chosen:continue
        assert d[35]==0
        x,y,z=(struct.unpack_from('<h',d,o)[0] for o in [0,2,6])
        props.append(dict(record=k,template=t,region=struct.unpack_from('<H',d,10)[0],position_native=[x,z,-y],**states[t]))
    a.out.mkdir(parents=True,exist_ok=True)
    for resource in set(chosen.values()):shutil.copyfile(a.sprites/f'prop_{resource}_mip_0.png',a.out/f'prop_{resource}.png')
    report=dict(props=props,count=len(props),scope='Original static placement/state dimensions and frame trims. Source resource routing flags0 only. Fixed-Y billboard, first frame, alpha and frame-flag orientation are preview assumptions; no spawn/interaction/collision parity. Column excluded because its template uses region-height flag2.')
    (a.out/'props.json').write_text(json.dumps(report,indent=2)+'\n');print('Exported',len(props),'static prop candidates')


if __name__=='__main__':main()
