"""LoL2 TRR tables in the original installation."""
from struct import iter_unpack

import modkit
from modkit_core import game_folder
from lol2_text_writer import read_trr, trr_sources, write_trr

from lol2_westwood_hash import ww_hash_v2


def font_sources(base):
    names = {ww_hash_v2(name): name for name in ("STD6P.FNT", "STD8P.FNT", "OPTION_L.FNT", "OPTION_H.FNT")}
    archives = {"LOCAL.MIX", "SETUP.MIX"}
    folders = [base, *(p for p in base.iterdir() if p.is_dir() and p.name.upper() == "DAT")]
    for folder in folders:
        for path in sorted(folder.iterdir()):
            if path.name.upper() not in archives or not path.is_file():
                continue
            archives.remove(path.name.upper())
            yield from fonts_in_archive(path, names)


def fonts_in_archive(path, names):
    with path.open("rb") as source:
        count = int.from_bytes(source.read(2), "little")
        source.read(4)
        rows = tuple(iter_unpack("<III", source.read(count * 12)))
        for key, at, size in rows:
            if not 20 <= size <= 65535:
                continue
            source.seek(at + 6 + count * 12)
            header = source.read(20)
            if (int.from_bytes(header[:2], "little") != size or header[2:4] != b"\x00\x05"
                    or header[4:8] != b"\x0e\x00\x14\x00"):
                continue
            yield f"{path.name}/{names.get(key, f'{key:08X}')}", header + source.read(size - 20)


def decode(raw):
    # The 0x80–0xAF glyph runs display CP437 accents and punctuation.
    # Outside the mapped range preserve the stored byte as an explicit escape.
    return "".join(bytes((i,)).decode("cp437") if i < 0xB0 else chr(0xDC00 + i) for i in raw)


def encode(text):
    out = bytearray()
    for index, char in enumerate(text):
        if 0xDC80 <= ord(char) <= 0xDCFF:
            out.append(ord(char) - 0xDC00)
            continue
        raw = char.encode("cp437")
        if raw[0] >= 0xB0:
            raise UnicodeEncodeError("game font", text, index, index + 1, "unmapped glyph value")
        out.extend(raw)
    return bytes(out)


def root(path):
    return game_folder(modkit, path)


def sources(base):
    dat = next((p for p in base.iterdir() if p.is_dir() and p.name.upper() == "DAT"), None)
    if dat is None:
        raise ValueError(f"Give --data {modkit.FOLDER}.")
    for path, index, key, at, blob in trr_sources(dat, indexed=True):
        label = path.name if key is None else f"{key:08X}.trr"
        yield path.relative_to(base).as_posix(), index, label, at, blob


def read(label, blob):
    limit = "locked" if label.lower() in ("qevent.trr", "devent.trr") else "no limit"
    return [(f"{key:08X}", decode(value), limit) for key, value in read_trr(blob)]


def write(label, blob, changes):
    if changes and label.lower() in ("qevent.trr", "devent.trr"):
        raise ValueError("Event tags join by their stored text. Keep them unchanged.")
    rows = read_trr(blob)
    for i, text in changes.items():
        try:
            value = encode(text)
        except UnicodeError:
            raise ValueError(f"Row {i + 1} has a character outside the mapped glyphs. Choose a character listed by translate fonts.") from None
        rows[i] = rows[i][0], value
    if sum(len(value) + 1 for _, value in rows) + 8 * len(rows) + 4 > 0xFFFFFFFF:
        raise ValueError("This TRR exceeds the 32-bit offset range. Shorten the new text.")
    return write_trr(rows)
