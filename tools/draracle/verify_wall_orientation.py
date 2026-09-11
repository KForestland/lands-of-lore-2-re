#!/usr/bin/env python3
"""Replay wall orientation setup; transformed vertex inputs supplied by fixture."""
import argparse,json,struct
from pathlib import Path
import capstone
from lol2_verify_flat_wall_spans import WallReplay,signed
from lol2_native_height_lookup import recover
from lol2_extract_draracle_geometry import decode

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
STARTS=[0x126f8f,0x1270a1,0x127180,0x127260]
ENDS=[0x12705b,0x12716c,0x12724c,0x12732c]
class Orientation(WallReplay):
 def orientation(self,points,mode):
  self.regs.update(esp=0x700000,edx=0x700404)
  self.mem[0x700404:0x700434]=struct.pack('<12i',*(v for p in points for v in p))
  stack=[];pc=STARTS[mode];less=False
  for _ in range(100):
   if pc==ENDS[mode]:
    assert not stack
    return [struct.unpack_from('<f',self.mem,0x700000+off)[0] for off in [0x440,0x444,0x448,0x4f0,0x4ec]]
   i=self.instructions[pc];o=i.operands;op=i.mnemonic;nxt=pc+i.size
   if op=='mov':self.put(i,o[0],self.get(i,o[1]))
   elif op=='cmp':less=signed(self.get(i,o[0]),32)<signed(self.get(i,o[1]),32);equal=self.get(i,o[0])==self.get(i,o[1])
   elif op in ['jmp','jge','jle']:
    if op=='jmp' or (op=='jge' and not less) or (op=='jle' and (less or equal)):nxt=self.get(i,o[0])
   elif op in ['fild','fld']:
    value=signed(self.get(i,o[0]),32) if op=='fild' else struct.unpack('<f',struct.pack('<I',self.get(i,o[0])))[0]
    stack.insert(0,float(value))
   elif op=='fxch':k=int(i.op_str[3:-1]);stack[0],stack[k]=stack[k],stack[0]
   elif op=='fmul':
    value=stack[int(i.op_str[3:-1])] if i.op_str.startswith('st(') else struct.unpack('<f',struct.pack('<I',self.get(i,o[0])))[0]
    stack[0]*=value
   elif op=='fmulp':k=int(i.op_str[3:-1]);stack[k]*=stack[0];stack.pop(0)
   elif op=='fstp':self.put(i,o[0],struct.unpack('<I',struct.pack('<f',stack.pop(0)))[0])
   elif op=='fsubr':stack[0]=struct.unpack('<f',struct.pack('<I',self.get(i,o[0])))[0]-stack[0]
   else:raise ValueError((hex(pc),op))
   pc=nxt
  raise ValueError('Instruction limit')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--geometry-evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 exe=(a.game_root/'LOLG.DAT').read_bytes();_,proof=recover(exe);_,_,raw,_,_,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 ins={i.address:i for i in md.disasm(exe[0x126f8f+0x37000:0x12732c+0x37000],0x126f8f)}
 m=Orientation(ins,b'');page=proof['pages'][0x4028//4096];m.mem[0x4028:0x402c]=exe[page['file_offset']+0x4028%4096:page['file_offset']+0x4028%4096+4]
 assert struct.unpack_from('<f',m.mem,0x4028)[0]==1/65536
 groups=['flat_wall_spans','upper_lower_walls','sloped_middle_walls','sloped_upper_lower_walls','connector_middle_walls','special_upper_lower_walls'];results=[];seen=set();cases=0
 for group in groups:
  path=next(a.geometry_evidence.glob('*/'+group+'.json'))
  for row in json.loads(path.read_text())['results']:
   index=row['record'];assert index not in seen;seen.add(index);points=row['points_fixed']
   values=[]
   for mode in range(4):
    first,second=[(0,1),(1,0),(3,2),(2,3)][mode]
    p0,p1=points[first],points[second];h=(min if mode<2 else max)(p0[1],p1[1])
    expected=[f32(p0[0]/65536),f32(h/65536),f32(p0[2]/65536),f32(f32(p0[0]/65536)-p1[0]/65536),f32(f32(p0[2]/65536)-p1[2]/65536)]
    actual=m.orientation(points,mode);assert actual==expected,(index,mode,actual,expected);values.append(actual);cases+=1
   source_flags=raw[30093+index*8+6];mode=(source_flags>>5)&3
   results.append(dict(record=index,source_orientation=mode,basis=values[mode]))
 a.out.mkdir(parents=True,exist_ok=True);report=dict(cases=cases,records=len(results),mismatches=0,results=results,scope='Original orientation block instruction order with host doubles and float32 stores. Four modes tested per verified wall. Original world vertices supplied as synthetic transformed inputs; camera transform, clipping, source flag constructor replay and final Godot UV parity remain open.')
 (a.out/'wall_orientation.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
