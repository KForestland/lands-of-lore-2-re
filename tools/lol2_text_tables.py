#!/usr/bin/env python3
"""Read the TRR message tables the LoL2 executable loads by name.

--data is the game DAT folder, or $LOL2_DAT. LOCALLNG.MIX and the loose
TRR files sit in the parent of that folder. MOVIES.MIX, TEXT.MIX and
TCEL.MIX sit inside it. --check re-reads those bytes and prints one line.
It writes nothing unless --out is set, and then only counts.
"""

from cli_errors import run_cli
import os
import struct
import sys

import lol2_cli
from lol2_mix_parser import read_mix_with_hashes
from lol2_westwood_hash import ww_hash_v1


def u32(blob, off):
    return struct.unpack_from("<I", blob, off)[0]


def parent_file(dat_dir, name):
    path = os.path.join(os.path.dirname(os.path.abspath(dat_dir)), name)
    if not os.path.isfile(path):
        raise FileNotFoundError("%s is not in the parent of the DAT folder" % name)
    return path


def mix_entry(path, index):
    data, entries, base = read_mix_with_hashes(path)
    if index < 0 or index >= len(entries):
        raise ValueError("%s index %s" % (os.path.basename(path), index))
    _key, offset, size = entries[index]
    return data[base + offset:base + offset + size], entries


def parse_trr(blob, label):
    """Return count, ids, absolute offsets. Reject a blob that is not this layout."""
    if len(blob) < 8:
        raise ValueError("%s short" % label)
    count = u32(blob, 0)
    if count < 1 or 8 * count + 8 > len(blob):
        raise ValueError("%s count %s" % (label, count))
    ids = list(struct.unpack_from("<%dI" % count, blob, 4))
    offs = list(struct.unpack_from("<%dI" % (count + 1), blob, 4 + 4 * count))
    if offs[0] != 8 * count + 4:
        raise ValueError("%s first offset %s" % (label, offs[0]))
    if offs[-1] != len(blob) - 4:
        raise ValueError("%s last offset %s" % (label, offs[-1]))
    if offs != sorted(offs) or len(set(offs)) != len(offs):
        raise ValueError("%s offsets" % label)
    heap = offs[0] + 4
    for index in range(count):
        start = heap + (offs[index] - offs[0])
        end = heap + (offs[index + 1] - offs[0])
        if not (heap <= start < end <= len(blob)):
            raise ValueError("%s span %s" % (label, index))
        record = blob[start:end]
        if record.count(b"\x00") != 1 or not record.endswith(b"\x00"):
            raise ValueError("%s record %s" % (label, index))
    return count, ids, offs


def records(blob):
    count, _ids, offs = parse_trr(blob, "record")
    heap = offs[0] + 4
    out = []
    for index in range(count):
        start = heap + (offs[index] - offs[0])
        end = heap + (offs[index + 1] - offs[0])
        out.append(blob[start:end])
    return out


def is_trr(blob):
    try:
        parse_trr(blob, "scan")
    except ValueError:
        return False
    return True


def body(record):
    return record[:-1]


