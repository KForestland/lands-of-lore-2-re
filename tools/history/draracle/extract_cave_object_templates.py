#!/usr/bin/env python3
"""Extract cave template/state/frame links identified from native loaders."""
import argparse,json,struct
from pathlib import Path
from lol2_extract_draracle_geometry import decode,parse_mix,u32


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    mix=(a.game_root/'DAT/L1_DC.MIX').read_bytes();_,_,geo,_,_,_=decode(mix)
    entry=next(e for e in parse_mix(mix) if e['key']==2971019266);raw=mix[entry['offset']:entry['offset']+entry['size']]
    offset,count=u32(raw,8),u32(raw,0x40);end=offset+count*55
    if end+4>len(raw):raise ValueError('Template extent')
    templates=[raw[offset+k*55:offset+(k+1)*55] for k in range(count)]
    ns=u32(raw,end);state_start=end+4;frame_count_offset=state_start+ns*16;nf=u32(raw,frame_count_offset);frame_start=frame_count_offset+4
    if frame_start+nf*12>len(raw):raise ValueError('Frame extent')
    rows=[];state_index=frame_index=0
    for k,t in enumerate(templates):
        states=[]
        for selector in range(t[46]+t[47]):
            if state_index>=ns:raise ValueError('State overrun')
            state=raw[state_start+state_index*16:state_start+(state_index+1)*16];signed_count=struct.unpack_from('<b',state,13)[0]
            frames=1 if signed_count<0 else signed_count
            if frame_index+frames>nf:raise ValueError('Frame overrun')
            refs=[struct.unpack_from('<h',raw,frame_start+(frame_index+j)*12)[0] for j in range(frames)]
            states.append(dict(selector=selector,state_record=state_index,frame_first=frame_index,frame_count=frames,signed_frame_count=signed_count,resource_references=refs))
            state_index+=1;frame_index+=frames
        rows.append(dict(template=k,resource_flags=t[50],states=states,placements=[]))
    if (state_index,frame_index)!=(ns,nf):raise ValueError('Unconsumed state/frame records')
    for k in range(u32(geo,0x60)):
        d=geo[u32(geo,0x14)+k*37:u32(geo,0x14)+(k+1)*37];t=struct.unpack_from('<H',d,32)[0];selector=d[35]
        if t>=count or selector>=len(rows[t]['states']):raise ValueError('Invalid placement template/selector')
        rows[t]['placements'].append(dict(record=k,selector=selector))
    report=dict(templates=count,states=ns,frames=nf,placements=sum(len(r['placements']) for r in rows),source_entry=entry,template_offset=offset,results=rows,
        scope='Source parse supported by disassembly: 9E0B0/9E0BE header8/count40; F1A14 reads55-byte templates; F2B94 reads16-byte states and12-byte frames. Template bytes2E+2F partition states; signed state byte0D partitions frames. Placement selector joins validated. Resource flags and signed references require native resource routing; no sprite pixel decode, transparency, human identity or live spawn proof.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'object_templates.json').write_text(json.dumps(report,indent=2)+'\n');print({k:report[k] for k in ['templates','states','frames','placements']})


if __name__=='__main__':main()
