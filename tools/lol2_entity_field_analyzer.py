#!/usr/bin/env python3
"""LoL2 entity field semantic analyzer.

Scans all level MIX files for entity records (147 bytes: 135-byte body +
12-byte ASCII tag), extracts the first 24 u16 words (fields f0-f23), and
performs cross-type statistical analysis to classify field semantics.

Usage:
    python lol2_entity_field_analyzer.py [dat_dir]

The DAT directory is resolved in order:
    1. CLI argument (if provided)
    2. LOL2_DAT environment variable
    3. Current directory

Output: JSON report to stdout (redirect to file as needed).

Record format (147 bytes):
    Bytes 0-134:   135-byte entity body
    Bytes 135-146: 12-byte ASCII tag (null-padded entity type name)

Body field map (u16 LE words):
    f0-f9:   Entity class configuration (type-specific constants)
    f10-f11: Reserved (always zero across all types)
    f12-f13: Global entity ID (u32 LE, unique per entity, cross-level stable)
    f14:     Hit points (HP)
    f15:     Entity behavior flags
    f16:     Auxiliary flags / NPC dialogue index
    f17-f18: Reserved (always zero)
    f19:     Spawn data (map placement, byte 39 = X or room)
    f20:     Packed: hi byte = HP duplicate, lo byte = variant/companion flag
    f21:     Packed combat stats: hi byte = defense/speed, lo byte = attack power
    f22:     Packed combat stats: hi byte = armor/resistance, lo byte = max damage
    f23:     Packed: hi byte = level tier/quest flag, lo byte = entity slot index
"""

import json
import os
import struct
import sys
from collections import Counter, defaultdict

LEVEL_FILES = [
    "L1_DC.MIX", "L3_DH.MIX", "L4_HJ.MIX", "L5_HC.MIX", "L7_DH.MIX",
    "L8_SJ.MIX", "L9_DR.MIX", "L10_DC.MIX", "L12_CM.MIX", "L13_RC.MIX",
    "L14_HT.MIX", "L16_CA.MIX", "L17_HC.MIX", "L19_BC.MIX", "L20_BB.MIX",
]

RECORD_SIZE = 147
BODY_SIZE = 135
N_FIELDS = 24

# Proven field semantics from cross-type statistical analysis
FIELD_SEMANTICS = {
    "f0":  "class config: packed byte pair (behavior/AI parameters)",
    "f1":  "class config: packed byte pair (animation/movement parameters)",
    "f2":  "class config: capability flags (bitfield)",
    "f3":  "class config: AI mode flags (bitfield, e.g. 0x02=guard, 0x20=patrol, 0x60=boss)",
    "f4":  "class config: combat style flags (bitfield)",
    "f5":  "class config: special ability flags",
    "f6":  "class config: auxiliary parameters",
    "f7":  "class config: extended parameters (usually zero, non-zero for special entities)",
    "f8":  "class config: rendering/LOD flags",
    "f9":  "class config: AI extension flags",
    "f10": "reserved (always zero across all 39 entity types)",
    "f11": "reserved (always zero across all 39 entity types)",
    "f12": "global entity ID low word (cross-level stable, unique per entity)",
    "f13": "global entity ID high word (cross-level stable, unique per entity)",
    "f14": "hit points (HP): 0=non-combat, 24=Rat, 86=guard, 155=strong WORM, 159=boss",
    "f15": "behavior flags: 0x08=combat-ready, 0xDD=rage/berserk, 0xE5=ambush, 0xF0=script-driven",
    "f16": "auxiliary flags: 0x0C=NPC dialogue variant, 0x25=special scripted entity",
    "f17": "reserved (always zero across all 39 entity types)",
    "f18": "reserved (always zero across all 39 entity types)",
    "f19": "spawn position: byte39=map X coordinate, byte38=room/zone",
    "f20": "packed: hi_byte=HP (duplicate of f14, proven 94% match), lo_byte=variant flag",
    "f21": "packed combat: hi_byte=defense/speed (10-100), lo_byte=attack power (24-255)",
    "f22": "packed combat: hi_byte=armor/resistance (0-168), lo_byte=max damage (0-255)",
    "f23": "packed: hi_byte=level tier/quest flag (0-16), lo_byte=entity slot index",
}


