#!/usr/bin/env python3
"""Read LoL2 executable item labels and the definitions they name.

--data is the game DAT folder, or $LOL2_DAT; LOLG.DAT sits in its parent and
GLOBAL.MIX in the folder. LOLG.DAT data offset 0xC610 holds 74 pairs of
(label pointer, value). At startup 0x95544 passes them to 0x623D4, which hashes
each label with the case-sensitive rotate-and-add routine 0x154880 and stores,
in the pair's value, the index of the 91-byte item definition whose identity
(+0x18) equals that hash (0x62694 returns the identity; store at 0x625EA).
Item handlers read these values as [[0x96904]] + 8*pair + 4.

--check joins all 74 labels and prints the replacement definitions read by
handlers 2, 8, 83 and 91-93 (pairs 17, 15, 22 and 37). Prints indexes only.
"""

from cli_errors import run_cli, game_path
import os
import struct
import sys

import lol2_cli

OBJ5 = 0x1C1024
TABLE, PAIRS = 0xC610, 74
ITEMS_KEY, STRIDE = 0xED7EC08D, 91
# handler -> (field offset in [[0x96904]], expected definition index)
REPLACEMENTS = {2: (0x8C, 58), 8: (0x7C, 56), 83: (0xB4, 67), 91: (0x12C, 98), 92: (0x12C, 98), 93: (0x12C, 98)}


def native_hash(text):
    """0x154880: rotate left 1 and add each little-endian dword; a short tail is zero-padded."""
    data, value = text, 0
    for at in range(0, len(data) - len(data) % 4, 4):
        value = ((value << 1 | value >> 31) & 0xFFFFFFFF) + struct.unpack_from("<I", data, at)[0] & 0xFFFFFFFF
    tail = data[len(data) - len(data) % 4:]
    if tail:
        value = ((value << 1 | value >> 31) & 0xFFFFFFFF) + int.from_bytes(tail.ljust(4, b"\0"), "little") & 0xFFFFFFFF
    return value


def item_entry(dat_dir):
    raw = game_path(dat_dir, "GLOBAL.MIX").read_bytes()
    count = struct.unpack_from("<H", raw)[0]
    base = 6 + 12 * count
    for i in range(count):
        key, offset, size = struct.unpack_from("<III", raw, 6 + 12 * i)
        if key == ITEMS_KEY:
            start = base + offset
            if start + size > len(raw):
                raise ValueError("item entry overruns GLOBAL.MIX")
            return start, raw[start:start + size]
    raise ValueError("item table entry not found in GLOBAL.MIX")


def item_layout(dat_dir):
    base, entry = item_entry(dat_dir)
    table, rows = struct.unpack_from("<I", entry, 4)[0], struct.unpack_from("<I", entry, 0x34)[0]
    if table + STRIDE * rows > len(entry):
        raise ValueError("item definitions overrun their MIX entry")
    return base + table, [entry[table + STRIDE * r:table + STRIDE * (r + 1)] for r in range(rows)]


def display_names(dat_dir):
    """Join each 30-byte name row to the corresponding definition identity."""
    _, entry = item_entry(dat_dir)
    table, end = struct.unpack_from("<II", entry, 4)
    count, = struct.unpack_from("<I", entry, 0x34)
    sizes = (16, 12)
    at = table + STRIDE * count
    for size in sizes:
        if at + 4 > len(entry):
            return {}
        n, = struct.unpack_from("<I", entry, at)
        at += 4 + size * n
    if at + 30 * count != end or end > len(entry):
        return {}
    names = {}
    for i in range(count):
        identity, = struct.unpack_from("<I", entry, table + STRIDE * i + 0x18)
        field = entry[at + 30 * i:at + 30 * i + 24].partition(b"\0")[0]
        label = field.decode("cp437").removeprefix(f"{i + 1}-").strip()
        if label and label.isprintable():
            names[identity] = label
    return names


def item_definitions(dat_dir):
    return item_layout(dat_dir)[1]


def join(dat_dir):
    image = open(str(game_path(os.path.dirname(os.path.abspath(dat_dir)), "LOLG.DAT")), "rb").read()
    rows = item_definitions(dat_dir)
    by_identity = {struct.unpack_from("<I", row, 0x18)[0]: i for i, row in enumerate(rows)}
    values = []
    for pair in range(PAIRS):
        pointer = struct.unpack_from("<I", image, OBJ5 + TABLE + 8 * pair)[0]
        label = image[OBJ5 + pointer:OBJ5 + pointer + 64].split(b"\0")[0]
        values.append(by_identity.get(native_hash(label)))
    return rows, values


def check(dat_dir):
    rows, values = join(dat_dir)
    if len(rows) != 170 or None in values:
        raise ValueError("%d definitions, %d of %d labels joined" % (len(rows), PAIRS - values.count(None), PAIRS))
    found = {}
    for handler, (field, expected) in REPLACEMENTS.items():
        got = values[(field - 4) // 8]
        if got != expected:
            raise ValueError("handler %d reads definition %s, expected %d" % (handler, got, expected))
        found[handler] = got
    users = {handler: [i for i, row in enumerate(rows) if row[0x42] == handler] for handler in REPLACEMENTS}
    pairs = ", ".join("%d: %s -> %d" % (h, "/".join(map(str, users[h])), found[h]) for h in REPLACEMENTS)
    return "CHECK item_labels: %d of %d executable item labels join a definition identity; handler: definitions -> replacement %s" % (
        PAIRS, PAIRS, pairs)


def main(argv):
    ap = lol2_cli.tool_args(__doc__)
    args = ap.parse_args(argv)
    try:
        if args.out:
            ap.error("prints only")
        print(check(args.data))
        return 0
    except (OSError, ValueError) as exc:
        print("CHECK item_labels: FAIL %s" % exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli(main, sys.argv[1:]))
