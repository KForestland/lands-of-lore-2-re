#!/usr/bin/env python3
"""Extract native compact commands; opcode effects remain unassigned."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import capstone
from lol2_extract_draracle_geometry import decode
from lol2_cache_named_wall_fixture import require, sha
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_target_resolver import ResolverReplay

# Explicit sizes from the native decision tree, not inferred from buffer fitting.
SIZES = {0: 4, 1: 6, 2: 6, 3: 12, 5: 6, 6: 6, 7: 6, 8: 8, 9: 6,
         11: 8, 12: 6, 13: 8, 14: 8, 15: 8, 16: 6, 17: 6, 18: 18,
         19: 10, 20: 10, 21: 6, 22: 18, 23: 6, 24: 10, 196: 12,
         197: 6, 198: 6, 199: 6, 200: 6, 201: 6, 204: 8, 205: 8,
         206: 6, 207: 6, 208: 8, 209: 10, 210: 6, 240: 6}


def extract(root, out):
    exe = (root / 'LOLG.DAT').read_bytes()
    require(sha(exe) == EXE_HASH, 'Executable changed')
    _, entry, raw, *_ = decode((root / 'DAT/L1_DC.MIX').read_bytes())
    out.mkdir(parents=True, exist_ok=True)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    ins, witnesses = {}, []
    for start, end in [(0x645e0, 0x646e9), (0x646ec, 0x6476f),
                       (0x9cf26, 0x9cf68), (0x9cfb0, 0x9cfe8),
                       (0x66264, 0x662b2)]:
        code = exe[start + 0x37000:end + 0x37000]
        rows = list(md.disasm(code, start))
        require(rows[-1].address + rows[-1].size == end, 'Instruction boundary')
        ins.update({i.address: i for i in rows})
        (out / f'code_{start:x}.txt').write_text('\n'.join(
            f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in rows) + '\n')
        witnesses.append(dict(address=start, file_offset=start + 0x37000, sha256=sha(code)))
    m = ResolverReplay(ins, b'')
    for opcode, expected in SIZES.items():
        m.writemem(0x600000, 1, opcode)
        require(m.resolve(0x600000, 0, 0x645e0) == expected, 'Native size table mismatch')
    streams = []
    for global_address, offset_field, size_field in [(0x2b51c, 0x3c, 0x84), (0x2b514, 0x44, 0x8c)]:
        offset = struct.unpack_from('<I', raw, offset_field)[0]
        size = struct.unpack_from('<I', raw, size_field)[0]
        require(offset + size <= len(raw), 'Stream bounds')
        data = raw[offset:offset + size]
        commands, cursor = [], 0
        while cursor < size:
            opcode = data[cursor]
            require(opcode in SIZES, f'Unsupported opcode at {cursor}')
            length = SIZES[opcode]
            require(cursor + length <= size, 'Truncated command')
            payload = data[cursor:cursor + length]
            m.mem[0x600000:0x600000 + length] = payload
            require(m.resolve(0x600000, 0, 0x645e0) == length, 'Native record size mismatch')
            commands.append(dict(offset=cursor, entry_offset=offset + cursor,
                                 source_offset=entry['offset'] + offset + cursor,
                                 opcode=opcode, kind=payload[1], target=struct.unpack_from('<H', payload, 2)[0],
                                 raw_hex=payload.hex(), size=length))
            cursor += length
        require(b''.join(bytes.fromhex(c['raw_hex']) for c in commands) == data, 'Round trip')
        groups, index = [], 0
        while index < len(commands):
            command = commands[index]
            count = bytes.fromhex(command['raw_hex'])[4] if command['opcode'] == 240 else 1
            first = index + 1 if command['opcode'] == 240 else index
            require(first + count <= len(commands), 'Group exceeds buffer')
            children = commands[first:first + count]
            require(all(c['opcode'] != 240 for c in children), 'Nested group needs separate interpretation')
            groups.append(dict(offset=command['offset'], count=count,
                               command_offsets=[c['offset'] for c in children]))
            index = first + count
        streams.append(dict(global_address=global_address, header_offset_field=offset_field,
                            header_size_field=size_field, entry_offset=offset, size=size, sha256=sha(data),
                            command_count=len(commands), opcode_counts=dict(Counter(c['opcode'] for c in commands)),
                            commands=commands, groups=groups,
                            target_544=[c for c in commands if c['opcode'] != 240 and c['kind'] == 3 and c['target'] == 544]))
    report = dict(executable_sha256=EXE_HASH, entry_sha256=sha(raw), code=witnesses,
                  native_size_checks=len(SIZES) + sum(s['command_count'] for s in streams),
                  mismatches=0, streams=streams,
                  scope='Original size routine replay, exact source round trips and static loader/group/target witnesses. No live capture, opcode effects, named-action conversion or complete event execution proof.')
    (out / 'progression_commands.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(native_size_checks=report['native_size_checks'], mismatches=0,
                          streams=[{k:s[k] for k in ['global_address','size','command_count','target_544']} for s in streams])))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    extract(args.game_root, args.out)
