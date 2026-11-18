#!/usr/bin/env python3
"""HMI-MIDISONG scores in LOCAL.MIX, converted to standard MIDI in memory.

--data is the game DAT folder, or $LOL2_DAT. LOCAL.MIX and LOLG.DAT sit in
the parent of that folder. --check walks all 33 songs, builds one standard
MIDI file per song in memory, and prints one line. It writes nothing.
--out writes one .mid per song and must be a directory outside this repository.
"""

import os
import struct
import sys

import lol2_cli
from lol2_westwood_hash import ww_hash_v1, ww_hash_v2

OBJ5 = 0x1C1024
MAGIC = b"HMI-MIDISONG061595"
TAIL = bytes.fromhex("2a2e6d69640000000000000000000000")
UNNAMED_KEY = 0x1305A4F0
DIVISION = 120


def u32(blob, off):
    return struct.unpack_from("<I", blob, off)[0]


def u16(blob, off):
    return struct.unpack_from("<H", blob, off)[0]


def parent_file(dat_dir, name):
    path = os.path.join(os.path.dirname(os.path.abspath(dat_dir)), name)
    if not os.path.isfile(path):
        raise FileNotFoundError("%s is not in the parent of the DAT folder" % name)
    return path


def read_vlq(blob, pos, end):
    """MIDI variable-length quantity. Returns (value, new position)."""
    value = 0
    used = 0
    while pos < end and used < 4:
        byte = blob[pos]
        pos += 1
        used += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            return value, pos
    raise ValueError("bad VLQ at %d" % (pos - used))


def write_vlq(value):
    if value < 0:
        raise ValueError("negative VLQ")
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def cstr(blob, off):
    end = blob.index(0, off)
    return blob[off:end].decode("ascii")


def stems_from(image):
    names = []
    for i in range(35):
        ptr = u32(image, 0x1CE10C + 4 * i)
        names.append(cstr(image, OBJ5 + ptr) if ptr else "")
    return names


def hmi_songs(local_bytes):
    data, entries, base = read_mix_with_hashes_bytes(local_bytes)
    songs = []
    for key, offset, size in entries:
        blob = data[base + offset:base + offset + size]
        if blob.startswith(b"HMI-MIDISONG"):
            songs.append((key, blob))
    return songs


def read_mix_with_hashes_bytes(blob):
    """Same layout as lol2_mix_parser, on bytes already read."""
    count, total = struct.unpack_from("<HI", blob, 0)
    base = 6 + 12 * count
    entries = []
    for i in range(count):
        key, offset, size = struct.unpack_from("<III", blob, 6 + 12 * i)
        if offset + size > total:
            raise ValueError("MIX entry exceeds its data")
        entries.append((key, offset, size))
    return blob, entries, base


def track_table(blob):
    if u16(blob, 0xE4) != u32(blob, 0xE4) or blob[0x21] != 0:
        raise ValueError("song count or relative flag")
    count = u16(blob, 0xE4)
    table = u32(blob, 0xE8)
    offsets = [u32(blob, table + 4 * i) for i in range(count)]
    if any(not (0 <= off < len(blob)) for off in offsets):
        raise ValueError("track offset outside the song")
    return offsets


