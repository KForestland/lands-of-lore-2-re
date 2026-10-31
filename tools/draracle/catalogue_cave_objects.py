#!/usr/bin/env python3
"""Catalogue verified spatial fields without guessing sprite or object classes."""
import argparse,csv,json,struct
from collections import defaultdict
from pathlib import Path
from lol2_extract_draracle_geometry import decode,u32


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--walk',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    _,_,raw,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    walk=json.loads(a.walk.read_text())[0]
    # Use companion floors.json to handle sloped anchor heights exactly.
    floors=json.loads((a.walk.parent/'floors.json').read_text())
    anchor=next(f for f in floors['faces'] if f['region']==walk['regions'][0])
    delta=[walk['faces'][0][0][i]-anchor['points'][0][i]*64 for i in range(3)]
    groups=defaultdict(list);rows=[]
    for k in range(u32(raw,0x60)):
        d=raw[u32(raw,0x14)+37*k:u32(raw,0x14)+37*(k+1)]
        x,y,z=(struct.unpack_from('<h',d,o)[0] for o in [0,2,6])
        region=struct.unpack_from('<H',d,10)[0];template=struct.unpack_from('<H',d,32)[0]
        if region>=len(regions):raise ValueError('Region outside cave')
        pos=[x+delta[0],z+delta[1],-y+delta[2]]
        nearest=min(range(len(walk['checkpoints'])),key=lambda i:sum((pos[j]-walk['checkpoints'][i]['start'][j])**2 for j in range(3)))
        row=dict(record=k,template=template,region=region,selector=d[35],initial_state=d[34],flags=d[36],position=pos,checkpoint=nearest+1)
        rows.append(row);groups[template].append(row)
    summary=[dict(template=t,placements=len(rs),regions=len({r['region'] for r in rs}),selectors=sorted({r['selector'] for r in rs}),sample_records=[r['record'] for r in rs[:5]],sample_checkpoints=sorted({r['checkpoint'] for r in rs[:5]})) for t,rs in sorted(groups.items(),key=lambda x:(-len(x[1]),x[0]))]
    report=dict(records=len(rows),templates=len(groups),translation=delta,groups=summary,placements=rows,scope='Spatial fields supported by native constructor replay. Nearest checkpoint is a geometric navigation hint, not a visibility or reachability claim. Template IDs are not yet plant/enemy identities; no sprite binding, spawn condition, animation or behavior inferred.')
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'object_catalogue.json').write_text(json.dumps(report,indent=2)+'\n')
    with (a.out/'placements.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['record','template','region','selector','initial_state','flags','x','height','z','nearest_checkpoint'])
        for r in rows:w.writerow([r[k] for k in ['record','template','region','selector','initial_state','flags']]+r['position']+[r['checkpoint']])
    lines=['# Cave object identification catalogue','','Object types and sprite bindings remain unverified. Checkpoints are proximity hints.','','| Template | Placements | Regions | Sample records | Nearby checkpoints |','|---|---:|---:|---|---|']
    for g in summary:lines.append(f"| {g['template']} | {g['placements']} | {g['regions']} | {g['sample_records']} | {g['sample_checkpoints']} |")
    (a.out/'README.md').write_text('\n'.join(lines)+'\n');print({k:report[k] for k in ['records','templates','translation']});print(summary[:5])


if __name__=='__main__':main()
