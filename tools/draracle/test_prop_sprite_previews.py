import struct
import unittest
from extract_prop_sprite_previews import decode_rows

class RowSpanTests(unittest.TestCase):
    def payload(self, control=0x4001, pixels=b'\x07\0\x09'):
        rows=struct.pack('<HH',control,len(pixels))+pixels
        return struct.pack('<4H',0x28e,5,1,len(rows))+rows
    def test_span_and_transparent_gaps(self):
        self.assertEqual(decode_rows(self.payload()),(5,1,b'\0\x07\0\x09\0',1))
    def test_flag_mismatch_rejected(self):
        with self.assertRaises(Exception):decode_rows(self.payload(control=1))
    def test_overrun_rejected(self):
        with self.assertRaises(Exception):decode_rows(self.payload(control=0x4004))
    def test_truncated_payload_rejected(self):
        with self.assertRaises(Exception):decode_rows(self.payload()[:-1])

    def test_sequence_flags_require_explicit_selection(self):
        payload = bytearray(self.payload())
        struct.pack_into('<H', payload, 0, 0x2c6)
        with self.assertRaises(ValueError):
            decode_rows(payload)
        self.assertEqual(decode_rows(payload, 0x2c6), (5, 1, b'\0\x07\0\x09\0', 1))
