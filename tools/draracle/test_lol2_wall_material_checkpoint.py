import struct
import unittest

from lol2_wall_material_checkpoint import find_material, material_record


def fixture():
    # Four section pointers, one 56-byte descriptor, five tiny raw mip records.
    blob = bytearray(160)
    struct.pack_into("<6I", blob, 0, 4, 0, 0, 0, 24, 80)
    offsets = [0, 9, 18, 27, 36]
    values = [99, 1, 1, 0xA9, 1, 0x305, 0] + offsets + [9] * 5
    struct.pack_into("<6H11I", blob, 24, *values)
    for offset in offsets:
        struct.pack_into("<4HB", blob, 80 + offset, 0xA9, 1, 1, 1, 123)
    return blob


class MaterialTests(unittest.TestCase):
    def test_lookup_uses_descriptor_offset(self):
        result = find_material(fixture(), 80)
        self.assertEqual(result["identifier"], 99)
        self.assertEqual(len(result["mips"]), 5)

    def test_bad_mip_extent_rejected(self):
        blob = fixture()
        struct.pack_into("<I", blob, 24 + 36, 10)
        with self.assertRaisesRegex(ValueError, "byte extent"):
            material_record(blob, 0)

    def test_bad_dimensions_rejected(self):
        blob = fixture()
        struct.pack_into("<H", blob, 80 + 2, 2)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            material_record(blob, 0)

    def test_unsupported_encoding_rejected(self):
        blob = fixture()
        struct.pack_into("<H", blob, 24 + 6, 0x80A9)
        with self.assertRaisesRegex(ValueError, "supports only"):
            material_record(blob, 0)

    def test_partial_mips_require_contiguous_zero_tail_and_count(self):
        blob = fixture()
        struct.pack_into('<H', blob, 34, 0x303)
        for level in (3, 4):
            struct.pack_into('<I', blob, 24 + 16 + level * 4, 0)
            struct.pack_into('<I', blob, 24 + 36 + level * 4, 0)
        self.assertEqual(len(material_record(blob, 0, allow_partial_mips=True)['mips']), 3)
        with self.assertRaises(ValueError):
            material_record(blob, 0)
        struct.pack_into('<I', blob, 24 + 16 + 4 * 4, 1)
        with self.assertRaisesRegex(ValueError, 'holes'):
            material_record(blob, 0, allow_partial_mips=True)

    def test_partial_mip_count_mismatch_rejected(self):
        blob = fixture()
        struct.pack_into('<H', blob, 34, 0x304)
        with self.assertRaisesRegex(ValueError, 'count field'):
            material_record(blob, 0, allow_partial_mips=True)

    def test_mip_cannot_escape_section(self):
        blob = fixture()
        struct.pack_into("<I", blob, 24 + 16, 1000)
        with self.assertRaisesRegex(ValueError, "outside payload"):
            material_record(blob, 0)


if __name__ == "__main__":
    unittest.main()
