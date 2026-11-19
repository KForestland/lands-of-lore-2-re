#!/usr/bin/env python3
"""Check a bounded wall projection block with synthetic host floating-point inputs."""
import argparse,json,struct,itertools
from pathlib import Path
import capstone
from lol2_native_height_lookup import recover

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();_,proof=recover(exe)
 page=proof['pages'][0x4028//4096];K=struct.unpack_from('<f',exe,page['file_offset']+0x4028%4096)[0];assert K==1/65536
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 instructions=list(md.disasm(exe[0x12766a+0x37000:0x1277a4+0x37000],0x12766a));cases=0
 for X,Y,Z,U,V,W in itertools.product([-2.,3.],[-1.,4.],[2.,8.],[-.5,1.],[-1.,.25],[-2.,.5]):
  for sx,sy in [(1.,1.),(2.,.5),(.5,2.),(4.,2.)]:
   mem={'dword ptr [0x4028]':K,'dword ptr [esp + 0x4b8]':sx/K,'dword ptr [esp + 0x4c0]':sy/K}
   for off,value in [(0x440,X),(0x444,Y),(0x448,Z),(0x4f0,U),(0x4ec,V),(0x4e4,W)]:mem[f'dword ptr [esp + {off:#x}]']=value
   stack=[]
   for i in instructions:
    op,t=i.mnemonic,i.op_str
    index=lambda operand:int(operand[3:-1])
    if op in ['fld','fild']:stack.insert(0,mem[t])
    elif op=='fxch':k=index(t);stack[0],stack[k]=stack[k],stack[0]
    elif op=='fmul':stack[0]*=stack[index(t)] if t.startswith('st(') else mem[t]
    elif op=='fmulp':k=index(t);stack[k]*=stack[0];stack.pop(0)
    elif op in ['fst','fstp']:
     mem[t]=f32(stack[0])
     if op=='fstp':stack.pop(0)
    elif op=='fchs':stack[0]=-stack[0]
    elif op=='fsubp':k=index(t);stack[k]-=stack[0];stack.pop(0)
    elif op not in ['mov','lea','push']:raise ValueError((i.address,op,t))
   expected={0x3cc:-W*X*sx*sy,0x3d0:U*Y*sx*sy,0x3d4:-U*W*sx*sy,0x3d8:W*Z*sy,0x3dc:-V*Y*sy,0x3e0:V*W*sy,0x3f0:sx*(V*X-U*Z)}
   assert not stack
   for off,value in expected.items():assert mem[f'dword ptr [esp + {off:#x}]']==value,(off,value)
   cases+=1
 a.out.mkdir(parents=True,exist_ok=True)
 report=dict(cases=cases,coefficients_per_case=7,mismatches=0,scope='Original x87 instruction order interpreted using host double arithmetic and float32 stores. Integer setup is supplied, not executed. Binary-exact synthetic inputs avoid rounding differences; no guest x87 control-state or arbitrary-input parity claim. Orientation setup and downstream rasterization remain open.')
 (a.out/'wall_projection.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
