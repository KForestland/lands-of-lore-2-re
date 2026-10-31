#!/usr/bin/env python3
"""Replay call-free native spatial constructor spans against every original record."""
import argparse,hashlib,json,struct
from pathlib import Path
import capstone
from lol2_verify_target_resolver import ResolverReplay
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_extract_draracle_geometry import decode,u32

class ConstructorReplay(ResolverReplay):
    def span(self,start,end):
        pc=start
        while pc<end:
            i=self.instructions[pc];o=i.operands;m=i.mnemonic
            if m=='push':
                v=self.get(i,o[0]);self.regs['esp']-=4;self.writemem(self.regs['esp'],4,v)
            elif m in ('mov','movsx','movzx'):
                v=self.get(i,o[1]);bits=o[1].size*8
                if m=='movsx' and v&(1<<(bits-1)):v-=1<<bits
                self.put(i,o[0],v)
            elif m=='lea':self.put(i,o[0],self.addr(i,o[1]))
            elif m in ('add','sub','xor','and','shl','sar'):
                a,b=self.get(i,o[0]),self.get(i,o[1]);bits=o[0].size*8
                if m=='add':v=a+b
                elif m=='sub':v=a-b
                elif m=='xor':v=a^b
                elif m=='and':v=a&b
                elif m=='shl':v=a<<(b&31)
                else:v=(a-(1<<bits) if a&(1<<(bits-1)) else a)>>(b&31)
                self.put(i,o[0],v)
            else:raise ValueError(f'Unsupported span instruction {pc:x}: {m}')
            pc+=i.size
        if pc!=end:raise ValueError('Span ended inside instruction')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    exe=(a.game_root/'LOLG.DAT').read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_HASH:raise ValueError('Executable changed')
    _,entry,raw,_,_,_=decode((a.game_root/'DAT/L1_DC.MIX').read_bytes())
    a.out.mkdir(parents=True,exist_ok=True);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={};proof=[]
    for start,end in [(0xae99a,0xaea19),(0xf2073,0xf20a1),(0xf20a6,0xf20cc),(0xf20de,0xf20e4),(0xf2128,0xf2176),(0x5f7c0,0x5f82e),(0x9d38e,0x9d3a9),(0x9ccce,0x9cce9)]:
        code=exe[start+0x37000:end+0x37000];ii=list(md.disasm(code,start));ins.update({i.address:i for i in ii})
        (a.out/f'code_{start:x}.bin').write_bytes(code);(a.out/f'code_{start:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ii)+'\n')
        proof.append(dict(va=hex(start),file_offset=start+0x37000,sha256=hashlib.sha256(code).hexdigest()))
    r=ConstructorReplay(ins,b'');results=[]
    for k in range(u32(raw,0x60)):
        d=raw[u32(raw,0x14)+k*37:u32(raw,0x14)+(k+1)*37]
        r.mem[0x500000:0x500025]=d;r.mem[0x600000:0x600038]=bytes(56)
        r.regs.update(ebx=0x600000,edx=0x500000,esi=0x500000,esp=0x700000)
        r.span(0xae99a,0xaea19)
        xyz=struct.unpack_from('<3i',r.mem,0x600000)
        expected=tuple(struct.unpack_from('<h',d,j)[0]*65536 for j in (0,2,6))
        if xyz!=expected:raise ValueError(('Position mismatch',k))
        r.regs.update(ebx=0x600000,esi=0x500000,esp=0x700000);r.writemem(0x22d48,4,0x400000)
        r.span(0xf2073,0xf20a1)
        template=struct.unpack_from('<H',d,32)[0]
        if r.regs['ebp']!=0x400000+template*55:raise ValueError(('Template mismatch',k))
        # Simulate only the called base constructor's return/stack convention.
        r.regs['eax']=0x600000;r.span(0xf20a6,0xf20cc);r.span(0xf20de,0xf20e4)
        fields=[r.readmem(0x600030,1),r.readmem(0x600031,1),r.readmem(0x600036,1)]
        if fields!=[d[35],d[34],d[36]]:raise ValueError(('Tail mismatch',k))
        results.append(dict(id=k,position_fixed=xyz,template_index=template,template_stride=55,selector_byte=d[35],initial_state_byte=d[34],flags_byte=d[36]))
    report=dict(method='Original instruction replay of call-free constructor spans. Allocation, helper calls and virtual initialization are not replayed.',executable_sha256=EXE_HASH,source_entry=entry,code=proof,records_checked=len(results),mismatches=0,results=results,
      loader_evidence='0x9D396 seeks to header +0x14; 0x9D39E passes count +0x60 to 0xF2128. That loop reads 37 bytes, allocates type-3 slot, calls 0xF2064.',
      index_limit='0x5F7C0 allocates the first free bitmap slot. Serialized order equals runtime indices only for an initially empty table with successful allocations. Fresh-table initialization and named-action conversion remain to verify.')
    (a.out/'constructor_replay.json').write_text(json.dumps(report,indent=2)+'\n');print(f'{len(results)} constructor records passed; placement 544:',results[544])
if __name__=='__main__':main()
