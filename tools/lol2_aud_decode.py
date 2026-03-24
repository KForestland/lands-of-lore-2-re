#!/usr/bin/env python3
"""Westwood AUD audio decoder for Lands of Lore 2.

Decodes IMA-ADPCM (codec 99) audio from Westwood MIX containers to WAV.

AUD header (12 bytes):
  u16 sample_rate
  u32 compressed_size
  u32 output_size
  u8  flags  (bit0=stereo, bit1=16bit)
  u8  codec  (99 = IMA-ADPCM)

Chunk format (8-byte header + data):
  u16 compressed_size
  u16 decompressed_size
  u32 id  (0x0000DEAF)
  [compressed_size bytes of IMA-ADPCM data]

Usage:
  python lol2_aud_decode.py <MIXFILE> [entry_index] [-o output.wav]
  python lol2_aud_decode.py --raw <AUD_FILE> [-o output.wav]

Environment:
  LOL2_DAT  - path to LoL2 game files directory (default: current directory)
"""

import os
import struct
import sys
import wave

# ---------------------------------------------------------------------------
# IMA-ADPCM tables (standard)
# ---------------------------------------------------------------------------
IMA_INDEX_TABLE = [
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8,
]

IMA_STEP_TABLE = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
    157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544,
    598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707,
    1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871,
    5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
    15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
]


def decode_ima_nibble(nibble, predictor, step_index):
    """Decode a single 4-bit IMA-ADPCM nibble.

    Returns (new_predictor, new_step_index).
    """
    step = IMA_STEP_TABLE[step_index]

    # Compute difference
    diff = step >> 3
    if nibble & 4:
        diff += step
    if nibble & 2:
        diff += step >> 1
    if nibble & 1:
        diff += step >> 2

    # Apply sign
    if nibble & 8:
        predictor -= diff
    else:
        predictor += diff

    # Clamp to 16-bit signed range
    if predictor > 32767:
        predictor = 32767
    elif predictor < -32768:
        predictor = -32768

    # Update step index
    step_index += IMA_INDEX_TABLE[nibble]
    if step_index < 0:
        step_index = 0
    elif step_index > 88:
        step_index = 88

    return predictor, step_index


def decode_ima_adpcm_block(data, predictor=0, step_index=0):
    """Decode a block of IMA-ADPCM data (packed nibbles, low nibble first).

    Returns (list_of_s16_samples, final_predictor, final_step_index).
    """
    samples = []
    for byte in data:
        # Low nibble first
        lo = byte & 0x0F
        hi = (byte >> 4) & 0x0F

        predictor, step_index = decode_ima_nibble(lo, predictor, step_index)
        samples.append(predictor)

        predictor, step_index = decode_ima_nibble(hi, predictor, step_index)
        samples.append(predictor)

    return samples, predictor, step_index


# ---------------------------------------------------------------------------
# AUD parser
# ---------------------------------------------------------------------------
AUD_HEADER_SIZE = 12
CHUNK_HEADER_SIZE = 8
CHUNK_MAGIC = 0x0000DEAF


def parse_aud_header(data):
    """Parse a 12-byte Westwood AUD header.

    Returns dict with keys: sample_rate, comp_size, output_size, stereo,
    is_16bit, codec.
    """
    if len(data) < AUD_HEADER_SIZE:
        raise ValueError(f"AUD data too short ({len(data)} bytes)")

    sample_rate = struct.unpack_from("<H", data, 0)[0]
    comp_size = struct.unpack_from("<I", data, 2)[0]
    output_size = struct.unpack_from("<I", data, 6)[0]
    flags = data[10]
    codec = data[11]

    return {
        "sample_rate": sample_rate,
        "comp_size": comp_size,
        "output_size": output_size,
        "stereo": bool(flags & 1),
        "is_16bit": bool(flags & 2),
        "codec": codec,
    }


def decode_aud(data):
    """Decode a Westwood AUD byte string to raw PCM samples.

    Returns (header_dict, pcm_bytes) where pcm_bytes is 16-bit LE signed PCM.
    """
    hdr = parse_aud_header(data)

    if hdr["codec"] != 99:
        raise ValueError(f"Unsupported codec {hdr['codec']} (only IMA-ADPCM / codec 99 supported)")

    channels = 2 if hdr["stereo"] else 1
    sample_width = 2 if hdr["is_16bit"] else 1

    # Walk the chunks
    pos = AUD_HEADER_SIZE
    end = AUD_HEADER_SIZE + hdr["comp_size"]
    all_samples = []
    predictor = 0
    step_index = 0
    chunk_count = 0

    while pos + CHUNK_HEADER_SIZE <= end:
        chunk_comp = struct.unpack_from("<H", data, pos)[0]
        chunk_decomp = struct.unpack_from("<H", data, pos + 2)[0]
        chunk_id = struct.unpack_from("<I", data, pos + 4)[0]

        if chunk_id != CHUNK_MAGIC:
            print(f"WARNING: chunk {chunk_count} at offset {pos} has unexpected id 0x{chunk_id:08X} (expected 0x{CHUNK_MAGIC:08X})",
                  file=sys.stderr)

        chunk_data = data[pos + CHUNK_HEADER_SIZE: pos + CHUNK_HEADER_SIZE + chunk_comp]
        if len(chunk_data) < chunk_comp:
            print(f"WARNING: chunk {chunk_count} truncated (expected {chunk_comp}, got {len(chunk_data)} bytes)",
                  file=sys.stderr)

        samples, predictor, step_index = decode_ima_adpcm_block(chunk_data, predictor, step_index)
        all_samples.extend(samples)
        chunk_count += 1
        pos += CHUNK_HEADER_SIZE + chunk_comp

    # Convert to 16-bit LE PCM bytes
    pcm = struct.pack(f"<{len(all_samples)}h", *all_samples)
    return hdr, pcm, chunk_count


