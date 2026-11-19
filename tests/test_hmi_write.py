import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from lol2_hmi_writer import MAGIC, read_song, write_song, write_track


class HmiWriteTests(unittest.TestCase):
    def test_round_trip_with_running_status_and_variable_length_fields(self):
        song = bytearray(0xEC)
        song[:len(MAGIC)] = MAGIC
        struct.pack_into("<II", song, 0xE4, 1, len(song))
        track = bytearray(0x80)
        track[:13] = b"HMI-MIDITRACK"
        struct.pack_into("<I", track, 0x57, len(track))
        track[0x7B] = 3
        stored = b"\x80\x00\x95\x20\x30\x07\x01\x21\x22\x80\x05\x00\xff\x2f\x00"
        source = bytes(song) + struct.pack("<I", len(song) + 4) + bytes(track) + stored
        parsed = read_song(source)
        _, rows, _ = parsed[2][0]
        self.assertEqual(rows[0]["delay"], (0, 2))
        self.assertEqual(rows[1]["status"], 0x95)
        self.assertFalse(rows[1]["explicit"])
        self.assertEqual(rows[1]["duration"], (5, 2))
        self.assertEqual(write_song(*parsed), source)
        rows[1]["duration"] = (4, 2)
        self.assertEqual(write_song(*parsed), source[:-5] + b"\x04" + source[-4:])

    def test_bad_running_status(self):
        bad = dict(delay=(1, 1), explicit=False, status=0x95, data=(3, 4), duration=(2, 1))
        with self.assertRaisesRegex(ValueError, "running status"):
            write_track(b"", [bad], b"")
