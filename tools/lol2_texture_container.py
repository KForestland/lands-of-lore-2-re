#!/usr/bin/env python3
"""Read LoL2 level texture containers (.TE_ entries in level MIX files).

A level MIX such as DAT/L1_DC.MIX holds one texture entry named
SPHERE<n>\\<LEVEL>\\<LEVEL>.TE_ (Westwood TD/RA filename hash). The entry is
LZO1X-blocked: u32 total size, then (u32 compressed size, LZO1X block) pairs
of up to 1 MiB decoded each, then a 4-byte zero trailer.

The decoded blob starts with u32 section count, u32 palette offset (seen in
L20_BB; see docs), then the section offset table at +8.
  section 2: 56-byte material descriptors ('<6H11I')
  section 3: material payload records referenced by the descriptors
  section 4: 256-byte shade (remap) rows

Only descriptor flag 0xA9 (raw 8-bit indices after an 8-byte header) is
decoded. Every other flag value is refused rather than guessed.

Requirements: Python 3.9+ standard library and the system liblzo2 shared
library (Debian/Ubuntu: liblzo2-2). It is loaded through ctypes; no python-lzo
package is needed. Reads only the user's own game files.

Usage:
  lol2_texture_container.py info     --mix DAT/L1_DC.MIX
  lol2_texture_container.py material --mix DAT/L1_DC.MIX --index 0
  lol2_texture_container.py export   --mix DAT/L1_DC.MIX --index 0 --out DIR
  lol2_texture_container.py blob     --mix DAT/L1_DC.MIX --out l1_dc.bin
"""
import argparse
import collections
import ctypes
import ctypes.util
import hashlib
import json
import os
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lol2_mix_parser import read_mix_with_hashes  # noqa: E402
from lol2_westwood_hash import ww_hash_v1  # noqa: E402

MAX_DECOMPRESSED = 64 * 1024 * 1024
LZO_BLOCK = 1024 * 1024
DESCRIPTOR_SIZE = 56
DESCRIPTOR_FORMAT = "<6H11I"
SHADE_ROW_BYTES = 256
INITIAL_SHADE_ROW = 64
RAW_FLAGS = 0xA9


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# MIX entry lookup and LZO1X block decode
# ---------------------------------------------------------------------------
def texture_entry_name(level, sphere):
    level = level.upper()
    return f"SPHERE{sphere}\\{level}\\{level}.TE_"


def find_texture_entry(mix_path, level=None):
    """Return (mix bytes, entry dict, entry name) for the level's .TE_ entry."""
    mix_path = Path(mix_path)
    level = (level or mix_path.stem).upper()
    data, entries, base = read_mix_with_hashes(str(mix_path))
    by_key = {key: (i, off, size) for i, (key, off, size) in enumerate(entries)}
    for sphere in range(0, 10):
        name = texture_entry_name(level, sphere)
        key = ww_hash_v1(name)
        if key in by_key:
            index, off, size = by_key[key]
            require(base + off + size <= len(data), "texture entry exceeds MIX data")
            return data, dict(index=index, key=key, offset=base + off, size=size), name
    raise ValueError(f"no SPHERE<n>\\{level}\\{level}.TE_ entry in {mix_path.name}")


def _lzo_decompress_fn():
    library = ctypes.util.find_library("lzo2")
    require(bool(library), "liblzo2 shared library is required (e.g. apt install liblzo2-2)")
    fn = ctypes.CDLL(library).lzo1x_decompress_safe
    fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                   ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
    fn.restype = ctypes.c_int
    return fn


