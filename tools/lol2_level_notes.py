#!/usr/bin/env python3
"""Write evidence notes and JSON Lines indexes for original LoL2 level scripts.

  lol2_level_notes.py --data DAT --out DIR [LEVEL]   # full group list + JSON Lines rows for your own copy
                                                    # (DIR must be outside the repository; all levels if no LEVEL)
  lol2_level_notes.py --data DAT --summary docs/levels/notes   # the small per-level summaries + one excerpt
  lol2_level_notes.py --data DAT --check             # re-derive and compare the committed summaries

The full listings are a transformed copy of the game's scripts: they are tool
output for the user's own game files and are never committed.

The output describes static commands, matcher operands and references. It never
runs a script. See docs/levels/notes/README.md for the row schema.
"""

import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

import lol2_cli
from lol2_disassemble_scripts import EXPECTED_LEVELS, select_archive, verify
from lol2_export_scripts import SourceError, export, require
from lol2_level_report import item_identities
from lol2_media_check import scene_names


# All instruction addresses use the retail 1.30 analysis convention from
# docs/lol2-script-opcodes.md and docs/lol2-script-events.md.
OBJECT_SELECTORS = {
    1: ('player', 0x5FC12), 2: ('actor', 0x5FC1B), 3: ('prop', 0x5FC43),
    4: ('placed_item', 0x5FC6B), 0x10: ('control', 0x5FC91),
    0x20: ('movable', 0x5FCB5), 0xC0: ('bound_object', 0x5FD29),
}
OBJECT_COMMANDS = {1, 3, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 19, 20, 23, 24}
OPCODE_EVIDENCE = {
    1: ('call object command vtable +0xAC', 0xB5937),
    3: ('call object command vtable +0xAC', 0xB5937),
    5: ('call object vtable +0xB0', 0xB5970),
    6: ('submit object action', 0xB3EC8),
    7: ('call object vtable +0xB4', 0xB5997),
    8: ('call object command vtable +0xAC', 0xB5A1B),
    9: ('submit object property', 0xB50C0),
    11: ('submit indexed request', 0xA1A74),
    12: ('submit resource or audio request', 0xED6D0),
    13: ('call object command vtable +0xAC', 0xB5937),
    15: ('submit secondary-object request', 0xB5C82),
    22: ('submit an audio request using sequence parameters', 0xB5C3B),
    196: ('submit signed region heights and flags', 0x64DDC),
    197: ('submit region action', 0x64CD4),
    204: ('update region or auxiliary row', 0x647B3),
    208: ('submit duration or region request', 0x65518),
    210: ('submit settings subcommand', 0x65954),
}
EVENTS = {
    1: ('object render parameter record', 0x5A344),
    2: ('timer record', 0xB8BA0), 3: ('event byte', 0xAD7F4),
    4: ('held-item test', 0xADD36), 5: ('event and value', 0xAD8E0),
    6: ('value byte', 0xADDE0), 7: ('health threshold', 0xAE134),
    8: ('value word (65535 wildcard)', 0xAE510), 9: ('hit filter', 0xAE2C8),
    10: ('region or object match', 0xAE608), 11: ('selector and event', 0xF2FC0),
    12: ('region event', 0xF2D87), 15: ('region comparison', 0xF37C8),
    19: ('predicate trailer', 0x66AB0),
}
TIMER_ACTIONS = ('change flags', 'change reload operand 1', 'change reload operand 2',
                 'start', 'stop', 'reload', 'reload with temporary operand 1')
TIMER_ADDRESSES = (0xB482C, 0xB483C, 0xB484C, 0xB485C, 0xB494B, 0xB49BA, 0xB49D1)
PROPERTIES = {2: ('unlink object', 0xB50E6), 3: ('link object', 0xB5117),
              16: ('stop object sound', 0xB5401), 17: ('set object flag 0x4000', 0xB50FB),
              18: ('clear object flag 0x4000', 0xB5109), 21: ('send kind 6 value 20', 0xB5448)}
ARRAYS = {198: ('local', 'set', 0x64887), 199: ('shared', 'set', 0x64A8C),
          200: ('shared', 'randomize up to', 0x64BB4), 201: ('local', 'randomize up to', 0x64906),
          206: ('shared', 'add', 0x64B1C), 207: ('local', 'add', 0x648AF)}
