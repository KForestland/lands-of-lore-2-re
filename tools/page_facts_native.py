"""Raw witnesses used by the LoL2 page-facts registry."""
from functools import lru_cache
from struct import iter_unpack, unpack_from

from cli_errors import game_path

DATA_ENV = "LOL2_DAT"
GAME_MARKER = "LOLG.DAT"


def game_file(data, name):
    if name.startswith("DAT/"):
        return game_path(data, name[4:])
    beside = game_path(data.resolve().parent, name)
    return beside if beside.is_file() else game_path(data, name)


@lru_cache(maxsize=8)
def read_file(path):
    return path.read_bytes()


def mix_member(data, key):
    rows = mix_directory(data)
    match = [(offset, size) for name, offset, size in rows if name == key]
    if len(match) != 1:
        raise ValueError(f"expected one in-range MIX entry with key {key:#x}")
    offset, size = match[0]
    return memoryview(data)[offset:offset + size], offset


def mix_directory(data):
    count, body_size = unpack_from("<HI", data)
    body = 6 + 12 * count
    if body + body_size != len(data):
        raise ValueError("MIX directory and data lengths disagree")
    rows = [(name, body + offset, size) for name, offset, size in iter_unpack("<III", data[6:body])]
    if any(offset + size > len(data) for _, offset, size in rows):
        raise ValueError("MIX entry exceeds its payload")
    return rows


def wsa_first_delta(image):
    # The WSA loader's argument block starts after the stream read and flag arm.
    # Decode its xor, mov, push, mov, push, mov, push, then the near call.
    start = 0x15BED2
    cursor = start + 0x37000
    for opcode, length in ((0x31, 2), (0x66, 4), (0x50, 1), (0x8B, 3),
                           (0x52, 1), (0x8B, 3), (0x53, 1)):
        if image[cursor] != opcode:
            raise ValueError(f"WSA argument block changed at VA {cursor - 0x37000:#x}")
        cursor += length
    opcode, delta = unpack_from("<Bi", image, cursor)
    address = cursor - 0x37000
    if opcode != 0xE8 or address + 5 + delta != 0x158D58:
        raise ValueError("WSA argument block no longer ends in a call to the delta decoder")
    return address, f"LOLG.DAT VA {start:#x}–{address + 4:#x}"


def music_stem(image, slot):
    base = 0x1C1024
    row = 0x1CE10C + 4 * slot
    offset = base + unpack_from("<I", image, row)[0]
    end = image.index(b"\0", offset)
    return image[offset:end].decode("ascii"), f"LOLG.DAT+{row:#x} -> +{offset:#x}"


def handler_count(raw, selector):
    start = unpack_from("<I", raw, 4)[0]
    count = unpack_from("<I", raw, 0x34)[0]
    end = start + 91 * count
    if end + 4 > len(raw) or unpack_from("<I", raw, end)[0] != count:
        raise ValueError("item definition and selector table extents disagree")
    return sum(raw[start + 91 * i + 0x42] == selector for i in range(count))


def corner_step(raw):
    start = unpack_from("<I", raw, 0x0C)[0]
    count = unpack_from("<I", raw, 0x58)[0]
    if start + 44 * count > len(raw):
        raise ValueError("region table exceeds the geometry entry")
    rows = [unpack_from("<8H", raw, start + 44 * i + 4) for i in range(count)]
    hits = {1: 0, -1: 0}
    for index, row in enumerate(rows):
        for side, neighbor in enumerate(row[:4]):
            if neighbor >= count or index not in rows[neighbor][:4]:
                continue
            other = rows[neighbor]
            back = other[:4].index(index)
            for step in hits:
                if {row[4 + side], row[4 + (side + step) % 4]} == {
                        other[4 + back], other[4 + (back + step) % 4]}:
                    hits[step] += 1
    best, alternate = sorted(hits, key=hits.get, reverse=True)
    if hits[best] == 0 or hits[best] < 2 * hits[alternate]:
        raise ValueError(f"shared-edge counts do not establish a corner direction: {hits}")
    return best


def wall_run_edge(raw):
    start = unpack_from("<I", raw, 0x0C)[0]
    count = unpack_from("<I", raw, 0x58)[0]
    total = unpack_from("<I", raw, 0x54)[0]
    runs = [(unpack_from("<H", raw, at + 0x1A)[0], raw[at + 0x1E])
            for at in range(start, start + 44 * count, 44)]

    def partitions(last):
        intervals = sorted((first - (length - 1 if last else 0), length)
                           for first, length in runs if length)
        end = 0
        for begin, length in intervals:
            if begin != end:
                return False
            end += length
        return end == total

    results = [name for last, name in ((False, "first"), (True, "last")) if partitions(last)]
    if len(results) != 1:
        raise ValueError("wall runs do not establish a unique endpoint")
    return results[0]


def edition_status(data):
    path = game_file(data, GAME_MARKER)
    if not path.is_file():
        return f"original {GAME_MARKER} unavailable"
    image = read_file(path)
    if len(image) != 1977007 or image[0x1C4714:0x1C471C] != b"DOS 1.30":
        return f"{GAME_MARKER} is not the measured DOS 1.30 build"
    return None


def read_witness(data, spec):
    kind, name, *args = spec
    path = game_file(data, name)
    if kind == "file_size":
        return path.stat().st_size, name
    raw = read_file(path)
    if kind == "archive_size":
        entry = args[0]
        _, offset, size = mix_directory(raw)[entry]
        return size, f"{name} entry {entry} at +{offset:#x}"
    if kind == "archive_form_type":
        forms = [raw[at + 8:at + 12] for _, at, size in mix_directory(raw)
                 if size >= 12 and raw[at:at + 4] == b"FORM"]
        if not forms or set(forms) - {b"XDIR", b"XMID"}:
            raise ValueError(f"{name} has no uniform XMIDI form entries")
        return "XMIDI scores", f"{name}, the FORM member type fields"
    if kind == "absolute_operand":
        va = args[0]
        offset = va + 0x37000
        if raw[offset] in {0x68, *range(0xB8, 0xC0)}:
            operand = offset + 1
        elif raw[offset:offset + 2] == b"\xc7\x00":  # mov dword [eax], imm32
            operand = offset + 2
        else:
            raise ValueError(f"no supported absolute operand at {name} VA {va:#x}")
        return unpack_from("<I", raw, operand)[0], f"{name} instruction at VA {va:#x}"
    if kind == "slot_level_count":
        at = 0xE7B3D + 0x37000
        if raw[at:at + 2] != b"\x83\xfe" or raw[at + 3] != 0x7E:
            raise ValueError("save writer level bound moved")
        return raw[at + 2], f"{name} VA {at - 0x37000:#x}, save writer's inclusive level bound"
    if kind == "wsa_first_delta":
        return wsa_first_delta(raw)
    if kind == "music_stem":
        return music_stem(raw, *args)
    if kind == "le_pages":
        le = raw.index(b"LE\0\0", 0x3B000, 0x3C000)
        return unpack_from("<I", raw, le + 0x14)[0], f"{name}+{le + 0x14:#x}, LE module page count"
    member, base = mix_member(raw, args[0])
    if kind == "handler_count":
        return handler_count(member, args[1]), f"{name} entry {args[0]:#010x} at +{base:#x}, handler byte +0x42"
    if kind == "corner_step":
        return corner_step(member), f"{name} entry {args[0]:#010x} at +{base:#x}, reciprocal region edges"
    if kind == "wall_run_edge":
        return wall_run_edge(member), f"{name} entry {args[0]:#010x} at +{base:#x}, partition of the wall table"
    raise ValueError(f"unknown byte witness {kind!r}")
