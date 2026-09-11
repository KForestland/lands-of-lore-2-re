#!/usr/bin/env python3
"""Build diagnostic wall review assets from pinned local game files."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--game-root',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--godot-project',type=Path)
 a=p.parse_args();game=a.game_root.resolve();out=a.out.resolve();here=Path(__file__).resolve().parent
 for name in ['LOLG.DAT','DAT/L1_DC.MIX','CDCACHE.LST','CDCACHE.MIX']:
  if not (game/name).is_file():p.error('Required local input missing: '+name)
 if a.godot_project and not (a.godot_project/'scenes/lol2/wall_texture_review.tscn').is_file():p.error('Godot checkout must include wall_texture_review.tscn')
 out.mkdir(parents=True,exist_ok=True)
 def run(script,*args):subprocess.run([sys.executable,str(here/script),*map(str,args)],check=True)
 geometry=out/'geometry';textures=out/'textures';uvs=out/'uvs'
 run('run_geometry_pipeline.py','--game-root',game,'--out',geometry)
 run('verify_wall_visibility.py','--game-root',game,'--geometry-evidence',geometry,'--out',out/'visibility')
 run('verify_wall_camera_clip.py','--game-root',game,'--out',out/'camera_clip')
 run('verify_wall_facing.py','--game-root',game,'--out',out/'facing')
 run('verify_wall_edge_mask.py','--game-root',game,'--out',out/'edge_mask')
 run('extract_wall_texture_review.py','--game-root',game,'--out',textures)
 for script,name in [('verify_wall_uv_inputs.py','uv_inputs'),('verify_wall_projection.py','projection')]:run(script,'--game-root',game,'--out',out/name)
 for script,name in [('verify_wall_mip_ids.py','mip_ids'),('verify_wall_uv_wrap.py','addressing')]:run(script,'--game-root',game,'--textures',textures/'wall_textures.json','--out',out/name)
 run('verify_wall_orientation.py','--game-root',game,'--geometry-evidence',geometry,'--out',out/'orientation')
 run('export_flat_wall_uvs.py','--game-root',game,'--geometry-evidence',geometry,'--textures',textures/'wall_textures.json','--out',uvs)
 walls=json.loads((uvs/'flat_wall_uvs.json').read_text());materials={m['descriptor']:m for m in json.loads((textures/'wall_textures.json').read_text())['materials']}
 assets=out/'godot_assets';assets.mkdir(exist_ok=True);files={}
 def copy(source,name):
  shutil.copyfile(source,assets/name);files[name]=hashlib.sha256((assets/name).read_bytes()).hexdigest()
 copy(uvs/'flat_wall_uvs.json','walls.json')
 for k in sorted({w['descriptor'] for w in walls['walls']}):
  for im in materials[k]['images']:
   if im['level']==0:copy(textures/im['png'],f'material_{k}_variant_{im["variant"]}.png')
 if a.godot_project:
  destination=a.godot_project.resolve()/'assets/lol2/generated/wall_review';destination.mkdir(parents=True,exist_ok=True)
  for name in files:shutil.copyfile(assets/name,destination/name)
 report=dict(walls=walls['exported'],materials=len({w['descriptor'] for w in walls['walls']}),files=files,scope='Diagnostic inferred UVs and manual variants; orientation, transparency, animation timing and live parity remain unresolved. Requires matching populated cache. Original game inputs read only.')
 (out/'build_manifest.json').write_text(json.dumps(report,indent=2));print('Wall review ready:',report['walls'],'walls;',len(files),'asset files')
if __name__=='__main__':main()
