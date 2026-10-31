import struct
import unittest
from verify_special_pixel_table_binding import fixups


class FixupTests(unittest.TestCase):
    def fixture(self, records):
        data = bytearray(512)
        struct.pack_into('<I', data, 0x68, 0x80)
        struct.pack_into('<I', data, 0x6c, 0xa0)
        struct.pack_into('<II', data, 0x80, 0, len(records))
        data[0xa0:0xa0 + len(records)] = records
        return data

    def test_internal_offsets_both_widths(self):
        data = self.fixture(bytes.fromhex('07001d04040040 07101204056c460100'))
        records = fixups(data, 0, 0)
        self.assertEqual(records[0x41d]['target_object'], 4)
        self.assertEqual(records[0x41d]['target_offset'], 0x4000)
        self.assertEqual(records[0x412]['target_offset'], 0x1466c)

    def test_reject_unknown_record_and_truncation(self):
        for code in ['02001d04040040', '07001d040400', '07101d04040040']:
            with self.subTest(code=code), self.assertRaises(ValueError):
                fixups(self.fixture(bytes.fromhex(code)), 0, 0)

    def test_reject_duplicate_source(self):
        with self.assertRaises(ValueError):
            fixups(self.fixture(bytes.fromhex('07001d04040040' * 2)), 0, 0)