SHARED_CAPS = {0: 10, 12: 2, 13: 2}
REGION_FLAGS = {0: ('+0x1C', 'clear', 1, 0x64D28), 1: ('+0x1C', 'clear', 2, 0x64D33),
                2: ('+0x1C', 'set', 1, 0x64D3E), 3: ('+0x1C', 'set', 2, 0x64D49),
                4: ('+0x1C', 'set', 3, 0x64D5F), 5: ('+0x1C', 'clear', 3, 0x64D54),
                6: ('secondary+0x19', 'clear', 4, 0x64D6A), 7: ('secondary+0x19', 'set', 4, 0x64D90),
                8: ('+0x1D', 'set', 1, 0x64D1D), 9: ('+0x1D', 'clear', 1, 0x64D12)}


def word(raw, offset):
    return struct.unpack_from('<H', raw, offset)[0]


def signed(value, bits=8):
    return value if value < (1 << (bits - 1)) else value - (1 << bits)


def effect(row, items, scenes):
    raw = bytes.fromhex(row['raw_hex'])
    opcode, kind, index = row['opcode'], row['kind'], row['target']
    target = None
    if opcode in OBJECT_COMMANDS and kind in OBJECT_SELECTORS:
        scope, selector = OBJECT_SELECTORS[kind]
        target = [scope, None if scope in ('player', 'bound_object') else index, selector]
    if opcode in (196, 197, 208, 209) and kind == 0x90:
        target = ['region', index, 0x5FCE6]
    if opcode == 2 and raw[1:5] == b'\x01\x00\x00\x1c':
        return f'request level {raw[5] & 31}, arrival {raw[5] >> 5}', 0xD8797, True, ['exit', raw[5] & 31, None]
    if opcode == 2:
        return f'submit game subcommand {raw[4]}, argument {raw[5]}', 0xB5BAC, False, None
    if opcode == 3 and kind in (1, 2):
        identity = struct.unpack_from('<I', raw, 4)[0]
        recipient = 'player' if kind == 1 else f'actor {index}'
        address = 0xD78D9 if kind == 1 else 0xA6334
        return (f'grant {recipient} item definition {items[identity]}, instance byte +4 = {raw[8]}',
                address, True, ['item_definition', items[identity], 0x95B80])
    if opcode == 13 and kind == 2 and raw[4] in (0, 1):
        label = 'behavior' if raw[4] == 0 else 'secondary action'
        address = (0xA6365, 0xA639A)[raw[4]]
        return f'set {label} pair to {raw[5]} for admitted actor', address, True, target
    if opcode == 14 and raw[4] < len(TIMER_ACTIONS):
        return (f'{TIMER_ACTIONS[raw[4]]} for kind-2 timer {raw[6]} (argument {raw[5]})',
                TIMER_ADDRESSES[raw[4]], True, target)
    if opcode in (16, 17):
        value = raw[4] if opcode == 16 else signed(raw[4])
        description = f'set object state +0x25 to {value}' if opcode == 16 else f'add {value} to object state +0x25 (0–255)'
        return description, (0xB5A3C if opcode == 16 else 0xB5A76), True, target
    if opcode in (5, 7):
        value = raw[4] if opcode == 5 else signed(raw[4])
        slot, address = (0xB0, 0xB5970) if opcode == 5 else (0xB4, 0xB5997)
        return f'call the selected object’s slot +0x{slot:X} with {value} and {raw[5]}', address, False, target
    if opcode == 15:
        other = OBJECT_SELECTORS.get(raw[5])
        secondary = f'{other[0].replace("_", " ")} {word(raw, 6)}' if other else f'selector {raw[5]}:{word(raw, 6)}'
        return (f'copy {secondary} coordinates, offset Z by its height byte and apply action {raw[4]}',
                0xB5C82, False, target)
    if opcode == 18:
        immediate = bool(word(raw, 0xA) & 0x20)
        description = ('reset sequence progress, clear slot and send kind 6 value 6' if immediate
                       else 'queue the sequence for the position and orientation update when its slot is vacant')
        return description, 0xB59CE, True, target
    if opcode == 19:
        return (f'deliver hit with masks 0x{word(raw,4):X}/0x{word(raw,6):X}, magnitude {raw[8]}, mode {raw[9]}',
                0x66130, True, target)
    if opcode == 20:
        return f'request audio index {word(raw,4)}', 0xB5C0D, True, target
    if opcode == 21:
        scene = raw[4]
        require(scene < len(scenes), f'out-of-range movie scene {scene}')
        return f'play movie scene {scene} `{scenes[scene]}`', 0xCF2B4, True, ['scene', scene, None]
    if opcode == 24:
        return (f'request sound resource 0x3103, send kind-8 value {word(raw, 4)} on early exit',
                0xE3FED, True, target)
    if opcode == 23:
        return 'store low byte of shifted RNG result in object state +0x25', 0xB5A4C, True, target
    if opcode == 9 and raw[4] in PROPERTIES:
        description, address = PROPERTIES[raw[4]]
        return description, address, True, target
    if opcode == 9 and raw[4] == 19:
        return f'set object byte +0x26 to {raw[5]}', 0xB5420, True, target
    if opcode in ARRAYS:
        scope, operation, address = ARRAYS[opcode]
        value = signed(raw[5]) if opcode in (206, 207) else raw[5]
        index = raw[4]
        cap = SHARED_CAPS.get(index) if scope == 'shared' else None
        qualifier = f' (cap {cap})' if cap is not None else ''
        if opcode in (206, 207):
            qualifier = f' (clamped to 0–{cap if cap is not None else 255})'
        return f'{operation} {value} at {scope} byte {index}{qualifier}', address, True, [scope, index, None]
    if opcode == 196:
        surface = 'ceiling' if raw[6] & 1 else 'floor'
        height = 'delta' if raw[6] & 8 else 'target height'
        return (f'move {surface}, {height} {signed(word(raw,4),16)}, rate operand {raw[7]}',
                0x64DDC, True, ['region', index, None])
    if opcode == 197 and raw[4] in REGION_FLAGS:
        field, operation, bits, address = REGION_FLAGS[raw[4]]
        return f'{operation} region bits 0x{bits:X} at {field}', address, True, ['region', index, None]
    if opcode == 204:
        selector, value = signed(word(raw,4),16), word(raw,6)
        if selector == -1:
            return f'update region bytes +0x20/+0x27 from {value}', 0xF44CC, True, ['region', index, None]
        if selector == -2:
            return f'set region byte +0x22 to {raw[6]}', 0x647B3, True, ['region', index, None]
        return f'set auxiliary row {selector} value to {value} and mark bit 0x40', 0x647B3, True, None
    if opcode == 208 and raw[4] == 0:
        return (f'update duration cells 0x26B4E/0x26B52 with mode {raw[5]} and {raw[6]} × 60 elapsed units',
                0x65518, True, ['duration_cells', None, None])
    if opcode == 209:
        deltas = struct.unpack_from('<hhh', raw, 4)
        return f'move eligible objects in region group by {deltas}', 0x6583C, True, target
    if opcode == 210:
        settings = {
            0: 'select primary music stem', 1: 'select secondary music stem',
            4: 'set both primary music values from', 5: 'set both secondary music values from',
            8: 'set primary music value or pair from', 9: 'set secondary music value or pair from',
        }
        if raw[4] in settings:
            return f'{settings[raw[4]]} {raw[5]}', 0x6596D, True, ['music_settings', None, None]
    if opcode == 9:
        return f'submit object property {raw[4]} with argument {raw[5]}', 0xB50C0, False, target
    description, address = OPCODE_EVIDENCE[opcode]
    return f'{description}, operand +4 = {raw[4]}', address, False, target


