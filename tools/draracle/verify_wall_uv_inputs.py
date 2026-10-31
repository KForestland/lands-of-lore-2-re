#!/usr/bin/env python3
"""Check native wall UV input conversion and recover scale constants, not projection."""
import argparse,json,struct
from pathlib import Path
import capstone
from lol2_extract_draracle_geometry import decode
from lol2_native_height_lookup import recover
from lol2_verify_spatial_constructor import ConstructorReplay

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();_,proof=recover(exe)
 _,_,raw,_,regions,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 start,end=0x12759c,0x1275ba;code=exe[start+0x37000:end+0x37000]
 ins={i.address:i for i in md.disasm(code,start)};m=ConstructorReplay(ins,b'');m.regs.update(ecx=0x600000,esp=0x700000)
 def check(u,v):
  m.writemem(0x600030,1,u);m.writemem(0x600031,1,v);m.span(start,end)
  actual=[m.readmem(0x7003fc,4),m.readmem(0x700400,4)]
  assert actual==[u<<16,v<<16]
  return actual
 results=[]
 for rid,r in enumerate(regions):
  for k in range(r[13],r[13]+(r[15]&255)):
   d=raw[30093+k*8:30101+k*8]
   results.append(dict(record=k,region=rid,offsets_fixed=check(d[2],d[3]),scale_mode=d[7]&3))
 for value in range(256):check(value,255-value);check(value,value)
 scales=[]
 for mode,constant,positive,negative in [(0,0x403c,0x127418,0x127408),(1,None,0x12746d,0x12745d),(2,0x4034,0x1274cc,0x1274bc),(3,0x402c,0x12752b,0x12751b)]:
  factor=1.0;location=None
  if constant is not None:
   page=proof['pages'][constant//4096];location=page['file_offset']+constant%4096;factor=struct.unpack_from('<d',exe,location)[0]
  values=[]
  for address in [positive,negative]:
   i=next(md.disasm(exe[address+0x37000:address+0x37010],address))
   assert i.mnemonic=='mov' and i.op_str.startswith('dword ptr [esp + 0x4e4],')
   values.append(struct.unpack('<f',struct.pack('<I',i.operands[1].imm&0xffffffff))[0])
  assert values==[1/factor,-1/factor]
  scales.append(dict(mode=mode,length_multiplier=factor,signed_vertical_coefficients=values,constant_file_offset=location))
 assert [x['length_multiplier'] for x in scales]==[2,1,.5,.25]
 a.out.mkdir(parents=True,exist_ok=True)
 report=dict(source_cases=len(results),synthetic_cases=512,mismatches=0,scales=scales,results=results,scope='Original integer offset-conversion instructions replayed. Scale constants and immediate coefficients checked from executable bytes. Inputs use serialized offsets; constructor-adjusted offsets, x87 normalization, orientation and final projection are not replayed here.')
 (a.out/'wall_uv_inputs.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
