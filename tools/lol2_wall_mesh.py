#!/usr/bin/env python3
"""
Generate 3D wall meshes (OBJ format) from LoL2 level geometry.
Reads the 18-sub-entry geometry block from a level MIX file, extracts
wall tiles and wall segments, and outputs a Wavefront OBJ file suitable
for viewing in any 3D viewer or importing into Godot.

Wall tile structure:
  Position: [1]=X, [2]=Z (world coordinates)
  Height: [17] (wall height in game units)
  Normal/direction: [4] (signed, determines wall facing)
  Texture ID: values 150-300 in [8-15] and [26-33]

Environment variables:
  LOL2_DAT   - path to the LoL2 DAT directory (default: current directory)
  LOL2_OUT   - output directory (default: current directory)
"""
import struct, os, sys, argparse
from collections import defaultdict


# ---------------------------------------------------------------------------
# MIX parsing
# ---------------------------------------------------------------------------
def read_mix(path):
    """Read a Westwood MIX archive."""
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack_from("<H", data, 0)[0]
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, o, s = struct.unpack_from("<III", data, off)
        entries.append((h, o, s))
    return data, entries, 6 + count * 12


def get_sub(data, base, entry_offset):
    """Parse sub-entry table from a geometry entry."""
    start = base + entry_offset
    sc = struct.unpack_from("<I", data, start)[0]
    so = [struct.unpack_from("<I", data, start + 4 + i*4)[0] for i in range(sc)]
    return sc, so, start


def s16(v):
    """Convert unsigned 16-bit to signed."""
    return v - 65536 if v > 32767 else v


def split_ffff(vals):
    """Split a u16 list by 0xFFFF delimiters."""
    groups, cur = [], []
    for v in vals:
        if v == 0xFFFF:
            groups.append(cur)
            cur = []
        else:
            cur.append(v)
    if cur:
        groups.append(cur)
    return groups


def read_u16(data, begin, end):
    """Read a range of bytes as little-endian u16 values."""
    return [struct.unpack_from("<H", data, i)[0] for i in range(begin, end-1, 2)]


# ---------------------------------------------------------------------------
# Tile extraction
# ---------------------------------------------------------------------------
def extract_tiles(rec):
    """Extract 37-word tiles from a face record."""
    tiles = []
    n = len(rec) // 37
    for i in range(n):
        tiles.append(rec[i*37:(i+1)*37])
    return tiles


def get_texture_id(tile):
    """Find the dominant texture ID in a tile's texture blocks."""
    tex_ids = defaultdict(int)
    for block_start in [8, 26]:
        for pos in range(block_start, block_start + 8):
            v = tile[pos]
            if 150 <= v <= 300:
                tex_ids[v] += 1
    if tex_ids:
        return max(tex_ids, key=tex_ids.get)
    return 0


def wall_normal_from_r4(r4):
    """Determine wall facing direction from rec[4] value.
    Returns (nx, nz) unit normal."""
    sr4 = s16(r4)
    if abs(sr4) < 30:
        return (0, 1)   # facing +Z (north)
    elif sr4 > 0:
        return (1, 0)   # facing +X (east)
    else:
        return (-1, 0)  # facing -X (west)


# ---------------------------------------------------------------------------
# Geometry entry auto-detection
# ---------------------------------------------------------------------------
def find_geometry_entry(data, entries, base):
    """Find the MIX entry index that contains an 18-sub-entry geometry block."""
    for i, (h, o, s) in enumerate(entries):
        start = base + o
        if start + 4 > len(data):
            continue
        sc = struct.unpack_from("<I", data, start)[0]
        if sc == 18:
            return i
    return None


