"""Assemble the largest component of tested seams without changing source vertices."""
import json, math
from collections import defaultdict, Counter
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out",type=Path,required=True)
parser.add_argument("--geometry",type=Path,required=True)
parser.add_argument("--all",action="store_true")
args=parser.parse_args()
ROOT=args.out
BASE=ROOT
data=json.loads((BASE/'floors.json').read_text())
pairs=json.loads((BASE/'traversal_expanded.json').read_text())
g=json.load(open(args.geometry))
faces={int(f['region']):f for f in data['faces']}
adj=defaultdict(set)
for pair in pairs:
 a,b=pair['regions'];adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for seed in sorted(adj):
 if seed in seen:continue
 stack=[seed];component=set()
 while stack:
  node=stack.pop()
  if node in component:continue
  component.add(node);stack.extend(adj[node]-component)
 seen |= component;components.append(component)
regions=sorted(max(components,key=lambda c:(len(c),-min(c))))
# Extend exactly one ring, accepting only ordinary reciprocal continuous floors.
original_regions=regions.copy()
expansion=[]
for a in original_regions:
 r=g['regions'][a]
 for edge,b in enumerate(r['neighbors']):
  if b is None or b in original_regions:continue
  other=g['regions'][b]; reason=None
  ids=[r['vertex_indices'][edge],r['vertex_indices'][(edge+1)%4]]
  matches=[j for j in range(4) if set(ids)==set([other['vertex_indices'][j],other['vertex_indices'][(j+1)%4]]) and other['neighbors'][j]==a]
  if b not in faces or other.get('record_role')!='primary_region' or other.get('floor_subdivisions') or other['flags']&0x10:reason='special/subdivision'
  elif len(matches)!=1:reason='nonstandard connection'
  elif any(other['floor_corners'][other['vertex_indices'].index(v)]!=r['floor_corners'][r['vertex_indices'].index(v)] for v in ids):reason='height discontinuity'
  if reason:expansion.append(dict(region=a,neighbor=b,status=reason));continue
  fs=[[[v*64 for v in p] for p in faces[x]['points']] for x in [a,b]]
  p,q=[fs[0][r['vertex_indices'].index(v)] for v in ids]
  mid=[(p[i]+q[i])/2 for i in range(3)]
  ends=[]
  for face in fs:
   c=[sum(p[i] for p in face)/4 for i in range(3)]
   distance=math.hypot(c[0]-mid[0],c[2]-mid[2])
   if distance<16:break
   ends.append([mid[i]+(c[i]-mid[i])*min(32,distance/2)/distance for i in range(3)])
  if len(ends)!=2 or math.dist(p,q)<32:
   expansion.append(dict(region=a,neighbor=b,status='insufficient experimental clearance'));continue
  rel=lambda p:[p[i]-mid[i] for i in range(3)]
  pairs.append(dict(regions=[a,b],faces=[[rel(p) for p in face] for face in fs],start=rel(ends[0]),end=rel(ends[1])))
  adj[a].add(b);adj[b].add(a)
  expansion.append(dict(region=a,neighbor=b,status='added continuous candidate'))
regions=sorted(set(original_regions)|{b for a in original_regions for b in adj[a]})
origin=[v*64 for v in faces[regions[0]]['points'][0]]
def local(p):return [p[i]*64-origin[i] for i in range(3)]
def seam(a,b):
 pair=next(p for p in pairs if set(p['regions'])=={a,b})
 source=faces[pair['regions'][0]]['points'][0]
 offset=[source[i]*64-pair['faces'][0][0][i]-origin[i] for i in range(3)]
 ends=[[p[i]+offset[i] for i in range(3)] for p in [pair['start'],pair['end']]]
 return ends if pair['regions'][0]==a else ends[::-1]
waypoints=[];visited=set()
def tour(a):
 visited.add(a)
 for b in sorted(adj[a]):
  if b in visited:continue
  before,after=seam(a,b);waypoints.extend([before,after]);tour(b);waypoints.extend([after,before])
tour(regions[0])
assert visited==set(regions)
exits=[];untested=[]
for a in regions:
 r=g['regions'][a]
 for edge,b in enumerate(r['neighbors']):
  if b is None:continue
  item=dict(region=a,neighbor=b,edge=edge,points=[local(faces[a]['points'][i]) for i in [edge,(edge+1)%4]])
  if b not in regions:exits.append(item)
  elif b not in adj[a]:untested.append(item)
shell=[f for f in data['shell'] if int(f['region']) in regions]
fixture=dict(regions=regions,kind='connected rock-floor area',faces=[[local(p) for p in faces[r]['points']] for r in regions],shell=[[local(p) for p in f['points']] for f in shell],start=waypoints[0],end=waypoints[-1],waypoints=waypoints[1:],exits=exits,untested_internal=untested)
(BASE/'connected_walk.json').write_text(json.dumps([fixture],indent=2))
audit=dict(regions=regions,region_count=len(regions),selected_edges=sum(len(adj[r]) for r in regions)//2,original_region_count=len(original_regions),expansion=expansion,shell_counts=dict(Counter(f['kind'] for f in shell)),external_openings=exits,untested_internal=untested,waypoint_count=len(waypoints)-1,scope='Tested-seam component plus one continuous candidate ring; original geometry translated only. Shell includes provisional boundary and interior spans. External openings are uncapped.')
(BASE/'connected_walk_audit.json').write_text(json.dumps(audit,indent=2))
print({k:v for k,v in audit.items() if k not in ['external_openings','untested_internal']});print('external openings',len(exits),'untested internal directions',len(untested))
