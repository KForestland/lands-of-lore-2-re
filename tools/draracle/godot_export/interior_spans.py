"""Geometric exposure candidates, not a port of the native wall builder."""
from itertools import combinations

def exposed(a,b):
    """Linear vertical intervals along an edge: return A's parts outside B."""
    lines=[a[0],a[1],b[0],b[1]]
    value=lambda line,t:line[0]+(line[1]-line[0])*t
    cuts={0.,1.}
    for x,y in combinations(lines,2):
        d0=x[0]-y[0];d1=x[1]-y[1]
        if d0*d1<0:cuts.add(d0/(d0-d1))
    cuts=sorted(cuts);out=[]
    for left,right in zip(cuts,cuts[1:]):
        mid=(left+right)/2
        for kind,low,high in [('step',a[0],min([a[1],b[0]],key=lambda x:value(x,mid))),('upper',max([a[0],b[1]],key=lambda x:value(x,mid)),a[1])]:
            if value(high,mid)-value(low,mid)<=1e-9:continue
            out.append(dict(kind=kind,t=[left,right],low=[value(low,left),value(low,right)],high=[value(high,left),value(high,right)]))
    return out

def build(g):
    spans=[];deferred=[];eligible=0
    for a in g['regions']:
        for edge,n in enumerate(a['neighbors']):
            if n is None:continue
            b=g['regions'][n];reason=None
            if a.get('record_role')!='primary_region' or b.get('record_role')!='primary_region' or a.get('floor_subdivisions') or b.get('floor_subdivisions'):reason='subdivision'
            elif (a['flags']|b['flags'])&0x10:reason='special connector'
            ids=[a['vertex_indices'][edge],a['vertex_indices'][(edge+1)%4]]
            matches=[j for j in range(4) if set(ids)==set([b['vertex_indices'][j],b['vertex_indices'][(j+1)%4]]) and b['neighbors'][j]==a['id']]
            if reason is None and len(matches)!=1:reason='no unique reciprocal indexed edge'
            if reason:
                deferred.append(dict(region=a['id'],edge=edge,neighbor=n,reason=reason));continue
            eligible+=1
            ia=[edge,(edge+1)%4];ib=[b['vertex_indices'].index(v) for v in ids]
            aa=tuple(tuple(a[k][i] for i in ia) for k in ['floor_corners','ceiling_corners']);bb=tuple(tuple(b[k][i] for i in ib) for k in ['floor_corners','ceiling_corners'])
            p0,p1=[g['vertices_fixed'][v] for v in ids]
            for part in exposed(aa,bb):
                pts=[]
                for t,z in [(part['t'][0],part['low'][0]),(part['t'][1],part['low'][1]),(part['t'][1],part['high'][1]),(part['t'][0],part['high'][0])]:
                    x=p0[0]+(p1[0]-p0[0])*t;y=p0[1]+(p1[1]-p0[1])*t;pts.append([x/65536/64,z/64,-y/65536/64])
                spans.append(dict(kind='interior',region=a['id'],neighbor=n,edge=edge,exposure=part,points=pts))
    return spans,dict(eligible_directed_edges=eligible,span_count=len(spans),deferred=deferred,scope='Geometric interval differences on reciprocal exact edges. Native wall/material/collision semantics unverified; special connectors and subdivisions deferred.')
