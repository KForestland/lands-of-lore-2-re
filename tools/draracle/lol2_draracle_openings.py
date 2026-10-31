#!/usr/bin/env python3
"""Interpret Draracle subdivision and narrow-connector records without snapping data."""
import argparse, collections, hashlib, json, math, struct
from pathlib import Path
from lol2_extract_draracle_geometry import decode, audit

def parents_and_chains(records):
    parents={}
    for i,r in enumerate(records):
        if r[14]&0x80:
            p=i-1
            while p>=0 and records[p][14]&0x80:p-=1
            if p<0:raise ValueError('Subdivision has no preceding owner')
            parents[i]=p
    chains=[]
    for i,r in enumerate(records):
        if i in parents:continue  # F3EF0 returns early for child records.
        for field,flag,slot in [('floor',0x20,16),('ceiling',0x40,17)]:
            if not r[14]&flag:continue
            start=r[slot];ids=[];j=start
            while True:
                if not 0<=j<len(records):raise ValueError('Subdivision chain out of bounds')
                if parents.get(j)!=i:raise ValueError('Chain member has different owner')
                ids.append(j)
                if records[j][11]==0:break
                j+=1
            chains.append(dict(parent=i,surface=field,start=start,children=ids,
                continuation_words=[records[j][11] for j in ids],
                proof='F3EF0 selects +32/+34, increments by 44, stops at +22 == 0; F3Cxx scans backward over flag 128.'))
    if set(parents)!=set(j for c in chains for j in c['children']):raise ValueError('Unaccounted subdivision records')
    return parents,chains

def edge_points(verts,records,region,side):
    ids=records[region][6:10]
    return [verts[ids[k]] for k in (side,(side+1)%4)]

def connector_side(records, connector, caller):
    """Native B18EC..B1921 / 114B08..114B45 chooses 0 when +4 names caller, else 2."""
    if not records[connector][14]&0x10:raise ValueError('Not a flagged connector')
    side=0 if records[connector][2]==caller else 2
    if records[connector][2+side]!=caller:raise ValueError('Caller not attached to selected connector side')
    return side

def compare_edges(a,b):
    a=[(x/65536,y/65536) for x,y in a];b=[(x/65536,y/65536) for x,y in b]
    u=[a[1][j]-a[0][j] for j in range(2)];length=math.hypot(*u)
    if not length:raise ValueError('Zero-length connector approach')
    distance=[abs(u[0]*(p[1]-a[0][1])-u[1]*(p[0]-a[0][0]))/length for p in b]
    t=[sum((p[j]-a[0][j])*u[j] for j in range(2))/(length*length) for p in b]
    return dict(max_line_distance_original_units=max(distance),connector_projection_on_approach=t,
                overlap_fraction=max(0,min(1,max(t))-max(0,min(t))),
                collinear_within_two_fixed_lsb=max(distance)<=2/65536)