def check(dat_dir):
    lng_path = parent_file(dat_dir, "LOCALLNG.MIX")
    _blob, lng_entries = mix_entry(lng_path, 0)

    expected = {
        0: ("automap.trr", 364, 4383, 285, {7: 57}),
        1: ("opttext.trr", 202, 4328, 11, {17: 2}),
        3: ("helptext.trr", 41, 3851, 5, {7: 1}),
        5: ("credits.trr", 43, 6041, 0, {}),
    }
    loaded = {}
    for index, (name, count, size, empty, controls) in expected.items():
        blob, entries = mix_entry(lng_path, index)
        key, _off, got = entries[index]
        if got != size or len(blob) != size:
            raise ValueError("%s size %s" % (name, len(blob)))
        if key != ww_hash_v1(name):
            raise ValueError("%s key" % name)
        got_count, ids, _offs = parse_trr(blob, name)
        if got_count != count:
            raise ValueError("%s count %s" % (name, got_count))
        rows = records(blob)
        if sum(1 for row in rows if row == b"\x00") != empty:
            raise ValueError("%s empty" % name)
        for byte, nrec in controls.items():
            hit = sum(1 for row in rows if byte in body(row))
            if hit != nrec:
                raise ValueError("%s byte %s in %s records" % (name, byte, hit))
            other = sum(1 for row in rows if any(c < 32 and c not in (9, 10, 13, byte) for c in body(row)))
            if other:
                raise ValueError("%s other control in %s records" % (name, other))
        loaded[name] = (blob, ids)

    help_ids = loaded["helptext.trr"][1]
    if help_ids != [n for n in range(50) if n < 10 or n > 18]:
        raise ValueError("helptext ids")
    help_rows = records(loaded["helptext.trr"][0])
    if len(help_rows[0]) != 262 or max(len(row) for row in help_rows) != 369:
        raise ValueError("helptext record lengths")
    auto_rows = records(loaded["automap.trr"][0])
    printable = sum(
        1 for row in auto_rows
        if row != b"\x00" and all(32 <= c < 127 or c in (9, 10, 13) for c in body(row))
    )
    if printable != 22:
        raise ValueError("automap printable %s" % printable)
    opt_ids = loaded["opttext.trr"][1]
    if opt_ids != list(range(202)):
        raise ValueError("opttext ids")
    credit_ids = loaded["credits.trr"][1]
    if credit_ids != list(range(43)):
        raise ValueError("credits ids")
    auto_ids = loaded["automap.trr"][1]
    if auto_ids != list(range(364)):
        raise ValueError("automap ids")

    # credits uses two bytes above 126 and no other non-ASCII byte
    high = set()
    for row in records(loaded["credits.trr"][0]):
        high.update(c for c in body(row) if c > 126)
    if high != {0x81, 0x82}:
        raise ValueError("credits high bytes %s" % sorted(high))

    movies = os.path.join(dat_dir, "MOVIES.MIX")
    movie_credits, _entries = mix_entry(movies, 28)
    if movie_credits != loaded["credits.trr"][0]:
        raise ValueError("MOVIES entry 28 is not the credits table")

    loose = {}
    for name, count, size in (
        ("ERRTEXT.TRR", 39, 2444),
        ("OPTTEXT.TRR", 212, 4587),
        ("CREDITS.TRR", 44, 6151),
    ):
        blob = open(parent_file(dat_dir, name), "rb").read()
        if len(blob) != size:
            raise ValueError("%s size %s" % (name, len(blob)))
        got, ids, _offs = parse_trr(blob, name)
        if got != count or (name == "ERRTEXT.TRR" and ids != list(range(39))):
            raise ValueError("%s count" % name)
        loose[name] = blob
    if loose["OPTTEXT.TRR"] == loaded["opttext.trr"][0]:
        raise ValueError("loose opttext matches the archive copy")
    if loose["CREDITS.TRR"] == loaded["credits.trr"][0]:
        raise ValueError("loose credits matches the archive copy")
    err = records(loose["ERRTEXT.TRR"])
    if any(c < 32 and c not in (9, 10, 13) or c > 126 for row in err for c in body(row)):
        raise ValueError("errtext byte")
    joined = b"".join(body(row) for row in err)
    if joined.count(b"\n") != 10 or joined.count(b"^") != 9:
        raise ValueError("errtext markers")
    if ww_hash_v1("errtext.trr") in {key for key, _o, _s in lng_entries}:
        raise ValueError("errtext is inside LOCALLNG")

    lang = open(parent_file(dat_dir, "LANGUAGE.ENG"), "rb").read()
    if lang != b"\r\n":
        raise ValueError("LANGUAGE.ENG")

    for name in ("TEXT.MIX", "TCEL.MIX"):
        data, entries, base = read_mix_with_hashes(os.path.join(dat_dir, name))
        for key, offset, size in entries:
            if is_trr(data[base + offset:base + offset + size]):
                raise ValueError("%s contains a TRR entry" % name)

    image = open(parent_file(dat_dir, "LOLG.DAT"), "rb").read()
    table = image[0x1DA744:0x1DA744 + 22]
    if table[:9] != bytes.fromhex("cfe1e6eff5f8f9fcfd") or table[9] != 0:
        raise ValueError("substitution source")
    if table[12:21] != bytes.fromhex("b0b1b2b3b4b5b6b7b8") or table[21] != 0:
        raise ValueError("substitution dest")
    sources = set(table[:9])
    for label, blob in (
        ("automap.trr", loaded["automap.trr"][0]),
        ("opttext.trr", loaded["opttext.trr"][0]),
        ("helptext.trr", loaded["helptext.trr"][0]),
        ("credits.trr", loaded["credits.trr"][0]),
        ("ERRTEXT.TRR", loose["ERRTEXT.TRR"]),
        ("OPTTEXT.TRR", loose["OPTTEXT.TRR"]),
        ("CREDITS.TRR", loose["CREDITS.TRR"]),
    ):
        used = sources.intersection(c for row in records(blob) for c in body(row))
        if used:
            raise ValueError("%s uses substitution source" % label)

    return ("CHECK text: help/opt/automap/credits in LOCALLNG, credits also MOVIES entry 28, "
            "loose ERRTEXT 39 / OPTTEXT 212 / CREDITS 44; TEXT and TCEL have no TRR entry")


def main(argv):
    parser = lol2_cli.tool_args(__doc__)
    args = parser.parse_args(argv)
    if args.out and not args.check:
        parser.error("--out is only the one-line check, with --check")
    if not args.check:
        parser.print_help()
        return 2
    try:
        line = check(args.data)
    except (OSError, ValueError, struct.error) as error:
        print("CHECK text: FAIL %s" % error)
        return 1
    if args.out:
        import os as _os, sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from lol2_cli import refuse_repo_output
        refuse_repo_output(args.out)
        with open(args.out, "w", encoding="ascii") as handle:
            handle.write(line + "\n")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main, sys.argv[1:]))
