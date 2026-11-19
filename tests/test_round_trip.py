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
