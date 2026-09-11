#!/usr/bin/env python3
"""Replay all three renderer wall UV addressing modes."""
import argparse,json
from pathlib import Path
import capstone
from lol2_verify_flat_wall_spans import WallReplay,signed
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_cache_named_wall_fixture import sha,require
from wall_uv_addressing import address_uv

def execute(m,u,v,uo,vo,level,width,height,flags=8):
 m.regs.update(ebx=u&0xffffffff,edx=v&0xffffffff,ecx=level,ebp=0xfffe0000,esi=0x600000)
 for address,value in [(0x60003c,uo<<16),(0x600040,vo<<16),(0x14550,width<<16),(0x14554,height<<16)]:m.writemem(address,4,value)
 m.writemem(0x600000,4,flags)
 pc=0x12d4d1;negative=False;zero=False
 for _ in range(10000):
  if pc==0x12d584:return m.regs['ebx'],m.regs['edx'],m.regs['ebp']
  i=m.instructions[pc];o=i.operands;op=i.mnemonic;nxt=pc+i.size
  if op=='mov':m.put(i,o[0],m.get(i,o[1]))
  elif op=='test':negative=False;zero=(m.get(i,o[0])&m.get(i,o[1]))==0
  elif op=='cmp':a,b=m.get(i,o[0]),m.get(i,o[1]);negative=signed(a,32)<signed(b,32);zero=a==b
  elif op in ['jge','jns','je','jne','jl','jmp']:
   if {'jge':not negative,'jns':not negative,'je':zero,'jne':not zero,'jl':negative,'jmp':True}[op]:nxt=m.get(i,o[0])
  elif op in ['xor','add','sub','shr','sar','dec']:
   a=m.get(i,o[0]);b=1 if op=='dec' else m.get(i,o[1])
   value={'dec':lambda:a-1,'xor':lambda:a^b,'add':lambda:a+b,'sub':lambda:a-b,'shr':lambda:a>>(b&31),'sar':lambda:signed(a,32)>>(b&31)}[op]()
   m.put(i,o[0],value);negative=signed(value,32)<0;zero=(value&0xffffffff)==0
  else:raise ValueError((pc,op))
  pc=nxt
 raise ValueError('Wrap instruction limit')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--textures',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed');md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 ins={i.address:i for i in md.disasm(exe[0x12d4d1+0x37000:0x12d584+0x37000],0x12d4d1)};m=WallReplay(ins,b'');cases=0
 layouts={(im['level'],im['width'],im['height']) for mat in json.loads(a.textures.read_text())['materials'] for im in mat['images']}
 for level,w,h in sorted(layouts):
  for u,v in [(-65536,-1),(0,0),(65535,65536),(w*65536*(1<<level),h*65536*(1<<level)),(123456789,98765432)]:
   for uo,vo in [(0,0),(255,255),(1,127)]:
    for flags in [0,8,16,24]:
     actual=execute(m,u,v,uo,vo,level,w,h,flags)
     expected=(*address_uv(u,v,uo,vo,level,w,h,flags),(-131072>>level)&0xffffffff)
     assert actual==expected,(flags,level,w,h,actual,expected);cases+=1
 a.out.mkdir(parents=True,exist_ok=True);report=dict(cases=cases,layouts=len(layouts),mismatches=0,scope='Original dispatch and three addressing branches replayed, including bit8 precedence over bit16. Synthetic non-overflow coordinates across extracted mip dimensions. Independent addressing port verified; projection, filtering and complete Godot UV parity remain open.')
 (a.out/'wall_uv_wrap.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