# ---------------------------------------------------------------------------
# MIX reader (inline, to avoid import path issues)
# ---------------------------------------------------------------------------
def read_mix_entry(path, idx):
    """Read a single entry from a Westwood MIX file."""
    with open(path, "rb") as f:
        raw = f.read()
    count = struct.unpack_from("<H", raw, 0)[0]
    if idx < 0 or idx >= count:
        raise IndexError(f"Entry {idx} out of range (file has {count} entries)")
    data_base = 6 + count * 12
    toc_off = 6 + idx * 12
    _h, off, size = struct.unpack_from("<III", raw, toc_off)
    return raw[data_base + off: data_base + off + size]


def list_mix_entries(path):
    """List entries in a MIX file."""
    with open(path, "rb") as f:
        raw = f.read()
    count = struct.unpack_from("<H", raw, 0)[0]
    entries = []
    for i in range(count):
        toc_off = 6 + i * 12
        h, off, size = struct.unpack_from("<III", raw, toc_off)
        entries.append((h, off, size))
    return entries


# ---------------------------------------------------------------------------
# WAV writer
# ---------------------------------------------------------------------------
def write_wav(filename, pcm_data, sample_rate, channels, sample_width):
    """Write raw PCM data to a WAV file."""
    with wave.open(filename, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(pcm_data)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Decode Westwood AUD audio from LoL2 MIX files")
    parser.add_argument("mixfile", help="MIX filename (resolved relative to LOL2_DAT)")
    parser.add_argument("entry", nargs="?", type=int, default=0, help="Entry index (default: 0)")
    parser.add_argument("-o", "--output", default=None, help="Output WAV file (default: auto-named)")
    parser.add_argument("--raw", action="store_true", help="Treat input as raw AUD file, not MIX")
    parser.add_argument("--info", action="store_true", help="Print header info only, don't decode")
    parser.add_argument("--list", action="store_true", help="List MIX entries and probe AUD headers")

    args = parser.parse_args()

    lol2_dat = os.environ.get("LOL2_DAT", ".")
    mix_path = args.mixfile
    if not os.path.isabs(mix_path):
        mix_path = os.path.join(lol2_dat, mix_path)

    if not os.path.isfile(mix_path):
        print(f"ERROR: file not found: {mix_path}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        entries = list_mix_entries(mix_path)
        print(f"MIX: {mix_path}")
        print(f"Entries: {len(entries)}")
        for i, (h, off, size) in enumerate(entries):
            # Try to parse AUD header for each entry
            entry_data = read_mix_entry(mix_path, i)
            tag = ""
            if len(entry_data) >= AUD_HEADER_SIZE:
                try:
                    hdr = parse_aud_header(entry_data)
                    if hdr["sample_rate"] in (11025, 22050, 44100) and hdr["codec"] == 99:
                        dur = hdr["output_size"] / (hdr["sample_rate"] * (2 if hdr["is_16bit"] else 1) * (2 if hdr["stereo"] else 1))
                        tag = f"  AUD {hdr['sample_rate']}Hz {'stereo' if hdr['stereo'] else 'mono'} {'16bit' if hdr['is_16bit'] else '8bit'} {dur:.1f}s"
                except Exception:
                    pass
            print(f"  [{i:3d}] hash=0x{h:08X}  size={size:8d}{tag}")
        return

    # Read entry data
    if args.raw:
        with open(mix_path, "rb") as f:
            aud_data = f.read()
    else:
        aud_data = read_mix_entry(mix_path, args.entry)

    hdr = parse_aud_header(aud_data)

    channels = 2 if hdr["stereo"] else 1
    sample_width = 2 if hdr["is_16bit"] else 1
    duration = hdr["output_size"] / (hdr["sample_rate"] * sample_width * channels)

    print(f"AUD header:")
    print(f"  Sample rate:  {hdr['sample_rate']} Hz")
    print(f"  Channels:     {'stereo' if hdr['stereo'] else 'mono'}")
    print(f"  Sample width: {'16-bit' if hdr['is_16bit'] else '8-bit'}")
    print(f"  Codec:        {hdr['codec']} ({'IMA-ADPCM' if hdr['codec'] == 99 else 'unknown'})")
    print(f"  Comp size:    {hdr['comp_size']} bytes")
    print(f"  Output size:  {hdr['output_size']} bytes")
    print(f"  Duration:     {duration:.1f}s")
    print(f"  Entry size:   {len(aud_data)} bytes")

    if args.info:
        return

    print(f"\nDecoding...")
    hdr, pcm, chunk_count = decode_aud(aud_data)

    # Determine output filename
    if args.output:
        out_path = args.output
    else:
        base = os.path.splitext(os.path.basename(mix_path))[0]
        out_path = f"{base}_entry{args.entry}.wav"

    write_wav(out_path, pcm, hdr["sample_rate"], channels, sample_width)

    actual_duration = len(pcm) / (hdr["sample_rate"] * sample_width * channels)
    print(f"  Chunks decoded: {chunk_count}")
    print(f"  PCM bytes:      {len(pcm)}")
    print(f"  Actual duration: {actual_duration:.1f}s")
    print(f"  Written: {out_path}")


if __name__ == "__main__":
    main()