def decode_lzo_container(raw):
    """Bounded liblzo2 decode of one .TE_ entry. Returns (blob, block list)."""
    fn = _lzo_decompress_fn()
    require(len(raw) >= 4, "entry truncated before size header")
    total = struct.unpack_from("<I", raw)[0]
    require(0 < total <= MAX_DECOMPRESSED, "decompressed size out of bounds")
    output = bytearray()
    cursor = 4
    blocks = []
    while len(output) < total:
        require(cursor + 4 <= len(raw), "truncated block header")
        size = struct.unpack_from("<I", raw, cursor)[0]
        cursor += 4
        require(0 < size <= len(raw) - cursor, "block size out of bounds")
        src = ctypes.create_string_buffer(raw[cursor:cursor + size])
        dst = ctypes.create_string_buffer(LZO_BLOCK)
        n = ctypes.c_size_t(len(dst))
        code = fn(src, size, dst, ctypes.byref(n), None)
        expected = min(LZO_BLOCK, total - len(output))
        require(code == 0 and n.value == expected,
                f"lzo1x_decompress_safe failed (code={code})")
        blocks.append(dict(offset=cursor, compressed=size, decoded=n.value))
        output.extend(dst.raw[:n.value])
        cursor += size
    require(raw[cursor:] == bytes(4), "unexpected trailer after blocks")
    return bytes(output), blocks


def load_blob(mix_path, level=None):
    data, entry, name = find_texture_entry(mix_path, level)
    blob, blocks = decode_lzo_container(data[entry["offset"]:entry["offset"] + entry["size"]])
    return blob, dict(entry_name=name, entry=entry, blocks=len(blocks),
                      size=len(blob), sha256=sha256(blob))


# ---------------------------------------------------------------------------
# Blob grammar
# ---------------------------------------------------------------------------
def sections(blob):
    require(len(blob) >= 8, "missing blob header")
    count = struct.unpack_from("<I", blob)[0]
    require(4 <= count <= 256 and 8 + 4 * count <= len(blob), "bad section count")
    offsets = struct.unpack_from("<" + "I" * count, blob, 8)
    require(all(v == 0 or 8 + 4 * count <= v <= len(blob) for v in offsets),
            "section outside blob")
    return offsets


def descriptor_count(blob):
    offsets = sections(blob)
    table, payload = offsets[2], offsets[3]
    require(table > 0 and payload > table and (payload - table) % DESCRIPTOR_SIZE == 0,
            "unsupported descriptor table extent")
    return (payload - table) // DESCRIPTOR_SIZE


def descriptor(blob, index):
    """Return the raw 56-byte descriptor fields (any flag value)."""
    offsets = sections(blob)
    count = descriptor_count(blob)
    require(0 <= index < count, "descriptor index outside table")
    position = offsets[2] + index * DESCRIPTOR_SIZE
    v = struct.unpack_from(DESCRIPTOR_FORMAT, blob, position)
    return dict(index=index, descriptor_start=position, identifier=v[0], width=v[1],
                height=v[2], flags=v[3], field8=v[4], field10=v[5],
                name_hash_candidate=v[6], mip_offsets=list(v[7:12]),
                mip_sizes=list(v[12:17]))


def material_record(blob, index, allow_partial_mips=False):
    """Validate one 0xA9 descriptor and its mip chain (5 levels by default)."""
    offsets = sections(blob)
    d = descriptor(blob, index)
    require(d["flags"] == RAW_FLAGS, f"flag 0x{d['flags']:X} unsupported (only 0xA9)")
    require(d["width"] > 0 and d["height"] > 0, "zero material dimension")
    payload = offsets[3]
    payload_end = min((v for v in offsets if v > payload), default=len(blob))
    sizes = d["mip_sizes"]
    levels = 5
    if allow_partial_mips:
        levels = sum(s != 0 for s in sizes)
        require(1 <= levels <= 5, "empty mip chain")
        require(all(sizes[k] > 0 for k in range(levels)) and
                all(sizes[k] == d["mip_offsets"][k] == 0 for k in range(levels, 5)),
                "mip chain has holes")
        require((d["field10"] & 255) == levels, "mip count field mismatch")
    mips = []
    for level in range(levels):
        start = payload + d["mip_offsets"][level]
        size = sizes[level]
        require(size >= 8 and payload <= start and start + size <= payload_end,
                "mip outside payload section")
        flags, w, h, length16 = struct.unpack_from("<4H", blob, start)
        require(flags == d["flags"], "descriptor/mip flags mismatch")
        require((w, h) == (max(1, d["width"] >> level), max(1, d["height"] >> level)),
                "descriptor/mip dimensions mismatch")
        require(size == 8 + w * h and length16 == (w * h) & 0xFFFF,
                "mip byte extent mismatch")
        mips.append(dict(level=level, start=start, data_start=start + 8, width=w,
                         height=h, record_size=size,
                         pixels_sha256=sha256(blob[start + 8:start + size])))
    d["mips"] = mips
    return d