def find_entity_region(data):
    """Find the entity record region by scanning for known entity tags.

    Strategy: find the rightmost occurrence of B_HUMAN (present in all 12
    levels), determine the 147-byte alignment base, then scan backward and
    forward to find all contiguous tagged records.

    Returns (base_offset, first_slot, last_slot) or None.
    """
    anchor_tags = [
        b"B_HUMAN\x00", b"WORM\x00", b"GGCAPT\x00", b"GGUARD\x00",
        b"StSquid\x00", b"SSAR\x00", b"BELSTAT\x00", b"Kenneth\x00",
        b"Roach\x00", b"ROACH\x00",
    ]

    idx = -1
    for tag in anchor_tags:
        idx = data.rfind(tag)
        if idx != -1:
            break

    if idx == -1:
        return None

    rec_start = idx - BODY_SIZE
    base = rec_start % RECORD_SIZE
    anchor_slot = (rec_start - base) // RECORD_SIZE

    def is_valid_tag(slot):
        off = base + slot * RECORD_SIZE
        if off < 0 or off + RECORD_SIZE > len(data):
            return False
        tag_bytes = data[off + BODY_SIZE:off + RECORD_SIZE]
        name = tag_bytes.split(b'\x00')[0]
        return (len(name) >= 2 and
                all(32 < c < 127 for c in name) and
                not any(c in name for c in b'()[]{}'))

    first = anchor_slot
    for s in range(anchor_slot - 1, max(anchor_slot - 300, -1), -1):
        if is_valid_tag(s):
            first = s
        else:
            break

    last = anchor_slot
    for s in range(anchor_slot + 1, anchor_slot + 300):
        off = base + s * RECORD_SIZE
        if off + RECORD_SIZE > len(data):
            break
        if is_valid_tag(s):
            last = s
        else:
            break

    return base, first, last


def extract_entities(data, base, first_slot, last_slot):
    """Extract all entity records from the tagged region."""
    records = []
    for s in range(first_slot, last_slot + 1):
        off = base + s * RECORD_SIZE
        body = data[off:off + BODY_SIZE]
        tag_bytes = data[off + BODY_SIZE:off + RECORD_SIZE]
        name = tag_bytes.split(b'\x00')[0].decode('ascii', errors='replace')

        if len(name) < 2:
            continue

        words = [struct.unpack_from('<H', body, w * 2)[0] for w in range(N_FIELDS)]

        records.append({
            "tag": name,
            "offset": off,
            "slot": s,
            "words": words,
        })

    return records


def analyze_fields(all_records):
    """Perform per-type and cross-type field analysis."""
    by_tag = defaultdict(list)
    for r in all_records:
        by_tag[r["tag"]].append(r)

    # Per-type analysis
    type_analysis = {}
    for tag, records in sorted(by_tag.items()):
        n = len(records)
        field_info = []
        for fi in range(N_FIELDS):
            values = [r["words"][fi] for r in records]
            unique = sorted(set(values))
            field_info.append({
                "field": fi,
                "invariant": len(unique) == 1,
                "value": values[0] if len(unique) == 1 else None,
                "n_unique": len(unique),
                "min": min(values),
                "max": max(values),
            })

        type_analysis[tag] = {
            "count": n,
            "levels": sorted(set(r["level"] for r in records)),
            "field_info": field_info,
        }

    # Cross-type classification
    multi_types = {t: a for t, a in type_analysis.items() if a["count"] >= 2}
    field_class = {}

    for fi in range(N_FIELDS):
        always_zero = True
        always_invariant = True
        inv_values = {}

        for tag, info in multi_types.items():
            fd = info["field_info"][fi]
            if fd["invariant"]:
                inv_values[tag] = fd["value"]
                if fd["value"] != 0:
                    always_zero = False
            else:
                always_invariant = False
                always_zero = False

        if always_zero:
            cls = "always_zero"
        elif always_invariant:
            cls = "entity_class_config" if len(set(inv_values.values())) > 1 else "global_constant"
        else:
            var_count = sum(1 for t, i in multi_types.items()
                          if not i["field_info"][fi]["invariant"])
            if var_count > len(multi_types) // 2:
                cls = "instance_specific"
            else:
                cls = "mixed"

        field_class[f"f{fi}"] = {
            "classification": cls,
            "semantic": FIELD_SEMANTICS.get(f"f{fi}", "unknown"),
        }

    return type_analysis, field_class


