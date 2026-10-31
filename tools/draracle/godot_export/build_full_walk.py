"""Assemble every recovered floor and shell face in one original-unit world."""
import json
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out",type=Path,required=True)
parser.add_argument("--geometry",type=Path,required=True)
parser.add_argument("--all",action="store_true")
args=parser.parse_args()
from collections import Counter
ROOT=args.out
BASE=ROOT
data=json.loads((BASE/'floors.json').read_text())
connected=json.loads((BASE/'connected_walk.json').read_text())[0]
faces={int(f['region']):f for f in data['faces']}
origin=[faces[connected['regions'][0]]['points'][0][i]*64-connected['faces'][0][0][i] for i in range(3)]
def local(p):return [p[i]*64-origin[i] for i in range(3)]
checkpoints=[]
for pair in json.loads((BASE/'traversal_expanded.json').read_text()):
 source=faces[pair['regions'][0]]['points'][0]
 offset=[source[i]*64-pair['faces'][0][0][i]-origin[i] for i in range(3)]
 checkpoints.append(dict(regions=pair['regions'],start=[pair['start'][i]+offset[i] for i in range(3)],end=[pair['end'][i]+offset[i] for i in range(3)]))
g=json.load(open(args.geometry))
markers=[]
for r in g['regions']:
 if r['id'] not in faces or not r['flags']&0x10:continue
 for e,n in enumerate(r['neighbors']):
  if n is not None:markers.append(dict(region=r['id'],neighbor=n,points=[local(faces[r['id']]['points'][i]) for i in [e,(e+1)%4]]))
fixture=dict(regions=list(faces),faces=[[local(p) for p in f['points']] for f in faces.values()],shell=[[local(p) for p in f['points']] for f in data['shell']],start=connected['start'],end=connected['end'],waypoints=connected['waypoints'],checkpoints=checkpoints,exits=markers,kind='full recovered cave',minimum_floor_y=min(local(p)[1] for f in faces.values() for p in f['points']))
(BASE/'full_walk.json').write_text(json.dumps([fixture],separators=(',',':')))
audit=dict(floors=len(faces),shell=dict(Counter(f['kind'] for f in data['shell'])),checkpoints=len(checkpoints),special_link_markers=len(markers),origin=origin,scope='All recovered floor and shell geometry loaded together. No native dynamic objects, hazards or verified wall/UV parity. Special links marked, not repaired.')
(BASE/'full_walk_audit.json').write_text(json.dumps(audit,indent=2));print(audit)
