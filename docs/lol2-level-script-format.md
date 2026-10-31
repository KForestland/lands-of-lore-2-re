# LoL2 level script format

Date: 2026-10-31

This note describes the script data inside each level archive (`DAT/L<n>_<xx>.MIX`) and the
exporter that reads it: [`tools/lol2_export_scripts.py`](../tools/lol2_export_scripts.py), with the shared
framing module [`tools/lol2_source_format.py`](../tools/lol2_source_format.py). Both are standard-library
Python and read the user's own game files. No game data is in this repository.

Addresses are virtual addresses in the flattened LE image of `LOLG.DAT` 1.30 (sha256 prefix `b27a3534`);
file offset = VA + 0x37000, as in [`lol2-script-engine-facts-2026-10.md`](lol2-script-engine-facts-2026-10.md).
Engine facts added since then are in [the addendum](lol2-script-engine-facts-2026-10-addendum.md).

## Running the exporter

```bash
python3 tools/lol2_export_scripts.py ./lol2_game L7_DH out/L7_DH.json
python3 tools/lol2_export_scripts.py ./lol2_game 7 out/L7_DH.json
```

The game root must contain `DAT/`. Pass `-` to use `$LOL2_GAME` (default `./lol2_game`). The output may not
be written inside the game directory. Exit code 1 means an opcode outside the size table was found; the
stream is then listed under `unsupported` and nothing is guessed.

Verified by running (2026-10-31, retail files, all 15 level archives): every stream frames exactly with the
37-opcode table (0 unsupported), every object and region list ends with a terminator inside its section,
and every group reference resolves. The totals are 42,594 commands using 32 distinct opcodes. The output
matched the private Godot-port producer it was ported from on every level (groups, objects, region lists,
streams, predicate table and counts).

## Finding the geometry entry

Each level archive holds one geometry entry. It is recognised by its header: dword +0 = 18 (0x12), dword +4
= 5300 (the vertex table offset), and at least 0x244 bytes. The native loader reads 0x244 header bytes and
continues only when dword +0 is 0x12 and dword +0x58 is not zero (PROVEN, loader around file 0xD3CBC).
The MIX key differs per level; it is not needed to find the entry.

## Header fields (PROVEN by consistent reading on all 15 levels)

All offsets are relative to the start of the geometry entry. Each table is "offset field / count field".

| Offset field | Count field | Stride | Contents |
|---|---|---|---|
| +0x04 | +0x50 | 8 | vertices (two s32) |
| +0x0C | +0x58 | 44 | geometry regions (22 u16) |
| +0x14 | +0x60 | 37 | props |
| +0x18 | +0x64 | 33 | controls |
| +0x1C | +0x68 | 56 | actors |
| +0x24 | +0x70 | 41 | movables |
| +0x38 | +0x80 (bytes) | 1 | region event-record lists |
| +0x3C | +0x84 (bytes) | 1 | command stream 0 |
| +0x40 | +0x88 (bytes) | 1 | object event-record lists |
| +0x44 | +0x8C (bytes) | 1 | command stream 1 |
| +0xA4 | +0xAC | 26 | region descriptors |
| +0xBC | +0xB8 | 5 | predicate table (note: offset field after count field) |

Checks behind the strides: on L1_DC and L7_DH the prop table ends exactly where the control table starts,
and stream 1, the object event lists and the prop table are back to back. All object list offsets and region
descriptor list offsets land on valid, terminated lists. The geometry region count (+0x58) matches the
region counts in the Act 2 survey. Other header dwords are not decoded here (UNKNOWN).

The predicate table offset and count were proven from the loader: it passes header +0xBC as a file offset
and +0xB8 as a count to 0x669D4, which reads count x 5 bytes and stores the pointer at 0x2B548 (PROVEN).
Every retail level has 255 entries.

## Object tables

Each object record (actor, prop, control, movable) holds, at word +12, the offset of its event-record list inside the object event-record blob.
The map tools read the first two s16 of each record as its map position (LIKELY; used, not traced).
Other placement bytes are exported raw (`placement_hex`); the documented ones are in
[`lol2-entity-object-map.md`](lol2-entity-object-map.md) and the static-collision notes in the facts doc.

Indexes are per table: actor 57, control 57 and movable 57 of one level are three different objects.

## Region descriptors

Region descriptors are 26-byte rows. Word +0x0A is the offset of the descriptor's event-record list inside
the region event-record blob. Several descriptors can share one list.

## Event records

An event-record list is a run of records: byte 0 = length, byte 1 = kind. A zero length or zero kind ends
the list (native walk, PROVEN). The kinds that name a command group:

- Object lists: kinds 2, 3, 4, 5, 6, 8, 9 and 10 carry a group offset in stream 1 at word +2.
- Region lists: kind 12 (`0x0C`) carries a stream-0 group at word +2, the region index at word +4, an event
  byte at +6 and a value byte at +7.
- Kind 19 (`0x13`) is not a group. A 4-byte kind-19 record directly after another record is that record's
  predicate trailer (`04 13 pp pp`, word +2 = predicate index). See the addendum.

How each kind is matched (byte versus word compares at +4, masks, modes) differs per kind and is in the
addendum. The exporter's `value` and `extra_hex` fields are storage labels, not the native matchers.
Hosts should match on `raw_hex`.

## Command streams

There are two command streams. Stream 0 (header +0x3C/+0x84) is the one named by region kind-12 records;
its base is kept in native global 0x2B51C. Stream 1 (header +0x44/+0x8C) is named by object records; its
base is kept in 0x2B514, and groups run through 0x646EC(group + [0x2B514]).

A command starts with its opcode byte. Its length comes only from the opcode. Opcode 240 (`F0`) heads a
group: byte +4 is the number of commands that follow, and groups do not nest. A command that is not inside
an F0 group is a group of one. A record's group offset is the offset of the F0 header (or the single command)
inside the stream.

## The size table (native 0x645E0)

`0x645E0` reads a command's first byte and returns its length through a compare tree. The 37 opcodes and
their lengths:

| Length | Opcodes |
|---|---|
| 4 | 0 |
| 6 | 1, 2, 5, 6, 7, 9, 12, 16, 17, 21, 23, 197, 198, 199, 200, 201, 206, 207, 210, 240 |
| 8 | 8, 11, 13, 14, 15, 204, 205, 208 |
| 10 | 19, 20, 24, 209 |
| 12 | 3, 196 |
| 18 | 18, 22 |

The returns for opcodes 3, 13 and 204 were read from the routine (PROVEN). The whole table is also
confirmed by framing: all 15 levels frame byte-exactly with it, with no unknown opcode. Opcodes 4, 10 and
25-195 do not occur.

The low dispatcher 0xB6B6E indexes a relocated table by opcode - 1 for opcodes 1-24 and rejects larger
opcodes. Opcodes 196 and 204 are handled by the high dispatcher 0x64770 (PROVEN; see the addendum). How
the other high opcodes are reached is not covered here.

## Level transitions

A command with bytes `02 01 00 00 1C xx` requests a level change: `xx & 31` is the destination level
number and `xx >> 5` is the arrival entry (selector) in that level. The exporter lists these under
`transitions`. Which object or region owns each one, and whether the player can reach it, is a separate
question; see [`lol2-level-graph.md`](lol2-level-graph.md).

## Still open

- Header dwords not listed above, and most placement bytes.
- The meaning of most opcodes; see the facts doc and addendum for the decoded ones.
- Command kind byte (+1) tables beyond the decoded cases.