def shade_row(blob, row=INITIAL_SHADE_ROW):
    """256-byte shade row: section 4 + row * 256, bounded by section 5."""
    offsets = sections(blob)
    require(len(offsets) > 4 and offsets[4] > 0, "shade section missing")
    start = offsets[4] + row * SHADE_ROW_BYTES
    end = start + SHADE_ROW_BYTES
    shade_end = offsets[5] if len(offsets) > 5 and offsets[5] else len(blob)
    require(0 <= row and end <= shade_end, "shade row outside shade section")
    return blob[start:end]


def palette_dac(blob):
    """768-byte 6-bit palette at the header dword +4 (witnessed for L20_BB)."""
    offset = struct.unpack_from("<I", blob, 4)[0]
    require(0 < offset and offset + 768 <= len(blob), "palette offset out of bounds")
    dac = blob[offset:offset + 768]
    require(max(dac) <= 63, "palette exceeds 6-bit DAC range")
    return dac


def column_major_to_rows(data, width, height):
    require(len(data) == width * height, "pixel extent mismatch")
    return bytes(data[x * height + y] for y in range(height) for x in range(width))


def png_rgb(width, height, pixels):
    def chunk(kind, content):
        return (struct.pack(">I", len(content)) + kind + content +
                struct.pack(">I", zlib.crc32(kind + content)))
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_info(args):
    blob, info = load_blob(args.mix, args.level)
    offsets = sections(blob)
    count = descriptor_count(blob)
    flags = collections.Counter(descriptor(blob, i)["flags"] for i in range(count))
    info.update(sections=[f"0x{v:X}" for v in offsets], descriptors=count,
                flags={f"0x{k:X}": v for k, v in sorted(flags.items())})
    print(json.dumps(info, indent=2))


def cmd_material(args):
    blob, _ = load_blob(args.mix, args.level)
    d = descriptor(blob, args.index)
    if d["flags"] == RAW_FLAGS:
        d = material_record(blob, args.index, args.partial_mips)
    else:
        d["note"] = "flag not decoded by this tool"
    print(json.dumps(d, indent=2))


def cmd_export(args):
    blob, info = load_blob(args.mix, args.level)
    d = material_record(blob, args.index, args.partial_mips)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rgb = bytes((v * 255 + 31) // 63 for v in palette_dac(blob))
    shade = shade_row(blob, args.shade_row) if args.shade_row is not None else None
    for mip in d["mips"]:
        w, h = mip["width"], mip["height"]
        raw = blob[mip["data_start"]:mip["data_start"] + w * h]
        indices = column_major_to_rows(raw, w, h)
        if shade is not None:
            indices = bytes(shade[i] for i in indices)
        pixels = b"".join(rgb[i * 3:i * 3 + 3] for i in indices)
        (out / f"material_{args.index}_mip{mip['level']}.png").write_bytes(png_rgb(w, h, pixels))
    print(f"wrote {len(d['mips'])} mip PNGs for descriptor {args.index} to {out}")


def cmd_blob(args):
    blob, info = load_blob(args.mix, args.level)
    Path(args.out).write_bytes(blob)
    print(json.dumps(info, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("info", cmd_info), ("material", cmd_material),
                     ("export", cmd_export), ("blob", cmd_blob)):
        p = sub.add_parser(name)
        p.add_argument("--mix", required=True, help="level MIX from your own install, e.g. ./lol2_game/DAT/L1_DC.MIX")
        p.add_argument("--level", help="level name if it differs from the MIX file stem")
        p.set_defaults(func=fn)
        if name in ("material", "export"):
            p.add_argument("--index", type=int, required=True, help="descriptor index")
            p.add_argument("--partial-mips", action="store_true",
                           help="accept fewer than five mip levels (count from field10)")
        if name == "export":
            p.add_argument("--out", required=True, help="output directory")
            p.add_argument("--shade-row", type=int, default=None,
                           help="apply this 256-byte shade row before the palette")
        if name == "blob":
            p.add_argument("--out", required=True, help="output file for the decoded blob")
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, OSError, struct.error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
