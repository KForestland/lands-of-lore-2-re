#!/usr/bin/env python3
"""Catalogue named cave definitions and their exact source table partitions."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named, require, sha
from lol2_extract_cave_materials import ASSET, HASH
from lol2_extract_draracle_geometry import parse_mix
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette
from extract_prop_sprite_previews import decode_rows

MIX_HASH = '6384ec4d4d78f1aadfc1f154d924e1e20636af037cf5af68fe35af8478854345'


def partition_entities(records, table):
    require(len(records) % 147 == 0, 'Partial entity record')
    rows = []
    cursor = 0
    for i in range(len(records) // 147):
        record = records[i*147:(i+1)*147]
        require(b'\0' in record[135:], 'Unterminated entity name')
        name = record[135:].split(b'\0', 1)[0].decode('ascii')
        offset = struct.unpack_from('<I', record, 55)[0]
        count = record[46]
        require(offset == cursor and offset + count*4 <= len(table), 'Table partition')
        entries = [list(table[offset+j*4:offset+(j+1)*4]) for j in range(count)]
        rows.append(dict(record=i, name=name, table_offset=offset, entry_count=count,
                         byte47=record[47], entries_bytes=entries))
        cursor += count*4
    require(cursor == len(table), 'Unconsumed table bytes')
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    mix = (a.game_root/'DAT/L1_DC.MIX').read_bytes()
    require(sha(mix) == MIX_HASH, 'Cave MIX changed')
    entry = next(e for e in parse_mix(mix) if e['key'] == 2971019266)
    raw = mix[entry['offset']:entry['offset']+entry['size']]
    entity_offset, table_offset = struct.unpack_from('<II', raw, 0x10)
    count, table_size = struct.unpack_from('<II', raw, 0x48)
    require(table_offset + table_size == entity_offset, 'Table/entity boundary')
    rows = partition_entities(raw[entity_offset:entity_offset+count*147], raw[table_offset:table_offset+table_size])
    _, blob, _, _ = load_named(a.game_root, ASSET)
    require(sha(blob) == HASH, 'Texture cache changed')
    s = sections(blob)
    v = struct.unpack_from('<6H11I', blob, s[2]+966*56)
    require(v[3] == 0x28e and v[4] == 1, 'Resource966 layout changed')
    paloff = struct.unpack_from('<I', blob, 4)[0]
    pal = rgb_palette(blob[paloff:paloff+768], 6)
    a.out.mkdir(parents=True, exist_ok=True)
    images = []
    for level in range(v[5] & 255):
        pos, size = s[3]+v[7+level], v[12+level]
        w,h,pixels,_ = decode_rows(blob[pos:pos+size])
        require((w,h) == (max(1,v[1]>>level),max(1,v[2]>>level)), 'Mip dimensions')
        rgba = bytes(c for x in pixels for c in [*pal[x*3:x*3+3],255 if x else 0])
        name = f'resource_966_mip_{level}.png'
        Image.frombytes('RGBA',(w,h),rgba).save(a.out/name)
        images.append(dict(png=name, width=w, height=h, payload_sha256=sha(blob[pos:pos+size])))
    report = dict(entity_offset=entity_offset, table_offset=table_offset, table_size=table_size,
                  entities=rows, total_entries=sum(r['entry_count'] for r in rows), resource966=images,
                  scope='Exact source partition, not native state semantics. Byte46 counts four-byte entries; byte55 dword is their table-relative offset for all11 definitions. Resource966 visually resembles a roach, but the named entity-to-resource link and spawn placement remain unverified. No animation decoding or live capture claimed.')
    (a.out/'entities.json').write_text(json.dumps(report,indent=2)+'\n')
    body = ''.join(f'<tr><td>{r["record"]}</td><td>{r["name"]}</td><td>{r["entry_count"]}</td><td>{r["table_offset"]}</td></tr>' for r in rows)
    (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Cave creature source review</title><style>body{background:#333;color:white;font:18px sans-serif}td,th{padding:6px 20px}img{image-rendering:pixelated;background:#555}</style><h1>Cave creature source review</h1><p>Resource966: visually a roach candidate. Named entity binding, scale, spawn and animation remain unverified.</p><img src="resource_966_mip_0.png"><h2>Original named definitions</h2><table><tr><th>Record</th><th>Name</th><th>Entries</th><th>Table offset</th></tr>'+body+'</table>')
    print(dict(entities=len(rows),entries=report['total_entries'],table_bytes=table_size,mips=len(images)))


if __name__ == '__main__':
    main()
