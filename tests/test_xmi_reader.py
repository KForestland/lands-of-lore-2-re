import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from lol2_xmi_reader import inspect_song


def chunk(tag, payload):
    return struct.pack(">4sI", tag, len(payload)) + payload + b"\0" * (len(payload) % 2)


def song(stream, timbres=b"\x01\x00\x05\x07", count=1):
    directory = chunk(b"FORM", b"XDIR" + chunk(b"INFO", struct.pack("<H", count)))
    frame = chunk(b"FORM", b"XMID" + chunk(b"TIMB", timbres) + chunk(b"EVNT", stream))
    return directory + chunk(b"CAT ", b"XMID" + frame)


class XmiReaderTests(unittest.TestCase):
    def test_note_delay_duration_and_end(self):
        raw = b"\x07\x03\x92\x31\x40\x81\x05\xff\x2f\x00\x00"
        _, pairs, seq, rows = inspect_song(song(raw))[0]
        self.assertEqual(pairs, ((5, 7),))
        self.assertEqual(rows, ((seq + 2, 10, 0x92, None, b"\x31\x40", 133),
                                (seq + 7, 10, 0xFF, 0x2F, b"", None)))

    def test_bad_count_or_truncated_event(self):
        with self.assertRaisesRegex(ValueError, "sequence directory"):
            inspect_song(song(b"\xff\x2f\x00", count=2))
        with self.assertRaisesRegex(ValueError, "TIMB count"):
            inspect_song(song(b"\xff\x2f\x00", timbres=b"\x02\0"))
        with self.assertRaisesRegex(ValueError, "channel operands"):
            inspect_song(song(b"\x90\0"))
