#!/usr/bin/env python3
"""Verify LE relocation and cache-load provenance of the initial index1 table."""
import argparse
import json
import struct
from pathlib import Path
from lol2_cache_named_wall_fixture import load_named, require, sha
from lol2_extract_cave_materials import ASSET, HASH
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_wall_material_checkpoint import sections


def fixups(exe, le, page):
    """Decode only the internal offset records used by the requested pages."""
    u = lambda o: struct.unpack_from('<I', exe, le + o)[0]
    start, end = struct.unpack_from('<II', exe, le + u(0x68) + page * 4)
    pos, stop = le + u(0x6c) + start, le + u(0x6c) + end
    result = {}
    while pos < stop:
        kind, flags = exe[pos:pos + 2]
        require(kind == 7 and flags in (0, 16), 'Unsupported fixup form')
        length = 9 if flags == 16 else 7
        require(pos + length <= stop, 'Truncated fixup')
        source = struct.unpack_from('<h', exe, pos + 2)[0]
        require(source not in result, 'Duplicate source fixup')
        result[source] = dict(target_object=exe[pos + 4],
            target_offset=int.from_bytes(exe[pos + 5:pos + length], 'little'),
            record_file_offset=pos, record_hex=exe[pos:pos + length].hex())
        pos += length
    return result


def verify(exe, blob):
    require(sha(exe) == EXE_HASH and sha(blob) == HASH, 'Source hash changed')
    mz = 0x39024
    le = mz + struct.unpack_from('<I', exe, mz + 0x3c)[0]
    require(exe[le:le + 2] == b'LE', 'Missing LE')
    u = lambda o: struct.unpack_from('<I', exe, le + o)[0]
    objects = le + u(0x40)
    size, base, flags, first, pages, _ = struct.unpack_from('<6I', exe, objects + 3 * 24)
    require((size, base, pages) == (0x14200, 0x160000, 0), 'Object4 changed')
    evidence = []
    for address, target_object, target_offset in [
            (0x12b441, 4, 0x4000), (0x12b75e, 4, 0x4000),
            (0x12b43c, 4, 0), (0x12b759, 4, 0), (0x9d9b4, 4, 0),
            (0x9d9c6, 5, 0x223e0), (0x9dbc6, 5, 0x223e0)]:
        code_offset = address - 0x59024
        record = fixups(exe, le, 1 + code_offset // 4096)[code_offset % 4096]
        require((record['target_object'], record['target_offset']) ==
                (target_object, target_offset), 'Unexpected relocation target')
        evidence.append(dict(analysis_address=hex(address), **record))
    # Hash-pinned native instructions: header read, table pointer assignment,
    # seek(header+0x18, SET), read(handle, table_base, 0x4200).
    witnesses = {
        0x9d8ec: '68a20600008d542404525089c3e822af0700',
        0x9d9b3: 'b800000000', 0x9d9c5: 'a3e0230200',
        0x9dbaf: '6a008b4c241c5153e830b0070083c40c68004200008b3de02302005753e84fac0700'}
    for address, code in witnesses.items():
        expected = bytes.fromhex(code)
        require(exe[address + 0x37000:address + 0x37000 + len(expected)] == expected,
                'Loader instruction witness changed')
    s = sections(blob)
    require(struct.unpack_from('<I', blob, 0x18)[0] == s[4], 'Shade offset mismatch')
    require(s[5] - s[4] == 0x4200, 'Shade section extent changed')
    table = blob[s[4] + 0x4000:s[4] + 0x4100]
    return table, dict(executable_sha256=EXE_HASH, cache_sha256=HASH,
        le_header=le, object4_virtual_size=size, object4_file_pages=pages,
        relocations=evidence, loader_instruction_hex={hex(k): v for k, v in witnesses.items()},
        shade_section_offset=s[4], shade_load_bytes=0x4200,
        remap_row=64, remap_file_offset=s[4] + 0x4000, remap_sha256=sha(table),
        scope='Static loader provenance: initial table is cache shade row64. No live capture or proof against subsequent runtime modification. Ordinary source shade selection remains outside this fixture.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    _, blob, _, _ = load_named(a.game_root, ASSET)
    table, report = verify((a.game_root / 'LOLG.DAT').read_bytes(), blob)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'initial_remap.bin').write_bytes(table)
    (a.out / 'binding.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Verified 7 LE fixups and initial shade row64 load; later runtime changes unverified')


if __name__ == '__main__':
    main()
