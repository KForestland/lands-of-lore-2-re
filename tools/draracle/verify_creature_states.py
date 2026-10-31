#!/usr/bin/env python3
"""Replay native state/view partitions and bearing selection on pinned code bytes."""
import argparse
import json
from pathlib import Path
import capstone
from extract_creature_states import load_states
from lol2_cache_named_wall_fixture import require, sha
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_target_resolver import ResolverReplay


def signed(value, bits=32):
    value &= (1 << bits)-1
    return value-(1 << bits) if value & (1 << (bits-1)) else value


class CreatureReplay(ResolverReplay):
    """Small call-free interpreter; unsupported instructions/addresses fail closed."""
    def execute(self, start, stop):
        pc = start
        stops = stop if isinstance(stop, set) else {stop}
        equal = less = below = False
        for _ in range(3000):
            if pc in stops:
                return pc
            i = self.instructions[pc]
            o, op, nxt = i.operands, i.mnemonic, pc+i.size
            if op in ('mov', 'movzx'):
                self.put(i, o[0], self.get(i, o[1]))
            elif op == 'lea':
                self.put(i, o[0], self.addr(i, o[1]))
            elif op == 'push':
                value = self.get(i, o[0])
                self.regs['esp'] -= 4
                self.writemem(self.regs['esp'], 4, value)
            elif op == 'pop':
                self.put(i, o[0], self.readmem(self.regs['esp'], 4))
                self.regs['esp'] += 4
            elif op == 'xchg':
                a, b = self.get(i, o[0]), self.get(i, o[1])
                self.put(i, o[0], b)
                self.put(i, o[1], a)
            elif op == 'neg':
                self.put(i, o[0], -self.get(i, o[0]))
            elif op == 'shld':
                a, b, n = (self.get(i, operand) for operand in o)
                self.put(i, o[0], ((a << 32 | b) << (n & 31)) >> 32)
            elif op in ('cmp', 'test'):
                a, b = self.get(i, o[0]), self.get(i, o[1])
                mask = (1 << (o[0].size*8))-1
                a, b = a & mask, b & mask
                equal = a == b if op == 'cmp' else (a & b) == 0
                below = a < b if op == 'cmp' else False
                less = signed(a, o[0].size*8) < signed(b, o[0].size*8) if op == 'cmp' else signed(a & b, o[0].size*8) < 0
            elif op in ('jmp', 'je', 'jne', 'jge', 'jl', 'jg', 'jle', 'jb', 'ja', 'jbe'):
                if {'jmp': True, 'je': equal, 'jne': not equal, 'jge': not less, 'jl': less, 'jg': not less and not equal, 'jle': less or equal, 'jb': below, 'ja': not below and not equal, 'jbe': below or equal}[op]:
                    nxt = self.get(i, o[0])
            elif op == 'imul' and len(o) == 1:
                require(o[0].size == 4, 'Only dword one-operand IMUL supported')
                product = signed(self.regs['eax'])*signed(self.get(i, o[0]))
                self.regs['eax'] = product & 0xffffffff
                self.regs['edx'] = (product >> 32) & 0xffffffff
            elif op in ('idiv', 'div'):
                dividend = (self.regs['edx'] << 32) | self.regs['eax']
                divisor = self.get(i, o[0])
                if op == 'idiv':
                    dividend, divisor = signed(dividend, 64), signed(divisor)
                q = abs(dividend)//abs(divisor)
                if (dividend < 0) != (divisor < 0):
                    q = -q
                require((-2**31 <= q < 2**31) if op == 'idiv' else (0 <= q < 2**32), 'Divide overflow')
                self.regs['eax'], self.regs['edx'] = q & 0xffffffff, (dividend-q*divisor) & 0xffffffff
            elif op in ('add', 'sub', 'xor', 'or', 'and', 'shl', 'shr', 'sar', 'inc', 'dec', 'imul'):
                a = self.get(i, o[0])
                b = 1 if op in ('inc', 'dec') else self.get(i, o[1])
                if op in ('add', 'inc'): value = a+b
                elif op in ('sub', 'dec'): value = a-b
                elif op == 'xor': value = a^b
                elif op == 'or': value = a|b
                elif op == 'and': value = a&b
                elif op == 'shl': value = a << (b&31)
                elif op == 'shr': value = (a&0xffffffff) >> (b&31)
                elif op == 'sar': value = signed(a, o[0].size*8) >> (b&31)
                elif len(o) == 3: value = b*self.get(i, o[2])
                else: value = a*b
                self.put(i, o[0], value)
                if op in ('xor', 'or', 'and', 'sub', 'add'):
                    equal, less = (value&0xffffffff) == 0, signed(value) < 0
                    below = ((a&0xffffffff)+(b&0xffffffff)>0xffffffff) if op == 'add' else (False if op != 'sub' else (a&0xffffffff) < (b&0xffffffff))
            else:
                raise ValueError(f'Unsupported instruction {pc:x}: {op}')
            pc = nxt
        raise ValueError('Replay instruction limit')