def event_fields(kind, raw, items):
    if kind == 1:
        return dict(flags=word(raw,2), progress=signed(word(raw,4),16), operand=word(raw,6),
                    operand_8=raw[8], start=signed(raw[9]), end=signed(raw[10]),
                    period=raw[11], z_offset=signed(raw[12]), live=raw[13])
    if kind == 2:
        return dict(flags=raw[4], status=raw[5], reload_a=raw[6], reload_b=raw[7], countdown=word(raw,8))
    if kind == 3:
        return dict(event=raw[4])
    if kind == 4:
        operand = struct.unpack_from('<I', raw, 6)[0]
        fields = dict(mode=raw[4], invert=bool(raw[5]), operand=operand)
        if raw[4] == 3:
            fields['item_definition'] = items.get(operand)
        return fields
    if kind == 5:
        return dict(event=raw[4], value=raw[5])
    if kind == 6:
        return dict(value=raw[4])
    if kind == 7:
        return dict(mode=raw[4], threshold=raw[5])
    if kind == 8:
        return dict(value=word(raw,4))
    if kind == 9:
        return dict(mask_a=word(raw,4), mask_b=word(raw,6), threshold=raw[8], flags=raw[9])
    if kind == 10:
        return dict(event=raw[4], selector=word(raw,6))
    if kind in (11, 12):
        return dict(selector=word(raw,4), event=raw[6], value=raw[7])
    if kind == 15:
        return dict(region=word(raw,4), mode=raw[6], operand_source=raw[7], value=word(raw,8))
    if kind == 19:
        return dict(predicate=word(raw,2))
    return {}


