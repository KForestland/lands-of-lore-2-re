#!/usr/bin/env python3
"""
LoL2 level geometry cracker — parse the 18-sub-entry geometry block from
level MIX files. Extracts vertices, sectors/faces (FFFF-delimited groups),
and generates 2D map visualizations.

Requires: Pillow (PIL)

Environment variables:
  LOL2_DAT   - path to the LoL2 DAT directory (default: current directory)
  LOL2_OUT   - output directory (default: ./lol2_geometry_out)
  LOL2_LEVEL - level name override (e.g. L1_DC, L10_DC)
"""
import struct, os, sys, argparse, json
from collections import Counter, defaultdict
from PIL import Image
import colorsys


# ---------------------------------------------------------------------------
# MIX parsing
# ---------------------------------------------------------------------------
def parse_mix(path):
    """Read a Westwood MIX archive."""
    with open(path, "rb") as f:
        blob = f.read()
    count = struct.unpack_from("<H", blob, 0)[0]
    hdr = 6 + count * 12
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, offset, size = struct.unpack_from("<III", blob, off)
        entries.append({"hash": h, "offset": hdr + offset, "size": size})
    return blob, entries


# ---------------------------------------------------------------------------
# Sub-entry parsing
# ---------------------------------------------------------------------------
def get_subs(data, total_size):
    """Parse a sub-entry table (count + offsets) from a geometry block."""
    if len(data) < 4:
        return {}
    count = struct.unpack_from("<I", data, 0)[0]
    if count > 100 or count < 1:
        return {}
    offsets = []
    for i in range(count):
        pos = 4 + i * 4
        if pos + 4 > len(data):
            break
        offsets.append(struct.unpack_from("<I", data, pos)[0])

    result = {}
    for i, off in enumerate(offsets):
        next_off = offsets[i+1] if i+1 < len(offsets) else total_size
        if 0 < off < total_size and next_off > off:
            result[i] = data[off:next_off]
    return result


