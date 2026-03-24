#!/usr/bin/env python3
"""Extract code/data segments from LOLG.DAT (DOS4GW LE executable).
LE header at 0x3BCB4, 5 objects, 4096-byte pages."""

import argparse
import struct
import os
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Extract code/data segments from LOLG.DAT (DOS4GW LE executable)."
    )
    parser.add_argument(
        "exe_path", nargs="?",
        default=os.environ.get(
            "LOL2_EXE",
            "/media/bob/Arikv/REFERENCE/game_files/lol2/LOLG.DAT"
        ),
        help="Path to LOLG.DAT (default: $LOL2_EXE or built-in path)"
    )
    parser.add_argument(
        "output_dir", nargs="?",
        default=os.environ.get("OUTPUT_DIR", "."),
        help="Directory for extracted segment files (default: $OUTPUT_DIR or '.')"
    )
    args = parser.parse_args()

    exe_path = args.exe_path
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    with open(exe_path, "rb") as f:
        exe = f.read()

    LE_OFF = 0x3BCB4
    print(f"LE header at 0x{LE_OFF:X}")
    print(f"Signature: {exe[LE_OFF:LE_OFF+2]}")

    # Parse LE header fields
    def le16(off): return struct.unpack_from("<H", exe, LE_OFF + off)[0]
    def le32(off): return struct.unpack_from("<I", exe, LE_OFF + off)[0]

    cpu_type = le16(0x04)
    os_type = le16(0x06)
    module_version = le32(0x08)
    module_flags = le32(0x0C)
    num_pages = le32(0x14)
    eip_object = le32(0x18)  # Object # for EIP (1-based)
    eip_offset = le32(0x1C)  # EIP offset within object
    esp_object = le32(0x20)
    esp_offset = le32(0x24)
    page_size = le32(0x28)
    last_page_size = le32(0x2C)
    fixup_size = le32(0x30)
    obj_table_off = le32(0x40)
    obj_count = le32(0x44)
    obj_page_table_off = le32(0x48)
    fixup_page_off = le32(0x68)
    fixup_record_off = le32(0x6C)
    data_pages_off = le32(0x80)  # from START OF FILE

    print(f"CPU: {cpu_type}, OS: {os_type}")
    print(f"Flags: 0x{module_flags:08X}")
    print(f"Pages: {num_pages}, page_size: {page_size}, last_page: {last_page_size}")
    print(f"EIP: object {eip_object}, offset 0x{eip_offset:X}")
    print(f"ESP: object {esp_object}, offset 0x{esp_offset:X}")
    print(f"Objects: {obj_count}")
    print(f"Object table: LE+0x{obj_table_off:X} = file 0x{LE_OFF + obj_table_off:X}")
    print(f"Page table: LE+0x{obj_page_table_off:X} = file 0x{LE_OFF + obj_page_table_off:X}")
    print(f"Data pages: file 0x{data_pages_off:X}")
    print(f"Fixup page table: LE+0x{fixup_page_off:X}")
    print(f"Fixup records: LE+0x{fixup_record_off:X}")

    # Parse object table
    print(f"\n{'='*70}")
    print("SEGMENTS")
    print(f"{'='*70}")

    abs_obj_table = LE_OFF + obj_table_off
    abs_page_table = LE_OFF + obj_page_table_off

    segments = []
    for i in range(obj_count):
        off = abs_obj_table + i * 24
        vsize = struct.unpack_from("<I", exe, off)[0]
        base = struct.unpack_from("<I", exe, off + 4)[0]
        flags = struct.unpack_from("<I", exe, off + 8)[0]
        page_map_idx = struct.unpack_from("<I", exe, off + 12)[0]  # 1-based into page table
        n_pages = struct.unpack_from("<I", exe, off + 16)[0]
        reserved = struct.unpack_from("<I", exe, off + 20)[0]

        flag_names = []
        if flags & 0x0001: flag_names.append("READ")
        if flags & 0x0002: flag_names.append("WRITE")
        if flags & 0x0004: flag_names.append("EXEC")
        if flags & 0x0008: flag_names.append("RESOURCE")
        if flags & 0x0010: flag_names.append("DISCARD")
        if flags & 0x0020: flag_names.append("SHARED")
        if flags & 0x0040: flag_names.append("PRELOAD")
        if flags & 0x2000: flag_names.append("BIG/32BIT")

        # Collect pages for this object
        seg_data = bytearray()
        for p in range(n_pages):
            # Page table entry: each entry is 4 bytes in LE format
            pt_off = abs_page_table + (page_map_idx - 1 + p) * 4
            pt_entry = struct.unpack_from("<I", exe, pt_off)[0]

            # LE page table entry format:
            # page_data_index (u16) + flags (u16)
            page_data_idx = struct.unpack_from("<H", exe, pt_off)[0]  # 1-based
            page_flags = struct.unpack_from("<H", exe, pt_off + 2)[0]

            if page_data_idx > 0:
                page_file_off = data_pages_off + (page_data_idx - 1) * page_size
                if p == n_pages - 1 and last_page_size > 0:
                    this_page_sz = last_page_size
                else:
                    this_page_sz = page_size
                page_bytes = exe[page_file_off:page_file_off + this_page_sz]
                seg_data.extend(page_bytes)
            else:
                # Zero page
                seg_data.extend(b'\x00' * page_size)

        # Trim to virtual size
        if len(seg_data) > vsize:
            seg_data = seg_data[:vsize]

        seg_type = "CODE" if (flags & 0x4) else "DATA"
        print(f"\n  Segment {i}: {seg_type}")
        print(f"    Base: 0x{base:08X}, VSize: {vsize} (0x{vsize:X})")
        print(f"    Flags: 0x{flags:04X} [{' '.join(flag_names)}]")
        print(f"    Pages: {page_map_idx} to {page_map_idx + n_pages - 1} ({n_pages} pages)")
        print(f"    Extracted: {len(seg_data)} bytes")

        # Save
        seg_path = os.path.join(output_dir, f"lolg_seg{i}_{seg_type.lower()}.bin")
        with open(seg_path, "wb") as f:
            f.write(seg_data)
        print(f"    Saved: {seg_path}")

        segments.append({
            "index": i,
            "base": base,
            "vsize": vsize,
            "flags": flags,
            "type": seg_type,
            "data": bytes(seg_data),
        })

    # Now find string references in code segments
    print(f"\n{'='*70}")
    print("STRING CROSS-REFERENCES")
    print(f"{'='*70}")

    # First, find all target strings in data segments
    targets = [
        b"Sector not found",
        b"No start sector!!",
        b"Too many sectors!",
        b"Bad Make_room_Grid",
        b"Unable to load level",
        b"Level Version:",
        b"No Sector!!!",
        b"!Force End Sector!",
        b"Bad Sector[%d]",
        b"path_collides:Bad",
        b"sphere1\\l1_dc",
        b".MIX\x00",
        b"I.MIX\x00",
        b"drmrmapr",
    ]

    for seg in segments:
        if seg["type"] != "DATA":
            continue
        print(f"\n  Searching in segment {seg['index']} (DATA, base=0x{seg['base']:08X})...")

        for target in targets:
            pos = seg["data"].find(target)
            if pos >= 0:
                # Virtual address = base + offset
                va = seg["base"] + pos
                print(f"    [{target[:30]}] at seg+0x{pos:X} = VA 0x{va:08X}")

                # Now search for this VA in ALL code segments
                va_bytes = struct.pack("<I", va)
                for code_seg in segments:
                    if not (code_seg["flags"] & 0x4):  # only code segments
                        continue
                    code_data = code_seg["data"]
                    ref_pos = 0
                    refs = []
                    while True:
                        ref = code_data.find(va_bytes, ref_pos)
                        if ref == -1:
                            break
                        refs.append(ref)
                        ref_pos = ref + 1

                    if refs:
                        print(f"      Referenced from code seg{code_seg['index']} at: "
                              f"{['0x%X (VA 0x%X)' % (r, code_seg['base']+r) for r in refs[:5]]}")

                        # Show disassembly context (raw bytes around ref)
                        for ref in refs[:3]:
                            ctx_start = max(0, ref - 16)
                            ctx_end = min(len(code_data), ref + 20)
                            ctx_hex = code_data[ctx_start:ctx_end].hex()
                            print(f"        Context at 0x{ref:X}: ...{ctx_hex}...")

    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
