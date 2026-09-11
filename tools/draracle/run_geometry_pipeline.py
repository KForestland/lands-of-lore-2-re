#!/usr/bin/env python3
"""Extract and verify pinned cave geometry and wall records from a local installation."""
import argparse,subprocess,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not (a.game_root/'DAT/L1_DC.MIX').is_file() or not (a.game_root/'LOLG.DAT').is_file():
        p.error('game-root must contain DAT/L1_DC.MIX and LOLG.DAT')
    steps=[('lol2_draracle_openings.py','geometry'),('lol2_verify_draracle_slopes.py','slopes'),('lol2_verify_draracle_connectors.py','connectors'),('lol2_extract_wall_records.py','walls')]
    for script,folder in steps:
        subprocess.run([sys.executable,str(Path(__file__).with_name(script)),'--game-root',str(a.game_root.resolve()),'--out',str((a.out/folder).resolve())],check=True)
    print('Geometry and wall-record checks complete. Texture/Godot generation is a separate, unfinished pipeline.')
if __name__=='__main__':main()