def decode_track(blob, track_off, end):
    """Return (messages, tail_len).

    messages are (tick, order, status, data_bytes). The player reads one VLQ
    delay, then an event. A note-on then has its own duration VLQ, and a
    normal event is followed by the VLQ delay of the next event. Meta 0x2F
    stops the track. The channel that is sent is the track byte at +0x7B.
    """
    if blob[track_off:track_off + 13] != b"HMI-MIDITRACK":
        raise ValueError("track magic")
    if blob[track_off + 0x21] != 0:
        raise ValueError("track relative flag")
    channel = blob[track_off + 0x7B]
    if blob[track_off + 0x7C] != 0 or channel > 15:
        raise ValueError("track channel")
    pos = track_off + u32(blob, track_off + 0x57)
    end_limit = end
    tick = 0
    order = 0
    running = None
    messages = []
    delay, pos = read_vlq(blob, pos, end_limit)
    tick += delay
    while pos < end_limit:
        status_at = blob[pos]
        if status_at >= 0x80:
            status = status_at
            running = status
            flag = 1
        else:
            if running is None:
                raise ValueError("running status missing")
            status = running
            flag = 0
        sent = (status & 0xF0) | channel
        kind = status & 0xF0
        if status == 0xFF:
            if blob[pos:pos + 3] != b"\xff\x2f\x00":
                raise ValueError("meta is not end of track")
            messages.append((tick, order, 0xFF, b"\x2f\x00"))
            tail = blob[pos + 3:end_limit]
            if tail not in (b"", TAIL):
                raise ValueError("unexpected bytes after end of track")
            return messages, len(tail)
        if kind == 0x90:
            if pos + flag + 2 > end_limit:
                raise ValueError("note truncated")
            note = blob[pos + flag]
            velocity = blob[pos + flag + 1]
            pos += flag + 2
            duration, pos = read_vlq(blob, pos, end_limit)
            messages.append((tick, order, sent, bytes((note, velocity))))
            order += 1
            messages.append((tick + duration, order, 0x80 | channel, bytes((note, 0))))
            order += 1
        elif kind in (0xA0, 0xB0, 0xE0):
            if pos + flag + 2 > end_limit:
                raise ValueError("short event")
            data = bytes(blob[pos + flag:pos + flag + 2])
            pos += flag + 2
            messages.append((tick, order, sent, data))
            order += 1
        elif kind in (0xC0, 0xD0):
            if pos + flag + 1 > end_limit:
                raise ValueError("short event")
            data = bytes(blob[pos + flag:pos + flag + 1])
            pos += flag + 1
            messages.append((tick, order, sent, data))
            order += 1
        else:
            raise ValueError("status %02x" % status)
        delay, pos = read_vlq(blob, pos, end_limit)
        tick += delay
    raise ValueError("track ended without FF 2F 00")


def encode_smf(tracks):
    """Format-1 standard MIDI. Division is the file's constant 120."""
    body = bytearray()
    for messages in tracks:
        chunk = bytearray()
        last = 0
        for tick, _order, status, data in sorted(messages):
            if tick < last:
                raise ValueError("tick went backwards")
            chunk += write_vlq(tick - last)
            if status == 0xFF:
                chunk += b"\xff" + data
            else:
                chunk += bytes((status,)) + data
            last = tick
        if not chunk.endswith(b"\xff\x2f\x00"):
            raise ValueError("encoded track has no end")
        body += b"MTrk" + struct.pack(">I", len(chunk)) + chunk
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), DIVISION)
    return header + body


def convert_song(blob):
    offsets = track_table(blob)
    ends = offsets[1:] + [len(blob)]
    decoded = [decode_track(blob, off, end) for off, end in zip(offsets, ends)]
    messages = [item[0] for item in decoded]
    tails = [item[1] for item in decoded]
    return encode_smf(messages), messages, tails


