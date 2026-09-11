#!/usr/bin/env python3
"""Static original-code target resolution with synthetic runtime tables, not placement binding."""
import argparse, hashlib, json
from pathlib import Path
import capstone
from lol2_verify_draracle_slopes import Replay, EXE_HASH

class ResolverReplay(Replay):
    def reg(self,n):
        if n in ('ah','bh','ch','dh'):return (self.regs['e'+n[0]+'x']>>8)&255
        if n in ('al','bl','cl','dl'):return self.regs['e'+n[0]+'x']&255
        return super().reg(n)
    def setreg(self,n,v):
        if n in ('ah','bh','ch','dh'):
            r='e'+n[0]+'x';self.regs[r]=(self.regs[r]&0xffff00ff)|((v&255)<<8)
        elif n in ('al','bl','cl','dl'):
            r='e'+n[0]+'x';self.regs[r]=(self.regs[r]&0xffffff00)|(v&255)
        else:super().setreg(n,v)
    def resolve(self,kind,target,entry=0x5fbc8):
        self.regs={r:0 for r in self.regs};self.regs['esp']=0x700000
        for off,v in [(0,0xdeadbeef),(4,kind),(8,target)]:self.writemem(0x700000+off,4,v)
        pc=entry;equal=below=False
        for _ in range(2000):
            i=self.instructions[pc];o=i.operands;m=i.mnemonic;n=pc+i.size
            if m=='push':
                v=self.get(i,o[0]);self.regs['esp']-=4;self.writemem(self.regs['esp'],4,v)
            elif m=='pop':
                self.put(i,o[0],self.readmem(self.regs['esp'],4));self.regs['esp']+=4
            elif m in ('call','ret'):
                if m=='call':
                    self.regs['esp']-=4;self.writemem(self.regs['esp'],4,n);n=self.get(i,o[0])
                else:
                    n=self.readmem(self.regs['esp'],4);self.regs['esp']+=4
                    if n==0xdeadbeef:
                        if self.regs['esp']!=0x700004:raise ValueError('Stack imbalance')
                        return self.regs['eax']
            elif m in ('mov','movsx'):
                v=self.get(i,o[1]);bits=o[1].size*8
                if m=='movsx' and v&(1<<(bits-1)):v-=1<<bits
                self.put(i,o[0],v)
            elif m=='lea':self.put(i,o[0],self.addr(i,o[1]))
            elif m in ('cmp','test'):
                a,b=self.get(i,o[0]),self.get(i,o[1]);equal=(a==b) if m=='cmp' else (a&b)==0;below=a<b if m=='cmp' else False
            elif m=='jmp':n=self.get(i,o[0])
            elif m=='inc':self.put(i,o[0],self.get(i,o[0])+1)
            elif m in ('je','jne','jb','jbe','ja','jae'):
                if {'je':equal,'jne':not equal,'jb':below,'jbe':below or equal,'ja':not below and not equal,'jae':not below}[m]:n=self.get(i,o[0])
            elif m in ('add','sub','xor','or','and','shl','sar','imul'):
                a,b=self.get(i,o[0]),self.get(i,o[1]);bits=o[0].size*8
                if m=='add':v=a+b
                elif m=='sub':v=a-b
                elif m=='xor':v=a^b
                elif m=='and':v=a&b
                elif m=='or':v=a|b
                elif m=='imul':v=a*b
                elif m=='shl':v=a<<(b&31)
                else:v=(a-(1<<bits) if a&(1<<(bits-1)) else a)>>(b&31)
                self.put(i,o[0],v)
            else:raise ValueError(f'Unsupported {pc:x}: {m}')
            pc=n
        raise ValueError('Instruction limit')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_HASH:raise ValueError('Executable changed')
    a.out.mkdir(parents=True,exist_ok=True);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={};proof=[]
    for start,end in [(0x5fbc8,0x5fd81),(0x5f878,0x5f8a5),(0x9d225,0x9d259),(0x66264,0x662b4)]:
        code=exe[start+0x37000:end+0x37000];ii=list(md.disasm(code,start));ins.update({i.address:i for i in ii})
        (a.out/f'code_{start:x}.bin').write_bytes(code)
        (a.out/f'code_{start:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ii)+'\n')
        proof.append(dict(va=hex(start),file_offset=start+0x37000,sha256=hashlib.sha256(code).hexdigest()))
    r=ResolverReplay(ins,b'');r.writemem(0xdb590,4,0x500000)
    # Table base, occupancy bitmap, capacity and stride. Deliberately synthetic.
    for off,v in [(0,0x600000),(4,0x510000),(8,1560),(12,56)]:r.writemem(0x500000+off,4,v)
    r.mem[0x510000:0x510000+195]=bytes([255])*195
    cases=[]
    for kind,target,expected in [(3,0,0x600000),(3,544,0x600000+544*56),(3,1559,0x600000+1559*56),(3,1560,0),(0x90,799,0x400000+799*44),(0x90,1953,0x400000+1953*44),(0,0,0),(5,544,0)]:
        actual=r.resolve(kind,target)
        if actual!=expected:raise ValueError((kind,target,actual,expected))
        cases.append(dict(kind=kind,target=target,actual=actual,expected=expected))
    r.mem[0x510000+544//8]&=~(1<<(544%8))
    if r.resolve(3,544)!=0:raise ValueError('Occupancy rejection failed')
    cases.append(dict(kind=3,target=544,occupied=False,actual=0,expected=0))
    report=dict(method='Bounded original x86 replay with synthetic tables; no live capture or serialized placement binding',executable_sha256=EXE_HASH,code=proof,cases=cases,mismatches=0,
        findings={'type_3':'Indexed occupied slot in table at global 0xdb590; base + index * stride, constructor passes stride 0x38 (56).','type_0x90':'Region array at 0x22d0c + index * 44.'},
        unresolved=['Which serialized records populate the type-3 table','Whether named action target 544 binds spatial record 544','Bridge chain template, animation and door geometry'])
    (a.out/'resolver_replay.json').write_text(json.dumps(report,indent=2)+'\n');print(f'{len(cases)} resolver cases passed; synthetic tables only')
if __name__=='__main__':main()