# ---------------------------------------------------------------------------
# Mesh generation
# ---------------------------------------------------------------------------
def generate_wall_mesh(mix_path, obj_path, geo_idx=None):
    """Generate an OBJ file for a level's wall geometry.
    If geo_idx is None, auto-detect the geometry entry."""
    data, entries, base = read_mix(mix_path)
    level_name = os.path.splitext(os.path.basename(mix_path))[0]

    if geo_idx is None:
        geo_idx = find_geometry_entry(data, entries, base)
        if geo_idx is None:
            print(f"Error: no 18-sub-entry geometry block found in {mix_path}",
                  file=sys.stderr)
            return None
        print(f"  Auto-detected geometry entry: {geo_idx}")

    if geo_idx >= len(entries):
        print(f"Error: entry index {geo_idx} out of range (max {len(entries)-1})",
              file=sys.stderr)
        return None

    geo = entries[geo_idx]
    sc, so, start = get_sub(data, base, geo[1])
    if sc <= 4:
        print(f"Error: entry {geo_idx} has only {sc} sub-entries (expected 18)",
              file=sys.stderr)
        return None

    # Read sub[4] face records
    s4 = read_u16(data, start+so[4], start+so[5])
    s4g = split_ffff(s4)

    # Extract face records
    faces = []
    for gi, grp in enumerate(s4g):
        pp = [i for i, v in enumerate(grp) if v == 768]
        for pi, pos in enumerate(pp):
            end = pp[pi+1] if pi+1 < len(pp) else len(grp)
            rec = grp[pos:end]
            if len(rec) >= 7:
                faces.append((gi, rec))

    # Read sub[0] g0 vertices for wall segments
    s0_all = read_u16(data, start+so[0], start+so[1])
    s0g = split_ffff(s0_all)
    g0 = s0g[0] if s0g else []
    g0_entries = len(g0) // 4

    # Collect all wall tiles
    tiles_data = []

    for gi, rec in faces:
        size = len(rec)

        if size >= 37:
            tile_list = extract_tiles(rec)
            for tile in tile_list:
                fx = s16(tile[1])
                fz = s16(tile[2])
                height = tile[17]
                tex_id = get_texture_id(tile)
                r4 = s16(tile[4])
                normal = wall_normal_from_r4(r4)
                f6 = tile[6]

                if abs(fz) < 50 and abs(fx) > 5000:
                    continue
                tiles_data.append((fx, fz, height, tex_id, normal, f6))

        elif 23 <= size < 37:
            fx = s16(rec[1])
            fz = s16(rec[2])
            height = rec[17] if len(rec) > 17 else 64
            tex_id = 0
            for pos in range(8, min(16, len(rec))):
                v = rec[pos]
                if 150 <= v <= 300:
                    tex_id = v
                    break
            r4 = s16(rec[4])
            normal = wall_normal_from_r4(r4)
            f6 = rec[6]

            if abs(fz) < 50 and abs(fx) > 5000:
                continue
            tiles_data.append((fx, fz, height, tex_id, normal, f6))

    # Generate vertices and faces
    vertices = []
    face_indices = []

    SCALE = 1.0 / 128.0
    WALL_THICKNESS = 4

    for fx, fz, height, tex_id, (nx, nz), f6 in tiles_data:
        if height <= 0:
            height = 64

        cx = fx * SCALE
        cy = 0
        cz = fz * SCALE
        h = height * SCALE

        tx, tz = -nz, nx
        hw = WALL_THICKNESS * SCALE

        v_base = len(vertices)
        vertices.append((cx - tx * hw, cy, cz - tz * hw))
        vertices.append((cx + tx * hw, cy, cz + tz * hw))
        vertices.append((cx + tx * hw, cy + h, cz + tz * hw))
        vertices.append((cx - tx * hw, cy + h, cz - tz * hw))

        face_indices.append((v_base + 1, v_base + 2, v_base + 3, v_base + 4))

    # Wall segments from sub[0] g0 consecutive vertices
    wall_segments = []
    for i in range(g0_entries - 1):
        x1 = s16(g0[i * 4 + 1])
        z1 = s16(g0[i * 4 + 3])
        x2 = s16(g0[(i + 1) * 4 + 1])
        z2 = s16(g0[(i + 1) * 4 + 3])

        dist = ((x2 - x1) ** 2 + (z2 - z1) ** 2) ** 0.5
        if 10 < dist < 500:
            wall_segments.append((x1, z1, x2, z2))

    SEGMENT_HEIGHT = 64 * SCALE
    for x1, z1, x2, z2 in wall_segments:
        v_base = len(vertices)
        vertices.append((x1 * SCALE, 0, z1 * SCALE))
        vertices.append((x2 * SCALE, 0, z2 * SCALE))
        vertices.append((x2 * SCALE, SEGMENT_HEIGHT, z2 * SCALE))
        vertices.append((x1 * SCALE, SEGMENT_HEIGHT, z1 * SCALE))
        face_indices.append((v_base + 1, v_base + 2, v_base + 3, v_base + 4))

    # Write OBJ
    os.makedirs(os.path.dirname(obj_path) if os.path.dirname(obj_path) else ".", exist_ok=True)
    with open(obj_path, "w") as f:
        f.write(f"# {level_name} wall geometry\n")
        f.write(f"# {len(tiles_data)} wall tiles + {len(wall_segments)} wall segments\n")
        f.write(f"# Scale: 1 unit = 128 game units\n\n")

        for v in vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")

        f.write(f"\n# Wall tiles\n")
        f.write(f"g wall_tiles\n")
        for v1, v2, v3, v4 in face_indices[:len(tiles_data)]:
            f.write(f"f {v1} {v2} {v3} {v4}\n")

        if wall_segments:
            f.write(f"\n# Wall segments from sub[0] g0\n")
            f.write(f"g wall_segments\n")
            for v1, v2, v3, v4 in face_indices[len(tiles_data):]:
                f.write(f"f {v1} {v2} {v3} {v4}\n")

    # Stats
    tex_dist = defaultdict(int)
    height_dist = defaultdict(int)
    for fx, fz, h, tid, n, f6 in tiles_data:
        tex_dist[tid] += 1
        height_dist[h] += 1

    stats = {
        'tiles': len(tiles_data),
        'segments': len(wall_segments),
        'vertices': len(vertices),
        'faces': len(face_indices),
        'tex_ids': dict(sorted(tex_dist.items(), key=lambda x: -x[1])[:5]),
        'heights': dict(sorted(height_dist.items(), key=lambda x: -x[1])[:5]),
    }

    print(f"  {level_name}: {stats['tiles']} tiles + {stats['segments']} segments "
          f"= {stats['faces']} faces, {stats['vertices']} vertices")
    print(f"  Output: {obj_path}")
    print(f"  Top texture IDs: {stats['tex_ids']}")
    print(f"  Top heights: {stats['heights']}")

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate OBJ wall meshes from LoL2 level MIX geometry.")
    parser.add_argument("mix_path",
                        help="Path to a level MIX file (e.g. L1_DC.MIX)")
    parser.add_argument("-o", "--output", default=None,
                        help="Output OBJ path (default: LOL2_OUT/<level>_walls.obj)")
    parser.add_argument("-g", "--geo-index", type=int, default=None,
                        help="Geometry entry index (auto-detected if omitted)")
    args = parser.parse_args()

    out_dir = os.environ.get("LOL2_OUT", ".")

    if not os.path.isfile(args.mix_path):
        print(f"Error: file not found: {args.mix_path}", file=sys.stderr)
        sys.exit(1)

    level_name = os.path.splitext(os.path.basename(args.mix_path))[0]

    if args.output:
        obj_path = args.output
    else:
        obj_path = os.path.join(out_dir, f"{level_name}_walls.obj")

    stats = generate_wall_mesh(args.mix_path, obj_path, args.geo_index)
    if stats is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