def make_index(level, items, scenes):
    """Build group rows plus placements, unique list starts and event records."""
    triggers = defaultdict(set)
    source_rows, lists, records = [], {}, {}
    for obj in level['objects']:
        if obj['table'] == 'region':
            continue
        source_rows.append(dict(type='placement', table=obj['table'], index=obj['index'],
                                offset=obj['file_offset'], list_offset=obj['list_file_offset']))
        lists[obj['list_file_offset']] = ('object', obj['events'], [])
    for entry in level['region_lists']:
        lists[entry['list_file_offset']] = ('region', entry['records'], entry['descriptors'])
    for offset, (space, events, descriptors) in sorted(lists.items()):
        source_rows.append(dict(type='list', space=space, offset=offset, descriptors=descriptors,
                                events=[event['file_offset'] for event in events]))
        for event in events:
            at, kind = event['file_offset'], event['kind']
            if at in records:
                continue
            label, matcher = EVENTS[kind]
            predicate = event.get('predicate')
            operands = event_fields(kind, bytes.fromhex(event['raw_hex']), items)
            group = [event['stream'], event['group']] if 'group' in event else None
            if group is not None:
                triggers[tuple(group)].add(at)
            records[at] = dict(type='event', space=space, offset=at, kind=kind, matcher=matcher,
                               effect=label, operands=operands, group=group,
                               predicate=[predicate['index'], predicate['trailer_file_offset'],
                                          predicate['entry_file_offset']] if predicate else None,
                               status='CONFIRMED' if matcher is not None else 'UNCONFIRMED')
    group_rows = []
    for group in level['groups']:
        stream, index = group['stream'], group['group']
        commands = []
        for command in group['commands']:
            description, address, confirmed, target = effect(command, items, scenes)
            commands.append([command['file_offset'], command['opcode'], command['kind'], command['target'],
                             target, description, address, 'CONFIRMED' if confirmed else 'UNCONFIRMED'])
        group_rows.append(dict(stream=stream, group=index, offset=group['file_offset'],
                               triggers=sorted(triggers[stream, index]), commands=commands))
    require(sum(len(row['commands']) for row in group_rows) == level['counts']['commands'], 'command lost')
    return group_rows, source_rows + [records[at] for at in sorted(records)]


def trigger_description(event, hosts):
    """Describe the native comparison at the matched placement or region."""
    data = event['operands']
    kind = event['kind']
    if kind == 11:
        return f'{hosts} matches selector {data["selector"]} and event {data["event"]}'
    if kind == 12:
        region, event_id, value = data['selector'], data['event'], data['value']
        values = {1: f' and input is at least {value} × 4',
                  8: f' and input is at least {value}',
                  9: f' and input is at least {value} × 4'}
        condition = ' and input is nonzero' if event_id in (2, 3, 4) and value else values.get(event_id, '')
        return f'region {region} receives event {event_id}{condition} ({hosts})'
    if kind == 15:
        return (f'region {data["region"]} passes comparison mode {data["mode"]} against '
                f'{data["value"]} from operand source {data["operand_source"]}')
    if kind == 2:
        return f'{hosts} timer expires (reload {data["reload_a"]}/{data["reload_b"]})'
    if kind == 3:
        return f'{hosts} receives event {data["event"]}'
    if kind == 4:
        if data['mode'] == 0:
            condition = 'has an item selected' if data['invert'] else 'has no item selected'
            return f'{hosts} interaction finds the player {condition}'
        item = data.get('item_definition')
        operand = f'item definition {item}' if item is not None else f'operand {data["operand"]}'
        inversion = ' inverted' if data['invert'] else ''
        return f'{hosts} passes held-item test {data["mode"]}{inversion} with {operand}'
    if kind == 5:
        value = data['value']
        return f'{hosts} receives event {data["event"]} with ' + ('any value' if value == 255 else f'value {value}')
    if kind in (6, 8):
        value = data['value']
        operand = 'any value' if kind == 8 and value == 65535 else f'value {value}'
        return f'{hosts} receives kind-{kind} {operand}'
    if kind == 7:
        return f'{hosts} meets health threshold {data["threshold"]} in mode {data["mode"]}'
    if kind == 9:
        return (f'{hosts} receives a hit matching masks {data["mask_a"]}/{data["mask_b"]}, '
                f'threshold {data["threshold"]} and flags {data["flags"]}')
    if kind == 10:
        return f'{hosts} matches event {data["event"]} with region or object selector {data["selector"]}'
    return f'{hosts} matches kind {kind} [UNCONFIRMED condition]'