def parse_ffff_groups(data):
    """Split u16 data by 0xFFFF delimiters, return list of u16 arrays."""
    vals = [struct.unpack_from("<H", data, i*2)[0] for i in range(len(data)//2)]
    groups = []
    current = []
    for v in vals:
        if v == 0xFFFF:
            if current:
                groups.append(current)
            current = []
        else:
            current.append(v)
    if current:
        groups.append(current)
    return groups


def find_strings(data, min_len=3):
    """Find ASCII strings in raw binary data."""
    result = []
    s = b""
    start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not s:
                start = i
            s += bytes([b])
        else:
            if len(s) >= min_len:
                result.append((start, s.decode("ascii")))
            s = b""
    if len(s) >= min_len:
        result.append((start, s.decode("ascii")))
    return result


# ---------------------------------------------------------------------------
# Level analysis
# ---------------------------------------------------------------------------
def analyze_level(name, path):
    """Full analysis of a level's geometry entry. Returns sub-entry results dict."""
    print(f"\n{'='*80}")
    print(f"  {name}")
    print(f"{'='*80}")

    blob, entries = parse_mix(path)

    # Find entries with 18 sub-entries (main geometry block)
    geo_entries = []
    for ei, e in enumerate(entries):
        data = blob[e["offset"]:e["offset"]+e["size"]]
        if len(data) >= 4:
            sc = struct.unpack_from("<I", data, 0)[0]
            if sc == 18:
                geo_entries.append((ei, e, data))

    if not geo_entries:
        print("  No 18-sub-entry geometry block found!")
        return None

    results = {}
    for geo_idx, (ei, e, data) in enumerate(geo_entries):
        label = f"Entry {ei} ({e['size']} bytes)"
        print(f"\n  --- {label} ---")

        subs = get_subs(data, e["size"])
        entry_results = {}

        for si in sorted(subs.keys()):
            sd = subs[si]
            sz = len(sd)

            ffff_groups = parse_ffff_groups(sd) if sz >= 4 else []
            strings = find_strings(sd)
            zero_pct = sd.count(0) / sz * 100 if sz > 0 else 0

            info = {
                "size": sz,
                "ffff_groups": len(ffff_groups),
                "strings": [s[1] for s in strings[:5]],
                "zero_pct": zero_pct,
            }

            # Try as u16 pairs (vertices)
            if sz >= 4 and sz % 4 == 0 and len(ffff_groups) <= 1:
                n = sz // 4
                pairs = []
                for j in range(n):
                    x = struct.unpack_from("<H", sd, j*4)[0]
                    y = struct.unpack_from("<H", sd, j*4+2)[0]
                    pairs.append((x, y))
                if pairs:
                    xs = [p[0] for p in pairs]
                    ys = [p[1] for p in pairs]
                    info["as_u16_pairs"] = {
                        "count": n,
                        "x_range": (min(xs), max(xs)),
                        "y_range": (min(ys), max(ys)),
                    }

            # FFFF group analysis
            if ffff_groups:
                gsizes = [len(g) for g in ffff_groups]
                info["group_sizes"] = Counter(gsizes).most_common(5)

                all_quads = []
                for g in ffff_groups:
                    for j in range(0, len(g)-3, 4):
                        all_quads.append(g[j:j+4])
                if all_quads:
                    info["quads"] = {
                        "count": len(all_quads),
                        "A": (min(q[0] for q in all_quads), max(q[0] for q in all_quads)),
                        "B": (min(q[1] for q in all_quads), max(q[1] for q in all_quads)),
                        "C": (min(q[2] for q in all_quads), max(q[2] for q in all_quads)),
                        "D": (min(q[3] for q in all_quads), max(q[3] for q in all_quads)),
                        "D_dist": Counter(q[3] for q in all_quads).most_common(10),
                    }

            entry_results[si] = {"info": info, "data": sd, "ffff_groups": ffff_groups}

            # Print summary
            extra = ""
            if info.get("as_u16_pairs"):
                p = info["as_u16_pairs"]
                extra = (f" -> {p['count']} pairs "
                         f"X[{p['x_range'][0]}-{p['x_range'][1]}] "
                         f"Y[{p['y_range'][0]}-{p['y_range'][1]}]")
            if info["ffff_groups"]:
                extra += f" -> {info['ffff_groups']} FFFF groups"
                if info.get("quads"):
                    extra += f", {info['quads']['count']} quads"
            if info["strings"]:
                extra += f" -> {info['strings'][:3]}"

            print(f"    sub[{si:2d}]: {sz:6d}B  zero={zero_pct:4.0f}%{extra}")

        results[ei] = entry_results

    return results


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def visualize_vertices(subs, ei, out_dir):
    """Plot vertex sub-entries as colored scatter plots."""
    saved = []
    for si in sorted(subs.keys()):
        info = subs[si]["info"]
        pairs = info.get("as_u16_pairs")
        if not pairs or pairs["count"] <= 10:
            continue

        sd = subs[si]["data"]
        n = pairs["count"]
        xs = [struct.unpack_from("<H", sd, j*4)[0] for j in range(n)]
        ys = [struct.unpack_from("<H", sd, j*4+2)[0] for j in range(n)]

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        if xmax == xmin or ymax == ymin:
            continue

        W = 800
        H = max(int(W * (ymax - ymin) / (xmax - xmin)), 100)

        img = Image.new('RGB', (W, H), (10, 10, 10))
        px = img.load()

        for j in range(n):
            ix = int((xs[j] - xmin) / (xmax - xmin) * (W - 1))
            iy = int((ys[j] - ymin) / (ymax - ymin) * (H - 1))
            r, g, b = colorsys.hsv_to_rgb((j / n) % 1.0, 0.8, 1.0)
            color = (int(r*255), int(g*255), int(b*255))
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = ix+dx, iy+dy
                    if 0 <= nx < W and 0 <= ny < H:
                        px[nx, ny] = color

        out_path = os.path.join(out_dir, f"entry{ei}_sub{si}_vertices.png")
        img.save(out_path)
        print(f"  Saved {out_path}: {n} vertices, X[{xmin}-{xmax}] Y[{ymin}-{ymax}]")
        saved.append(out_path)

    return saved


def visualize_sectors(subs, ei, out_dir):
    """Plot FFFF-group sector/face data as colored scatter plots."""
    saved = []
    for si in sorted(subs.keys()):
        info = subs[si]["info"]
        if not info.get("quads") or info["quads"]["count"] <= 5:
            continue

        groups = subs[si]["ffff_groups"]

        all_ab = []
        for g in groups:
            for j in range(0, len(g)-3, 4):
                all_ab.append((g[j], g[j+1]))

        if not all_ab:
            continue

        ax = [p[0] for p in all_ab]
        ay = [p[1] for p in all_ab]
        xmin, xmax = min(ax), max(ax)
        ymin, ymax = min(ay), max(ay)
        if xmax == xmin or ymax == ymin:
            continue

        W = 800
        H = max(int(W * (ymax - ymin) / (xmax - xmin)), 100)

        img = Image.new('RGB', (W, H), (10, 10, 10))
        px = img.load()

        for gi, g in enumerate(groups):
            r, g_c, b = colorsys.hsv_to_rgb((gi / len(groups)) % 1.0, 0.7, 0.9)
            color = (int(r*255), int(g_c*255), int(b*255))
            for j in range(0, len(g)-3, 4):
                a, b_v = g[j], g[j+1]
                ix = int((a - xmin) / (xmax - xmin) * (W - 1))
                iy = int((b_v - ymin) / (ymax - ymin) * (H - 1))
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        nx, ny = ix+dx, iy+dy
                        if 0 <= nx < W and 0 <= ny < H:
                            px[nx, ny] = color

        out_path = os.path.join(out_dir, f"entry{ei}_sub{si}_sectors.png")
        img.save(out_path)
        print(f"  Saved {out_path}: {len(groups)} groups, {len(all_ab)} quads")
        saved.append(out_path)

    return saved


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Parse and visualize LoL2 level geometry from MIX archives.")
    parser.add_argument("mix_path", nargs="?",
                        help="Path to a level MIX file (e.g. L1_DC.MIX). "
                             "If omitted, uses LOL2_DAT + LOL2_LEVEL.")
    parser.add_argument("-o", "--output", default=None,
                        help="Output directory (default: LOL2_OUT or ./lol2_geometry_out)")
    parser.add_argument("-l", "--level", default=None,
                        help="Level name (e.g. L1_DC). Overrides LOL2_LEVEL env var.")
    parser.add_argument("--no-viz", action="store_true",
                        help="Skip visualization output (text analysis only)")
    args = parser.parse_args()

    dat_dir = os.environ.get("LOL2_DAT", ".")
    out_dir = args.output or os.environ.get("LOL2_OUT", "./lol2_geometry_out")
    level = args.level or os.environ.get("LOL2_LEVEL", "L1_DC")
    os.makedirs(out_dir, exist_ok=True)

    if args.mix_path:
        mix_path = args.mix_path
        level = os.path.splitext(os.path.basename(mix_path))[0]
    else:
        mix_path = os.path.join(dat_dir, f"{level}.MIX")

    if not os.path.isfile(mix_path):
        print(f"Error: file not found: {mix_path}", file=sys.stderr)
        sys.exit(1)

    results = analyze_level(level, mix_path)

    if results and not args.no_viz:
        print(f"\nGenerating visualizations...")
        for ei, subs in results.items():
            visualize_vertices(subs, ei, out_dir)
            visualize_sectors(subs, ei, out_dir)

    # Export sub-entry structure summary as JSON
    if results:
        summary = {}
        for ei, subs in results.items():
            entry_summary = {}
            for si, sub in subs.items():
                info = sub["info"]
                # Remove non-serializable Counter items
                clean = {k: v for k, v in info.items() if k != "group_sizes"}
                if "quads" in clean:
                    q = clean["quads"]
                    q["D_dist"] = list(q["D_dist"])
                if "group_sizes" in info:
                    clean["group_sizes"] = list(info["group_sizes"])
                entry_summary[si] = clean
            summary[ei] = entry_summary

        json_path = os.path.join(out_dir, f"{level}_geometry_summary.json")
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\nSummary written to {json_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
