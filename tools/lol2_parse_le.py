#!/usr/bin/env python3
"""
Parse DOS4GW LE (Linear Executable) from LOLG.DAT and extract segments.

LOLG.DAT structure: MZ stub + BW (DOS4GW extender) + LE executable
The LE header is located by brute-force scanning for the 'LE' signature
with valid byte/word order fields (both 0) since the standard e_lfanew
mechanism is not used in bound DOS4GW executables.
"""

import argparse
import struct
import os
import sys

# LE Object flags
OBJ_READABLE   = 0x0001
OBJ_WRITABLE   = 0x0002
OBJ_EXECUTABLE = 0x0004
OBJ_RESOURCE   = 0x0008
OBJ_DISCARDABLE= 0x0010
OBJ_SHARED     = 0x0020
OBJ_PRELOAD    = 0x0040
OBJ_INVALID    = 0x0080
OBJ_ZEROED     = 0x0100  # has zero-fill pages
OBJ_RESIDENT   = 0x0200
OBJ_CONTIGUOUS = 0x0300  # resident + contiguous
OBJ_LOCKABLE   = 0x0400
OBJ_16BIT      = 0x2000
OBJ_BIG        = 0x2000  # "Big/Default" bit (32-bit for code, 4GB for data)
OBJ_CONFORMING = 0x4000
OBJ_IOPL       = 0x8000


def find_le_header(data):
    """Scan for a valid LE header (byte_order=0, word_order=0, cpu=2/3)."""
    pos = 0
    while pos < len(data) - 16:
        idx = data.find(b'LE', pos)
        if idx == -1:
            return None
        # Check byte_order and word_order are both 0 (little-endian)
        if data[idx + 2] == 0 and data[idx + 3] == 0:
            cpu = struct.unpack_from('<H', data, idx + 8)[0]
            if cpu in (2, 3):  # 386 or 486
                return idx
        pos = idx + 1
    return None


def flags_str(flags):
    """Human-readable object flags."""
    parts = []
    if flags & OBJ_READABLE:
        parts.append("READ")
    if flags & OBJ_WRITABLE:
        parts.append("WRITE")
    if flags & OBJ_EXECUTABLE:
        parts.append("EXEC")
    if flags & OBJ_RESOURCE:
        parts.append("RESOURCE")
    if flags & OBJ_DISCARDABLE:
        parts.append("DISCARD")
    if flags & OBJ_SHARED:
        parts.append("SHARED")
    if flags & OBJ_PRELOAD:
        parts.append("PRELOAD")
    if flags & OBJ_BIG:
        parts.append("BIG/32BIT")
    return "|".join(parts) if parts else "NONE"