def verify(game_root, out):
    source = load_states(game_root)
    exe = (game_root/'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH, 'Executable changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    ins, proof = {}, []
    # Include loader/caller context in evidence; only the three declared slices are replayed.
    for start, end in [(0xa1c04, 0xa1d9e), (0xf2b94, 0xf2cbf), (0xf1b95, 0xf1bdb)]:
        code = exe[start+0x37000:end+0x37000]
        decoded = list(md.disasm(code, start))
        require(decoded[-1].address+decoded[-1].size == end, 'Incomplete disassembly')
        ins.update({i.address: i for i in decoded})
        (out/f'code_{start:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in decoded)+'\n')
        proof.append(dict(analysis_address=start, file_offset=start+0x37000, size=len(code), sha256=sha(code)))
    m = CreatureReplay(ins, b'')
    entities, states, views, stack = 0x400000, 0x500000, 0x600000, 0x700000
    all_states = [s for e in source['entities'] for s in e['states']]
    for e in source['entities']:
        data = bytes.fromhex(e['raw_hex'])[:135]
        pos = entities+e['record']*139
        m.mem[pos:pos+len(data)] = data
    for s in all_states:
        pos = states+s['record']*16
        m.mem[pos:pos+16] = bytes.fromhex(s['raw_hex'])
    m.regs.update(eax=states, esi=source['entity_count'], esp=stack)
    m.writemem(stack+12, 4, entities)
    m.execute(0xa1d6b, 0xa1d92)
    for e in source['entities']:
        require(m.readmem(entities+e['record']*139+20, 4) == states+e['states'][0]['record']*16, 'Native entity state pointer mismatch')
    require(m.regs['edx'] == states+source['state_count']*16, 'Native state partition end')
    m.regs.update(esi=views, ebx=states, esp=stack)
    m.writemem(stack, 4, source['state_count'])
    m.execute(0xf2c1f, 0xf2c48)
    for s in all_states:
        require(m.readmem(states+s['record']*16, 4) == views+s['view_first']*12, 'Native state view pointer mismatch')
    require(m.regs['eax'] == views+source['view_count']*12, 'Native view partition end')
    # F2C89 starts AFTER the bearing helper. Its result is a fixture input,
    # not a replay of coordinates -> bearing or proof of Godot heading convention.
    cases = 0
    headings = [0, 1, 255, 256, 4095, 4096, 8191, 8192, 16383, 16384, 32767, 32768, 65534, 65535]
    for count in (8, 16):
        for heading in headings:
            for bearing in range(256):
                m.regs.update(eax=bearing, ebp=stack, esp=stack-16)
                m.writemem(stack+12, 4, states)
                m.writemem(stack+20, 4, heading)
                m.writemem(states+13, 1, count)
                m.execute(0xf2c89, 0xf2cbc)
                adjusted_heading = ((heading-(32768//count)) & 0xffffffff) >> 8
                expected = (((bearing-adjusted_heading) & 255)*count) >> 8
                require(m.regs['eax'] == expected and 0 <= expected < count, 'Native bearing slot mismatch')
                cases += 1
    report = dict(executable_sha256=EXE_HASH, code=proof, entity_pointer_checks=source['entity_count'],
                  state_pointer_checks=source['state_count'], view_records=source['view_count'],
                  bearing_cases=cases, mismatches=0,
                  scope='Call-free original x86 replay with source records and synthetic pointers. '
                        'Bearing helper result supplied as input; native coordinate bearing, AI state '
                        'selection, playback clock and live creature spawn are outside this proof.')
    (out/'native_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    print(verify(a.game_root, a.out))
