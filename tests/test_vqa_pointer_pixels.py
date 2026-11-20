import struct
import sys
import unittest
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from lol2_vqa_v2_decode import VQAError, draw_pointer_stream


def words(*values):
    return struct.pack("<" + "H" * len(values), *values)


@unittest.skipIf(np is None, "NumPy is needed for indexed video decoding")
class PointerPixelsTests(unittest.TestCase):
    def test_draw_and_retain_indices(self):
        dest = np.full((2, 7, 4, 4), 77, dtype=np.uint8)
        known = np.zeros(dest.shape, dtype=bool)
        book = np.arange(16, dtype=np.uint8).reshape(1, 4, 4)

        raw = words(0x0000, 0xA002, 0xC000, 0xB100, 0xC002, 0x0900, 0xF00A,
                    0xE000, 0xA002, 0x800B, 0xA002, 0x0000, 0xB20C)
        draw_pointer_stream(raw, book, dest, known, "test")
        self.assertEqual(dest[:, :, 0, 0].tolist(),
                         [[0, 77, 77, 77, 9, 77, 10], [77, 11, 11, 0, 0, 12, 12]])
        self.assertEqual(known[:, :, 0, 0].tolist(),
                         [[True, False, False, False, True, False, True],
                          [False, True, True, True, True, True, True]])
        np.testing.assert_array_equal(dest[0, 1, 0], [77, 1, 2, 3])

        draw_pointer_stream(words(0xB700, 0xB700), book, dest, known, "next frame")
        self.assertEqual(dest[0, 6, 0, 0], 10)
        self.assertTrue(known[0, 6].all())
        self.assertFalse(known[0, 5].any())

    def test_row_extent(self):
        dest = np.zeros((2, 2, 4, 4), dtype=np.uint8)
        with self.assertRaisesRegex(VQAError, "crosses a row"):
            draw_pointer_stream(words(0xB301), [], dest, dest.astype(bool), "test")