def segment_type(flags):
    """Determine if segment is CODE or DATA."""
    if flags & OBJ_EXECUTABLE:
        return "CODE"
    elif flags & OBJ_WRITABLE:
        return "DATA"
    elif flags & OBJ_READABLE:
        return "RODATA"
    else:
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(
        description="Parse DOS4GW LE (Linear Executable) header and extract segments."
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

    input_file = args.exe_path
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "rb") as f:
        data = f.read()

    file_size = len(data)
    print(f"File: {input_file}")
    print(f"Size: {file_size} bytes (0x{file_size:X})")

    # --- MZ Header ---
    if data[:2] != b'MZ':
        print("ERROR: Not an MZ executable")
        sys.exit(1)

    mz_cblp = struct.unpack_from('<H', data, 2)[0]
    mz_cp = struct.unpack_from('<H', data, 4)[0]
    mz_cparhdr = struct.unpack_from('<H', data, 8)[0]
    mz_size = (mz_cp - 1) * 512 + mz_cblp if mz_cblp else mz_cp * 512
    print(f"\n=== MZ Header ===")
    print(f"MZ stub size: {mz_size} bytes (0x{mz_size:X})")
    print(f"Header paragraphs: {mz_cparhdr}")

    # --- Find BW header (DOS4GW extender) ---
    bw_off = mz_size
    if data[bw_off:bw_off + 2] == b'BW':
        bw_cblp = struct.unpack_from('<H', data, bw_off + 2)[0]
        bw_cp = struct.unpack_from('<H', data, bw_off + 4)[0]
        bw_size = (bw_cp - 1) * 512 + bw_cblp if bw_cblp else bw_cp * 512
        print(f"\n=== BW Header (DOS4GW extender) at 0x{bw_off:X} ===")
        print(f"BW image size: {bw_size} bytes (0x{bw_size:X})")
    else:
        print(f"\nNo BW header found at MZ end (0x{bw_off:X})")

    # --- Find LE header by scanning ---
    le_off = find_le_header(data)
    if le_off is None:
        print("ERROR: Could not find LE header")
        sys.exit(1)

    print(f"\n=== LE Header at 0x{le_off:X} ===")

    # Parse LE header fields
    signature     = data[le_off:le_off + 2].decode('ascii')
    byte_order    = data[le_off + 2]
    word_order    = data[le_off + 3]
    format_level  = struct.unpack_from('<I', data, le_off + 0x04)[0]
    cpu_type      = struct.unpack_from('<H', data, le_off + 0x08)[0]
    os_type       = struct.unpack_from('<H', data, le_off + 0x0A)[0]
    module_ver    = struct.unpack_from('<I', data, le_off + 0x0C)[0]
    module_flags  = struct.unpack_from('<I', data, le_off + 0x10)[0]
    num_pages     = struct.unpack_from('<I', data, le_off + 0x14)[0]
    eip_object    = struct.unpack_from('<I', data, le_off + 0x18)[0]
    eip_offset    = struct.unpack_from('<I', data, le_off + 0x1C)[0]
    esp_object    = struct.unpack_from('<I', data, le_off + 0x20)[0]
    esp_offset    = struct.unpack_from('<I', data, le_off + 0x24)[0]
    page_size     = struct.unpack_from('<I', data, le_off + 0x28)[0]
    last_page_sz  = struct.unpack_from('<I', data, le_off + 0x2C)[0]
    fixup_size    = struct.unpack_from('<I', data, le_off + 0x30)[0]
    fixup_checksum= struct.unpack_from('<I', data, le_off + 0x34)[0]
    loader_size   = struct.unpack_from('<I', data, le_off + 0x38)[0]
    loader_chksum = struct.unpack_from('<I', data, le_off + 0x3C)[0]
    obj_table_off = struct.unpack_from('<I', data, le_off + 0x40)[0]
    obj_count     = struct.unpack_from('<I', data, le_off + 0x44)[0]
    obj_page_off  = struct.unpack_from('<I', data, le_off + 0x48)[0]
    obj_iter_off  = struct.unpack_from('<I', data, le_off + 0x4C)[0]
    rsrc_table_off= struct.unpack_from('<I', data, le_off + 0x50)[0]
    rsrc_count    = struct.unpack_from('<I', data, le_off + 0x54)[0]
    resname_off   = struct.unpack_from('<I', data, le_off + 0x58)[0]
    entry_table_off=struct.unpack_from('<I', data, le_off + 0x5C)[0]
    module_dir_off= struct.unpack_from('<I', data, le_off + 0x60)[0]
    module_dir_cnt= struct.unpack_from('<I', data, le_off + 0x64)[0]
    fixup_page_off= struct.unpack_from('<I', data, le_off + 0x68)[0]
    fixup_rec_off = struct.unpack_from('<I', data, le_off + 0x6C)[0]
    import_mod_off= struct.unpack_from('<I', data, le_off + 0x70)[0]
    import_mod_cnt= struct.unpack_from('<I', data, le_off + 0x74)[0]
    import_proc_off=struct.unpack_from('<I', data, le_off + 0x78)[0]
    per_page_chk  = struct.unpack_from('<I', data, le_off + 0x7C)[0]
    data_pages_off= struct.unpack_from('<I', data, le_off + 0x80)[0]
    preload_pages = struct.unpack_from('<I', data, le_off + 0x84)[0]
    nonres_name_off=struct.unpack_from('<I', data, le_off + 0x88)[0]
    nonres_name_sz= struct.unpack_from('<I', data, le_off + 0x8C)[0]
    nonres_chksum = struct.unpack_from('<I', data, le_off + 0x90)[0]
    auto_ds_obj   = struct.unpack_from('<I', data, le_off + 0x94)[0]
    debug_info_off= struct.unpack_from('<I', data, le_off + 0x98)[0]
    debug_info_len= struct.unpack_from('<I', data, le_off + 0x9C)[0]
    inst_preload  = struct.unpack_from('<I', data, le_off + 0xA0)[0]
    inst_demand   = struct.unpack_from('<I', data, le_off + 0xA4)[0]
    heap_size     = struct.unpack_from('<I', data, le_off + 0xA8)[0]

    cpu_names = {1: "286", 2: "386", 3: "486", 4: "Pentium"}
    os_names = {0: "Unknown", 1: "OS/2", 2: "Windows", 3: "DOS", 4: "Windows 386"}

    print(f"Signature:        {signature}")
    print(f"Byte/Word order:  {byte_order}/{word_order}")
    print(f"Format level:     {format_level}")
    print(f"CPU type:         {cpu_type} ({cpu_names.get(cpu_type, '?')})")
    print(f"Target OS:        {os_type} ({os_names.get(os_type, '?')})")
    print(f"Module version:   {module_ver}")
    print(f"Module flags:     0x{module_flags:08X}")
    print(f"Number of pages:  {num_pages}")
    print(f"Page size:        {page_size}")
    print(f"Last page size:   {last_page_sz}")
    print(f"EIP object:       {eip_object}, offset: 0x{eip_offset:X}")
    print(f"ESP object:       {esp_object}, offset: 0x{esp_offset:X}")
    print(f"Object table:     LE+0x{obj_table_off:X} (abs 0x{le_off + obj_table_off:X})")
    print(f"Object count:     {obj_count}")
    print(f"Object page tbl:  LE+0x{obj_page_off:X} (abs 0x{le_off + obj_page_off:X})")
    print(f"Data pages:       file+0x{data_pages_off:X}")
    print(f"Fixup page tbl:   LE+0x{fixup_page_off:X}")
    print(f"Fixup record tbl: LE+0x{fixup_rec_off:X}")
    print(f"Fixup section sz: {fixup_size}")
    print(f"Auto DS object:   {auto_ds_obj}")
    print(f"Heap size:        {heap_size}")

    # --- Parse Object Table ---
    print(f"\n=== Object Table ({obj_count} entries) ===")
    obj_table_abs = le_off + obj_table_off
    objects = []

    for i in range(obj_count):
        entry_off = obj_table_abs + i * 24
        virt_size  = struct.unpack_from('<I', data, entry_off + 0)[0]
        reloc_base = struct.unpack_from('<I', data, entry_off + 4)[0]
        obj_flags  = struct.unpack_from('<I', data, entry_off + 8)[0]
        page_idx   = struct.unpack_from('<I', data, entry_off + 12)[0]  # 1-based
        num_pte    = struct.unpack_from('<I', data, entry_off + 16)[0]
        reserved   = struct.unpack_from('<I', data, entry_off + 20)[0]

        stype = segment_type(obj_flags)
        print(f"\n  Object #{i}:")
        print(f"    Virtual size:    {virt_size} bytes (0x{virt_size:X})")
        print(f"    Reloc base:      0x{reloc_base:08X}")
        print(f"    Flags:           0x{obj_flags:08X} ({flags_str(obj_flags)})")
        print(f"    Type:            {stype}")
        print(f"    Page table idx:  {page_idx} (1-based)")
        print(f"    Num page entries:{num_pte}")
        print(f"    Reserved:        0x{reserved:08X}")

        objects.append({
            'index': i,
            'virt_size': virt_size,
            'reloc_base': reloc_base,
            'flags': obj_flags,
            'page_idx': page_idx,
            'num_pages': num_pte,
            'type': stype,
        })

    # --- Parse Object Page Table and extract segments ---
    # LE page table entry format (4 bytes):
    #   Bytes 0-1: Page Data Offset (high word of 24-bit value)
    #   Byte 2:    Page Data Offset (low byte of 24-bit value)
    #   Byte 3:    Type/flags (0=Legal, 1=Iterated, 2=Invalid, 3=Zeroed)
    # The 24-bit offset = (high16 << 8) | low8, giving a 1-based page number
    # Actual file offset = data_pages_off + (page_number - 1) * page_size

    page_table_abs = le_off + obj_page_off
    print(f"\n=== Page Table at 0x{page_table_abs:X} ===")
    print(f"First 10 page table entries (raw bytes):")
    for i in range(min(10, num_pages)):
        entry_bytes = data[page_table_abs + i*4 : page_table_abs + i*4 + 4]
        vals = struct.unpack_from('<HBB', entry_bytes, 0)
        u32 = struct.unpack_from('<I', entry_bytes, 0)[0]
        print(f"  Page {i+1}: raw={entry_bytes.hex()} "
              f"as_u32=0x{u32:08X} "
              f"high16=0x{vals[0]:04X} low8=0x{vals[1]:02X} flags=0x{vals[2]:02X}")

    print(f"\n=== Extracting Segments ===")
    segment_data = {}

    for obj in objects:
        seg_bytes = bytearray()
        start_page = obj['page_idx']  # 1-based

        for p in range(obj['num_pages']):
            global_page_idx = start_page - 1 + p  # 0-based index into page table
            pte_off = page_table_abs + global_page_idx * 4

            pte_high = struct.unpack_from('<H', data, pte_off)[0]
            pte_low = data[pte_off + 2]
            pte_flags = data[pte_off + 3]

            page_num = (pte_high << 8) | pte_low  # 24-bit page number, 1-based

            if pte_flags == 0:  # Legal/valid page
                if page_num == 0:
                    # Zero page
                    seg_bytes.extend(b'\x00' * page_size)
                else:
                    page_file_off = data_pages_off + (page_num - 1) * page_size
                    # Last page might be smaller
                    is_last_global = (global_page_idx == num_pages - 1)
                    if is_last_global and last_page_sz > 0:
                        actual_size = last_page_sz
                    else:
                        actual_size = page_size

                    page_data_chunk = data[page_file_off:page_file_off + actual_size]
                    seg_bytes.extend(page_data_chunk)
                    # Pad to full page size if needed (for non-last pages)
                    if len(page_data_chunk) < page_size and not is_last_global:
                        seg_bytes.extend(b'\x00' * (page_size - len(page_data_chunk)))
            elif pte_flags == 2:  # Invalid page
                seg_bytes.extend(b'\x00' * page_size)
            elif pte_flags == 3:  # Zeroed page
                seg_bytes.extend(b'\x00' * page_size)
            elif pte_flags == 1:  # Iterated
                page_file_off = data_pages_off + (page_num - 1) * page_size
                # For iterated pages, just read raw for now
                seg_bytes.extend(data[page_file_off:page_file_off + page_size])
            else:
                print(f"    WARNING: Unknown page type {pte_flags} for page {global_page_idx}")
                seg_bytes.extend(b'\x00' * page_size)

        # Trim to virtual size
        if len(seg_bytes) > obj['virt_size']:
            seg_bytes = seg_bytes[:obj['virt_size']]

        segment_data[obj['index']] = bytes(seg_bytes)

        out_path = os.path.join(output_dir, f"lolg_seg{obj['index']}.bin")
        with open(out_path, 'wb') as f:
            f.write(seg_bytes)

        print(f"  Seg {obj['index']} ({obj['type']}): {len(seg_bytes)} bytes -> {out_path}")

    # --- Summary ---
    print(f"\n{'='*72}")
    print(f"SEGMENT SUMMARY")
    print(f"{'='*72}")
    print(f"{'#':<4} {'Type':<8} {'Base Address':<14} {'Virtual Size':<14} {'Extracted':<14} {'Flags'}")
    print(f"{'-'*4} {'-'*8} {'-'*14} {'-'*14} {'-'*14} {'-'*30}")
    for obj in objects:
        extracted_sz = len(segment_data[obj['index']])
        print(f"{obj['index']:<4} {obj['type']:<8} 0x{obj['reloc_base']:08X}   "
              f"0x{obj['virt_size']:08X}   0x{extracted_sz:08X}   {flags_str(obj['flags'])}")

    # --- String search ---
    print(f"\n{'='*72}")
    print(f"STRING SEARCH")
    print(f"{'='*72}")

    target_strings = [
        b"Sector not found",
        b"No start sector!!",
        b"Too many sectors!",
        b"Unable to load level",
        b"Level Version:",
    ]

    # Find strings in all segments (typically DATA)
    string_locations = {}  # string -> list of (seg_idx, offset, virtual_addr)

    for obj in objects:
        seg = segment_data[obj['index']]
        for s in target_strings:
            off = 0
            while True:
                idx = seg.find(s, off)
                if idx == -1:
                    break
                vaddr = obj['reloc_base'] + idx
                if s not in string_locations:
                    string_locations[s] = []
                string_locations[s].append((obj['index'], idx, vaddr, obj['type']))
                off = idx + 1

    for s in target_strings:
        s_str = s.decode('ascii', errors='replace')
        if s in string_locations:
            for seg_idx, offset, vaddr, stype in string_locations[s]:
                print(f"\n  \"{s_str}\"")
                print(f"    Found in Seg {seg_idx} ({stype}) at offset 0x{offset:X}, VA 0x{vaddr:08X}")

                # Show context (16 bytes before and after)
                seg = segment_data[seg_idx]
                ctx_start = max(0, offset - 16)
                ctx_end = min(len(seg), offset + len(s) + 16)
                ctx = seg[ctx_start:ctx_end]
                ascii_repr = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
                print(f"    Context: {ctx.hex()}")
                print(f"    ASCII:   {ascii_repr}")

                # Search for references to this VA in CODE segments
                va_bytes_le = struct.pack('<I', vaddr)
                print(f"    Searching for references to VA 0x{vaddr:08X} ({va_bytes_le.hex()}) in CODE segments...")

                for code_obj in objects:
                    if not (code_obj['flags'] & OBJ_EXECUTABLE):
                        continue
                    code_seg = segment_data[code_obj['index']]
                    ref_off = 0
                    ref_count = 0
                    while True:
                        ref_idx = code_seg.find(va_bytes_le, ref_off)
                        if ref_idx == -1:
                            break
                        ref_va = code_obj['reloc_base'] + ref_idx
                        print(f"      REF in Seg {code_obj['index']} at offset 0x{ref_idx:X} (VA 0x{ref_va:08X})")
                        # Show disassembly context (bytes around the reference)
                        ctx_s = max(0, ref_idx - 8)
                        ctx_e = min(len(code_seg), ref_idx + 12)
                        ref_ctx = code_seg[ctx_s:ctx_e]
                        print(f"        Bytes: {ref_ctx.hex()}")
                        ref_off = ref_idx + 1
                        ref_count += 1
                        if ref_count >= 10:
                            print(f"        ... (truncated, too many refs)")
                            break
                    if ref_count == 0:
                        print(f"      No direct references found in Seg {code_obj['index']}")
        else:
            print(f"\n  \"{s_str}\" - NOT FOUND in any segment")

    # --- Additional: look for relocations that might point to these strings ---
    print(f"\n{'='*72}")
    print(f"FIXUP/RELOCATION INFO")
    print(f"{'='*72}")
    fixup_page_abs = le_off + fixup_page_off
    fixup_rec_abs = le_off + fixup_rec_off
    print(f"Fixup page table at:   0x{fixup_page_abs:X}")
    print(f"Fixup record table at: 0x{fixup_rec_abs:X}")
    print(f"Fixup section size:    {fixup_size} bytes")

    # The fixup page table has (num_pages + 1) uint32 entries
    # Each entry is an offset into the fixup record table
    # The fixups for page N are between fixup_page[N-1] and fixup_page[N]
    if fixup_size > 0 and num_pages > 0:
        fp_entries = []
        for i in range(num_pages + 1):
            fp_off = fixup_page_abs + i * 4
            if fp_off + 4 <= len(data):
                val = struct.unpack_from('<I', data, fp_off)[0]
                fp_entries.append(val)

        total_fixups = fp_entries[-1] if fp_entries else 0
        print(f"Total fixup records size: {total_fixups} bytes")

        # Count how many pages have fixups
        pages_with_fixups = sum(1 for i in range(len(fp_entries)-1) if fp_entries[i+1] > fp_entries[i])
        print(f"Pages with fixups: {pages_with_fixups} / {num_pages}")

    print(f"\nDone. Segments saved to {output_dir}/lolg_seg*.bin")


if __name__ == '__main__':
    main()
