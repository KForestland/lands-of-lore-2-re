#!/usr/bin/env python3
"""Build diagnostic full-cave Godot assets from pinned original game and cache files."""
import argparse,hashlib,json,platform,shutil,subprocess,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True,help='Local evidence output directory')
    p.add_argument('--godot-project',type=Path,help='Optional destination Godot checkout; otherwise export to out/godot_assets')
    a=p.parse_args();game=a.game_root.resolve();out=a.out.resolve();here=Path(__file__).resolve().parent
    for name in ['DAT/L1_DC.MIX','LOLG.DAT','CDCACHE.LST','CDCACHE.MIX']:
        if not (game/name).is_file():p.error('Required local input missing: '+name)
    if platform.machine().lower() not in ['x86_64','amd64'] or not shutil.which('cc'):
        p.error('The recovered x87 initializer requires an x86-64 host and a C compiler (cc).')
    if a.godot_project and not (a.godot_project/'project.godot').is_file():p.error('godot-project must be an existing Godot checkout')
    out.mkdir(parents=True,exist_ok=True)
    def folder(name):return out/('draracle_'+name+'_2026-09-11')
    steps=[('lol2_draracle_openings.py','openings',[]),('lol2_extract_cave_materials.py','materials',[]),('lol2_extract_bound_floor_variants.py','floor_variants',[]),('lol2_extract_surface_presets.py','surface_presets',[]),('lol2_bind_floor_materials.py','floor_bindings',['--presets',str(folder('surface_presets')/'floor_presets.json')]),('lol2_verify_floor_setup.py','floor_setup',[]),('lol2_recover_rotation_table.py','rotation_table',[])]
    for script,name,extra in steps:
        subprocess.run([sys.executable,str(here/script),'--game-root',str(game),'--out',str(folder(name)),*extra],check=True)
    assets=(a.godot_project.resolve()/'assets/lol2/generated/original_floors') if a.godot_project else out/'godot_assets'
    subprocess.run([sys.executable,str(here/'godot_export/import_original_floors.py'),'--evidence-root',str(out),'--out',str(assets)],check=True)
    for script in ['build_traversal_fixtures.py','build_connected_walk.py','build_full_walk.py']:
        subprocess.run([sys.executable,str(here/'godot_export'/script),'--out',str(assets),'--geometry',str(folder('openings')/'geometry_v2.json'),'--all'],check=True)
    # The subset audit also expects the original six-pair fixture file.
    subprocess.run([sys.executable,str(here/'godot_export/build_traversal_fixtures.py'),'--out',str(assets),'--geometry',str(folder('openings')/'geometry_v2.json')],check=True)
    files={str(f.relative_to(assets)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(assets.iterdir()) if f.is_file()}
    report=dict(scope='Diagnostic recovered static cave, not native rendering/gameplay parity. Requires a matching populated stored cache; does not reconstruct the cache from retail archives.',assets=str(assets),files=files,full_map=json.loads((assets/'full_walk_audit.json').read_text()))
    (out/'build_manifest.json').write_text(json.dumps(report,indent=2))
    print('Full cave assets built:',assets)
if __name__=='__main__':main()
