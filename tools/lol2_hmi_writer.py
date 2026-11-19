#!/usr/bin/env python3
"""Read stored HMI delays and events and reconstruct each native score."""
from pathlib import Path
import struct

from cli_errors import run_cli
import lol2_cli
from lol2_hmi_midi import MAGIC, TAIL, parent_file, read_vlq, track_table, u16, u32, write_vlq
from lol2_source_format import parse_mix

DATA_SIZES = {0x90: 2, 0xA0: 2, 0xB0: 2, 0xC0: 1, 0xD0: 1, 0xE0: 2}


def read_quantity(blob, at, end):
    value, next_at = read_vlq(blob, at, end)
    return (value, next_at - at), next_at


def write_quantity(field):
    value, width = field
    raw = write_vlq(value)
    if not len(raw) <= width <= 4:
        raise ValueError("value does not fit the stored HMI VLQ width")
    return b"\x80" * (width - len(raw)) + raw


def read_track(blob, start, end):
    if blob[start:start + 13] != b"HMI-MIDITRACK" or blob[start + 0x21] != 0:
        raise ValueError("invalid HMI track header")
    relative = u32(blob, start + 0x57)
    pos = start + relative
    if not 0x7D <= relative < end - start:
        raise ValueError("HMI event offset outside track")
    running, events = None, []
    while pos < end:
        delay, pos = read_quantity(blob, pos, end)
        if pos == end:
            break
        explicit = blob[pos] >= 0x80
        if explicit:
            running = blob[pos]
            pos += 1
        if running is None:
            raise ValueError("missing status before HMI data bytes")
        event = dict(delay=delay, status=running, explicit=explicit)
        if running == 0xFF:
            if not explicit or blob[pos:pos + 2] != b"\x2f\0":
                raise ValueError("unsupported HMI meta event")
            event["data"] = (0x2F, 0)
            events.append(event)
            tail = blob[pos + 2:end]
            if tail not in (b"", TAIL):
                raise ValueError("unrecognized HMI track tail")
            return blob[start:start + relative], events, tail
        kind = running & 0xF0
        width = DATA_SIZES.get(kind)
        if width is None or pos + width > end:
            raise ValueError(f"invalid HMI event {running:#x} at +{pos:#x}")
        event["data"] = tuple(blob[pos:pos + width])
        pos += width
        if kind == 0x90:
            event["duration"], pos = read_quantity(blob, pos, end)
        events.append(event)
    raise ValueError("HMI track has no end event")


def write_track(header, events, tail):
    out = bytearray(header)
    running = None
    for row in events:
        out.extend(write_quantity(row["delay"]))
        status = row["status"]
        if row["explicit"]:
            out.append(status)
            running = status
        elif status != running:
            raise ValueError("implicit HMI event does not match its running status")
        out.extend(row["data"])
        if "duration" in row:
            out.extend(write_quantity(row["duration"]))
    out.extend(tail)
    return bytes(out)


def read_song(blob):
    if not blob.startswith(MAGIC):
        raise ValueError("not a native HMI song")
    offsets = track_table(blob)
    directory = u32(blob, 0xE8)
    table_end = directory + 4 * len(offsets)
    if (not offsets or not 0xEC <= directory <= table_end <= offsets[0]
            or any(a >= b for a, b in zip(offsets, offsets[1:]))):
        raise ValueError("invalid HMI track directory")
    tracks = [read_track(blob, off, end) for off, end in zip(offsets, offsets[1:] + [len(blob)])]
    return blob[:directory], blob[table_end:offsets[0]], tracks


def write_song(header, gap, tracks):
    if u16(header, 0xE4) != len(tracks) or u32(header, 0xE8) != len(header):
        raise ValueError("HMI track count and directory must agree with the header")
    cursor = len(header) + 4 * len(tracks) + len(gap)
    offsets, bodies = [], []
    for track in tracks:
        offsets.append(cursor)
        body = write_track(*track)
        bodies.append(body)
        cursor += len(body)
    return header + struct.pack(f"<{len(offsets)}I", *offsets) + gap + b"".join(bodies)


def check(data):
    path = Path(parent_file(data, "LOCAL.MIX"))
    original = path.read_bytes()
    totals = dict(songs=0, tracks=0, events=0, explicit=0, tails=0)
    for row in parse_mix(original):
        at = row["offset"]
        if original[at:at + len(MAGIC)] != MAGIC:
            continue
        blob = original[at:at + row["size"]]
        song = read_song(blob)
        if write_song(*song) != blob:
            raise ValueError(f"LOCAL.MIX+{at:#x}: reconstructed HMI bytes differ")
        totals["songs"] += 1
        totals["tracks"] += len(song[2])
        totals["events"] += sum(len(events) for _, events, _ in song[2])
        totals["explicit"] += sum(row["explicit"] for _, events, _ in song[2] for row in events)
        totals["tails"] += sum(bool(tail) for _, _, tail in song[2])
    if (totals["songs"], totals["tracks"]) != (33, 438):
        raise ValueError(f"expected 33 songs and 438 tracks, found {totals}")
    print(f"CHECK HMI write: {totals['songs']} byte-identical songs, {totals['tracks']} tracks, "
          f"{totals['events']} events, {totals['explicit']} explicit status bytes, {totals['tails']} tails")


def main():
    parser = lol2_cli.tool_args(__doc__, writes=False)
    args = parser.parse_args()
    if not args.check:
        parser.error("give --check to compare the original scores in memory")
    check(args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
