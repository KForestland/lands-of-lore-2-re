#!/usr/bin/env python3
"""Reproduce recovered rotation initializer with original constants and host x87."""
import argparse,json,struct,math,subprocess
from pathlib import Path
import capstone
from lol2_native_height_lookup import recover
from lol2_cache_named_wall_fixture import sha,require

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();exe=(a.game_root/'LOLG.DAT').read_bytes();_,proof=recover(exe);a.out.mkdir(parents=True,exist_ok=True)
 constants=bytearray();locations=[]
 for offset in [0x344c,0x3454]:
  page=proof['pages'][offset//4096];fileoff=page['file_offset']+offset%4096;constants.extend(exe[fileoff:fileoff+8]);locations.append(dict(object_offset=offset,file_offset=fileoff))
 step,scale=struct.unpack('<2d',constants);require(scale==65536,'Unexpected initializer scale');(a.out/'constants.bin').write_bytes(constants)
 compiler=['cc','-O2','-Wall','-Wextra',str(Path(__file__).with_name('lol2_x87_sine_table.c')),'-o',str(a.out/'x87_sine_table')];subprocess.run(compiler,check=True)
 table=subprocess.check_output([str(a.out/'x87_sine_table'),str(a.out/'constants.bin')]);require(len(table)==16384,'Generated table extent');values=struct.unpack('<4096i',table);comparison=[math.trunc(math.sin(i*step)*scale) for i in range(4096)];mismatches=[i for i in range(4096) if values[i]!=comparison[i]];require(not mismatches,'Host x87 and independent libm port disagree')
 (a.out/'rotation_table.bin').write_bytes(table);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);code=[]
 for x,y in [(0xfb6c4,0xfb718),(0x158ede,0x158efb)]:
  raw=exe[x+0x37000:y+0x37000];(a.out/f'code_{x:x}.bin').write_bytes(raw);(a.out/f'code_{x:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in md.disasm(raw,x))+'\n');code.append(dict(va=hex(x),file_offset=x+0x37000,sha256=sha(raw)))
 report=dict(executable_sha256=proof['executable_sha256'],constants=locations,angle_step=step,scale=scale,table_sha256=sha(table),entries=4096,host_x87_vs_libm_mismatches=0,code=code,method='Disassembly-backed port using original double constants; host x87 FSIN with default extended precision and truncation, cross-checked against Python libm. Not original binary execution or live guest memory capture.',scope='Runtime table initializer recovered. Host/platform FSIN and startup control-state equivalence to guest remain to verify. Final projection and Godot UV integration remain open.')
 (a.out/'rotation_table.json').write_text(json.dumps(report,indent=2)+'\n');print('4096 entries agree between host x87 and independent libm; original step:',step)
if __name__=='__main__':main()
