#!/usr/bin/env python3
"""Extract witnessed L20 material mipmaps and audit captured addressing/shading.

Requires only Python's standard library and lol2_cache_named_wall_fixture.py.
Images are grayscale index diagnostics, not claims about final RGB colors.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import struct
from pathlib import Path

import lol2_cache_named_wall_fixture as cache

SITES = {"F9DF", "FA6B", "FAAD"}
SHADE_BASE = 0x10199000


def sections(blob: bytes) -> tuple[int, ...]:
    cache.require(len(blob) >= 8, "missing blob header")
    count = struct.unpack_from("<I", blob)[0]
    cache.require(4 <= count <= 256 and 8 + 4 * count <= len(blob), "bad section count")
    offsets = struct.unpack_from("<" + "I" * count, blob, 8)
    cache.require(all(v == 0 or 8 + 4 * count <= v <= len(blob) for v in offsets),
                  "section outside named blob")
    return offsets


def material_record(blob: bytes, index: int, *, allow_partial_mips: bool = False) -> dict:
    offsets = sections(blob)
    table, payload = offsets[2], offsets[3]
    cache.require(table > 0 and payload > table and (payload - table) % 56 == 0,
                  "unsupported descriptor table extent")
    count = (payload - table) // 56
    cache.require(0 <= index < count, "descriptor index outside table")
    position = table + index * 56
    values = struct.unpack_from("<6H11I", blob, position)
    identifier, width, height, flags, field8, field10 = values[:6]
    name_hash_candidate = values[6]
    mip_offsets, mip_sizes = values[7:12], values[12:17]
    cache.require(flags == 0xA9, "this extractor supports only witnessed 0xA9 records")
    cache.require(width > 0 and height > 0, "zero material dimension")
    payload_end = min((v for v in offsets if v > payload), default=len(blob))
    mips = []
    active_levels = 5
    if allow_partial_mips:
        active_levels = sum(size != 0 for size in mip_sizes)
        cache.require(1 <= active_levels <= 5, "empty mip chain")
        cache.require(all(mip_sizes[k] > 0 for k in range(active_levels)) and
                      all(mip_sizes[k] == mip_offsets[k] == 0 for k in range(active_levels, 5)),
                      "mip chain has holes or nonzero unused offsets")
        cache.require((field10 & 255) == active_levels, "mip count field mismatch")
    for level, (relative, size) in enumerate(zip(mip_offsets, mip_sizes)):
        if level >= active_levels:
            break
        start = payload + relative
        cache.require(size >= 8 and payload <= start and start + size <= payload_end,
                      "mip outside payload section")
        mip_flags, w, h, length16 = struct.unpack_from("<4H", blob, start)
        cache.require(mip_flags == flags, "descriptor/mip flags mismatch")
        cache.require((w, h) == (max(1, width >> level), max(1, height >> level)),
                      "descriptor/mip dimensions mismatch")
        cache.require(size == 8 + w * h and length16 == (w * h) & 0xFFFF,
                      "mip byte extent mismatch")
        mips.append(dict(level=level, start=start, data_start=start + 8,
                         width=w, height=h, record_size=size,
                         stored_length16=length16,
                         pixels_sha256=cache.sha(blob[start + 8:start + size])))
    return dict(index=index, descriptor_start=position, descriptor_count=count,
                identifier=identifier, width=width, height=height, flags=flags,
                field8=field8, field10=field10, name_hash_candidate=name_hash_candidate,
                payload_section_start=payload, mips=mips)


def find_material(blob: bytes, captured_start: int) -> dict:
    offsets = sections(blob)
    table, payload = offsets[2], offsets[3]
    cache.require(payload > table and (payload - table) % 56 == 0,
                  "unsupported descriptor table")
    matches = [index for index in range((payload - table) // 56)
               if payload + struct.unpack_from("<I", blob, table + index * 56 + 16)[0]
               == captured_start]
    cache.require(len(matches) == 1, "captured material missing or ambiguous")
    return material_record(blob, matches[0])


def audit_trace(trace: Path, pixels: bytes, width: int, height: int,
                comparison_table: bytes | None) -> tuple[dict, list[dict], list[dict]]:
    read_counts = collections.Counter()
    headers = collections.Counter()
    source_bad = address_bad = 0
    pending = None
    pairs = []
    file_reads = []
    dump_ranges = []
    full_register_anchors = []
    base = None
    watch_offset = None
    malformed = 0
    for number, line in enumerate(trace.open(encoding="utf-8"), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        event, ip = row.get("event"), row.get("ip")
        if event == "watch_pivot_rearm":
            base, watch_offset = row["pivot_base"], row["watch_offset"]
            pending = None
        if event == "read" and row.get("guest_name") == "CDCACHE.MIX":
            file_reads.append(dict(line=number, offset=row["offset"], size=row["actual"],
                                   preview=row.get("preview", "")))
        if event == "big_dump":
            dump_ranges.append((int(row["addr"], 0), row["len"]))
        if event == "watch_read_code_dump" and ip in SITES | {"EEF1"}:
            full_register_anchors.append(dict(line=number, site=ip,
                **{k: v for k, v in row.items() if k.startswith("reg_")}))
        if event == "watch_read":
            pending = None
            if base is None or row.get("watch_guest_addr") != base:
                continue
            rel = row["addr"] - base
            if ip == "EEF1":
                if rel in (2, 4):
                    value = int.from_bytes(bytes.fromhex(row["preview"]), "little")
                    headers[(rel, value)] += 1
            if ip not in SITES:
                continue
            cache.require(row["size"] == 1, "unsupported source-read width")
            source_offset = rel - 8
            cache.require(0 <= source_offset < len(pixels), "source read outside material")
            source = pixels[source_offset]
            source_bad += source != int(row["preview"], 16)
            address_bad += source_offset != int(row["ax"], 16)
            read_counts[ip] += 1
            pending = (number, row, source_offset, source)
        elif event == "watch_follow_write" and pending:
            # Only the next write after a matching source read is paired.
            read_line, read, source_offset, source = pending
            pending = None
            if ip != read["ip"] or row.get("watch_guest_addr") != base:
                continue
            cache.require(row["size"] == 1, "unsupported output-write width")
            shade = (int(read["bx"], 16) >> 8) & 255
            output = int(row["preview"], 16)
            pair = dict(read_line=read_line, write_line=number, site=ip,
                        source_offset=source_offset, source_x=source_offset % width,
                        source_y=source_offset // width, source_index=source,
                        shade_row=shade, shade_address=SHADE_BASE + (shade << 8) + source,
                        destination=row["addr"], output_index=output)
            if comparison_table is not None:
                table_offset = pair["shade_address"] - 0x10190000
                cache.require(0 <= table_offset < len(comparison_table), "short comparison table")
                pair["earlier_table_index"] = comparison_table[table_offset]
                pair["earlier_table_match"] = comparison_table[table_offset] == output
            pairs.append(pair)
    cache.require(base is not None and read_counts, "no material renderer witness")
    cache.require(not source_bad and not address_bad, "source/address replay mismatch")
    cache.require(headers and all((offset, value) in {(2, width), (4, height)}
                                  for offset, value in headers), "runtime dimensions mismatch")
    mapping = collections.defaultdict(set)
    for pair in pairs:
        mapping[(pair["shade_row"], pair["source_index"])].add(pair["output_index"])
    observed = [dict(shade_row=shade, source_index=source, outputs=sorted(outputs))
                for (shade, source), outputs in sorted(mapping.items())]
    # File read previews are independent of the source-watch page boundaries.
    header = struct.pack("<4H", 0xA9, width, height, (width * height) & 0xFFFF)
    material = header + pixels
    covering = [r for r in file_reads if watch_offset <= r["offset"] < watch_offset + len(material)]
    preview_bad = 0
    covered = set()
    for row in covering:
        rel = row["offset"] - watch_offset
        preview = bytes.fromhex(row["preview"])
        preview_bad += preview != material[rel:rel + len(preview)]
        covered.update(range(rel, min(rel + row["size"], len(material))))
    cache.require(preview_bad == 0, "material file-read preview mismatch")
    summary = dict(trace_sha256=cache.sha(trace.read_bytes()), malformed_json_lines=malformed,
                   source_reads=dict(read_counts), source_read_rows=sum(read_counts.values()),
                   source_mismatches=source_bad, payload_offset_vs_ax_mismatches=address_bad,
                   header_reads=[dict(offset=o, value=v, rows=n) for (o, v), n in sorted(headers.items())],
                   runtime_payload_base=base + 8, runtime_file_offset=watch_offset,
                   file_read_events=covering, file_read_extent_coverage=len(covered),
                   file_preview_mismatches=preview_bad,
                   paired_output_events=len(pairs), observed_shade_entries=len(mapping),
                   observed_shade_conflicts=sum(len(v) > 1 for v in mapping.values()),
                   full_register_anchors=full_register_anchors,
                   same_trace_dump_covers_shade_row=any(
                       a <= SHADE_BASE + 0x2D00 and SHADE_BASE + 0x2E00 <= a + n
                       for a, n in dump_ranges),
                   shade_scope="Observed input/output pairs only; outputs define this partial mapping. "
                               "Not an independent native shading or RGB validation.")
    if comparison_table is not None:
        summary["earlier_table_comparison"] = dict(
            sha256=cache.sha(comparison_table),
            match=sum(p["earlier_table_match"] for p in pairs),
            mismatch=sum(not p["earlier_table_match"] for p in pairs))
    return summary, pairs, observed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--earlier-table", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rec, blob, identity, _ = cache.load_named(args.reference_root, cache.ASSET)
    cache.require(cache.sha(blob) == cache.BLOB_SHA256, "unsupported named blob hash")
    material = find_material(blob, cache.PAGE_REL)
    neighbor = material_record(blob, material["index"] + 1)
    mip = material["mips"][0]
    pixels = blob[mip["data_start"]:mip["start"] + mip["record_size"]]
    audit, pairs, observed = audit_trace(args.trace, pixels, material["width"], material["height"],
        args.earlier_table.read_bytes() if args.earlier_table else None)
    args.out.mkdir(parents=True, exist_ok=True)
    output_files = []
    for entry in (material, neighbor):
        for level in entry["mips"]:
            data = blob[level["data_start"]:level["start"] + level["record_size"]]
            stem = f"descriptor_{entry['index']}_mip{level['level']}_{level['width']}x{level['height']}"
            pgm = f"P5\n{level['width']} {level['height']}\n255\n".encode() + data
            for suffix, content in [(".indices.bin", data), (".pgm", pgm)]:
                name = stem + suffix
                (args.out / name).write_bytes(content)
                output_files.append(name)
    with (args.out / "paired_output_events.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    (args.out / "observed_partial_shade_map.json").write_text(json.dumps(observed, indent=2) + "\n")
    report = dict(schema_version=1, reference=identity, cache_record=rec,
                  material=material, static_neighbor=neighbor, trace_audit=audit,
                  orientation="256-byte linear row layout is supported; world-space UV orientation remains open.",
                  image_scope="PGMs show palette indices as gray values, not final game colors.",
                  next_capture="At the identified source consumer, capture full EBX and EDX, "
                               "0x10199000 shade data (including row 0x2D), "
                               "0x101C23F0..0x101C25B0 addressing state, and active VGA palette "
                               "in the same scene/time window as source reads and output writes.")
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    summary = [f"descriptor_index={material['index']}", f"identifier={material['identifier']}",
               f"dimensions={material['width']}x{material['height']}",
               "mips=" + ",".join(f"{m['width']}x{m['height']}" for m in material["mips"]),
               f"source_read_rows={audit['source_read_rows']}", "source_and_address_mismatches=0",
               f"file_read_extent_coverage={audit['file_read_extent_coverage']}",
               f"paired_output_events={audit['paired_output_events']}",
               f"observed_shade_entries={audit['observed_shade_entries']}",
               f"observed_shade_conflicts={audit['observed_shade_conflicts']}",
               f"earlier_table_comparison={audit.get('earlier_table_comparison')}",
               f"image_scope={report['image_scope']}", f"shade_scope={audit['shade_scope']}"]
    (args.out / "report.txt").write_text("\n".join(summary) + "\n")
    output_files += ["paired_output_events.csv", "observed_partial_shade_map.json", "report.json", "report.txt"]
    (args.out / "MANIFEST.sha256").write_text("".join(
        f"{cache.sha((args.out / name).read_bytes())}  {name}\n" for name in output_files))
    print("\n".join(summary))


if __name__ == "__main__":
    main()
