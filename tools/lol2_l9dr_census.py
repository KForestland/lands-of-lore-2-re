#!/usr/bin/env python3
"""
LoL2 L9_DR.MIX static census.
Extracts all fixed-stride records, catalogs tags, and computes simple per-tag
field invariants for the first staged 24-word prefix.
"""

import json
import os
import struct
from collections import Counter, defaultdict

MIX_PATH = os.environ.get(
    "MIX_PATH",
    "/media/bob/Arikv/REFERENCE/game_files/lol2/DAT/L9_DR.MIX",
)
RECORD_SIZE = 147
BODY_SIZE = 135
N_HEADER_WORDS = 24
OUTPUT_JSON = os.environ.get("OUTPUT_JSON", "/tmp/lol2_l9dr_census.json")


def main() -> None:
    with open(MIX_PATH, "rb") as f:
        data = f.read()

    file_size = len(data)
    n_records = file_size // RECORD_SIZE
    tail_bytes = file_size % RECORD_SIZE

    tag_counts = Counter()
    tag_records = defaultdict(list)

    for i in range(n_records):
        offset = i * RECORD_SIZE
        body = data[offset : offset + BODY_SIZE]
        tag_raw = data[offset + BODY_SIZE : offset + RECORD_SIZE]
        tag = tag_raw.split(b"\x00")[0].decode("ascii", errors="replace") or "<empty>"
        words = [struct.unpack_from("<H", body, w * 2)[0] for w in range(N_HEADER_WORDS)]
        tag_counts[tag] += 1
        if len(tag_records[tag]) < 500:
            tag_records[tag].append((offset, words))

    tag_analysis = {}
    for tag, count in tag_counts.most_common():
        if count < 2:
            continue
        records = tag_records[tag]
        field_stats = []
        for fi in range(N_HEADER_WORDS):
            values = [r[1][fi] for r in records]
            unique = set(values)
            field_stats.append(
                {
                    "field": fi,
                    "n_unique": len(unique),
                    "invariant": len(unique) == 1,
                    "value": values[0] if len(unique) == 1 else None,
                }
            )

        invariant_fields = [fs for fs in field_stats if fs["invariant"]]
        variable_fields = [fs["field"] for fs in field_stats if not fs["invariant"]]
        f23_dist = Counter(r[1][23] for r in records)

        tag_analysis[tag] = {
            "count": count,
            "sampled": len(records),
            "invariant_count": len(invariant_fields),
            "variable_count": len(variable_fields),
            "invariant_fields": {
                f"f{fs['field']}": f"0x{fs['value']:04x}" for fs in invariant_fields
            },
            "variable_fields": variable_fields,
            "f23_top5": {f"0x{v:04x}": c for v, c in f23_dist.most_common(5)},
            "f23_unique_count": len(f23_dist),
            "f23_invariant": len(f23_dist) == 1,
        }

    output = {
        "file": MIX_PATH,
        "file_size": file_size,
        "total_records": n_records,
        "tail_bytes": tail_bytes,
        "unique_tags": len(tag_counts),
        "tag_inventory": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common()],
        "per_tag_analysis": tag_analysis,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Saved census to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