def group_description(group, events, event_owners, level_names):
    """Describe each group's trigger, effects and targets in stream order."""
    matches = []
    for at in group['triggers']:
        event = events[at]
        hosts = ', '.join(sorted(event_owners[at]))
        guard = f' and predicate {event["predicate"][0]} passes' if event['predicate'] else ''
        matches.append(trigger_description(event, hosts) + guard)
    when = ' or '.join(matches) if matches else 'UNCONFIRMED producer'
    actions, targets = [], []
    for offset, opcode, kind, index, target, description, address, status in group['commands']:
        if target:
            scope, selector, _ = target
            if scope == 'exit':
                name = level_names.get(selector, f'level {selector}')
                description = description.replace(f'level {selector},', f'{name},', 1)
                targets.append(f'exit to {name}')
            else:
                label = scope.replace('_', ' ')
                targets.append(label if selector is None else f'{label} {selector}')
        if opcode == 14:
            targets.append(description.split(' for ', 1)[1].split(' (', 1)[0])
        if kind == 2 and opcode == 3:
            targets.append(f'actor {index}')
        state = ' [UNCONFIRMED]' if status == 'UNCONFIRMED' else ''
        actions.append(f'{description} (op {opcode}, code `0x{address:X}`){state}')
    does = ' → '.join(actions) if actions else 'empty command list'
    touches = ', '.join(dict.fromkeys(targets)) or 'no explicit target decoded'
    return (f'- **{group["stream"]}:{group["group"]}** (`0x{group["offset"]:X}`) — *When* {when}. '
            f'*Does* {does}. *Touches* {touches}.')


def split_files(stem, extension, lines, heading=''):
    """Split large local listings at row boundaries."""
    files, part, size = {}, [], len(heading.encode('utf-8'))
    for line in lines:
        length = len(line.encode('utf-8'))
        if part and size + length > 900_000:
            suffix = f'-{len(files) + 1}' if files else ''
            files[f'{stem}{suffix}.{extension}'] = heading + ''.join(part)
            part, size = [], len(heading.encode('utf-8'))
        part.append(line)
        size += length
    suffix = f'-{len(files) + 1}' if files else ''
    files[f'{stem}{suffix}.{extension}'] = heading + ''.join(part)
    return files


def jsonl_files(name, category, rows):
    return split_files(f'{name}.{category}', 'jsonl',
                       (json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows))


