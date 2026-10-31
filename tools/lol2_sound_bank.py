#!/usr/bin/env python3
"""List or extract the named AUD sound bank in LoL2's LOCALLNG.MIX.

LOCALLNG.MIX entry key 1570429112 (0x5D9B5EB8) is one bank blob:
  +0x000  dev path string "F:\\PROJECTS\\LOL_2\\LEVED\\GLOBAL\\AUD", zero padded
  +0x258  u32 row count (1179 in the GOG release)
  +0x25C  u32 row-table offset inside the bank
  table   count x 60-byte rows: u32 offset, u32 size, u32 unknown,
          u32 placeholder flag, char name[44] (NUL terminated, e.g. "bird1.aud")

Rows with size 1 are placeholders (flag 1); the rest are complete Westwood
AUD files (12-byte header, codec 99 IMA-ADPCM, 0xDEAF chunks). Extraction
writes each AUD unchanged; decode it with tools/lol2_aud_decode.py --raw.

Standard library only. Reads only your own LOCALLNG.MIX.

Usage:
  lol2_sound_bank.py ./lol2_game/LOCALLNG.MIX                # list rows
  lol2_sound_bank.py ./lol2_game/LOCALLNG.MIX --json
  lol2_sound_bank.py ./lol2_game/LOCALLNG.MIX --extract OUTDIR [--index N ...]
"""
import argparse
import collections
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lol2_mix_parser import read_mix_with_hashes  # noqa: E402
from lol2_aud_decode import parse_aud_header, CHUNK_MAGIC  # noqa: E402

BANK_KEY = 1570429112
COUNT_OFFSET = 0x258
ROW_SIZE = 60
NAME_OFFSET = 16


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bank(mix_path):
    data, entries, base = read_mix_with_hashes(str(mix_path))
    rows = [(o, s) for key, o, s in entries if key == BANK_KEY]
    require(len(rows) == 1, f"expected one entry with key {BANK_KEY}, found {len(rows)}")
    offset, size = rows[0]
    require(base + offset + size <= len(data), "bank entry exceeds MIX data")
    return data[base + offset:base + offset + size]


def check_aud(audio):
    """Validate one AUD clip: header size, codec, and the 0xDEAF chunk walk."""
    hdr = parse_aud_header(audio)
    require(len(audio) == hdr["comp_size"] + 12, "AUD size does not match header")
    cursor, chunks = 12, 0
    while cursor < len(audio):
        size_in, _size_out, magic = struct.unpack_from("<HHI", audio, cursor)
        require(magic == CHUNK_MAGIC, f"bad chunk magic at {cursor}")
        cursor += 8 + size_in
        chunks += 1
    require(cursor == len(audio), "chunk walk overruns clip")
    hdr["chunks"] = chunks
    return hdr


def parse_rows(bank):
    count, table = struct.unpack_from("<II", bank, COUNT_OFFSET)
    require(table + count * ROW_SIZE <= len(bank), "row table outside bank")
    rows = []
    for index in range(count):
        raw = bank[table + index * ROW_SIZE:table + (index + 1) * ROW_SIZE]
        offset, size, unknown, placeholder = struct.unpack_from("<IIII", raw)
        name = raw[NAME_OFFSET:].split(b"\0")[0].decode("ascii", "replace")
        require(offset + size <= table, f"row {index} points outside clip area")
        row = dict(index=index, name=name, offset=offset, size=size,
                   unknown=unknown, placeholder=placeholder)
        if size >= 12:
            hdr = check_aud(bank[offset:offset + size])
            row.update(rate=hdr["sample_rate"], codec=hdr["codec"],
                       stereo=hdr["stereo"], bits=16 if hdr["is_16bit"] else 8,
                       chunks=hdr["chunks"],
                       seconds=round(hdr["output_size"] / (2 if hdr["is_16bit"] else 1)
                                     / hdr["sample_rate"], 3))
        rows.append(row)
    return count, table, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mix", help="path to LOCALLNG.MIX from your own install")
    parser.add_argument("--json", action="store_true", help="print rows as JSON")
    parser.add_argument("--extract", metavar="DIR", help="write raw AUD clips to DIR")
    parser.add_argument("--index", type=int, action="append",
                        help="row index to extract (repeatable; default all)")
    args = parser.parse_args()
    try:
        bank = read_bank(args.mix)
        count, table, rows = parse_rows(bank)
    except (ValueError, OSError, struct.error) as error:
        parser.error(str(error))

    clips = [r for r in rows if r["size"] >= 12]
    summary = dict(rows=count, table_offset=table, clips=len(clips),
                   placeholders=sum(r["size"] < 12 for r in rows),
                   formats={f"{k[0]} Hz codec {k[1]} {'stereo' if k[2] else 'mono'} {k[3]}-bit": v
                            for k, v in collections.Counter(
                                (r["rate"], r["codec"], r["stereo"], r["bits"]) for r in clips).items()})
    if args.json:
        print(json.dumps(dict(summary=summary, rows=rows), indent=2))
    else:
        for r in rows:
            detail = (f"{r['rate']} Hz {r['seconds']:.3f} s" if r["size"] >= 12
                      else "placeholder")
            print(f"{r['index']:5d}  {r['name']:<14s} {r['size']:9d}  {detail}")
        print(json.dumps(summary, indent=2))

    if args.extract:
        wanted = set(args.index) if args.index else None
        out = Path(args.extract)
        out.mkdir(parents=True, exist_ok=True)
        written = 0
        for r in clips:
            if wanted is None or r["index"] in wanted:
                target = out / f"{r['index']:04d}_{Path(r['name']).name}"
                target.write_bytes(bank[r["offset"]:r["offset"] + r["size"]])
                written += 1
        print(f"wrote {written} AUD clips to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