def check(dat_dir):
    image_path = parent_file(dat_dir, "LOLG.DAT")
    local_path = parent_file(dat_dir, "LOCAL.MIX")
    image = open(image_path, "rb").read()
    local = open(local_path, "rb").read()
    if image[0x1C5D90:0x1C5D90 + len(MAGIC)] != MAGIC:
        raise ValueError("magic string moved")
    names = stems_from(image)
    if names[10] != "CLAWWAN1" or names[29] != "SSARPIT1" or names[3] != "badfile":
        raise ValueError("stem table moved")
    wanted = {}
    for stem in names:
        if not stem or stem == "badfile":
            continue
        key = ww_hash_v1("MUSIC\\%s.HMI" % stem)
        if key != ww_hash_v2("MUSIC\\%s.HMI" % stem):
            raise ValueError("hash pair disagrees")
        wanted[key] = stem
    songs = hmi_songs(local)
    if len(songs) != 33 or len(wanted) != 32:
        raise ValueError("song or stem count")
    keys = {key for key, _blob in songs}
    if set(wanted) - keys or keys - set(wanted) != {UNNAMED_KEY}:
        raise ValueError("HMI names")
    note_ons = controllers = pitch = pressure = programs = 0
    tracks = 0
    long_tails = 0
    smallest = None
    for key, blob in songs:
        if not blob.startswith(MAGIC) or u16(blob, 0xD2) != DIVISION or u16(blob, 0xD4) != DIVISION:
            raise ValueError("header")
        if blob[0xA6:0xC6] != b"\x00" * 32:
            raise ValueError("block at 0xA6")
        smf, messages, tails = convert_song(blob)
        if smf[:4] != b"MThd" or struct.unpack_from(">H", smf, 8)[0] != 1:
            raise ValueError("midi header")
        if struct.unpack_from(">H", smf, 10)[0] != len(messages):
            raise ValueError("midi track count")
        if struct.unpack_from(">H", smf, 12)[0] != DIVISION:
            raise ValueError("midi division")
        tracks += len(messages)
        long_tails += sum(1 for n in tails if n == 16)
        if sum(1 for n in tails if n not in (0, 16)):
            raise ValueError("tail length")
        for track in messages:
            for _tick, _order, status, data in track:
                if status == 0xFF:
                    continue
                kind = status & 0xF0
                if any(byte > 127 for byte in data):
                    raise ValueError("data byte")
                if kind == 0x90:
                    note_ons += 1
                elif kind == 0x80:
                    pass
                elif kind == 0xB0:
                    controllers += 1
                elif kind == 0xE0:
                    pitch += 1
                elif kind == 0xA0:
                    pressure += 1
                elif kind == 0xC0:
                    programs += 1
                else:
                    raise ValueError("unexpected status")
        if smallest is None or len(blob) < smallest[0]:
            smallest = (len(blob), key, len(messages), messages[0])
    if tracks != 438 or long_tails != 33:
        raise ValueError("track census")
    if (note_ons, controllers, pitch, pressure, programs) != (80067, 22243, 6188, 1289, 500):
        raise ValueError("event census %s" % ((note_ons, controllers, pitch, pressure, programs),))
    size, key, ntracks, first = smallest
    if (size, key, ntracks) != (5442, 0xD9023FF9, 6):
        raise ValueError("smallest song")
    # First event of the first track: a controller, after a zero delay.
    tick, _order, status, data = first[0]
    if (tick, status & 0xF0, data) != (0, 0xB0, b"\x69\x01"):
        raise ValueError("worked example")
    return ("CHECK hmi: 33 songs, 438 tracks, all end on FF 2F 00; "
            "80067 note-ons with a duration; 32 named, 1 unnamed; "
            "standard MIDI in memory, division 120")


def write_songs(dat_dir, out_dir):
    lol2_cli.refuse_repo_output(out_dir)
    os.makedirs(out_dir)
    image = open(parent_file(dat_dir, "LOLG.DAT"), "rb").read()
    local = open(parent_file(dat_dir, "LOCAL.MIX"), "rb").read()
    names = {ww_hash_v1("MUSIC\\%s.HMI" % stem): stem
             for stem in stems_from(image) if stem and stem != "badfile"}
    for key, blob in hmi_songs(local):
        smf, _messages, _tails = convert_song(blob)
        stem = names.get(key, "unnamed_%08x" % key)
        path = os.path.join(out_dir, stem + ".mid")
        with open(path, "wb") as handle:
            handle.write(smf)


def main(argv):
    ap = lol2_cli.tool_args(
        __doc__,
        out_help="directory outside this repository; one .mid per song (ignored with --check)")
    args = ap.parse_args(argv)
    try:
        if args.check:
            print(check(args.data))
            return 0
        if not args.out:
            ap.print_help()
            return 2
        write_songs(args.data, args.out)
    except (OSError, ValueError) as exc:
        print("CHECK hmi: FAIL %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
