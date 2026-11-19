#!/usr/bin/env python3
"""Read L9_DR.MIX in 147-byte slots for an exploratory census.


LoL2 L9_DR.MIX static census (EXPLORATORY: it reads the whole archive as
147-byte records from offset 0, ignoring the MIX structure; for the real
entity records use lol2_entity_field_analyzer.py, which finds their region).
Extracts all fixed-stride records, catalogs tags, and computes simple per-tag
field invariants for the first staged 24-word prefix.
"""

from cli_errors import run_cli
import json
import os
import struct
from collections import Counter, defaultdict

RECORD_SIZE = 147
BODY_SIZE = 135
N_HEADER_WORDS = 24



def main() -> int:
    import lol2_cli
    ap = lol2_cli.tool_args((__doc__ or "") + """
  lol2_l9dr_census.py [--data DAT] --out census.json
  lol2_l9dr_census.py --check     # how many 147-byte slots carry a printable tag
""")
    a = ap.parse_args()
    MIX_PATH = os.path.join(a.data, "L9_DR.MIX")
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

    if a.check:
        printable = sum(c for t, c in tag_counts.items() if t != "<empty>" and all(32 <= ord(ch) < 127 for ch in t))
        print(f"CHECK l9dr_census (exploratory): L9_DR.MIX read as {n_records} slots of {RECORD_SIZE} bytes "
              f"(+{tail_bytes} tail); {printable} slots end in a printable tag, {len(tag_counts)} distinct tag strings")
        return 0
    output = {
        "file": "L9_DR.MIX",
        "file_size": file_size,
        "total_records": n_records,
        "tail_bytes": tail_bytes,
        "unique_tags": len(tag_counts),
        "tag_inventory": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common()],
        "per_tag_analysis": tag_analysis,
    }

    if not a.out:
        print(f"{n_records} slots, {len(tag_counts)} distinct tag strings (use --out FILE for the JSON census)")
        return 0
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Saved census to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
