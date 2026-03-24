#!/usr/bin/env python3
"""
Decode VQA (Vector Quantization Animation) texture files from LoL2 MIX archives.
Parses the IFF FORM/WVQA chunk structure: VQHD headers, FINF frame indices,
codebook chunks (CBF0/CBFZ/CBP0/CBPZ), vector pointer chunks (VPT0/VPTZ/VPTR/VPRZ),
palette (CPL0), and audio chunks (SND0/SND1/SND2).

Environment variables:
  LOL2_DAT   - path to the LoL2 DAT directory (default: current directory)
  LOL2_OUT   - output directory (default: ./lol2_vqa_out)
"""
import struct, os, sys, argparse
from collections import defaultdict


def read_mix(path):
    """Read a Westwood MIX archive, return (raw_data, entry_list, data_base_offset)."""
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack_from("<H", data, 0)[0]
    entries = []
    for i in range(count):
        off = 6 + i * 12
        h, o, s = struct.unpack_from("<III", data, off)
        entries.append((h, o, s))
    return data, entries, 6 + count * 12


def parse_vqa_chunks(edata):
    """Parse all IFF chunks from a FORM/WVQA entry. Returns list of (chunk_id, chunk_data)."""
    if len(edata) < 12 or edata[:4] != b'FORM' or edata[8:12] != b'WVQA':
        return None

    form_size = struct.unpack_from(">I", edata, 4)[0]
    chunks = []
    pos = 12
    while pos + 8 <= len(edata):
        chunk_id = edata[pos:pos+4]
        chunk_size = struct.unpack_from(">I", edata, pos+4)[0]
        chunk_data = edata[pos+8:pos+8+chunk_size]
        chunks.append((chunk_id, chunk_data))
        pos += 8 + chunk_size
        if chunk_size % 2:
            pos += 1  # IFF padding to even boundary
    return chunks


def parse_vqhd(chunk_data):
    """Parse a VQHD (VQA Header) chunk, return dict of fields."""
    if len(chunk_data) < 24:
        return {"raw": list(chunk_data)}
    return {
        "version":    struct.unpack_from("<H", chunk_data, 0)[0],
        "flags":      struct.unpack_from("<H", chunk_data, 2)[0],
        "num_frames": struct.unpack_from("<H", chunk_data, 4)[0],
        "width":      struct.unpack_from("<H", chunk_data, 6)[0],
        "height":     struct.unpack_from("<H", chunk_data, 8)[0],
        "block_w":    chunk_data[10],
        "block_h":    chunk_data[11],
        "frame_rate": chunk_data[12],
        "cbparts":    chunk_data[13],
        "colors":     struct.unpack_from("<H", chunk_data, 14)[0],
        "max_blocks": struct.unpack_from("<H", chunk_data, 16)[0],
    }


def describe_chunk(chunk_id, chunk_data):
    """Return a human-readable description of a chunk."""
    cid = chunk_id.decode('ascii', errors='replace')
    sz = len(chunk_data)

    if chunk_id == b'VQHD':
        hdr = parse_vqhd(chunk_data)
        if "width" in hdr:
            return (f"VQHD: ver={hdr['version']} flags=0x{hdr['flags']:04X} "
                    f"frames={hdr['num_frames']} {hdr['width']}x{hdr['height']} "
                    f"block={hdr['block_w']}x{hdr['block_h']} fps={hdr['frame_rate']} "
                    f"cbparts={hdr['cbparts']} colors={hdr['colors']} "
                    f"max_blocks={hdr['max_blocks']}")
        return f"VQHD: {sz} bytes (short header)"

    if chunk_id == b'FINF':
        return f"FINF: {sz} bytes (frame index)"

    if chunk_id in (b'CBF0', b'CBFZ', b'CBP0', b'CBPZ'):
        return f"{cid}: {sz} bytes (codebook)"

    if chunk_id in (b'VPT0', b'VPTZ', b'VPTR', b'VPRZ'):
        return f"{cid}: {sz} bytes (vector pointers)"

    if chunk_id == b'CPL0':
        info = f"CPL0: {sz} bytes (palette)"
        if sz >= 30:
            max_val = max(chunk_data[:min(768, sz)])
            info += f" max_val={max_val} {'(VGA 6-bit)' if max_val <= 63 else '(8-bit)'}"
        return info

    if chunk_id in (b'SND0', b'SND1', b'SND2'):
        return f"{cid}: {sz} bytes (audio)"

    return f"{cid}: {sz} bytes"


def process_mix(mix_path, verbose=False):
    """Parse all VQA entries in a MIX file. Returns list of entry info dicts."""
    data, entries, base = read_mix(mix_path)
    results = []

    print(f"\n{os.path.basename(mix_path)}: {len(entries)} entries")

    dim_counts = defaultdict(int)

    for i, (h, o, s) in enumerate(entries):
        edata = data[base+o:base+o+s]

        if edata[:4] != b'FORM' or len(edata) < 12 or edata[8:12] != b'WVQA':
            if verbose:
                magic = edata[:4].hex() if len(edata) >= 4 else "short"
                print(f"  Entry {i}: non-VQA ({magic}, {s} bytes)")
            continue

        chunks = parse_vqa_chunks(edata)
        if chunks is None:
            continue

        # Extract header info
        hdr = None
        chunk_summary = []
        for chunk_id, chunk_data in chunks:
            chunk_summary.append(describe_chunk(chunk_id, chunk_data))
            if chunk_id == b'VQHD':
                hdr = parse_vqhd(chunk_data)

        entry_info = {
            "index": i,
            "size": s,
            "header": hdr,
            "num_chunks": len(chunks),
            "chunk_types": [c[0].decode('ascii', errors='replace') for c, _ in
                           [(cid, cd) for cid, cd in chunks]],
        }
        results.append(entry_info)

        if hdr and "width" in hdr:
            dim_counts[(hdr["width"], hdr["height"])] += 1

        print(f"\n  Entry {i}: FORM/WVQA size={s}")
        for desc in chunk_summary:
            print(f"    {desc}")

    # Summary
    if dim_counts:
        print(f"\n  Dimension summary ({len(results)} VQA files):")
        for (w, h), cnt in sorted(dim_counts.items()):
            print(f"    {w}x{h}: {cnt} files")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parse VQA (FORM/WVQA) entries from a LoL2 MIX archive.")
    parser.add_argument("mix_path", nargs="?",
                        help="Path to a MIX file (e.g. L10_DCI.MIX). "
                             "If omitted, uses LOL2_DAT/L10_DCI.MIX")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show non-VQA entries too")
    args = parser.parse_args()

    dat_dir = os.environ.get("LOL2_DAT", ".")

    if args.mix_path:
        mix_path = args.mix_path
    else:
        mix_path = os.path.join(dat_dir, "L10_DCI.MIX")

    if not os.path.isfile(mix_path):
        print(f"Error: file not found: {mix_path}", file=sys.stderr)
        sys.exit(1)

    process_mix(mix_path, verbose=args.verbose)


if __name__ == "__main__":
    main()