def notes(level, groups, sources, group_files, event_files, full=True):
    name, counts = level['area'], level['counts']
    events = {row['offset']: row for row in sources if row['type'] == 'event'}
    owners = defaultdict(set)
    for row in sources:
        if row['type'] == 'placement':
            owners[row['list_offset']].add(f"{row['table']} {row['index']}")
    event_owners = defaultdict(set)
    for row in sources:
        if row['type'] == 'list':
            hosts = owners[row['offset']] or {f'descriptor {i}' for i in row['descriptors']}
            for at in row['events']:
                event_owners[at].update(hosts)
    kinds = Counter(row['kind'] for row in events.values())
    unconfirmed = Counter(cmd[1] for group in groups for cmd in group['commands'] if cmd[-1] == 'UNCONFIRMED')
    direct = sum(bool(g['triggers']) for g in groups)
    geo = level['source']['geometry_entry_offset']
    group_links = ', '.join(f'[{i}]({path})' for i, path in enumerate(group_files, 1))
    event_links = ', '.join(f'[{i}]({path})' for i, path in enumerate(event_files, 1))
    groups_line = (f'- [Groups and commands]({next(iter(group_files))})' if len(group_files) == 1
                   else f'- Groups and commands, parts {group_links}')
    events_line = (f'- [Placements, lists and event records]({next(iter(event_files))})' if len(event_files) == 1
                   else f'- Placements, lists and event records, parts {event_links}')
    lines = [f'# {name} script records', '',
             f'**CONFIRMED.** `{name}.MIX+0x{geo:X}` is the base for the geometry header. '
             f'Both streams (`+0x3C` and `+0x44` header fields) frame {counts["commands"]:,} commands in '
             f'{len(groups):,} groups. {direct:,} groups have at least one direct event reference. '
             f'The four placement tables supply {counts["placements"]:,} rows and the region table supplies '
             f'{counts["region_descriptors"]:,} descriptor rows. Their lists contain {len(events):,} distinct '
             'event record offsets. The files use absolute MIX offsets and retail 1.30 analysis addresses.', '',
             *([groups_line, events_line] if full else [
                 f'- The full group list and the JSON Lines rows are output of `tools/lol2_level_notes.py --data DAT '
                 f'--out <folder outside the repository> {name}`; they are not part of the repository.'] +
                 ([f'- [Worked excerpt: the first {EXCERPT_GROUPS} groups with a direct trigger]({name}.excerpt.md)']
                  if name == EXCERPT_LEVEL else [])),
             '- [Schema, commands and matcher evidence](README.md)', '', '## Matchers in this archive', '',
             '| Kind | Records at distinct offsets | First MIX offset | Matcher | Status |',
             '|---:|---:|---:|---|---|']
    for kind, count in sorted(kinds.items()):
        at = min(at for at, row in events.items() if row['kind'] == kind)
        label, address = EVENTS[kind]
        evidence = f'`0x{address:X}`' if address is not None else 'native consumer open'
        status = 'CONFIRMED' if address is not None else 'UNCONFIRMED'
        lines.append(f'| {kind} | {count:,} | `0x{at:X}` | {evidence} | {status} |')
    lines.extend(('', '## Traced command sites', '',
                  '| Group | First linked event examined | Command MIX offset | Effect | Code VA |',
                  '|---|---|---|---|---|'))
    categories = {'exit': False, 'item_definition': False, 'local': False, 'shared': False,
                  'actor': False, 'timer': False, 'state': False, 'region': False}
    for group in groups:
        if not group['triggers']:
            continue
        at = group['triggers'][0]
        event = events[at]
        owner = ', '.join(sorted(event_owners[at])[:2])
        predicate = f' / pred. {event["predicate"][0]}' if event['predicate'] else ''
        for offset, opcode, _, _, target, description, address, status in group['commands']:
            category = {13: 'actor', 14: 'timer', 16: 'state', 17: 'state'}.get(opcode)
            if category is None and target and target[0] != 'actor':
                category = target[0]
            if status != 'CONFIRMED' or category not in categories or categories[category]:
                continue
            categories[category] = True
            lines.append(f'| {group["stream"]}:{group["group"]} | {owner} / kind {event["kind"]} '
                         f'`0x{at:X}`{predicate} | `0x{offset:X}` | {description} | `0x{address:X}` |')
    lines.extend(('', 'The table shows **CONFIRMED** static effects at admitted command sites. '
                  'For a row with a predicate, evaluate the trailer before treating the event as eligible. '
                  'Native match conditions are in the [event reference](../../lol2-script-events.md#event-records).', '',
                  *(['## Groups', '',
                  'Each line gives the direct event alternatives, admitted commands in stream order, and explicit targets. '
                  'Offsets refer to this MIX. Event links, commands and targets are **CONFIRMED** unless marked '
                  '**UNCONFIRMED**. A matcher plus a predicate guard describes eligibility.', ''] if full else []),
                  '## Open behavior', '',
                  '**UNCONFIRMED.** The annotated archive data identify the exact dispatch sites and operands '
                  'below any unresolved effects. An empty direct-trigger list leaves the producer open. '
                  'For virtual calls, resolve the target placement’s runtime class and its table slot, '
                  'then trace that implementation. For unresolved event IDs, trace callers to the matcher '
                  'addresses listed above.', '',
                  'Opcode sites with effects still open: ' + (', '.join(f'{k} ×{v}' for k, v in sorted(unconfirmed.items()))
                                                             if unconfirmed else 'none') + '.'))
    level_names = {int(stem.split('_')[0][1:]): stem for stem in EXPECTED_LEVELS}
    details = [group_description(group, events, event_owners, level_names) + '\n' for group in groups]
    if not full:
        return '\n'.join(lines) + '\n', details
    at = lines.index('## Open behavior')
    part_files = {}
    if sum(len(line.encode('utf-8')) for line in details) < 850_000:
        lines[at:at] = [''.join(details).rstrip(), '']
    else:
        heading = f'# {name} groups\n\nOriginal MIX offsets and native VAs. [Evidence and matchers]({name}.md).\n\n'
        part_files = split_files(f'{name}.group-notes', 'md', details, heading)
        links = [f'- [Part {i}]({path})' for i, path in enumerate(part_files, 1)]
        lines[at:at] = links + ['']
    return '\n'.join(lines) + '\n', part_files