def interpret(verts,records,regions):
    parents,chains=parents_and_chains(records);old,edges=audit(verts,records,regions)
    links=[]
    for i,k,n in old['neighbor_edge_mismatches']:
        row=dict(source=i,side=k,target=n)
        if parents.get(i)==n:
            row['kind']='subdivision_to_owner'
        else:
            if records[n][14]&0x10:connector=n;caller=i
            elif records[i][14]&0x10:connector=i;caller=n
            else:raise ValueError('Unclassified exceptional link')
            side=connector_side(records,connector,caller)
            caller_side=records[caller][2:6].index(connector)
            a=edge_points(verts,records,caller,caller_side);b=edge_points(verts,records,connector,side)
            row.update(kind='flag16_connector',connector=connector,caller=caller,
                connector_side=side,caller_side=caller_side,approach_endpoints_fixed=a,
                selected_endpoints_fixed=b,comparison=compare_edges(a,b))
        links.append(row)
    nonrec=[dict(source=i,side=k,target=n,kind='subdivision_to_owner' if parents.get(i)==n else 'unresolved') for i,k,n in old['nonreciprocal']]
    if any(x['kind']=='unresolved' for x in nonrec):raise ValueError('Unclassified nonreciprocal link')
    # Add role-aware fields. Keep the old raw record bytes for byte-for-byte round trips.
    corrected=[]
    for r in regions:
        r=dict(r);i=r['id'];r['storage_word_22']=records[i][11]
        if i in parents:
            r.update(record_role='floor_subdivision',owner=parents[i],ceiling_base=None,ceiling_corners=None,
                list_continuation=records[i][11],floor_link_flag=False,ceiling_link_flag=False,
                standalone_ceiling=False,standalone_walls=False)
        else:r.update(record_role='primary_region',owner=None,standalone_ceiling=True,standalone_walls=True)
        r['floor_subdivisions']=next((c['children'] for c in chains if c['parent']==i and c['surface']=='floor'),[])
        corrected.append(r)
    summary=dict(primary_regions=len(records)-len(parents),floor_subdivisions=len(parents),
        exceptional_links=len(links),exception_classes=dict(collections.Counter(x['kind'] for x in links)),
        nonreciprocal_links=len(nonrec),nonreciprocal_owner_links=len(nonrec),
        connector_directed_links=sum(x['kind']=='flag16_connector' for x in links),
        connector_unique_pairs=len({tuple(sorted((x['source'],x['target']))) for x in links if x['kind']=='flag16_connector'}),
        off_line_connector_pairs=sorted({tuple(sorted((x['source'],x['target']))) for x in links if x['kind']=='flag16_connector' and not x['comparison']['collinear_within_two_fixed_lsb']}))
    return dict(summary=summary,subdivision_chains=chains,exceptional_links=links,nonreciprocal_links=nonrec),corrected

def obj_preview(path,verts,regions):
    lines=['# Original geometry, role-aware v2. No child ceilings or child boundary walls.',
           '# Connector/wall synthesis is still incomplete; not a final collision mesh.'];vi=0
    def face(name,pts):
        nonlocal vi
        lines.append('g '+name)
        lines.extend(f'v {x:.8f} {y:.8f} {-z:.8f}' for x,y,z in pts)
        lines.extend(f'f {vi+1} {vi+j+1} {vi+j+2}' for j in range(1,len(pts)-1));vi+=len(pts)
    for r in regions:
        coords=[verts[k] for k in r['vertex_indices']]
        for surface in ['floor','ceiling']:
            if surface=='floor' and r['floor_subdivisions']:continue
            h=r[surface+'_corners']
            if h is None:continue
            pts=[(p[0]/65536,z,p[1]/65536) for p,z in zip(coords,h)]
            if surface=='ceiling':pts=[pts[0],pts[3],pts[2],pts[1]]
            face(f'{surface}_{r["id"]}',pts)
        if not r['standalone_walls']:continue
        for k,n in enumerate(r['neighbors']):
            if n is not None:continue
            j=(k+1)%4;a,b=coords[k],coords[j]
            face(f'boundary_{r["id"]}_{k}',[(a[0]/65536,r['floor_corners'][k],a[1]/65536),(b[0]/65536,r['floor_corners'][j],b[1]/65536),(b[0]/65536,r['ceiling_corners'][j],b[1]/65536),(a[0]/65536,r['ceiling_corners'][k],a[1]/65536)])
    path.write_text('\n'.join(lines)+'\n')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    entries,e,raw,verts,records,regions=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    report,corrected=interpret(verts,records,regions);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'openings.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out/'geometry_v2.json').write_text(json.dumps(dict(schema='lol2-draracle-geometry-v2',source_entry=e,
        source_sha256=hashlib.sha256(raw).hexdigest(),vertices_fixed=verts,regions=corrected,
        scope='Role-aware static extraction. Connector endpoints preserved exactly; no live collision or moving-object proof.'),indent=2)+'\n')
    obj_preview(a.out/'draracle_surfaces_v2.obj',verts,corrected)
    print(json.dumps(report['summary']))
if __name__=='__main__':main()
