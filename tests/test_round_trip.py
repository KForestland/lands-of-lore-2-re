"""Synthetic witnesses for the format writers."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from lol2_mix_writer import write_mix
from lol2_source_format import parse_mix


class MixRoundTrip(unittest.TestCase):
    def test_directory_order_differs_from_payload_order(self):
        original = (struct.pack("<H7I", 2, 7, 0x80000001, 4, 2, 2, 1, 1)
                    + b"\0A\0\0BC\0")
        entries = [(0x80000001, 4, b"BC"), (2, 1, b"A")]
        rebuilt = write_mix(entries, 7)
        self.assertEqual(rebuilt, original)
        self.assertEqual([row["key"] for row in parse_mix(rebuilt)], [0x80000001, 2])

    def test_reject_bad_ranges(self):
        for entries in ([(1, 9, b"AB")], [(1, 0, b"AB"), (2, 1, b"B")]):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                write_mix(entries, 9)

    def test_changed_member_changes_output(self):
        entries = [(0x80000001, 4, b"BC"), (2, 1, b"A")]
        rebuilt = write_mix(entries, 7)
        changed = write_mix([(0x80000001, 4, b"BD"), (2, 1, b"A")], 7)
        self.assertNotEqual(changed, rebuilt)
        self.assertEqual([i for i in range(len(changed)) if changed[i] != rebuilt[i]], [len(changed) - 2])
        rows = parse_mix(changed)
        self.assertEqual([(row["key"], row["size"]) for row in rows], [(0x80000001, 2), (2, 1)])

class WestwoodRoundTrip(unittest.TestCase):
    def test_modes_and_terminator(self):
        from lol2_decompress_westwood import decompress_westwood
        from lol2_westwood_writer import encode_westwood
        repeated = bytes(range(16)) * 500
        absolute = encode_westwood(repeated)
        relative = encode_westwood(repeated, relative=True)
        self.assertEqual(absolute[17:22], struct.pack("<BHH", 0xFF, len(repeated) - 16, 0))
        self.assertEqual(relative[18:23], struct.pack("<BHH", 0xFF, len(repeated) - 16, 16))
        for original in (b"", b"Z" * 70000, repeated, bytes(range(255))):
            for mode in (False, True):
                encoded = encode_westwood(original, mode)
                self.assertEqual(decompress_westwood(encoded, len(original) + 1), (original, 0, len(encoded)))


class SaveRoundTrip(unittest.TestCase):
    def test_regenerates_directories_and_chunk_headers(self):
        from dataclasses import replace
        from lol2_save_writer import Packed, parse_slot, synthetic_slot, write_slot
        preview = Packed(((1, b"\x12P\x11\0\0"), (1, b"\x12Q\x11\0\0")))
        slot = replace(synthetic_slot(), preview=preview, dimensions=(2, 1))
        data = write_slot(slot)
        self.assertEqual(parse_slot(data), slot)
        self.assertEqual(struct.unpack_from("<I", data, 0xA4)[0], 0x25D)
        self.assertEqual(struct.unpack_from("<2I", data, 0x25D), (1, 5))
        self.assertEqual(struct.unpack_from("<I", data, 0x20E)[0], 0x2FE)

    def test_invalid_packed_extent(self):
        from lol2_save_writer import parse_packed
        with self.assertRaises(ValueError):
            parse_packed(struct.pack("<II", 0x2001, 1) + b"x")
