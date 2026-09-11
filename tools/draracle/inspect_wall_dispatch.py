#!/usr/bin/env python3
"""Recover stored wall renderer slots; leave relocation and live selection explicit."""
import argparse,json,struct
from pathlib import Path
from lol2_native_height_lookup import recover

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();_,provenance=recover(exe)
 data=b''.join(exe[x['file_offset']:x['file_offset']+4096] for x in provenance['pages'])[:provenance['initialized_bytes']]
 tables=[]
 for base in [0x5d18,0x5da4]:
  slot=base+0x28;page=provenance['pages'][slot//4096]
  value=struct.unpack_from('<I',data,slot)[0]
  tables.append(dict(table_object_offset=base,callback_slot=slot,stored_value=value,file_offset=page['file_offset']+slot%4096))
 assert [x['stored_value'] for x in tables]==[0xcdc08,0xdfc88]
 report=dict(tables=tables,provenance=provenance,scope='Stored initialized-data values only. LE fixups, runtime callback addresses, active renderer and UV semantics unresolved. Do not disassemble stored values as resolved code addresses.')
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_dispatch.json').write_text(json.dumps(report,indent=2));print(tables)
if __name__=='__main__':main()