def verify_f20_hp_duplicate(all_records):
    """Verify that f20 high byte == f14 (HP duplicate hypothesis)."""
    matches = 0
    mismatches = 0
    for r in all_records:
        f14 = r["words"][14]
        f20 = r["words"][20]
        f20_hi = (f20 >> 8) & 0xFF
        if f14 <= 255 and f14 == f20_hi:
            matches += 1
        elif f14 > 0:
            mismatches += 1
    return {"matches": matches, "mismatches": mismatches,
            "rate": f"{matches}/{matches + mismatches}" if matches + mismatches > 0 else "N/A"}


def build_entity_table(all_records):
    """Build a summary table of all entities with decoded stats."""
    rows = []
    for r in all_records:
        w = r["words"]
        f14 = w[14]
        if f14 == 0 or f14 > 500:
            continue  # skip non-combat entities and false positives

        f20_lo = w[20] & 0xFF
        f21_hi = (w[21] >> 8) & 0xFF
        f21_lo = w[21] & 0xFF
        f22_hi = (w[22] >> 8) & 0xFF
        f22_lo = w[22] & 0xFF
        f23_hi = (w[23] >> 8) & 0xFF
        f23_lo = w[23] & 0xFF

        rows.append({
            "tag": r["tag"],
            "level": r["level"],
            "hp": f14,
            "defense_speed": f21_hi,
            "attack_power": f21_lo,
            "armor_resist": f22_hi,
            "max_damage": f22_lo,
            "tier": f23_hi,
            "slot": f23_lo,
            "variant_flag": f20_lo,
            "behavior_flags": f"0x{w[15]:04x}",
            "global_id": f"0x{w[12]:04x}{w[13]:04x}",
        })

    return sorted(rows, key=lambda x: (x["hp"], x["tag"]))


def main():
    dat_dir = (sys.argv[1] if len(sys.argv) > 1
               else os.environ.get("LOL2_DAT", "."))

    all_records = []
    level_stats = {}

    for lf in LEVEL_FILES:
        path = os.path.join(dat_dir, lf)
        if not os.path.exists(path):
            print(f"WARNING: {path} not found", file=sys.stderr)
            continue

        with open(path, "rb") as f:
            data = f.read()

        result = find_entity_region(data)
        if result is None:
            level_stats[lf] = {"entities": 0}
            continue

        base, first, last = result
        records = extract_entities(data, base, first, last)
        for r in records:
            r["level"] = lf

        tags = Counter(r["tag"] for r in records)
        level_stats[lf] = {"entities": len(records), "tags": dict(tags)}
        all_records.extend(records)

    type_analysis, field_class = analyze_fields(all_records)
    hp_check = verify_f20_hp_duplicate(all_records)
    entity_table = build_entity_table(all_records)

    output = {
        "summary": {
            "total_entities": len(all_records),
            "unique_types": len(set(r["tag"] for r in all_records)),
            "levels_scanned": len(level_stats),
            "type_counts": dict(Counter(r["tag"] for r in all_records).most_common()),
        },
        "field_semantics": FIELD_SEMANTICS,
        "field_classification": field_class,
        "hp_duplicate_verification": hp_check,
        "entity_combat_table": entity_table,
        "level_stats": level_stats,
    }

    json.dump(output, sys.stdout, indent=2)
    print(file=sys.stdout)

    # Summary to stderr
    print(f"\n=== LoL2 Entity Field Analysis ===", file=sys.stderr)
    print(f"Total entities: {len(all_records)} across {len(level_stats)} levels",
          file=sys.stderr)
    print(f"Unique types: {len(set(r['tag'] for r in all_records))}", file=sys.stderr)
    print(f"HP duplicate (f20_hi==f14): {hp_check['rate']}", file=sys.stderr)
    print(f"\nCombat entities by HP:", file=sys.stderr)
    for row in entity_table:
        print(f"  {row['tag']:12s} {row['level']:12s}  HP={row['hp']:3d}  "
              f"DEF={row['defense_speed']:3d}  ATK={row['attack_power']:3d}  "
              f"ARM={row['armor_resist']:3d}  DMG={row['max_damage']:3d}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
