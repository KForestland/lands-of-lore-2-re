import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from lol2_level_writer import read_command, read_pool, write_command, write_pool
from lol2_text_writer import read_trr, write_trr


class NativeRoundTripTests(unittest.TestCase):
    def test_command_fields_and_tail(self):
        body = bytes((14, 2, 88, 0, 6, 12, 5, 222))
        row = read_command(body)
        self.assertEqual(row["fields"]["timer"], 5)
        row["fields"]["timer"] = 7
        self.assertEqual(write_command(row), body[:6] + b"\x07" + body[7:])

    def test_event_pool_and_unreferenced_bytes(self):
        timer = struct.pack("<BBHBBBBH", 10, 2, 160, 48, 1, 5, 0, 300)
        predicate = b"\x04\x13\x08\x00"
        pool = b"xx" + timer + predicate + b"\0\xff"
        rows, terminals, gaps = read_pool(pool, [2, 12])
        self.assertEqual(len(rows), 2)
        self.assertEqual(gaps, [(0, b"xx")])
        self.assertEqual(rows[12]["fields"]["predicate"], 8)
        rows[2]["fields"]["countdown"] = 200
        expected = pool[:10] + b"\xc8\x00" + pool[12:]
        self.assertEqual(write_pool(len(pool), rows, terminals, gaps), expected)

    def test_text_with_sparse_duplicate_ids_and_control_byte(self):
        rows = [(4, b""), (99, b"test\x07text"), (99, b"other")]
        self.assertEqual(read_trr(write_trr(rows)), rows)
        rows[1] = (99, b"longer string")
        self.assertEqual(read_trr(write_trr(rows)), rows)
        with self.assertRaises(ValueError):
            write_trr([(1, b"\x00")])
