#!/usr/bin/env python3
"""Replay call-free native flat middle wall spans; defer slopes/special links."""
import argparse,json,struct,hashlib
from pathlib import Path
import capstone
from lol2_extract_draracle_geometry import decode,s16
from lol2_verify_target_resolver import ResolverReplay
from lol2_verify_draracle_slopes import EXE_HASH

def signed(v,bits):
 v&=(1<<bits)-1
 return v-(1<<bits) if v&(1<<(bits-1)) else v
class WallReplay(ResolverReplay):
 def execute(self,region,code,flags=0,vertical_offset=0):
  self.regs={r:0 for r in self.regs};self.regs['esp']=0x700000
  for off,value in [(0,0xdeadbeef),(4,0x600000),(8,0x400000+44*region),(12,0)]:self.writemem(0x700000+off,4,value)
  self.mem[0x600000:0x600046]=bytes(70);self.writemem(0x600042,1,code)
  self.writemem(0x60003e,2,flags);self.writemem(0x600031,1,vertical_offset)
  pc=0x114aa4;zero=less=below=False
  for _ in range(1000):
   i=self.instructions[pc];o=i.operands;op=i.mnemonic;nxt=pc+i.size
   if op=='push':
    v=self.get(i,o[0]);self.regs['esp']-=4;self.writemem(self.regs['esp'],4,v)
   elif op=='pop':self.put(i,o[0],self.readmem(self.regs['esp'],4));self.regs['esp']+=4
   elif op=='call':
    destination=self.get(i,o[0])
    if destination not in [0xf4504,0xf4590,0xf49fc]:raise ValueError('Unapproved helper call')
    self.regs['esp']-=4;self.writemem(self.regs['esp'],4,nxt);nxt=destination
   elif op=='ret':
    destination=self.readmem(self.regs['esp'],4)
    if destination!=0xdeadbeef:
     self.regs['esp']+=4;pc=destination;continue
    assert self.readmem(self.regs['esp'],4)==0xdeadbeef
    return [list(struct.unpack_from('<3i',self.mem,0x600000+j*12)) for j in range(4)],bool(self.readmem(0x600044,1))
   elif op in ['mov','movzx']:self.put(i,o[0],self.get(i,o[1]))
   elif op=='lea':self.put(i,o[0],self.addr(i,o[1]))
   elif op in ['cmp','test']:
    a,b=self.get(i,o[0]),self.get(i,o[1]);bits=o[0].size*8;mask=(1<<bits)-1
    zero=((a-b)&mask)==0 if op=='cmp' else ((a&b)&mask)==0
    less=signed(a,bits)<signed(b,bits) if op=='cmp' else signed(a&b,bits)<0
    below=(a&mask)<(b&mask) if op=='cmp' else False
   elif op=='setne':self.put(i,o[0],int(not zero))
   elif op.startswith('j'):
    take={'jmp':True,'je':zero,'jne':not zero,'jl':less,'jge':not less,'jle':less or zero,'jg':not less and not zero,'jb':below,'jbe':below or zero,'ja':not below and not zero}.get(op)
    if take is None:raise ValueError(op)
    if take:nxt=self.get(i,o[0])
   elif op in ['add','sub','and','xor','shl','shr','sar','inc','dec']:
    a=self.get(i,o[0]);b=1 if op in ['inc','dec'] else self.get(i,o[1]);bits=o[0].size*8
    if op in ['add','inc']:v=a+b
    elif op in ['sub','dec']:v=a-b
    elif op=='and':v=a&b
    elif op=='xor':v=a^b
    elif op=='shl':v=a<<(b&31)
    elif op=='shr':v=(a&((1<<bits)-1))>>(b&31)
    else:v=signed(a,bits)>>(b&31)
    self.put(i,o[0],v);zero=(v&((1<<bits)-1))==0
    # Only logical-operation flags are used by selected paths; arithmetic branches have CMP.
    if op in ['and','xor']:less=signed(v,bits)<0;below=False
   else:raise ValueError(f'Unsupported instruction {pc:x}: {op}')
   pc=nxt
  raise ValueError('Instruction limit')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 source=(a.game_root/'DAT/L1_DC.MIX').read_bytes();_,e,raw,verts,records,regions=decode(source)
 exe=(a.game_root/'LOLG.DAT').read_bytes();assert hashlib.sha256(exe).hexdigest()==EXE_HASH
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 code=exe[0x114aa4+0x37000:0x115119+0x37000];instructions={i.address:i for i in md.disasm(code,0x114aa4)}
 m=WallReplay(instructions,raw[54509:54509+1954*44]);m.writemem(0x22d04,4,0x500000)
 m.mem[0x500000:0x500000+len(verts)*8]=b''.join(struct.pack('<2i',*v) for v in verts)
 out=[];deferred=[]
 for rid,r in enumerate(records):
  for index in range(r[13],r[13]+(r[15]&255)):
   d=raw[30093+index*8:30101+index*8];c=d[5]&31;edge=c&3;neighbor=r[2+edge];nr=records[neighbor] if neighbor!=65535 else None
   if c&12 not in [4,12] or r[14]&0xbc or (nr and nr[14]&0x9c):
    deferred.append(index);continue
   low=s16(r[10]);high=s16(r[11])
   if nr:low=max(low,s16(nr[10]));high=min(high,s16(nr[11]))
   p0,p1=[verts[r[6+k]] for k in [edge,(edge+1)%4]]
   expected=[[p0[0],high*65536,p0[1]],[p1[0],high*65536,p1[1]],[p1[0],low*65536,p1[1]],[p0[0],low*65536,p0[1]]]
   expected_active=p0!=p1 and low<high
   actual,active=m.execute(rid,c)
   if actual!=expected or active!=expected_active:raise ValueError((index,actual,expected,active,expected_active))
   out.append(dict(record=index,region=rid,edge=edge,neighbor=None if nr is None else neighbor,surface_code=c,descriptor_candidate=struct.unpack_from('<h',d)[0],points_fixed=actual,active=active))
 synthetic=0
 square=[(0,0),(128*65536,0),(128*65536,128*65536),(0,128*65536)]
 m.mem[0x500000:0x500020]=b''.join(struct.pack('<2i',*v) for v in square)
 for edge in range(4):
  for span in [4,12]:
   for neighbor_heights in [None,(-80,80),(20,60),(120,160),(-200,-150)]:
    row=[0]*22;row[2:6]=[65535]*4;row[6:10]=[0,1,2,3];row[10]=(-100)&65535;row[11]=100
    lower,upper=-100,100
    if neighbor_heights is not None:
     row[2+edge]=1;other=row.copy();other[10]=neighbor_heights[0]&65535;other[11]=neighbor_heights[1]&65535
     m.mem[0x40002c:0x400058]=struct.pack('<22H',*other)
     lower=max(lower,neighbor_heights[0]);upper=min(upper,neighbor_heights[1])
    m.mem[0x400000:0x40002c]=struct.pack('<22H',*row)
    a0,a1=square[edge],square[(edge+1)%4]
    expected=[[a0[0],upper*65536,a0[1]],[a1[0],upper*65536,a1[1]],[a1[0],lower*65536,a1[1]],[a0[0],lower*65536,a0[1]]]
    actual,active=m.execute(0,edge|span)
    assert actual==expected and active==(lower<upper)
    synthetic+=1
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'native_wall_shape.bin').write_bytes(code)
 (a.out/'native_wall_shape.asm').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in instructions.values()))
 report=dict(synthetic_cases=synthetic,cases=len(out),active=sum(x['active'] for x in out),deferred=len(deferred),mismatches=0,results=out,scope='Call-free original wall routine replay for flat class 4/12 surfaces; original region/vertex inputs, supplied runtime pointers. Independent interval-intersection comparison. Slopes, child records, special connectors and classes 0/8 deferred. No UV or loader/global proof.')
 (a.out/'flat_wall_spans.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='results'})
if __name__=='__main__':main()
