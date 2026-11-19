#!/usr/bin/env python3
"""Recover stored wall renderer slots; leave relocation and live selection explicit."""
import argparse,json,struct
from pathlib import Path
from lol2_native_height_lookup import recover

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();_,provenance=recover(exe)
 data=b''.join(exe[x['file_offset']:x['file_offset']+4096] for x in provenance['pages'])[:provenance['initialized_bytes']]
 le=provenance['le_header'];u=lambda o:struct.unpack_from('<I',exe,le+o)[0]
 objects=le+u(0x40);page_map=le+u(0x48)
 data_first=struct.unpack_from('<I',exe,objects+4*24+12)[0]
 page_index=data_first-1+5
 begin,end=struct.unpack_from('<2I',exe,le+u(0x68)+page_index*4)
 cursor=le+u(0x6c)+begin;limit=le+u(0x6c)+end;fixups={}
 while cursor<limit:
  start=cursor;source,flags,offset,obj=struct.unpack_from('<BBhB',exe,cursor)
  assert source==7 and flags in [0,16], 'Unsupported fixup record'
  width=4 if flags==16 else 2
  target=int.from_bytes(exe[cursor+5:cursor+5+width],'little');cursor+=5+width
  assert offset not in fixups
  fixups[offset]=(obj,target,start)
 assert cursor==limit
 tables=[]
 for base in [0x5d18,0x5da4]:
  slot=base+0x28;page=provenance['pages'][slot//4096]
  value=struct.unpack_from('<I',data,slot)[0]
  obj,target,fixup_file=fixups[slot%4096];assert obj==2 and target==value
  size,virtual,flags,first,pages,_=struct.unpack_from('<6I',exe,objects+(obj-1)*24)
  assert target<size and target//4096<pages
  entry=exe[page_map+(first-1+target//4096)*4:page_map+(first+target//4096)*4]
  assert entry[3]==0
  physical=int.from_bytes(entry[:3],'big')
  code_file=provenance['data_pages_file_offset']+(physical-1)*4096+target%4096
  assert exe[code_file:code_file+4]==bytes.fromhex('53565755')
  tables.append(dict(table_object_offset=base,callback_slot=slot,stored_value=value,file_offset=page['file_offset']+slot%4096,fixup_file_offset=fixup_file,target_object=obj,target_object_offset=target,target_preferred_linear=virtual+target,code_file_offset=code_file,analysis_address=code_file-0x37000))
 assert [x['stored_value'] for x in tables]==[0xcdc08,0xdfc88]
 report=dict(tables=tables,provenance=provenance,scope='Pinned internal 32-bit offset fixups resolved through target object and physical page map. Analysis addresses use existing file-minus-37000 convention, not live guest addresses. Active renderer and UV semantics unresolved.')
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'wall_dispatch.json').write_text(json.dumps(report,indent=2));print(tables)
if __name__=='__main__':main()
