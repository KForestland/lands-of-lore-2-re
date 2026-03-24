#!/usr/bin/env python3
"""Extract B_HUMAN and WORM entity records across all LoL2 level MIX files.

For each record: file, offset, tag suffix, f0.f1, f21, f22, f23.
Groups results by f23, suffix, and f0.f1 to identify cross-level entity IDs.

Usage:
    python lol2_cross_level_witnesses.py [DAT_DIR]

The DAT directory is resolved in order:
    1. CLI argument (if provided)
    2. LOL2_DAT environment variable
    3. Current directory
"""

import os
import struct
import sys
from collections import defaultdict

LEVEL_FILES = [
    "L1_DC.MIX", "L3_DH.MIX", "L5_HC.MIX", "L7_DH.MIX",
    "L9_DR.MIX", "L10_DC.MIX", "L12_CM.MIX", "L13_RC.MIX",
    "L14_HT.MIX", "L16_CA.MIX", "L17_HC.MIX", "L19_BC.MIX",
]

TARGET_TAGS = {"B_HUMAN", "WORM"}


def find_tagged_region(data):
    """Find the tagged entity region by searching for B_HUMAN near EOF.

    Returns (base_offset, (first_slot, last_slot)) or (None, None).
    """
    tag = b"B_HUMAN\x00"
    idx = data.rfind(tag)
    if idx == -1:
        return None, None

    record_start = idx - 135
    base = record_start % 147

    b_slot = (record_start - base) // 147

    # Scan backward
    first = b_slot
    for s in range(b_slot - 1, max(b_slot - 200, -1), -1):
        off = base + s * 147
        if off < 0 or off + 147 > len(data):
            break
        tb = data[off + 135:off + 147]
        name = tb.split(b'\x00')[0]
        if len(name) >= 2 and all(32 < c < 127 for c in name):
            first = s
        else:
            break

    # Scan forward
    last = b_slot
    for s in range(b_slot + 1, b_slot + 100):
        off = base + s * 147
        if off + 147 > len(data):
            break
        tb = data[off + 135:off + 147]
        name = tb.split(b'\x00')[0]
        if len(name) >= 2 and all(32 < c < 127 for c in name):
            last = s
        else:
            break

    return base, (first, last)


def extract_records(data, base, slot_range, target_tags):
    """Extract records matching target tags from the tagged entity region."""
    results = []
    first, last = slot_range
    for s in range(first, last + 1):
        off = base + s * 147
        body = data[off:off + 135]
        tag_bytes = data[off + 135:off + 147]
        name = tag_bytes.split(b'\x00')[0].decode('ascii', errors='replace')

        if name not in target_tags:
            continue

        # Suffix: bytes after first null in the 12-byte tag field
        null_pos = tag_bytes.find(b'\x00')
        suffix_raw = tag_bytes[null_pos + 1:] if null_pos >= 0 else b''
        suffix_hex = suffix_raw.hex()
        suffix_ascii = ''.join(chr(b) if 32 <= b < 127 else '.' for b in suffix_raw)
        suffix_clean = suffix_raw.rstrip(b'\x00')
        suffix_str = suffix_clean.decode('ascii', errors='replace') if suffix_clean else ""

        words = [struct.unpack_from('<H', body, w * 2)[0] for w in range(24)]

        results.append({
            "tag": name,
            "offset": off,
            "slot": s,
            "suffix_hex": suffix_hex,
            "suffix_str": suffix_str,
            "f0": words[0],
            "f1": words[1],
            "f21": words[21],
            "f22": words[22],
            "f23": words[23],
            "words": words,
        })

    return results


def print_tag_table(tag, records):
    """Print a formatted table and groupings for a single entity tag."""
    print(f"=== {tag} WITNESSES ===")
    print(f"{'File':15s} {'Offset':>10s} {'Suffix':>8s} {'f0.f1':>10s} {'f21':>6s} {'f22':>6s} {'f23':>6s}")
    print("-" * 70)
    for r in sorted(records, key=lambda x: (x["f23"], x["file"])):
        print(f"{r['file']:15s} {r['offset']:10d} {r['suffix_str']:>8s} "
              f"{r['f0']:04x}.{r['f1']:04x} "
              f"{r['f21']:04x}  {r['f22']:04x}  {r['f23']:04x}")

    # Group by f23
    print(f"\n=== {tag} GROUPED BY f23 ===")
    f23_groups = defaultdict(list)
    for r in records:
        f23_groups[r["f23"]].append(r)
    for f23_val in sorted(f23_groups.keys()):
        recs = f23_groups[f23_val]
        files = sorted(set(r["file"] for r in recs))
        suffixes = sorted(set(r["suffix_str"] for r in recs))
        print(f"  f23=0x{f23_val:04x}: {len(recs)} records in {files}")
        if tag == "B_HUMAN":
            f01s = sorted(set(f"{r['f0']:04x}.{r['f1']:04x}" for r in recs))
            print(f"    suffixes: {suffixes}")
            print(f"    f0.f1 pairs: {f01s}")
        else:
            print(f"    suffixes: {suffixes}")


def main():
    dat_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LOL2_DAT", ".")

    all_records = defaultdict(list)

    for fname in LEVEL_FILES:
        path = os.path.join(dat_dir, fname)
        try:
            with open(path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            print(f"WARNING: {path} not found, skipping")
            continue

        base, slot_range = find_tagged_region(data)
        if base is None:
            continue

        records = extract_records(data, base, slot_range, TARGET_TAGS)
        for r in records:
            r["file"] = fname
            all_records[r["tag"]].append(r)

    # Print B_HUMAN table and groupings
    if all_records["B_HUMAN"]:
        print_tag_table("B_HUMAN", all_records["B_HUMAN"])

        # Additional B_HUMAN groupings
        print(f"\n=== B_HUMAN GROUPED BY SUFFIX ===")
        suffix_groups = defaultdict(list)
        for r in all_records["B_HUMAN"]:
            suffix_groups[r["suffix_str"]].append(r)
        for suffix in sorted(suffix_groups.keys()):
            recs = suffix_groups[suffix]
            f23s = sorted(set(f"0x{r['f23']:04x}" for r in recs))
            print(f"  suffix=\"{suffix}\": {len(recs)} records, f23 values: {f23s}")

        print(f"\n=== B_HUMAN GROUPED BY f0.f1 ===")
        f01_groups = defaultdict(list)
        for r in all_records["B_HUMAN"]:
            f01_groups[(r["f0"], r["f1"])].append(r)
        for f01 in sorted(f01_groups.keys()):
            recs = f01_groups[f01]
            f23s = sorted(set(f"0x{r['f23']:04x}" for r in recs))
            print(f"  f0.f1={f01[0]:04x}.{f01[1]:04x}: {len(recs)} records, f23 values: {f23s}")

    # Print WORM table and groupings
    if all_records["WORM"]:
        print(f"\n")
        print_tag_table("WORM", all_records["WORM"])


if __name__ == "__main__":
    main()
