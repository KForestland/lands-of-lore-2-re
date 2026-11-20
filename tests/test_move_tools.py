"""Data-free tests of anchored placement changes."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import level_edit as editor
from level_move_ui import SCRIPT


class Moves(unittest.TestCase):
    def test_only_coordinate_words_change(self):
        raw = bytearray(b"\x44" * 25)
        struct.pack_into("<hh", raw, 4, 2, 3)
        struct.pack_into("<H", raw, 14, 0)
        square = [(0, 0), (655360, 0), (655360, 655360), (0, 655360)]
        with patch("level_edit.adapter.fields", return_value=([square], [("item-7", 4)])):
            self.assertEqual(editor.changed(raw, []), (raw, 0))
            result, count = editor.changed(raw, [["item-7", 8, 10]])
            self.assertEqual(count, 1)
            self.assertEqual(result[4:8], struct.pack("<hh", 8, 10))
            self.assertEqual((result[:4], result[8:]), (raw[:4], raw[8:]))
            with self.assertRaisesRegex(ValueError, "must stay"):
                editor.changed(raw, [["item-7", 11, 1]])
            with self.assertRaisesRegex(ValueError, "repeated"):
                editor.changed(raw, [["item-7", 2, 3], ["item-7", 2, 3]])

    def test_export_keeps_an_escaped_newline_in_javascript(self):
        self.assertIn("JSON.stringify(change, null, 2) + '\\n'", SCRIPT)
