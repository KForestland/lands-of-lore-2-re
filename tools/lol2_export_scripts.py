#!/usr/bin/env python3
"""Export one LoL2 level's native script data as JSON.

    python3 tools/lol2_export_scripts.py ./lol2_game L7_DH out/L7_DH.json
    python3 tools/lol2_export_scripts.py ./lol2_game 7 out/L7_DH.json

GAME is the game root (it must contain DAT/L<n>_<xx>.MIX); it is only read.
LEVEL is an archive stem such as L7_DH, or a level number.
The game root can also come from the LOL2_GAME environment variable (pass '-').

What is written (see docs/lol2-level-script-format.md):
- the two command streams, framed with the 37-opcode SIZES table (native
  0x645E0) and split into F0 groups (byte +4 = child count, no nesting);
- the four object tables (actor 56, prop 37, control 33, movable 41 bytes),
  with each object's event-record list (list offset = record word +12);
- the region descriptor table (header 0xA4/0xAC, 26-byte rows, list offset =
  row word +0x0A) and the region event-record lists;
- kind-19 predicate trailers and the 5-byte predicate table (header 0xBC/0xB8).

Data only. No opcode effect or event meaning is assigned. Undecoded bytes stay
raw hex. An opcode outside SIZES stops framing of that stream, is listed under
"unsupported", and the exit code is 1. Nothing is guessed.

Standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lol2_source_format import SIZES, level_geometry, u32  # noqa: E402

FORMAT = 'lol2-native-scripts-2'
# stream, header offset field, header size field, native global that holds the stream base
STREAMS = [(0, 0x3C, 0x84, 0x2B51C), (1, 0x44, 0x8C, 0x2B514)]
# label, header offset field, header count field, record stride (event list offset = record word +12)
TABLES = [('actor', 0x1C, 0x68, 56), ('prop', 0x14, 0x60, 37), ('control', 0x18, 0x64, 33),
          ('movable', 0x24, 0x70, 41)]
OBJECT_EVENTS = (0x40, 0x88)      # object event-record blob: offset, size
REGION_EVENTS = (0x38, 0x80)      # region event-record blob: offset, size
REGION_DESCRIPTORS = (0xA4, 0xAC, 26)
PREDICATE_TABLE = (0xBC, 0xB8, 5)
# Object record kinds whose word +2 names a stream-1 group.
OBJECT_GROUP_KINDS = (2, 3, 4, 5, 6, 8, 9, 10)
REGION_GROUP_KIND = 12
PREDICATE_KIND = 19


class SourceError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise SourceError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def section(raw, offset_field, count_field, stride):
    offset, count = u32(raw, offset_field), u32(raw, count_field)
    require(offset + count * stride <= len(raw), f'section {offset_field:#x}/{count_field:#x} exceeds geometry')
    return offset, count, raw[offset:offset + count * stride]


def walk(blob, start):
    """Native list walk: byte0 length, byte1 kind; zero length or zero kind ends the list."""
    cursor, rows = start, []
    while True:
        require(cursor + 2 <= len(blob), f'event list {start} leaves its section at {cursor}')
        length, kind = blob[cursor], blob[cursor + 1]
        if not length or not kind:
            return rows, cursor
        require(length >= 2 and cursor + length <= len(blob), f'event record length {length} at {cursor}')
        rows.append((cursor, blob[cursor:cursor + length]))
        cursor += length


def frame(blob):
    """Split one stream into commands with SIZES. Stops at the first unsupported opcode."""
    commands, cursor = [], 0
    while cursor < len(blob):
        opcode = blob[cursor]
        length = SIZES.get(opcode)
        if length is None:
            return commands, dict(offset=cursor, opcode=opcode, reason='opcode not in the 37-entry size table')
        if cursor + length > len(blob):
            return commands, dict(offset=cursor, opcode=opcode, reason='command runs past the stream end')
        commands.append((cursor, blob[cursor:cursor + length]))
        cursor += length
    require(b''.join(body for _, body in commands) == blob, 'stream round trip')
    return commands, None


def group(commands):
    """Opcode 240 (F0) heads a group; its byte +4 is the child count. Other commands are single groups."""
    index, rows = 0, []
    while index < len(commands):
        offset, head = commands[index]
        grouped = head[0] == 240
        count = head[4] if grouped else 1
        first = index + int(grouped)
        children = commands[first:first + count]
        require(len(children) == count, f'group {offset} needs {count} commands')
        require(all(body[0] != 240 for _, body in children), f'nested group at {offset}')
        rows.append((offset, head if grouped else None, children))
        index = first + count
    return rows


def command_row(base, offset, body):
    return dict(offset=offset, file_offset=base + offset, opcode=body[0], kind=body[1],
                target=struct.unpack_from('<H', body, 2)[0], raw_hex=body.hex())


def export(archive_path):
    archive = archive_path.read_bytes()
    entry, raw = level_geometry(archive)
    base = entry['offset']

    streams, groups, unsupported, group_index = [], [], [], set()
    for stream, offset_field, size_field, native_global in STREAMS:
        start, size, blob = section(raw, offset_field, size_field, 1)
        commands, stop = frame(blob)
        if stop is not None:
            unsupported.append(dict(stream=stream, file_offset=base + start + stop['offset'], **stop))
        rows = group(commands)
        streams.append(dict(stream=stream, native_global=native_global, header_offset_field=offset_field,
                            header_size_field=size_field, entry_offset=start, file_offset=base + start, size=size,
                            sha256=sha(blob), framed_bytes=sum(len(b) for _, b in commands),
                            command_count=len(commands) - sum(1 for _, h, _ in rows if h is not None),
                            group_count=len(rows)))
        for offset, head, children in rows:
            end = (children[-1][0] + len(children[-1][1])) if children else offset + len(head)
            groups.append(dict(stream=stream, group=offset, file_offset=base + start + offset,
                               header_hex=head.hex() if head is not None else None, count=len(children),
                               raw_hex=blob[offset:end].hex(),
                               commands=[command_row(base + start, o, b) for o, b in children]))
            group_index.add((stream, offset))

    pred_start, pred_count, pred_blob = section(raw, *PREDICATE_TABLE)

    def predicate(blob, blob_file, cursor, length):
        following = blob[cursor + length:cursor + length + 4]
        if len(following) < 4 or following[1] != PREDICATE_KIND:
            return None
        index = struct.unpack_from('<H', following, 2)[0]
        row = dict(trailer_hex=following.hex(), trailer_file_offset=blob_file + cursor + length, index=index)
        if index < pred_count:
            row.update(entry_hex=pred_blob[index * 5:index * 5 + 5].hex(),
                       entry_file_offset=base + pred_start + index * 5)
        else:
            row.update(entry_hex=None, entry_file_offset=None)
        return row

    objects, record_counts, unlinked, table_sizes = [], Counter(), Counter(), {}
    obj_start, _, obj_blob = section(raw, *OBJECT_EVENTS, 1)
    for label, offset_field, count_field, stride in TABLES:
        table_start, count, records = section(raw, offset_field, count_field, stride)
        table_sizes[label] = count
        for index in range(count):
            list_offset = struct.unpack_from('<H', records, index * stride + 12)[0]
            rows, terminator = walk(obj_blob, list_offset)
            events = []
            for cursor, body in rows:
                record_counts[body[1]] += 1
                event = dict(offset=cursor, file_offset=base + obj_start + cursor, kind=body[1], raw_hex=body.hex())
                if body[1] in OBJECT_GROUP_KINDS:
                    require(len(body) >= 5, f'object record at {cursor} is too short')
                    target = struct.unpack_from('<H', body, 2)[0]
                    require((1, target) in group_index, f'object record at {cursor} names no stream-1 group {target}')
                    event.update(stream=1, group=target, value=body[4], extra_hex=body[5:].hex())
                    event['predicate'] = predicate(obj_blob, base + obj_start, cursor, len(body))
                elif body[1] != PREDICATE_KIND:
                    unlinked[body[1]] += 1
                events.append(event)
            objects.append(dict(ref=f'{label}:{index}', table=label, index=index,
                                file_offset=base + table_start + index * stride,
                                placement_hex=records[index * stride:(index + 1) * stride].hex(),
                                list_offset=list_offset, list_file_offset=base + obj_start + list_offset,
                                terminator_offset=terminator, events=events))

    reg_start, _, reg_blob = section(raw, *REGION_EVENTS, 1)
    desc_start, desc_count, descriptors = section(raw, *REGION_DESCRIPTORS)
    lists = {}
    for index in range(desc_count):
        lists.setdefault(struct.unpack_from('<H', descriptors, index * 26 + 10)[0], []).append(index)
    regions, region_lists = {}, []
    for list_offset in sorted(lists):
        rows, terminator = walk(reg_blob, list_offset)
        listed = []
        for cursor, body in rows:
            record_counts[('region', body[1])] += 1
            event = dict(offset=cursor, file_offset=base + reg_start + cursor, kind=body[1], raw_hex=body.hex())
            if body[1] == REGION_GROUP_KIND:
                require(len(body) >= 8, f'region record at {cursor} is too short')
                target, region, event_byte, value = struct.unpack_from('<HHBB', body, 2)
                require((0, target) in group_index, f'region record at {cursor} names no stream-0 group {target}')
                event.update(stream=0, group=target, region=region, event=event_byte, value=value,
                             extra_hex=body[8:].hex(), descriptors=lists[list_offset])
                event['predicate'] = predicate(reg_blob, base + reg_start, cursor, len(body))
                regions.setdefault(region, []).append(event)
            elif body[1] != PREDICATE_KIND:
                unlinked[('region', body[1])] += 1
            listed.append(event)
        region_lists.append(dict(list_offset=list_offset, list_file_offset=base + reg_start + list_offset,
                                 descriptors=lists[list_offset], terminator_offset=terminator, records=listed))
    for region in sorted(regions):
        objects.append(dict(ref=f'region:{region}', table='region', index=region, events=regions[region]))

    # Level-transition commands: bytes 02 01 00 00 1c, byte 5 = level (low 5 bits) | entry (high 3 bits).
    transitions = []
    for g in groups:
        for c in g['commands']:
            body = bytes.fromhex(c['raw_hex'])
            if body[:5] == bytes.fromhex('020100001c'):
                transitions.append(dict(stream=g['stream'], group=g['group'], file_offset=c['file_offset'],
                                        destination_level=body[5] & 31, destination_entry=body[5] >> 5))

    opcode_use = Counter(c['opcode'] for g in groups for c in g['commands'])
    counts = dict(objects=sum(1 for o in objects if o['events']),
                  placements=sum(1 for o in objects if 'placement_hex' in o),
                  object_tables=table_sizes, region_descriptors=desc_count,
                  region_lists=len(region_lists), groups=len(groups),
                  commands=sum(len(g['commands']) for g in groups),
                  event_links=sum(1 for o in objects for e in o['events'] if 'group' in e),
                  predicate_trailers=sum(1 for o in objects for e in o['events'] if e.get('predicate')),
                  predicate_entries=pred_count, transitions=len(transitions),
                  distinct_opcodes=len(opcode_use),
                  opcode_use={str(op): n for op, n in sorted(opcode_use.items(), key=lambda kv: (-kv[1], kv[0]))},
                  unlinked_record_kinds={str(k): n for k, n in sorted(unlinked.items(), key=str)},
                  unsupported=len(unsupported))
    return dict(format=FORMAT, area=archive_path.stem, level=int(archive_path.stem.split('_')[0][1:]),
                source=dict(file='DAT/' + archive_path.name, sha256=sha(archive), geometry_key=entry['key'],
                            geometry_sha256=sha(raw), geometry_entry_offset=base, geometry_entry_size=entry['size']),
                size_table={str(op): n for op, n in sorted(SIZES.items())},
                streams=streams,
                predicate_table=dict(file_offset=base + pred_start, count=pred_count, entry_size=5,
                                     entries=[pred_blob[i * 5:i * 5 + 5].hex() for i in range(pred_count)]),
                counts=counts, unsupported=unsupported, transitions=transitions, groups=groups, objects=objects,
                region_lists=region_lists,
                scope=('Static data: streams framed by the native size table, F0 groups, object and region event '
                       'records with raw bytes and kind-19 trailers, and the 5-byte predicate table. For object '
                       'records value is byte +4 and extra_hex every later byte; for region kind 12, region is the '
                       'u16 at +4, event byte +6, value byte +7. These are storage labels, not the native matchers '
                       '(the matcher width differs per kind; match on raw_hex). No opcode effect, event meaning, '
                       'execution order or timing is claimed.'))


def find_archive(game, level):
    dat = game / 'DAT'
    if re.fullmatch(r'\d+', level):
        hits = sorted(p for p in dat.glob(f'L{int(level)}_*.MIX') if re.fullmatch(r'L\d+_[A-Z]{2}', p.stem.upper()))
    else:
        hits = [p for p in dat.glob('*.MIX') if p.stem.upper() == level.upper()]
    if len(hits) != 1:
        raise SourceError(f'level {level!r}: expected one archive in {dat}, found {len(hits)}')
    return hits[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('game', help="game root containing DAT/ (read only); '-' uses $LOL2_GAME or ./lol2_game")
    parser.add_argument('level', help='archive stem such as L7_DH, or a level number')
    parser.add_argument('output', type=Path, help='output JSON path')
    args = parser.parse_args(argv)
    game = Path(os.environ.get('LOL2_GAME', './lol2_game') if args.game == '-' else args.game).resolve()
    out = args.output.resolve()
    if game == out or game in out.parents:
        parser.error('output must not be inside the game directory')
    try:
        data = export(find_archive(game, args.level))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')
    c = data['counts']
    print(f"{data['area']}: tables {c['object_tables']}, region descriptors {c['region_descriptors']}, "
          f"groups {c['groups']}, commands {c['commands']}, event links {c['event_links']}, "
          f"predicates {c['predicate_trailers']}/{c['predicate_entries']}, transitions {c['transitions']}, "
          f"distinct opcodes {c['distinct_opcodes']}, unsupported {c['unsupported']}")
    for row in data['unsupported']:
        print(f"  UNSUPPORTED stream {row['stream']} file {row['file_offset']} opcode {row['opcode']}: {row['reason']}")
    return 1 if data['unsupported'] else 0


if __name__ == '__main__':
    sys.exit(main())
