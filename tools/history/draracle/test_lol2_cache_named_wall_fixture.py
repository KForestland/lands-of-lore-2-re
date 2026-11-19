"""Boundary checks for the named-cache extractor; synthetic data only."""
import csv
import struct
import tempfile
import unittest
from pathlib import Path

from lol2_cache_named_wall_fixture import load_named, parse_records, replay_reads, section_for


def index(state=2, pointer=4, length=4):
    data = bytearray(8 + 256)
    struct.pack_into("<II", data, 0, 8, 1)
    name = b"sphere3\\l20_bb\\l20_bb.te_\0"
    data[16:16 + len(name)] = name
    struct.pack_into("<II", data, 8 + 0xD8, state, length)
    struct.pack_into("<I", data, 8 + 0xE8, pointer)
    return data


class CacheTests(unittest.TestCase):
    def test_named_lookup_and_direct_pointer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "CDCACHE.LST").write_bytes(index())
            (root / "CDCACHE.MIX").write_bytes(b"skipDATA")
            rec, blob, _, _ = load_named(root, "sphere3/l20_bb/l20_bb.tex")
            self.assertEqual(blob, b"DATA")
            self.assertEqual(rec["pointer"], 4)

    def test_unsupported_state_never_guesses_pointer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "CDCACHE.LST").write_bytes(index(state=0xFFFFFFFF))
            with self.assertRaisesRegex(ValueError, "unsupported cache record state"):
                load_named(root, "sphere3/l20_bb/l20_bb.tex")

    def test_truncated_and_bad_index(self):
        for data in [b"", bytes(index()[:-1]), struct.pack("<II", 10000, 1)]:
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                parse_records(data)

    def test_blob_bounds(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "CDCACHE.LST").write_bytes(index(pointer=6))
            (root / "CDCACHE.MIX").write_bytes(b"skipDATA")
            with self.assertRaisesRegex(ValueError, "outside file"):
                load_named(root, "sphere3/l20_bb/l20_bb.tex")

    def test_section_must_contain_whole_page(self):
        blob = struct.pack("<IIII", 2, 0, 16, 24) + bytes(16)
        self.assertEqual(section_for(blob, 16, 8)["index"], 0)
        with self.assertRaisesRegex(ValueError, "one bounded section"):
            section_for(blob, 20, 8)

    def test_read_replay_rejects_mismatch_and_bounds(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reads.csv"
            for offset, preview, error in [(0, "FF", "mismatches"), (4, "01", "outside page")]:
                with path.open("w", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(["page_offset", "size", "trace_preview"])
                    writer.writerow([offset, 1, preview])
                with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, error):
                    replay_reads(b"\x01\x02", path)


if __name__ == "__main__":
    unittest.main()
