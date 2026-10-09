#!/usr/bin/env python3
"""Recover named creature -> native state -> view-resource links, without AI labels."""
import argparse
import json
import struct
from pathlib import Path
from catalogue_cave_entities import MIX_HASH, partition_entities
from lol2_cache_named_wall_fixture import require, sha
from lol2_extract_draracle_geometry import parse_mix


def extent(raw, offset, count, stride, label):
    require(0 <= offset <= len(raw) and 0 <= count <= (len(raw)-offset)//stride,
            f'{label} extent')
    return raw[offset:offset+count*stride]


def parse_states(raw):
    require(len(raw) >= 0x50, 'Truncated header')
    entity_offset, table_offset = struct.unpack_from('<II', raw, 0x10)
    count, table_size = struct.unpack_from('<II', raw, 0x48)
    require(table_offset + table_size == entity_offset, 'Table/entity boundary')
    records = extent(raw, entity_offset, count, 147, 'Entity')
    table = extent(raw, table_offset, table_size, 1, 'Four-byte table')
    entities = partition_entities(records, table)
    state_count_offset = entity_offset + len(records)
    ns = struct.unpack('<I', extent(raw, state_count_offset, 1, 4, 'State count'))[0]
    state_start = state_count_offset + 4
    states = extent(raw, state_start, ns, 16, 'State')
    frame_count_offset = state_start + len(states)
    nf = struct.unpack('<I', extent(raw, frame_count_offset, 1, 4, 'View count'))[0]
    frame_start = frame_count_offset + 4
    views = extent(raw, frame_start, nf, 12, 'View')
    si = vi = 0
    for entity in entities:
        entity['source_offset'] = entity_offset + entity['record']*147
        entity['raw_hex'] = records[entity['record']*147:(entity['record']+1)*147].hex()
        entity['states'] = []
        # A1D7B..A1D89 sums both bytes here; only byte46 counts the separate table.
        for selector in range(entity['entry_count'] + entity['byte47']):
            require(si < ns, 'Entity state partition overrun')
            state = states[si*16:(si+1)*16]
            signed_count = struct.unpack_from('<b', state, 13)[0]
            n = 1 if signed_count < 0 else signed_count
            require(vi+n <= nf, 'State view partition overrun')
            refs = []
            for slot in range(n):
                frame = views[(vi+slot)*12:(vi+slot+1)*12]
                refs.append(dict(slot=slot, record=vi+slot, source_offset=frame_start+(vi+slot)*12,
                                 resource_reference=struct.unpack_from('<h', frame)[0],
                                 flags_byte2=frame[2], raw_hex=frame.hex()))
            entity['states'].append(dict(selector=selector, record=si,
                source_offset=state_start+si*16, raw_hex=state.hex(),
                signed_view_count=signed_count, view_first=vi, views=refs))
            si += 1
            vi += n
    require(si == ns and vi == nf, 'Unconsumed state/view records')
    return dict(entity_offset=entity_offset, entity_count=count, state_count_offset=state_count_offset,
                state_offset=state_start, state_count=ns, view_count_offset=frame_count_offset,
                view_offset=frame_start, view_count=nf, end_offset=frame_start+len(views), entities=entities)


def load_states(game_root):
    mix = (game_root/'DAT/L1_DC.MIX').read_bytes()
    require(sha(mix) == MIX_HASH, 'Cave MIX changed')
    entry = next(e for e in parse_mix(mix) if e['key'] == 2971019266)
    raw = mix[entry['offset']:entry['offset']+entry['size']]
    report = parse_states(raw)
    report.update(mix_sha256=MIX_HASH, source_entry=entry, entry_sha256=sha(raw),
        scope='A1C04 reads 135-byte bodies plus 12-byte names and calls F2B94 for states/views. '
              'A1D71 partitions states by byte46+byte47; F2C21 partitions 12-byte views by signed '
              'state byte13. F2C54 selects a view by relative bearing, then F1BCC..F1BD6 reads '
              'its signed resource reference. AI action meanings, animation timing, mirror flag '
              'semantics and live spawn identity are not established. Source offsets are entry-relative.')
    return report


def resource_bindings(report, resource):
    return [dict(entity_record=e['record'], name=e['name'], selector=s['selector'],
                 state_record=s['record'], state_source_offset=s['source_offset'],
                 view_slot=v['slot'], view_source_offset=v['source_offset'],
                 view_raw_hex=v['raw_hex'])
            for e in report['entities'] for s in e['states'] for v in s['views']
            if v['resource_reference'] == resource]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    report = load_states(a.game_root)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/'creature_states.json').write_text(json.dumps(report, indent=2)+'\n')
    print({k: report[k] for k in ['entity_count', 'state_count', 'view_count', 'end_offset']})


if __name__ == '__main__':
    main()
