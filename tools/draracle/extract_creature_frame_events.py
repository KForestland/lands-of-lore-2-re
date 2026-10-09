#!/usr/bin/env python3
"""Extract native state-linked eight-byte frame-event lists from the pinned cave."""
import argparse
import json
import struct
from pathlib import Path
from extract_creature_states import load_states
from catalogue_cave_entities import MIX_HASH
from lol2_cache_named_wall_fixture import require, sha


def read_events(raw, offset, count, first):
    require(0 <= first < count and 0 <= offset <= len(raw) and count <= (len(raw)-offset)//8, 'Event table extent/index')
    result=[]
    for index in range(first,count):
        row=raw[offset+index*8:offset+(index+1)*8]
        if row[0] == 0:
            return result,index
        result.append(dict(record=index,source_offset=offset+index*8,kind=row[0],frame=row[1],
                           value_word=struct.unpack_from('<H',row,2)[0],raw_hex=row.hex()))
    raise ValueError('Unterminated frame-event list')


def load_events(game_root):
    source=load_states(game_root)
    mix=(game_root/'DAT/L1_DC.MIX').read_bytes()
    require(sha(mix)==MIX_HASH,'Cave MIX changed')
    entry=source['source_entry'];raw=mix[entry['offset']:entry['offset']+entry['size']]
    count,offset=struct.unpack_from('<II',raw,0x50)
    require(offset+count*8+1==len(raw),'Event table/trailer boundary')
    for entity in source['entities']:
        for state in entity['states']:
            state_raw=bytes.fromhex(state['raw_hex'])
            first=struct.unpack_from('<H',state_raw,8)[0]
            events,end=read_events(raw,offset,count,first)
            state.update(frame_event_first=first,frame_events=events,event_terminator=end,
                         native_interval_units=struct.unpack_from('<i',state_raw,4)[0] >> 8)
    source.update(frame_event_offset=offset,frame_event_count=count,
        event_scope='Header50 count/header54 offset loaded as8-byte records to level+80 (current level22CD8 ->22D58). State word8 indexes records. F2814 matches event byte1 to current frame and uses byte0 as event kind. Kind1 is consumed in the creature attack path; native damage request context and clock-to-seconds remain open.')
    return source


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=load_events(a.game_root);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'creature_frame_events.json').write_text(json.dumps(r,indent=2)+'\n')
    print(dict(records=r['frame_event_count'],states=r['state_count'],offset=r['frame_event_offset']))
