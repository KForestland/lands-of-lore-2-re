#!/usr/bin/env python3
"""Extract the captured LoL2 wall page by named cache record, using stdlib only.

Supports the witnessed CDCACHE.LST table and stored-record state 2 only.
All input locations are explicit; original data files are never modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path

ASSET = "sphere3\\l20_bb\\l20_bb.tex"
BLOB_SHA256 = "adf44e535d7b890f0f47e28266e480559fa0417094e0b5495f0775e06c41ef21"
PAGE_SHA256 = "f6cf252268cc38dd16198fa7b55c39586db67d58ec6bcbad5e681e352f5d8ee1"
PAGE_REL = 0x113E883
PAGE_LEN = 8192


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical_name(name: str) -> str:
    name = name.lower().replace("/", "\\")
    return name[:-1] + "x" if name.endswith(".te_") else name


def parse_records(data: bytes) -> list[dict]:
    require(len(data) >= 8, "truncated LST header")
    table_end = struct.unpack_from("<I", data)[0]
    require(8 <= table_end <= len(data) and table_end % 8 == 0,
            "invalid LST table extent")
    require((len(data) - table_end) % 256 == 0, "partial LST record")
    offsets = set()
    for pos in range(0, table_end, 8):
        offset, _tag = struct.unpack_from("<II", data, pos)
        require(offset >= table_end and (offset - table_end) % 256 == 0
                and offset + 256 <= len(data), "out-of-bounds LST record pointer")
        offsets.add(offset)
    require(offsets == set(range(table_end, len(data), 256)),
            "LST table does not cover the record area")
    records = []
    for offset in sorted(offsets):
        raw = data[offset:offset + 256]
        name_bytes = raw[8:128]
        require(b"\0" in name_bytes, "unterminated cache name")
        name = name_bytes.split(b"\0", 1)[0].decode("ascii")
        state, length = struct.unpack_from("<II", raw, 0xD8)
        pointer = struct.unpack_from("<I", raw, 0xE8)[0]
        records.append(dict(record_offset=offset, name=name,
                            canonical_name=canonical_name(name), state=state,
                            length=length, pointer=pointer))
    return records


def load_named(root: Path, asset: str) -> tuple[dict, bytes, dict, list[dict]]:
    lst = (root / "CDCACHE.LST").read_bytes()
    records = parse_records(lst)
    candidates = [r for r in records if r["canonical_name"] == canonical_name(asset)]
    require(len(candidates) == 1, "named cache record missing or ambiguous")
    record = candidates[0]
    require(record["state"] == 2, "unsupported cache record state; no pointer fallback allowed")
    data = (root / "CDCACHE.MIX").read_bytes()
    start, length = record["pointer"], record["length"]
    require(length > 0 and start + length <= len(data), "cache blob outside file")
    blob = data[start:start + length]
    identity = dict(root=str(root.resolve()), lst_sha256=sha(lst),
                    mix_sha256=sha(data), blob_sha256=sha(blob), mix_size=len(data))
    return record, blob, identity, records


def section_for(blob: bytes, relative: int, length: int) -> dict:
    require(len(blob) >= 8, "truncated section header")
    count = struct.unpack_from("<I", blob)[0]
    require(0 < count <= 256 and 8 + count * 4 <= len(blob), "invalid section count")
    rels = struct.unpack_from("<" + "I" * count, blob, 8)
    require(all(v == 0 or 8 + count * 4 <= v <= len(blob) for v in rels),
            "section offset outside blob")
    boundaries = sorted(set(v for v in rels if v)) + [len(blob)]
    matches = []
    for index, start in enumerate(rels):
        if not start:
            continue
        end = next((v for v in boundaries if v > start), len(blob))
        if start <= relative and relative + length <= end:
            matches.append(dict(index=index, start=start, end=end,
                                page_relative_to_section=relative - start))
    require(len(matches) == 1, "page does not resolve to one bounded section")
    return matches[0]


def replay_reads(page: bytes, path: Path) -> dict:
    rows = mismatches = 0
    unique = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            offset, size = int(row["page_offset"], 0), int(row["size"])
            require(size > 0 and 0 <= offset and offset + size <= len(page),
                    "trace read outside page")
            expected = bytes.fromhex(row["trace_preview"])
            require(len(expected) == size, "trace preview length mismatch")
            mismatches += page[offset:offset + size] != expected
            rows += 1
            unique.update(range(offset, offset + size))
    require(rows > 0, "empty read fixture")
    require(mismatches == 0, f"renderer source-read mismatches: {mismatches}")
    return dict(rows=rows, unique_offsets=len(unique), mismatches=mismatches,
                csv_sha256=sha(path.read_bytes()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--reads-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    record, blob, identity, _ = load_named(args.reference_root, ASSET)
    require(sha(blob) == BLOB_SHA256, "unsupported wall blob hash")
    page = blob[PAGE_REL:PAGE_REL + PAGE_LEN]
    require(len(page) == PAGE_LEN and sha(page) == PAGE_SHA256, "wall page hash mismatch")
    section = section_for(blob, PAGE_REL, PAGE_LEN)
    replay = replay_reads(page, args.reads_csv)
    require(replay["rows"] == 5940 and replay["unique_offsets"] == 2080,
            "incomplete or unexpected captured source-read fixture")
    report = dict(schema_version=1, asset=ASSET, reference=identity, record=record,
                  page_relative_to_blob=PAGE_REL, page_length=PAGE_LEN,
                  reference_page_offset=record["pointer"] + PAGE_REL,
                  page_sha256=sha(page), section=section, source_read_replay=replay,
                  scope="Named stored-blob source extraction and source-read replay only; "
                        "not wall dimensions, palette, output replay, or general cache-update grammar.")
    if args.runtime_root:
        run_record, run_blob, run_identity, run_records = load_named(args.runtime_root, ASSET)
        require(run_blob == blob, "runtime and reference named blobs differ")
        report["runtime_comparison"] = dict(
            identity=run_identity, record=run_record, entire_blob_equal=True,
            compared_bytes=len(blob), page_offset=run_record["pointer"] + PAGE_REL,
            reference_minus_runtime=record["pointer"] - run_record["pointer"],
            section=section_for(run_blob, PAGE_REL, PAGE_LEN), records=run_records)
        # A second independently identified blob tests the two-block reorder explanation.
        l1, l1_blob, _, _ = load_named(args.reference_root, "sphere1\\l1_dc\\l1_dc.tex")
        with (args.runtime_root / "CDCACHE.MIX").open("rb") as handle:
            appended_start = run_record["pointer"] + run_record["length"]
            handle.seek(appended_start)
            appended = handle.read(len(l1_blob))
        report["two_blob_layout"] = dict(
            reference_l1_record=l1,
            reference_l1_end_equals_l20_start=l1["pointer"] + len(l1_blob) == record["pointer"],
            runtime_following_l1_offset=appended_start,
            runtime_following_l1_equals_reference=appended == l1_blob,
            l1_sha256=sha(l1_blob), l1_length=len(l1_blob))
    # Do not leave apparently successful output when any validation above failed.
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "wall_page.bin").write_bytes(page)
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    summary = [f"asset={ASSET}", f"reference_page_offset=0x{report['reference_page_offset']:X}",
               f"blob_sha256={sha(blob)}", f"page_sha256={sha(page)}",
               f"section={section['index']}", f"source_read_rows={replay['rows']}",
               f"unique_offsets={replay['unique_offsets']}", "source_read_mismatches=0",
               f"scope={report['scope']}"]
    if args.runtime_root:
        summary += [f"whole_blob_equal_bytes={len(blob)}",
                    f"reference_minus_runtime=0x{report['runtime_comparison']['reference_minus_runtime']:X}",
                    f"following_l1_blob_equal={report['two_blob_layout']['runtime_following_l1_equals_reference']}"]
    (args.out / "report.txt").write_text("\n".join(summary) + "\n")
    names = ["wall_page.bin", "report.json", "report.txt"]
    (args.out / "MANIFEST.sha256").write_text("".join(
        f"{sha((args.out / name).read_bytes())}  {name}\n" for name in names))
    print("\n".join(summary))


if __name__ == "__main__":
    main()
