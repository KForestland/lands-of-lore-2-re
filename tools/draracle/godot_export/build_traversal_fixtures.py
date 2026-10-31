"""Select ordinary continuous seams for a bounded, non-native capsule experiment."""
import json, math, sys
expanded = "--all" in sys.argv
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out",type=Path,required=True)
parser.add_argument("--geometry",type=Path,required=True)
parser.add_argument("--all",action="store_true")
args=parser.parse_args()
ROOT=args.out
g=json.load(open(args.geometry))
data=json.load(open(ROOT/'floors.json'))
f={int(x['region']):x for x in data['faces']}
out=[];counts={'flat':0,'slope':0}
for a in g['regions']:
 for edge,n in enumerate(a['neighbors']):
  if n is None or n<=a['id']:continue
  b=g['regions'][n]
  if any(r.get('record_role')!='primary_region' or r.get('floor_subdivisions') or r['flags']&0x10 for r in (a,b)):continue
  ids=[a['vertex_indices'][edge],a['vertex_indices'][(edge+1)%4]]
  matches=[j for j in range(4) if set(ids)==set([b['vertex_indices'][j],b['vertex_indices'][(j+1)%4]]) and b['neighbors'][j]==a['id']]
  if len(matches)!=1:continue
  if any(abs(a['floor_corners'][a['vertex_indices'].index(v)]-b['floor_corners'][b['vertex_indices'].index(v)])>1e-6 for v in ids):continue
  faces=[[[v*64 for v in p] for p in f[r['id']]['points']] for r in (a,b)]
  p,q=[faces[0][a['vertex_indices'].index(v)] for v in ids]
  if math.dist(p,q)<128:continue
  mid=[(x+y)/2 for x,y in zip(p,q)]
  ends=[]
  for face in faces:
   center=[sum(p[i] for p in face)/4 for i in range(3)]
   dist=math.hypot(center[0]-mid[0],center[2]-mid[2])
   if dist<48:break
   ends.append([mid[i]+(center[i]-mid[i])*32/dist for i in range(3)])
  if len(ends)!=2:continue
  kind='flat' if all(max(p[1] for p in face)-min(p[1] for p in face)<1e-6 for face in faces) else 'slope'
  if not expanded and counts[kind]>=3:continue
  counts[kind]+=1
  local=lambda p:[p[i]-mid[i] for i in range(3)]
  out.append(dict(regions=[a['id'],n],kind=kind,faces=[[local(p) for p in face] for face in faces],shell=[[local([v*64 for v in p]) for p in face['points']] for face in data['shell'] if int(face['region']) in (a['id'],n)],start=local(ends[0]),end=local(ends[1])))
 if not expanded and all(v==3 for v in counts.values()):break
assert all(v>=3 for v in counts.values()),counts
path=ROOT/('traversal_expanded.json' if expanded else 'traversal_fixtures.json')
path.write_text(json.dumps(out,indent=2));print(counts, 'total', len(out))
