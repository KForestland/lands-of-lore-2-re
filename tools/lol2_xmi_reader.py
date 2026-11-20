#!/usr/bin/env python3
"""Read the original XMIDI scores in LoL2 LOCAL.MIX. Lists metadata only."""

from collections import Counter
from pathlib import Path
from struct import iter_unpack, unpack_from

from cli_errors import run_cli, game_path
import lol2_cli
from lol2_hmi_midi import credits_paths, read_vlq, stems_from
from lol2_source_format import parse_mix
from lol2_westwood_hash import ww_hash_v1, ww_hash_v2


def chunks(blob, start, end):
    """Yield each IFF tag and payload bounds, accounting for alignment."""
    while start < end:
        if start + 8 > end:
            raise ValueError(f"incomplete IFF header at +{start:#x}")
        tag, size = unpack_from(">4sI", blob, start)
        payload = start + 8
        finish = payload + size
        after = finish + (size & 1)
        if after > end:
            raise ValueError(f"IFF chunk at +{start:#x} extends outside its container")
        yield tag, payload, finish
        start = after


def events(blob, start, end):
    """Yield (offset, tick, status, meta_type, channel data, duration)."""
    at = start
    tick = 0
    while at < end:
        while at < end and blob[at] < 0x80:
            tick += blob[at]
            at += 1
        if at == end:
            break
        offset, status = at, blob[at]
        at += 1
        meta = duration = None
        family = status >> 4
        if 8 <= family <= 14:
            size = 1 if family in (12, 13) else 2
            if at + size > end or any(byte & 0x80 for byte in blob[at:at + size]):
                raise ValueError(f"invalid XMIDI channel operands at +{offset:#x}")
            data = blob[at:at + size]
            at += size
            if family == 9:
                duration, at = read_vlq(blob, at, end)
        elif status in (0xF0, 0xF7, 0xFF):
            if status == 0xFF:
                if at == end:
                    raise ValueError(f"missing meta type at +{offset:#x}")
                meta = blob[at]
                at += 1
            size, at = read_vlq(blob, at, end)
            if at + size > end:
                raise ValueError(f"invalid XMIDI system record at +{offset:#x}")
            data = blob[at:at + size]
            at += size
        else:
            raise ValueError(f"unknown XMIDI status {status:#x} at +{offset:#x}")
        yield offset, tick, status, meta, data, duration
        if status == 0xFF and meta == 0x2F:
            if data or blob[at:end] not in (b"", b"\0"):
                raise ValueError(f"unexpected bytes at end of XMIDI sequence +{offset:#x}")
            return
    raise ValueError("XMIDI sequence lacks an end marker")


def inspect_song(blob):
    """Read the retail FORM XDIR and CAT XMID framing and every stored event."""
    outer = list(chunks(blob, 0, len(blob)))
    if [tag for tag, _, _ in outer] != [b"FORM", b"CAT "]:
        raise ValueError("expected FORM XDIR followed by CAT XMID")
    (_, xdir, directory_end), (_, xmid, catalog_end) = outer
    if blob[xdir:xdir + 4] != b"XDIR" or blob[xmid:xmid + 4] != b"XMID":
        raise ValueError("wrong XMIDI container types")
    directory = list(chunks(blob, xdir + 4, directory_end))
    if len(directory) != 1 or directory[0][0] != b"INFO":
        raise ValueError("missing XMIDI sequence count")
    _, info, info_end = directory[0]
    if info_end - info != 2:
        raise ValueError("wrong INFO length")
    count, = unpack_from("<H", blob, info)
    sequences = list(chunks(blob, xmid + 4, catalog_end))
    if not count or count != len(sequences):
        raise ValueError("XMIDI sequence directory count disagrees with CAT")

    output = []
    for tag, start, end in sequences:
        if tag != b"FORM" or blob[start:start + 4] != b"XMID":
            raise ValueError("expected XMID sequence")
        sections = list(chunks(blob, start + 4, end))
        if [tag for tag, _, _ in sections] != [b"TIMB", b"EVNT"]:
            raise ValueError("expected a TIMB list and EVNT sequence")
        (_, table, table_end), (_, seq, seq_end) = sections
        if table_end - table < 2:
            raise ValueError("short TIMB")
        timbres, = unpack_from("<H", blob, table)
        if table_end - table != 2 + 2 * timbres:
            raise ValueError("TIMB count disagrees with its length")
        pairs = tuple(iter_unpack("BB", blob[table + 2:table_end]))
        output.append((table, pairs, seq, tuple(events(blob, seq, seq_end))))
    return output


def check(data, listing):
    image = game_path(data.parent, "LOLG.DAT").read_bytes()
    _, credits = credits_paths(image)
    paths = [f"MUSIC\\{s}.XMI" for s in stems_from(image) if s and s != "badfile"]
    paths.append(credits[:-4] + ".XMI")
    names = {}
    for path in paths:
        key = ww_hash_v1(path)
        if ww_hash_v2(path) != key or key in names:
            raise ValueError(f"ambiguous XMIDI key for {path}")
        names[key] = path
    seen = set()
    counts = Counter()
    local = game_path(data.parent, "LOCAL.MIX").read_bytes()
    for row in parse_mix(local):
        key, at, size = row["key"], row["offset"], row["size"]
        if local[at:at + 4] != b"FORM":
            continue
        if key not in names or key in seen:
            raise ValueError(f"LOCAL.MIX+{at:#x}: unknown or duplicate FORM key")
        seen.add(key)
        try:
            sequences = inspect_song(local[at:at + size])
        except ValueError as error:
            raise ValueError(f"LOCAL.MIX+{at:#x}: {error}") from error
        for table, pairs, seq, stream in sequences:
            counts["sequences"] += 1
            counts["timbres"] += len(pairs)
            counts["events"] += len(stream)
            counts["notes"] += sum(duration is not None for *_, duration in stream)
            if listing:
                print(f"{names[key]} entry {row['index']} key={key:08X} LOCAL.MIX+{at:#x} "
                      f"TIMB+{table:#x} ({len(pairs)}) EVNT+{seq:#x} ({len(stream)} events)")
    if seen != names.keys() or len(seen) != 33 or counts["sequences"] != 33:
        raise ValueError(f"incomplete LoL2 XMIDI corpus: {len(seen)} entries, {counts['sequences']} sequences")
    print(f"CHECK XMIDI: {len(seen)} named FORM entries, {counts['sequences']} sequences, "
          f"{counts['timbres']} TIMB pairs, {counts['events']} events ({counts['notes']} note-ons with duration)")


def main():
    parser = lol2_cli.tool_args(__doc__, writes=False)
    parser.add_argument("--list", action="store_true", help="show score names, offsets and counts")
    args = parser.parse_args()
    if not (args.check or args.list):
        parser.error("give --check or --list")
    check(Path(args.data), args.list)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
