#!/usr/bin/env python3
"""Replay original connector-side and endpoint selection on all exceptional links."""
import argparse,json,hashlib,struct
from pathlib import Path
import capstone
from lol2_verify_draracle_slopes import Replay, EXE_HASH
from lol2_extract_draracle_geometry import decode
from lol2_draracle_openings import interpret

class ConnectorReplay(Replay):
    def execute(self,start,stop):
        pc=start
        for _ in range(150):
            if pc==stop:return
            i=self.instructions[pc];o=i.operands;m=i.mnemonic;next_pc=pc+i.size
            if m=='mov':self.put(i,o[0],self.get(i,o[1]))
            elif m=='lea':self.put(i,o[0],self.addr(i,o[1]))
            elif m=='cmp':self.equal=self.get(i,o[0])==self.get(i,o[1])
            elif m=='jne':
                if not self.equal:next_pc=self.get(i,o[0])
            elif m=='jmp':next_pc=self.get(i,o[0])
            elif m=='inc':self.put(i,o[0],self.get(i,o[0])+1)
            elif m=='idiv':
                n=(self.regs['edx']<<32)|self.regs['eax']
                if n&(1<<63):n-=1<<64
                d=self.get(i,o[0]);d=d-(1<<32) if d&(1<<31) else d
                if d==0:raise ValueError('Division by zero')
                q=abs(n)//abs(d)*(1 if (n>=0)==(d>=0) else -1)
                self.regs['eax']=q&0xffffffff;self.regs['edx']=(n-q*d)&0xffffffff
            elif m in ['add','sub','xor','and','shl','shr','sar']:
                a,b=self.get(i,o[0]),self.get(i,o[1]);bits=o[0].size*8
                if m=='add':v=a+b
                elif m=='sub':v=a-b
                elif m=='xor':v=a^b
                elif m=='and':v=a&b
                elif m=='shl':v=a<<(b&31)
                elif m=='shr':v=(a&((1<<bits)-1))>>(b&31)
                else:v=(a-(1<<bits) if a&(1<<(bits-1)) else a)>>(b&31)
                self.put(i,o[0],v)
            else:raise ValueError(f'Unsupported instruction {pc:x}: {m}')
            pc=next_pc
        raise ValueError('Instruction limit')
    def select(self,connector,caller):
        self.regs={r:0 for r in self.regs};self.regs['esp']=0x700000
        self.regs['ecx']=0x400000+44*connector
        self.writemem(0x700034,4,0x400000+44*caller)
        self.execute(0x114b08,0x114b45)
        side=self.regs['edx'];self.regs['ebx']=0x600000
        self.execute(0x114b7a,0x114bc8)
        vals=[struct.unpack_from('<i',self.mem,0x600000+o)[0] for o in [0x18,0x20,0x24,0x2c]]
        return side,[vals[:2],vals[2:]]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_HASH:raise ValueError('Unpinned executable')
    _,_,raw,verts,records,regions=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes());report,_=interpret(verts,records,regions)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={};proof=[]
    a.out.mkdir(parents=True,exist_ok=True)
    for start,end in [(0x114b08,0x114b45),(0x114b7a,0x114bca),(0xf3ef0,0xf3fdb),(0xf3b90,0xf3ca9)]:
        code=exe[start+0x37000:end+0x37000];decoded=list(md.disasm(code,start));ins.update({i.address:i for i in decoded})
        (a.out/f'code_{start:x}.bin').write_bytes(code)
        (a.out/f'code_{start:x}.txt').write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in decoded)+'\n')
        proof.append(dict(va=hex(start),file_offset=start+0x37000,sha256=hashlib.sha256(code).hexdigest()))
    machine=ConnectorReplay(ins,raw[54509:140485]);vertex_data=raw[5300:26860]
    machine.mem[0x500000:0x500000+len(vertex_data)]=vertex_data;machine.writemem(0x22d04,4,0x500000)
    cases=[]
    for x in report['exceptional_links']:
        if x['kind']!='flag16_connector':continue
        side,pts=machine.select(x['connector'],x['caller'])
        if side!=x['connector_side'] or pts!=[list(p) for p in x['selected_endpoints_fixed']]:raise ValueError('Original selection differs')
        cases.append(dict(source=x['source'],target=x['target'],selected_side=side,endpoints_fixed=pts))
    result=dict(method='Bounded original-x86 instruction replay; not live runtime',executable_sha256=EXE_HASH,
        cases=len(cases),fixed_coordinate_values=len(cases)*4,mismatches=0,code=proof,results=cases)
    (a.out/'connector_replay.json').write_text(json.dumps(result,indent=2)+'\n');print('Original connector selection:',len(cases),'cases,',len(cases)*4,'coordinate values; zero mismatches')
if __name__=='__main__':main()
