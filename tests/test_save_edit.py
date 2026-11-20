"""Save editor on synthetic LoL2 slots: fields, read-back, refused outputs and one-line errors."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import save_edit

from lol2_save_writer import synthetic_slot, write_slot

GROUP = 0x180
LEVEL = 0x17C
NUMBER = "heading"


def source_slot():
    return write_slot(synthetic_slot())


class SaveEditTest(unittest.TestCase):
    def test_heading_and_position_tuple(self):
        raw = source_slot()
        edited, change = save_edit.edit(raw, "heading", "0x2345")
        self.assertTrue(change.startswith("heading 0x") and change.endswith(" -> 0x2345"), change)
        self.assertEqual(edited, raw[:GROUP + 8] + b"\x45\x23" + raw[GROUP + 10:])
        donor = bytearray(raw)
        replacement = struct.pack("<iiIH", -10 << 16, 9 << 16, 0xA000, 12)
        donor[GROUP:GROUP + 14] = replacement
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "matching slot"
            path.write_bytes(donor)
            shifted, change = save_edit.edit(raw, "position-from", str(path))
            self.assertTrue(change.endswith("-> (x -10, y 9, heading 0xa000, region 12)"), change)
            self.assertEqual(shifted, raw[:GROUP] + replacement + raw[GROUP + 14:])
            donor[LEVEL] ^= 1
            path.write_bytes(donor)
            with self.assertRaisesRegex(ValueError, "same level"):
                save_edit.edit(raw, "position-from", str(path))
            with self.assertRaisesRegex(ValueError, "donor save not found"):
                save_edit.edit(raw, "position-from", str(path) + " missing")


WORDS = ("Traceback", "Errno", "int()", "codec", "Expecting")


class OutputTest(unittest.TestCase):
    def run_edit(self, *args, ok=True):
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "save_edit.py"), "set", *map(str, args)],
                             capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(run.returncode == 0, ok, run.stdout + run.stderr)
        if not ok:
            self.assertEqual(len(run.stderr.strip().splitlines()), 1, run.stderr)
            for word in WORDS:
                self.assertNotIn(word, run.stderr)
        return run.stdout + run.stderr

    def test_new_file_only(self):
        with tempfile.TemporaryDirectory(prefix="save edit ") as temp:
            saves, out = Path(temp) / "my saves", Path(temp) / "edited"
            saves.mkdir()
            out.mkdir()
            original = saves / "slot one"
            raw = source_slot()
            original.write_bytes(raw)
            said = self.run_edit(original, "name", "Synthetic", "--out", out / "new slot")
            self.assertIn("name ", said)
            self.assertIn(" -> 'Synthetic'", said)
            self.assertEqual(original.read_bytes(), raw)
            self.assertEqual((out / "new slot").read_bytes(), b"Synthetic\0" + raw[10:])
            for args, message in (
                    ((original, "name", "Synthetic", "--out", original), "outside"),
                    ((original, "name", "Synthetic", "--out", saves / "beside"), "outside"),
                    ((original, "name", "Synthetic", "--out", out / "new slot"), "already exists"),
                    ((original, "name", "Sünthetic", "--out", out / "a"), "plain ASCII"),
                    ((original, NUMBER, "lots", "--out", out / "b"), "whole number"),
                    ((original, NUMBER, "99999999", "--out", out / "c"), "whole number"),
                    ((saves / "missing", "name", "X", "--out", out / "d"), "save not found"),
                    ((original, "name", "X", "--out", out / "no folder" / "e"), "does not exist")):
                said = self.run_edit(*args, ok=False)
                self.assertIn(message, said, args)
            damaged = saves / "damaged"
            damaged.write_bytes(raw[:200])
            self.run_edit(damaged, "name", "X", "--out", out / "g", ok=False)
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["new slot"])
            self.assertEqual(original.read_bytes(), raw)

    def test_leading_zero_and_hex(self):
        self.assertEqual(save_edit.integer("08", 0, 9), 8)
        self.assertEqual(save_edit.integer("0x10", 0, 99), 16)


if __name__ == "__main__":
    unittest.main()
