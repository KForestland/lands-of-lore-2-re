#!/usr/bin/env python3
"""Replay native floor preset setup; UV normalization remains unresolved."""
import argparse,json,struct
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import sha,require
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_target_resolver import ResolverReplay
from lol2_extract_draracle_geometry import decode,u32

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed');source=(a.game_root/'DAT/L1_DC.MIX').read_bytes();entries,*_=decode(source);e=entries[0];b=source[e['offset']:e['offset']+e['size']];start,count=u32(b,4),u32(b,0x3c)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={};a.out.mkdir(parents=True,exist_ok=True);code=[]
 for x,y in [(0x67754,0x677d4),(0x127ec3,0x127f7f),(0x128c58,0x128c8e)]:
  raw=exe[x+0x37000:y+0x37000];ii=list(md.disasm(raw,x));ins.update({i.address:i for i in ii});(a.out/f'code_{x:x}.bin').write_bytes(raw);(a.out/f'code_{x:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ii)+'\n');code.append(dict(va=hex(x),file_offset=x+0x37000,sha256=sha(raw)))
 machine=ResolverReplay(ins,b'');results=[]
 for k in range(count):
  d=b[start+k*24:start+(k+1)*24];name=b[start+count*24+k*22:start+count*24+(k+1)*22].split(b'\0')[0].decode('ascii');mode=bool(d[19]);angle=struct.unpack_from('<H',d,6)[0]
  offset_x,offset_y=(struct.unpack_from('<h',d,j)[0]*65536 if mode else 0 for j in [8,10]);bytes30_31=[0,0] if mode else [d[8],d[10]]
  for initial_flags in [0,0x1234]:
   machine.mem[0x500000:0x500018]=d;machine.mem[0x600000:0x600080]=bytes([0xcd])*128;machine.writemem(0x60003e,2,initial_flags);machine.resolve(0x500000,0x600000,entry=0x67754)
   actual=dict(angle_word=machine.readmem(0xfe464,2),offset_x_fixed=struct.unpack_from('<i',machine.mem,0xfe468)[0],offset_y_fixed=struct.unpack_from('<i',machine.mem,0xfe46c)[0],object_bytes_30_31=list(machine.mem[0x600030:0x600032]),object_flags_3e=machine.readmem(0x60003e,2))
   expected=dict(angle_word=angle,offset_x_fixed=offset_x,offset_y_fixed=offset_y,object_bytes_30_31=bytes30_31,object_flags_3e=(initial_flags|(d[20]<<14))&65535)
   require(actual==expected,f'Preset {k} setup mismatch');results.append(dict(preset=k,name=name,coordinate_mode_byte=d[19],initial_flags=initial_flags,**actual))
 report=dict(executable_sha256=EXE_HASH,method='Original instruction replay of complete 0x67754 setup routine with original preset records and synthetic destination object',cases=len(results),mismatches=0,code=code,results=results,scope='Angle word and offset/byte setup proven. Consumers subtract offsets and use quarter-turn-separated lookup indices. Final UV axes, normalization, wrapping and dynamic behavior still need proof.')
 (a.out/'setup_replay.json').write_text(json.dumps(report,indent=2)+'\n');print(len(results),'native setup cases pass')
if __name__=='__main__':main()
