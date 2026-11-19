#!/usr/bin/env python3
"""Re-read movie scene ids, one sound-bank row, music stem hashes and room-archive code entries.

Reads the player's own files. Writes nothing. --help does not open a file.
--data is the game DAT folder, or $LOL2_DAT. LOLG.DAT, DMUSIC.MIX, LOCAL.MIX
and LOCALLNG.MIX are read from that folder's parent. --check prints one line.

    python3 tools/lol2_media_check.py --data /path/to/DAT --check

Expected output is in tools/README.md.
"""
from cli_errors import run_cli
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lol2_cli import tool_args  # noqa: E402
from lol2_decompress_westwood import decompress_westwood  # noqa: E402
from lol2_hmi_midi import credits_paths  # noqa: E402
from lol2_source_format import SIZES  # noqa: E402
from lol2_westwood_hash import ww_hash_v1, ww_hash_v2  # noqa: E402

OBJ5 = 0x1C1024
SHA_PREFIX = "b27a3534"


def mix_dir(path):
    """Return (file_size, body, [{index, key, offset, size}]). Offsets are absolute."""
    with open(path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        file_size = handle.tell()
        handle.seek(0)
        count, total = struct.unpack("<HI", handle.read(6))
        raw = handle.read(12 * count)
    body = 6 + 12 * count
    if body + total != file_size:
        raise ValueError("MIX size mismatch: %s" % os.path.basename(path))
    entries = []
    for i in range(count):
        key, off, size = struct.unpack_from("<III", raw, 12 * i)
        if off + size > total:
            raise ValueError("entry exceeds MIX data")
        entries.append(dict(index=i, key=key, offset=body + off, size=size))
    return file_size, body, entries


def read_at(path, offset, size):
    with open(path, "rb") as handle:
        handle.seek(offset)
        data = handle.read(size)
    if len(data) != size:
        raise ValueError("short read")
    return data


def u32(buf, offset):
    return struct.unpack_from("<I", buf, offset)[0]


def cstr(image, offset):
    end = image.find(b"\x00", offset)
    return image[offset:end].decode("ascii")


def vqhd(path, offset):
    head = read_at(path, offset, 36)
    if head[:4] != b"FORM" or head[8:12] != b"WVQA" or head[12:16] != b"VQHD":
        raise ValueError("not FORM/WVQA/VQHD")
    size = struct.unpack_from(">I", head, 16)[0]
    if size != 42:
        raise ValueError("VQHD size %s" % size)
    payload = read_at(path, offset + 20, 14)
    version, _second, frames, width, height = struct.unpack_from("<HHHHH", payload)
    block_w, block_h, rate, parts = struct.unpack_from("<BBBB", payload, 10)
    return version, frames, width, height, block_w, block_h, rate, parts


def aud_head(path, offset):
    raw = read_at(path, offset, 20)
    rate, comp, out, flags, codec = struct.unpack_from("<HIIBB", raw)
    magic = struct.unpack_from("<I", raw, 16)[0]
    return rate, comp, out, flags, codec, magic


def geometry_stream(path):
    """Return (archive_offset_of_stream, stream_bytes) for command stream 1."""
    _size, _body, entries = mix_dir(path)
    found = None
    for entry in entries:
        head = read_at(path, entry["offset"], 8)
        if struct.unpack_from("<II", head) == (18, 5300) and entry["size"] >= 0x244:
            if found is not None:
                raise ValueError("two geometry entries")
            found = entry
    if found is None:
        raise ValueError("no geometry entry")
    header = read_at(path, found["offset"], 0x244)
    stream_at = u32(header, 0x44)
    stream_size = u32(header, 0x8C)
    stream = read_at(path, found["offset"] + stream_at, stream_size)
    return found["offset"] + stream_at, stream


def walk(stream):
    commands = []
    i = 0
    while i < len(stream):
        op = stream[i]
        if op not in SIZES:
            raise ValueError("opcode %s at %s" % (op, i))
        n = SIZES[op]
        if i + n > len(stream):
            raise ValueError("command overruns the stream")
        commands.append((i, stream[i:i + n]))
        i += n
    return commands


BANNER = b"This is a linear executable dll\n"
PROLOGUE = b"\x53\x56\x57\x55"


def parent_file(dat_dir, name):
    """LOLG.DAT and the loose MIX files sit next to the DAT folder, not inside it."""
    path = os.path.join(os.path.dirname(os.path.abspath(dat_dir)), name)
    if not os.path.isfile(path):
        raise FileNotFoundError("%s is not in the parent of the DAT folder" % name)
    return path


def scene_names(dat_dir):
    image_path = parent_file(dat_dir, "LOLG.DAT")
    image = open(image_path, "rb").read()
    import hashlib
    digest = hashlib.sha256(image).hexdigest()
    if not digest.startswith(SHA_PREFIX) or len(image) != 0x1E2AAF:
        raise ValueError("LOLG.DAT is not the 1.30 image this note describes")

    limit = u32(image, OBJ5 + 0xE740)
    if limit != 85:
        raise ValueError("scene limit %s" % limit)
    names = [cstr(image, OBJ5 + u32(image, OBJ5 + 0xE568 + 4 * i)) for i in range(limit + 1)]
    if names[0] != "lolg" or names[13] != "citadel" or names[85] != "-----":
        raise ValueError("scene names moved")

    return image, names


def room_module_fixups(path, member, entry_offset):
    raw = read_at(path, member["offset"], member["size"])
    _, _, sites = room_module_layout(raw, entry_offset)
    return len(sites)


def room_module_layout(raw, entry_offset=None):
    if not raw.startswith(BANNER) or len(raw) < len(BANNER) + 16:
        raise ValueError("room module header")
    version, body_length, offset, count = struct.unpack_from("<4I", raw, len(BANNER))
    body_start = len(BANNER) + 16
    body_end = body_start + body_length
    if (version != 0x101 or (entry_offset is not None and offset != entry_offset) or offset + 4 > body_length
            or body_end + 4 * count != len(raw)
            or raw[body_start + offset:body_start + offset + 4] != PROLOGUE):
        raise ValueError("room module extent")
    sites = [site for (site,) in struct.iter_unpack("<I", raw[body_end:])]
    for site in sites:
        if site + 4 > body_length or u32(raw, body_start + site) >= body_length:
            raise ValueError("room module relocation")
    return body_length, offset, sites


def check_conditional_resource_names(image):
    """Byte 0x223D6 selects the leved names or the shipped global names."""
    code = 0x37000
    tex = bytes.fromhex(
        "8a15d623020083c40884d27417b9430c0000b8580c0000be2e0c0000"
        "894de88945e0eb15ba7e0c0000bb900c0000be6c0c00008955e8895de06a0156e818a40700"
    )
    sounds = bytes.fromhex(
        "8a1dd623020083c40484db74186868110000e8ac87070083c40485c07419"
        "687d110000eb05689211000068683c0200e863340400"
    )
    if image[0x9E2D7 + code:0x9E2D7 + code + len(tex)] != tex:
        raise ValueError("global resource name selector")
    if image[0xA0171 + code:0xA0171 + code + len(sounds)] != sounds:
        raise ValueError("sounds resource name selector")
    names = {
        0xC2E: b"c:\\leved\\-global.tex\x00",
        0xC43: b"c:\\leved\\-global.odf\x00",
        0xC58: b"c:\\leved\\-spell.odf\x00",
        0xC6C: b"global\\global.tex\x00",
        0xC7E: b"global\\global.odf\x00",
        0xC90: b"global\\spell.odf\x00",
        0x1168: b"c:\\leved\\_sounds.efx\x00",
        0x117D: b"c:\\leved\\_sounds.efx\x00",
        0x1192: b"global\\sounds.efx\x00",
    }
    for cell, text in names.items():
        if image[OBJ5 + cell:OBJ5 + cell + len(text)] != text:
            raise ValueError("resource name at %X" % cell)
    # Direct absolute byte stores. A store through a register stays open.
    flag = b"\xd6\x23\x02\x00"
    direct = [b"\xA2" + flag, b"\xC6\x05" + flag]
    direct += [bytes((0x88, (reg << 3) | 5)) + flag for reg in range(8)]
    code_obj = image[0x90024:0x1C1024]
    if any(pattern in code_obj for pattern in direct):
        raise ValueError("direct store of resource name flag")


def check_global_texture_books(image, local, entries):
    name = cstr(image, OBJ5 + 0xC6C)
    key = ww_hash_v1(name)
    entry = next((row for row in entries if row["key"] == key), None)
    if key != 0xEF88C09F or entry is None or entry["index"] != 50:
        raise ValueError("global texture archive entry")
    member = read_at(local, entry["offset"], entry["size"])
    base = u32(member, 0x298)
    table = base + u32(member, base + 0x2C)
    count = u32(member, base + 0x2A4)
    if (base, entry["offset"] + table, count) != (0x18AE18, 0x339FA5, 15):
        raise ValueError("global texture book directory")
    decoded_bytes = 0
    for i in range(count):
        relative, capacity, packed = struct.unpack_from("<III", member, table + 12 * i)
        start = base + relative
        if not 0 < packed <= capacity or not start + packed <= table:
            raise ValueError("global texture book extent")
        data, errors, used = decompress_westwood(member[start:start + packed], capacity)
        if errors or used != packed or not 0 < len(data) <= capacity or len(data) % 16:
            raise ValueError("global texture book profile")
        decoded_bytes += len(data)
    if decoded_bytes != 466864:
        raise ValueError("global texture book count")


def check_vqa_buffer_callbacks(image):
    """Check the DOS movie allocator and memory-lock callback arms."""
    code_bias = 0x37000
    code_base = 0x59024
    for word, slot in ((0xCA6F0, 0xCA713), (0xCF489, 0xCF4A4),
                       (0x1127E9, 0x1127E3), (0x113905, 0x113928)):
        if u32(image, word + code_bias) + code_base != 0x113550:
            raise ValueError(f"movie memory callback at 0x{slot:X}")
    for callback, table, arm in ((0x113550, 0x113538, 0x113588),
                                 (0x16D7D8, 0x16D7C0, 0x16D814)):
        if u32(image, table + code_bias + 3 * 4) + code_base != arm:
            raise ValueError(f"movie callback 0x{callback:X} operation 4")
    for address, sequence in (
        (0x15DE76, "c74204b4471100"),  # default memory callback
        (0x16CD89, "8b966207000052506a0456ff5504"),
        (0x11356B, "6a008d422050e86ac60300"),  # allocate with flags zero
        (0x14FD66, "f6450c02740c576a0053e82ffbffff"),
        (0x113588, "803dd523020000740d8d42205053e865c50300"),
        (0x16D814, "525689f3e8e322feff"),
        (0x14FB22, "c745d800060000"),  # DPMI function AX=0x0600
        (0x14FB60, "6a31e85a1d0100"),
    ):
        expected = bytes.fromhex(sequence)
        start = address + code_bias
        if image[start:start + len(expected)] != expected:
            raise ValueError(f"movie buffer callback instruction at 0x{address:X}")


def panel_names(image):
    names = set()
    for cell in range(0xC488, 0xC4F0, 4):
        pointer = u32(image, OBJ5 + cell)
        if pointer:
            name = cstr(image, OBJ5 + pointer)
            if name:
                names.add(name)
    return sorted(names)


def wsa_frames(member):
    count, _, _, width, height, capacity, flags = struct.unpack_from("<7H", member)
    offsets = struct.unpack_from(f"<{count + 2}I", member, 14)
    if flags or min(width, height, capacity) == 0 or offsets[0] != 14 + 4 * len(offsets) or offsets[-1] != len(member):
        raise ValueError("WSA header or extent")
    spans = []
    for start, end in zip(offsets, offsets[1:]):
        if end <= start:
            raise ValueError("WSA delta extent")
        delta, errors, used = decompress_westwood(member[start:end], capacity)
        if errors or used != end - start or not delta:
            raise ValueError(f"WSA delta at {start:#x}")
        spans.append((start, end - start, len(delta)))
    return count, width, height, spans


def check_wsa_frames(image, local, entries):
    """Join the native panel animation names and consume each compressed delta."""
    names = panel_names(image)
    index = {row["key"]: row for row in entries}
    frames = decoded_bytes = 0
    for name in names:
        row = index.get(ww_hash_v1(name))
        if row is None or not name.endswith(".WSA"):
            raise ValueError(f"missing panel animation {name}")
        member = read_at(local, row["offset"], row["size"])
        _, _, _, spans = wsa_frames(member)
        frames += len(spans)
        decoded_bytes += sum(length for _, _, length in spans)
    if (len(names), frames, decoded_bytes) != (21, 640, 670607):
        raise ValueError("WSA animation corpus changed")
    for address, target in ((0x72E39, 0x15BB9C), (0x79397, 0x15BB9C),
                            (0x7AE1E, 0x15BB9C), (0x7B27D, 0x15BB9C),
                            (0x15C08A, 0x15C3F4), (0x15BEE1, 0x158D58), (0x15C50D, 0x158D58)):
        opcode, displacement = struct.unpack_from("<Bi", image, address + 0x37000)
        if opcode != 0xE8 or address + 5 + displacement != target:
            raise ValueError(f"WSA call at 0x{address:X}")


def check(dat_dir):
    image, names = scene_names(dat_dir)
    check_vqa_buffer_callbacks(image)
    formats = image[OBJ5 + 0x2C84:OBJ5 + 0x2CC0]
    if formats[:3] != b"ss-" or b"%s.vqa" not in formats or b"outtakes\\%s" not in formats:
        raise ValueError("movie format strings moved")
    if image[OBJ5 + 0x2CA9:OBJ5 + 0x2CAE] != b"%s\\%s":
        raise ValueError("directory format moved")

    level = os.path.join(dat_dir, "L12_CM.MIX")
    stream_file, stream = geometry_stream(level)
    commands = walk(stream)
    want21 = bytes.fromhex("150378000d00")
    want20 = bytes.fromhex("140304001904fffdfafa")
    want210 = bytes.fromhex("d2000000000a")
    found = {}
    for rel, raw in commands:
        if raw in (want21, want20, want210):
            found[raw] = stream_file + rel
    if set(found) != {want21, want20, want210}:
        raise ValueError("worked-example commands missing")
    if (found[want21], found[want20], found[want210]) != (9823886, 9821090, 9823696):
        raise ValueError("worked-example offsets moved")

    movies = os.path.join(dat_dir, "L12_CMI.MIX")
    key = ww_hash_v1("sphere2\\l12_cm\\citadel.vqa")
    if key != ww_hash_v2("sphere2\\l12_cm\\citadel.vqa"):
        raise ValueError("citadel hash variants disagree")
    _size, _body, entries = mix_dir(movies)
    hit = [e for e in entries if e["key"] == key]
    if len(hit) != 1:
        raise ValueError("citadel key")
    fields = vqhd(movies, hit[0]["offset"])
    if hit[0]["index"] != 21 or hit[0]["size"] != 14680498 or fields[:4] != (2, 591, 640, 400):
        raise ValueError("citadel entry changed")

    movies_mix = os.path.join(dat_dir, "MOVIES.MIX")
    _size, _body, mentries = mix_dir(movies_mix)
    lolg = ww_hash_v1("outtakes\\lolg.vqa")
    if lolg != ww_hash_v2("outtakes\\lolg.vqa"):
        raise ValueError("lolg hash variants disagree")
    hit = [e for e in mentries if e["key"] == lolg]
    if len(hit) != 1:
        raise ValueError("lolg key")
    fields = vqhd(movies_mix, hit[0]["offset"])
    form = 0
    for entry in mentries:
        if read_at(movies_mix, entry["offset"], 4) == b"FORM":
            form += 1
    if hit[0]["index"] != 2 or hit[0]["size"] != 82206194 or fields[:4] != (2, 3576, 640, 400):
        raise ValueError("lolg entry changed")
    if len(mentries) != 29 or form != 28:
        raise ValueError("MOVIES.MIX form count")

    bank_mix = parent_file(dat_dir, "LOCALLNG.MIX")
    _size, _body, bentries = mix_dir(bank_mix)
    bank = [e for e in bentries if e["key"] == 1570429112]
    if len(bank) != 1:
        raise ValueError("sound bank key")
    bank = bank[0]
    count, table = struct.unpack("<II", read_at(bank_mix, bank["offset"] + 0x258, 8))
    if count != 1179:
        raise ValueError("bank rows %s" % count)
    row_off = bank["offset"] + table + 1049 * 60
    _clip, size, _unk, flag = struct.unpack("<IIII", read_at(bank_mix, row_off, 16))
    name = read_at(bank_mix, row_off + 16, 32).split(b"\x00", 1)[0].decode("ascii")
    clip = struct.unpack_from("<I", read_at(bank_mix, row_off, 4))[0]
    rate, _comp, _out, flags, codec, _magic = aud_head(bank_mix, bank["offset"] + clip)
    if name != "0190108e.aud" or rate != 22050 or codec != 99 or flags != 2 or flag != 0:
        raise ValueError("row 1049 changed")
    if size < 12:
        raise ValueError("row 1049 is not a clip")

    stems = []
    for i in range(35):
        ptr = u32(image, 0x1CE10C + 4 * i)
        stems.append(cstr(image, OBJ5 + ptr) if ptr else "")
    if stems[10] != "CLAWWAN1" or stems[29] != "SSARPIT1" or stems[3] != "badfile":
        raise ValueError("stem table moved")
    if image[OBJ5 + 0x1244:OBJ5 + 0x1251] != b"MUSIC\\%s.AUD\x00":
        raise ValueError("AUD format moved")
    if image[OBJ5 + 0x1251:OBJ5 + 0x125E] != b"MUSIC\\%s.HMI\x00":
        raise ValueError("HMI format moved")

    dmusic = parent_file(dat_dir, "DMUSIC.MIX")
    _size, _body, dentries = mix_dir(dmusic)
    by_key = {e["key"]: e for e in dentries}
    aud_hits = 0
    for stem in stems:
        if not stem or stem == "badfile":
            continue
        name = "MUSIC\\%s.AUD" % stem
        h1, h2 = ww_hash_v1(name), ww_hash_v2(name)
        if h1 != h2 or h1 not in by_key:
            raise ValueError("AUD hash miss %s" % stem)
        aud_hits += 1
    if aud_hits != 32:
        raise ValueError("aud hits %s" % aud_hits)
    if ww_hash_v1("MUSIC\\badfile.AUD") in by_key:
        raise ValueError("badfile hashed into DMUSIC")
    local = parent_file(dat_dir, "LOCAL.MIX")
    _size, _body, lentries = mix_dir(local)
    check_global_texture_books(image, local, lentries)
    check_conditional_resource_names(image)
    check_wsa_frames(image, local, lentries)
    local_keys = {e["key"] for e in lentries}
    hmi_hits = 0
    for stem in stems:
        if not stem or stem == "badfile":
            continue
        h1 = ww_hash_v1("MUSIC\\%s.HMI" % stem)
        if h1 != ww_hash_v2("MUSIC\\%s.HMI" % stem) or h1 not in local_keys:
            raise ValueError("HMI hash miss %s" % stem)
        hmi_hits += 1
    if hmi_hits != 32:
        raise ValueError("hmi hits %s" % hmi_hits)
    credits_aud, credits_hmi = credits_paths(image)
    credits_aud_key = ww_hash_v1(credits_aud)
    credits_hmi_key = ww_hash_v1(credits_hmi)
    if (credits_aud_key != ww_hash_v2(credits_aud) or credits_hmi_key != ww_hash_v2(credits_hmi)
            or credits_aud_key != 0x22F7A4EB or credits_hmi_key != 0x1305A4F0
            or by_key.get(credits_aud_key, {}).get("index") != 16
            or credits_hmi_key not in local_keys):
        raise ValueError("credits music entries changed")
    rates = {}
    odd = 0
    for entry in dentries:
        rate, comp, _out, flags, codec, magic = aud_head(dmusic, entry["offset"])
        rates[rate] = rates.get(rate, 0) + 1
        if codec != 99 or magic != 0xDEAF or flags != 2 or comp + 12 != entry["size"]:
            odd += 1
    if odd or rates.get(22050) != 32 or rates.get(44100) != 1:
        raise ValueError("AUD headers %s odd %s" % (rates, odd))
    pit = by_key[ww_hash_v1("MUSIC\\SSARPIT1.AUD")]
    if pit["index"] != 10:
        raise ValueError("SSARPIT1 index")
    rate, _comp, _out, flags, codec, _magic = aud_head(dmusic, pit["offset"])
    if rate != 44100 or codec != 99 or flags != 2:
        raise ValueError("SSARPIT1 header")

    def container(name, count, banner_index, size_word, form_indexes):
        path = os.path.join(dat_dir, name)
        _size, _body, entries = mix_dir(path)
        if len(entries) != count:
            raise ValueError("%s count" % name)
        raw = read_at(path, entries[banner_index]["offset"], 0x68)
        if raw[:32] != BANNER:
            raise ValueError("%s banner" % name)
        words = struct.unpack_from("<III", raw, 32)
        if words != (0x101, size_word, 0x34):
            raise ValueError("%s header %s" % (name, words))
        if raw[0x64:0x68] != PROLOGUE:
            raise ValueError("%s prologue" % name)
        echo = read_at(path, entries[1]["offset"], entries[1]["size"])
        if echo != b"ECHO is OFF\r\n":
            raise ValueError("%s echo" % name)
        for index in form_indexes:
            head = read_at(path, entries[index]["offset"], 12)
            if head[:4] != b"FORM" or head[8:12] != b"WVQA":
                raise ValueError("%s form %s" % (name, index))

    container("TEXT.MIX", 3, 0, 0x698, (2,))
    container("TCEL.MIX", 4, 3, 0x838, (0, 2))

    prefixes = []
    for i in range(46):
        ptr = u32(image, OBJ5 + 0xEA6C + 4 * i)
        prefixes.append(cstr(image, OBJ5 + ptr))
    if prefixes[0] != "pool_" or prefixes[16] != "tcel_" or prefixes[44] != "text_" or prefixes[45] != "altar_":
        raise ValueError("room-name table moved")
    room_fixups = 0
    for prefix in prefixes:
        cut = prefix.find("_")
        if cut <= 0:
            raise ValueError("room name %s" % prefix)
        path = os.path.join(dat_dir, prefix[:cut].upper() + ".MIX")
        _size, _body, entries = mix_dir(path)
        hits = 0
        for entry in entries:
            if entry["size"] < 0x68:
                continue
            raw = read_at(path, entry["offset"], 0x68)
            if raw[:32] != BANNER:
                continue
            words = struct.unpack_from("<III", raw, 32)
            if words[0] != 0x101 or words[2] != 0x34 or raw[0x64:0x68] != PROLOGUE:
                raise ValueError("code entry shape %s" % prefix)
            room_fixups += room_module_fixups(path, entry, 0x34)
            hits += 1
        if hits != 1:
            raise ValueError("%s code entries %s" % (prefix, hits))

    arena = os.path.join(dat_dir, "ARENA.MIX")
    _size, _body, arena_entries = mix_dir(arena)
    if len(arena_entries) != 2 or arena_entries[1]["key"] != 0x0CBF521D:
        raise ValueError("Arena room module directory")
    arena_fixups = room_module_fixups(arena, arena_entries[1], 0x2C)
    if arena_fixups != 72 or room_fixups + arena_fixups != 8469:
        raise ValueError("room module relocation census")

    return ("CHECK media: scene limit 85; L12 opcode 21/20/210 at 9823886/9821090/9823696; "
            "citadel L12_CMI entry 21; lolg MOVIES entry 2; bank 1179 row 1049 0190108e.aud; "
            "32 table stems and CREDITS in both formats; "
            "47 room modules contain 8469 relocations; 15 global texture books; 640 WSA deltas")


def main(argv):
    parser = tool_args(__doc__)
    args = parser.parse_args(argv)
    if not args.check:
        parser.print_help()
        return 2
    try:
        print(check(args.data))
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        print("CHECK media: FAIL %s" % error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main, sys.argv[1:]))
