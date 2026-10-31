#!/usr/bin/env python3
"""Bounded instruction replay of two original corner-height routines.
Capstone decodes original executable bytes; this deliberately small interpreter
rejects any unsupported instruction. This is static replay, not a live capture.
"""
import argparse, hashlib, json, struct
from pathlib import Path
import capstone
from capstone.x86_const import X86_OP_REG, X86_OP_IMM, X86_OP_MEM
from lol2_extract_draracle_geometry import decode, slope_corners, s16

EXE_HASH='b27a35341c6e877e40b1540b6482748e7a750c605fefe6452431b18a5d766775'
ROUTINES=[(False,0xf4504,1225988,137),(True,0xf4590,1226128,132)]

class Replay:
    def __init__(self, instructions, records):
        self.instructions=instructions
        self.regs={r:0 for r in ['eax','ebx','ecx','edx','esi','edi','ebp','esp']}
        self.mem=bytearray(0x800000)
        self.mem[0x400000:0x400000+len(records)]=records
        struct.pack_into('<I',self.mem,0x22d0c,0x400000)
        self.equal=False
    def reg(self,name):
        if name in ['ax','bx','cx','dx','si','di','bp','sp']:return self.regs['e'+name]&65535
        return self.regs[name]
    def setreg(self,name,v):
        if name in ['ax','bx','cx','dx','si','di','bp','sp']:
            self.regs['e'+name]=(self.regs['e'+name]&0xffff0000)|(v&65535)
        else:self.regs[name]=v&0xffffffff
    def addr(self,ins,o):
        m=o.mem
        return ((self.reg(ins.reg_name(m.base)) if m.base else 0)+(self.reg(ins.reg_name(m.index))*m.scale if m.index else 0)+m.disp)&0xffffffff
    def readmem(self,a,n):
        if not 0<=a<=len(self.mem)-n:raise ValueError('Replay memory bounds')
        return int.from_bytes(self.mem[a:a+n],'little')
    def writemem(self,a,n,v):
        if not 0<=a<=len(self.mem)-n:raise ValueError('Replay memory bounds')
        self.mem[a:a+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little')
    def get(self,i,o):
        if o.type==X86_OP_IMM:return o.imm
        if o.type==X86_OP_REG:return self.reg(i.reg_name(o.reg))
        if o.type==X86_OP_MEM:return self.readmem(self.addr(i,o),o.size)
        raise ValueError('Unsupported operand')
    def put(self,i,o,v):
        if o.type==X86_OP_REG:self.setreg(i.reg_name(o.reg),v)
        elif o.type==X86_OP_MEM:self.writemem(self.addr(i,o),o.size,v)
        else:raise ValueError('Unsupported destination')
    def run(self,entry,region):
        self.regs={r:0 for r in self.regs};self.regs['esp']=0x700000
        self.writemem(0x700000,4,0xdeadbeef)
        self.writemem(0x700004,4,0x400000+region*44)
        self.writemem(0x700008,4,0x600000)
        self.mem[0x600000:0x600010]=bytes([0xcc])*16
        pc=entry
        for _ in range(150):
            i=self.instructions[pc];o=i.operands;next_pc=pc+i.size;m=i.mnemonic
            if m=='push':
                v=self.get(i,o[0]);self.regs['esp']-=4;self.writemem(self.regs['esp'],4,v)
            elif m=='pop':
                self.put(i,o[0],self.readmem(self.regs['esp'],4));self.regs['esp']+=4
            elif m=='ret':
                if self.readmem(self.regs['esp'],4)!=0xdeadbeef:raise ValueError('Unbalanced stack')
                return [v//65536 for v in struct.unpack_from('<4i',self.mem,0x600000)]
            elif m=='mov':self.put(i,o[0],self.get(i,o[1]))
            elif m=='lea':self.put(i,o[0],self.addr(i,o[1]))
            elif m=='cmp':self.equal=self.get(i,o[0])==self.get(i,o[1])
            elif m=='jmp':next_pc=self.get(i,o[0])
            elif m=='jne':
                if not self.equal:next_pc=self.get(i,o[0])
            elif m in ['add','sub','and','xor','shl','shr','sar']:
                a,c=self.get(i,o[0]),self.get(i,o[1]);bits=o[0].size*8
                if m=='add':v=a+c
                elif m=='sub':v=a-c
                elif m=='and':v=a&c
                elif m=='xor':v=a^c
                elif m=='shl':v=a<<(c&31)
                elif m=='shr':v=(a&((1<<bits)-1))>>(c&31)
                else:v=(a-(1<<bits) if a&(1<<(bits-1)) else a)>>(c&31)
                self.put(i,o[0],v)
            else:raise ValueError(f'Unsupported instruction at {pc:x}: {m}')
            pc=next_pc
        raise ValueError('Replay instruction limit')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_HASH:raise ValueError('Executable changed')
    _,_,raw,_,records,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    a.out.mkdir(parents=True,exist_ok=True);result=[]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    for ceiling,entry,fileoff,length in ROUTINES:
        code=exe[fileoff:fileoff+length];ins={i.address:i for i in md.disasm(code,entry)}
        replay=Replay(ins,raw[54509:54509+1954*44]);count=0
        for k,r in enumerate(records):
            if not r[14]&(8 if ceiling else 4):continue
            actual=replay.run(entry,k);expected=slope_corners(records,k,ceiling)
            if actual!=expected:raise ValueError(f'Region {k}: original {actual}, port {expected}')
            count+=1
        # Synthetic inputs exercise every direction and the no-neighbor fallback.
        synthetic_count=0
        for side in range(4):
            for missing in [False,True]:
                rs=[list(records[0]),list(records[1])]
                rs[0][10:12]=[(-300)&65535,140];rs[1][10:12]=[(-170)&65535,250]
                rs[0][2:6]=[65535]*4;rs[0][2+side]=65535 if missing else 1
                rs[0][14]=(8 if ceiling else 4)|(side<<(14 if ceiling else 12))
                packed=b''.join(struct.pack('<22H',*r) for r in rs)
                check=Replay(ins,packed)
                assert check.run(entry,0)==slope_corners(rs,0,ceiling)
                synthetic_count+=1
        (a.out/f'routine_{entry:x}.bin').write_bytes(code)
        (a.out/f'routine_{entry:x}.txt').write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in ins.values())+'\n')
        result.append(dict(ceiling=ceiling,virtual_address=hex(entry),executable_file_offset=fileoff,code_sha256=hashlib.sha256(code).hexdigest(),regions_checked=count,corner_values_checked=count*4,synthetic_cases=synthetic_count,mismatches=0))
    report=dict(method='Bounded interpretation of original x86 bytes, not live runtime capture',executable_sha256=EXE_HASH,routines=result)
    (a.out/'slope_replay.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