EXCERPT_LEVEL = 'L1_DC'
EXCERPT_GROUPS = 20


def summary_files(data, name, items, scenes):
    """The small per-level summary kept in the repository, plus the one worked excerpt."""
    level = export(select_archive(data, name))
    verify(level)
    groups, events = make_index(level, items, scenes)
    name = level['area']
    page, details = notes(level, groups, events, {}, {}, full=False)
    files = {f'{name}.md': page}
    if name == EXCERPT_LEVEL:
        picked = [d for g, d in zip(groups, details) if g['triggers']][:EXCERPT_GROUPS]
        files[f'{name}.excerpt.md'] = (
            f'# {name}: worked excerpt\n\nThe first {len(picked)} groups of `{name}` that have a direct event trigger, '
            'as written by `tools/lol2_level_notes.py`. Each line gives the trigger, the commands in order and what '
            'they touch. The full list for every level is output of the tool on your own game files and is not part '
            f'of the repository. [Summary]({name}.md), [schema](README.md).\n\n' + ''.join(picked))
    return files


def render(data, name, items, scenes):
    level = export(select_archive(data, name))
    verify(level)
    groups, events = make_index(level, items, scenes)
    name = level['area']
    group_files = jsonl_files(name, 'groups', groups)
    event_files = jsonl_files(name, 'events', events)
    page, part_files = notes(level, groups, events, group_files, event_files)
    return {f'{name}.md': page, **group_files, **event_files, **part_files}


def main():
    parser = lol2_cli.tool_args(__doc__, out_help='directory outside the repository for full notes')
    parser.add_argument('level', nargs='?')
    parser.add_argument('--summary', help='write the per-level summaries and the worked excerpt here (docs/levels/notes in this repository)')
    args = parser.parse_args()
    data = Path(args.data).resolve()
    try:
        items = item_identities(data)
        _, scenes = scene_names(data)
        if args.check:
            if args.level or args.out or args.summary:
                parser.error('--check re-derives the committed summaries without writing')
            root = Path(__file__).resolve().parents[1] / 'docs' / 'levels' / 'notes'
            groups = commands = 0
            for name in EXPECTED_LEVELS:
                for filename, content in summary_files(data, name, items, scenes).items():
                    require((root / filename).read_text(encoding='utf-8') == content, f'stale summary: {filename}')
                level = export(select_archive(data, name))
                g, _ = make_index(level, items, scenes)
                require(len(g) == level['counts']['groups'], f'{name}: group count')
                groups += len(g)
                commands += sum(len(x['commands']) for x in g)
            print(f'CHECK level_notes: {len(EXPECTED_LEVELS)} level summaries and the {EXCERPT_LEVEL} excerpt reproduced '
                  f'byte-for-byte; {groups:,} groups with {commands:,} commands re-derived (full listings are tool output, '
                  'not tracked)')
        elif args.summary:
            output = Path(args.summary)
            output.mkdir(parents=True, exist_ok=True)
            for name in EXPECTED_LEVELS:
                for filename, content in summary_files(data, name, items, scenes).items():
                    (output / filename).write_text(content, encoding='utf-8')
            print(f'wrote {len(EXPECTED_LEVELS)} summaries to {output}')
        elif args.out:
            output = Path(lol2_cli.refuse_repo_output(args.out)).resolve()
            require(data.parent != output and data.parent not in output.parents,
                    'output must be outside the game directory')
            output.mkdir(parents=True, exist_ok=True)
            for name in ([args.level] if args.level else EXPECTED_LEVELS):
                for filename, body in render(data, name, items, scenes).items():
                    (output / filename).write_text(body, encoding='utf-8')
            print(f'wrote the full notes to {output}')
        else:
            parser.error('give --out DIR (full listings, outside the repository), --summary DIR, or --check')
    except (OSError, SourceError, KeyError, ValueError, struct.error) as error:
        print(f'level_notes: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
