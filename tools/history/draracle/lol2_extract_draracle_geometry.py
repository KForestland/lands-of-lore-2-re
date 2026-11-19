#!/usr/bin/env python3
"""Extract the pinned L1_DC cave's original coordinates, regions and slope corners.
No textures/audio. Unknown bytes are preserved, never interpreted as invented geometry.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, re, struct
from pathlib import Path

MIX_HASH = '6384ec4d4d78f1aadfc1f154d924e1e20636af037cf5af68fe35af8478854345'
GEO_HASH_ID = 0xB1202500

def sha(b): return hashlib.sha256(b).hexdigest()
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def s16(n): return n-65536 if n & 32768 else n

def parse_mix(b):
    if len(b)<6: raise ValueError('Truncated MIX header')
    count,total=struct.unpack_from('<HI',b)
    base=6+12*count
    if base>len(b) or base+total!=len(b): raise ValueError('MIX size mismatch')
    entries=[]
    for i in range(count):
        key,off,size=struct.unpack_from('<III',b,6+12*i)
        if off+size>total: raise ValueError('Entry exceeds MIX data')
        entries.append(dict(index=i,key=key,offset=base+off,size=size))
    spans=sorted((e['offset'],e['offset']+e['size']) for e in entries)
    if any(a[1]>c[0] for a,c in zip(spans,spans[1:])): raise ValueError('Overlapping MIX entries')
    return entries

def slope_corners(records, i, ceiling=False):
    """Port of original routines 0xF4504 / 0xF4590, gated by flags 4 / 8.
    Heights returned in signed original integer units, before 16.16 expansion.
    """
    r=records[i]; flag=8 if ceiling else 4
    base=s16(r[11 if ceiling else 10])
    corners=[base]*4
    if r[14]&flag:
        side=(r[14]>>(14 if ceiling else 12))&3
        other=r[2+side]
        if other==65535:
            edge=s16(r[10 if ceiling else 11])
        else:
            if other>=len(records):raise ValueError('Slope neighbor out of bounds')
            edge=s16(records[other][11 if ceiling else 10])
        corners[side]=corners[(side+1)%4]=edge
    return corners

def decode(b):
    if sha(b)!=MIX_HASH: raise ValueError('Unsupported or changed L1_DC.MIX; expected pinned GOG fixture')
    entries=parse_mix(b)
    e=next(e for e in entries if e['key']==GEO_HASH_ID)
    raw=b[e['offset']:e['offset']+e['size']]
    if u32(raw,0)!=18:raise ValueError('Unsupported format marker')
    nv,nr=u32(raw,0x50),u32(raw,0x58)
    vo,ro=u32(raw,4),u32(raw,12)
    if (nv,nr,vo,ro)!=(2695,1954,5300,54509):raise ValueError('Pinned geometry header mismatch')
    verts=list(struct.iter_unpack('<ii',raw[vo:vo+nv*8]))
    records=[struct.unpack_from('<22H',raw,ro+i*44) for i in range(nr)]
    for r in records:
        if any(x>=nv for x in r[6:10]):raise ValueError('Vertex reference outside table')
        if any(x!=65535 and x>=nr for x in r[2:6]):raise ValueError('Region reference outside table')
    regions=[]
    for i,r in enumerate(records):
        regions.append(dict(id=i,source_offset=e['offset']+ro+i*44,
            raw_hex=raw[ro+i*44:ro+(i+1)*44].hex(),vertex_indices=list(r[6:10]),
            neighbors=[None if x==65535 else x for x in r[2:6]],
            floor_base=s16(r[10]),ceiling_base=s16(r[11]),
            floor_corners=slope_corners(records,i),ceiling_corners=slope_corners(records,i,True),
            group_candidate=r[12],flags=r[14],unknown_words=list(r[12:]),
            floor_slope=bool(r[14]&4),ceiling_slope=bool(r[14]&8),
            subregion_flag=bool(r[14]&128),floor_link_flag=bool(r[14]&32),ceiling_link_flag=bool(r[14]&64)))
    return entries,e,raw,verts,records,regions

def audit(verts,records,regions):
    edges=collections.defaultdict(list)
    for i,r in enumerate(records):
        for k in range(4):edges[tuple(sorted((r[6+k],r[6+(k+1)%4])))].append((i,k))
    nonrec=[];mismatch=[];directed=0;match=0;reciprocal=0
    for i,r in enumerate(records):
        for k,n in enumerate(r[2:6]):
            if n==65535:continue
            directed+=1
            if i in records[n][2:6]:reciprocal+=1
            else:nonrec.append([i,k,n])
            edge=tuple(sorted((r[6+k],r[6+(k+1)%4])))
            if any(j==n for j,_ in edges[edge]):match+=1
            else:mismatch.append([i,k,n])
    graph=[set() for _ in records]
    for i,r in enumerate(records):
        for n in r[2:6]:
            if n!=65535:graph[i].add(n);graph[n].add(i)
    remaining=set(range(len(records)));components=[]
    while remaining:
        queue=[min(remaining)];component=set()
        while queue:
            v=queue.pop()
            if v in component:continue
            component.add(v);queue.extend(graph[v]-component)
        remaining-=component;components.append(sorted(component))
    inverted=[];nonplanar=[]
    for r in regions:
        if any(f>c for f,c in zip(r['floor_corners'],r['ceiling_corners'])):inverted.append(r['id'])
        for name in ['floor_corners','ceiling_corners']:
            ps=[(verts[v][0]/65536,h,verts[v][1]/65536) for v,h in zip(r['vertex_indices'],r[name])]
            a=[ps[1][j]-ps[0][j] for j in range(3)];b=[ps[2][j]-ps[0][j] for j in range(3)];c=[ps[3][j]-ps[0][j] for j in range(3)]
            cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
            normal=math.sqrt(sum(x*x for x in cross))
            distance=abs(sum(x*y for x,y in zip(c,cross)))/normal if normal else 0
            if distance>0.01:nonplanar.append(dict(region=r['id'],surface=name,fourth_corner_plane_distance=distance))
    return dict(vertices=len(verts),regions=len(records),directed_neighbors=directed,
        reciprocal_neighbors=reciprocal,shared_edge_neighbors=match,
        nonreciprocal=nonrec,neighbor_edge_mismatches=mismatch,
        edge_multiplicity=dict(collections.Counter(len(v) for v in edges.values())),
        components=sorted(components,key=lambda c:-len(c)),floor_slope_regions=sum(r['floor_slope'] for r in regions),
        ceiling_slope_regions=sum(r['ceiling_slope'] for r in regions),
        inverted_corner_regions=inverted,nonplanar_surfaces=nonplanar),edges

def export_obj(out,verts,regions,edges):
    # Raw original units. Each polygon retains its own heights and identity.
    lines=['# Draracle extracted surfaces: original X, height, -original planar Y',
           '# Corner heights and 0-2 triangle diagonal follow static code. Boundary-wall synthesis is provisional.',
           '# Includes auxiliary/subregions; this is not a final collision mesh.']
    vi=0
    def face(name,points):
        nonlocal vi
        lines.append('g '+name)
        for x,y,z in points:lines.append(f'v {x:.8f} {y:.8f} {z:.8f}')
        for k in range(1,len(points)-1):lines.append(f'f {vi+1} {vi+k+1} {vi+k+2}')
        vi+=len(points)
    for r in regions:
        for surface in ['floor','ceiling']:
            pts=[(verts[v][0]/65536,h,-verts[v][1]/65536) for v,h in zip(r['vertex_indices'],r[surface+'_corners'])]
            if surface=='ceiling':pts=[pts[0],pts[3],pts[2],pts[1]]
            face(f'region_{r["id"]}_{surface}',pts)
        for k,n in enumerate(r['neighbors']):
            if n is not None:continue
            j=(k+1)%4
            a,c=[verts[r['vertex_indices'][s]] for s in (k,j)]
            face(f'region_{r["id"]}_boundary_{k}',[(a[0]/65536,r['floor_corners'][k],-a[1]/65536),(c[0]/65536,r['floor_corners'][j],-c[1]/65536),(c[0]/65536,r['ceiling_corners'][j],-c[1]/65536),(a[0]/65536,r['ceiling_corners'][k],-a[1]/65536)])
    (out/'draracle_surfaces_preview.obj').write_text('\n'.join(lines)+'\n')

def export_svg(out,verts,regions,edges):
    # Metric scale retained, Y flipped only for north-up presentation.
    xs=[v[0]/65536 for v in verts];ys=[v[1]/65536 for v in verts]
    x0,x1=min(xs)-100,max(xs)+100;y0,y1=min(ys)-100,max(ys)+100
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {-y1} {x1-x0} {y1-y0}">',f'<rect x="{x0}" y="{-y1}" width="{x1-x0}" height="{y1-y0}" fill="#101720"/>']
    for r in regions:
        points=' '.join(f'{verts[v][0]/65536},{-verts[v][1]/65536}' for v in r['vertex_indices'])
        lines.append(f'<polygon points="{points}" fill="#334553" stroke="#526574" stroke-width="3"><title>Region {r["id"]}; floor {r["floor_base"]}; ceiling {r["ceiling_base"]}</title></polygon>')
    for (a,b),ids in edges.items():
        if len(ids)==1:lines.append(f'<path d="M{verts[a][0]/65536},{-verts[a][1]/65536} L{verts[b][0]/65536},{-verts[b][1]/65536}" stroke="#69ded5" stroke-width="9"/>')
    (out/'draracle_footprint.svg').write_text('\n'.join(lines+['</svg>']))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();src=args.game_root/'DAT/L1_DC.MIX';b=src.read_bytes()
    entries,e,raw,verts,records,regions=decode(b);report,edges=audit(verts,records,regions)
    out=args.out;out.mkdir(parents=True,exist_ok=True);(out/'raw').mkdir(exist_ok=True)
    # Preserve every byte of both non-texture entries, including unresolved metadata.
    for en in entries:
        if en['index']!=2:(out/'raw'/f'entry_{en["index"]}_{en["key"]:08x}.bin').write_bytes(b[en['offset']:en['offset']+en['size']])
    pointers=struct.unpack_from('<19I',raw,4)
    boundaries=sorted(set([0,len(raw),*filter(lambda n:0<n<len(raw),pointers)]))
    sections=[]
    for a,c in zip(boundaries,boundaries[1:]):
        fn=f'section_{a:06x}_{c:06x}.bin';chunk=raw[a:c];(out/'raw'/fn).write_bytes(chunk)
        sections.append(dict(start=a,end=c,absolute_start=e['offset']+a,sha256=sha(chunk),file=fn,pointer_slots=[i for i,n in enumerate(pointers) if n==a]))
    marker_count,marker_start=u32(raw,0xc4),u32(raw,0xc8)
    names_start=marker_start+marker_count*8
    if names_start+marker_count*26 != u32(raw,0xdc):raise ValueError('Marker block bounds differ')
    markers=[]
    for i in range(marker_count):
        x,y,region,flags=struct.unpack_from('<hhHH',raw,marker_start+8*i)
        name_bytes=raw[names_start+26*i:names_start+26*(i+1)]
        name=name_bytes.split(b'\0',1)[0].decode('ascii')
        if region>=len(regions):raise ValueError('Marker region reference out of range')
        markers.append(dict(id=i,x=x,y=y,region=region,flags_uninterpreted=flags,name=name,
            source_offset=e['offset']+marker_start+8*i,name_offset=e['offset']+names_start+26*i,
            scope='Stored marker and region reference; runtime spawn/path behavior unverified'))
    (out/'markers.json').write_text(json.dumps(markers,indent=2)+'\n')
    labels=[]
    for en in entries:
        if en['index']==2:continue
        payload=b[en['offset']:en['offset']+en['size']]
        for m in re.finditer(rb"[A-Za-z][A-Za-z0-9_ .\\:/\x27-]{5,}",payload):
            labels.append(dict(entry=en['index'],entry_offset=m.start(),absolute_offset=en['offset']+m.start(),
                text=m.group().decode('ascii'),status='literal ASCII run; semantic role unassigned'))
    (out/'labels.json').write_text(json.dumps(labels,indent=2)+'\n')
    data=dict(schema='lol2-draracle-geometry-v1',source=dict(file=str(src),sha256=sha(b),entry=e,entry_sha256=sha(raw)),
        coordinate_contract='Planar pairs: signed 16.16. Height corners: original integer units. Metre scale not established.',
        proof_scope='Original bytes + static code interpretation + automap visual correspondence. No live geometry capture yet.',
        vertices=[dict(id=i,x_fixed=x,y_fixed=y) for i,(x,y) in enumerate(verts)],regions=regions,sections=sections)
    (out/'geometry.json').write_text(json.dumps(data,indent=2)+'\n')
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    export_svg(out,verts,regions,edges);export_obj(out,verts,regions,edges)
    manifest={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k in ['vertices','regions','directed_neighbors','reciprocal_neighbors','shared_edge_neighbors','floor_slope_regions','ceiling_slope_regions']}))
    print('Extracted to',out)
if __name__=='__main__':main()
