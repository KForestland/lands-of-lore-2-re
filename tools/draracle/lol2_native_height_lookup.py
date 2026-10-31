#!/usr/bin/env python3
"""Recover initialized LE data through the embedded MZ header and native page map."""
import argparse,json,struct
from pathlib import Path
from lol2_cache_named_wall_fixture import sha,require
from lol2_verify_draracle_slopes import EXE_HASH

def recover(exe):
 require(sha(exe)==EXE_HASH,'Executable changed');mz=0x39024;require(exe[mz:mz+2]==b'MZ','Embedded MZ missing')
 le=mz+struct.unpack_from('<I',exe,mz+0x3c)[0];require(exe[le:le+2]==b'LE','Embedded LE missing')
 u=lambda o:struct.unpack_from('<I',exe,le+o)[0]
 page_size=u(0x28);objects=le+u(0x40);count=u(0x44);page_map=le+u(0x48);data=mz+u(0x80)
 require(count==5 and page_size==4096,'Unexpected LE layout')
 size,base,flags,first,pages,reserved=struct.unpack_from('<6I',exe,objects+4*24)
 require(base==0x180000 and pages==0x22,'Unexpected initialized data object')
 chunks=[];mapping=[]
 for k in range(pages):
  entry=exe[page_map+(first-1+k)*4:page_map+(first+k)*4];number=int.from_bytes(entry[:3],'big');require(entry[3]==0 and number>0,'Unsupported LE page type');off=data+(number-1)*page_size;length=u(0x2c) if number==u(0x14) else page_size;require(0<length<=page_size,'Invalid page length');chunk=exe[off:off+length];require(len(chunk)==length,'Truncated initialized page');chunks.append(chunk);mapping.append(dict(object_page=k,physical_page=number,file_offset=off))
 initialized=b''.join(chunks);offset=0x143f0;lookup=initialized[offset:offset+257];require(len(lookup)==257,'Height table outside initialized data')
 witnesses=[dict(height=1<<k,shift=lookup[1<<k]) for k in range(9)];require(all(v['shift']==k for k,v in enumerate(witnesses)),'Native powers-of-two mismatch')
 return lookup,dict(executable_sha256=EXE_HASH,embedded_mz=mz,le_header=le,data_pages_file_offset=data,object_base=base,object_virtual_size=size,initialized_bytes=len(initialized),pages=mapping,height_table_object_offset=offset,height_table_sha256=sha(lookup),witnesses=witnesses,rotation_table_scope='0xDB650 lies beyond this object initialized bytes; no file-backed rotation values claimed.')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();lookup,report=recover((a.game_root/'LOLG.DAT').read_bytes());a.out.mkdir(parents=True,exist_ok=True);(a.out/'height_lookup.bin').write_bytes(lookup);(a.out/'height_lookup.json').write_text(json.dumps(report,indent=2)+'\n');print(report['witnesses'])
if __name__=='__main__':main()
