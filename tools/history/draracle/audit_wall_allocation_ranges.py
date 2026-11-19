#!/usr/bin/env python3
"""Audit cave descriptor ranges identified from loader header offsets."""
import argparse,json,struct
from pathlib import Path
from lol2_extract_draracle_geometry import decode


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    _,_,raw,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    offset,count=(struct.unpack_from('<I',raw,k)[0] for k in [0xa4,0xac])
    if offset+count*26>len(raw):raise ValueError('Descriptor table outside source')
    rows=[];owners={}
    for k in range(count):
        record=raw[offset+k*26:offset+(k+1)*26]
        first=struct.unpack_from('<H',record)[0];size=record[23]
        if not size or first+size>len(regions):raise ValueError('Invalid region range')
        for region in range(first,first+size):
            if region in owners:raise ValueError('Overlapping ranges')
            owners[region]=k
        rows.append(dict(descriptor=k,source_offset=offset+k*26,first_region=first,region_count=size,requested_bytes=size*160))
    if len(owners)!=len(regions):raise ValueError('Incomplete region coverage')
    report=dict(descriptors=count,source_offset=offset,regions=len(regions),requested_object_bytes=sum(r['requested_bytes'] for r in rows),overlaps=0,uncovered=0,
        scope='Pinned original cave bytes: header A4 offset/AC count, 26-byte records, first word and byte17 allocation fields. Ranges form exact region partition. Loader E24D4 reads26 into stride42, clears byte10, masks byte19 to low nibble and zeroes16-byte tail by disassembly. Loader return stored at world+38; global22D10 handoff and live allocations not replayed.',results=rows)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_allocation_ranges.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='results'})


if __name__=='__main__':main()
