"""File reader commands report bad inputs without Python tracebacks."""
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"


class ReaderErrors(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ("LOL1_DATA", "LOL2_DAT", "LOL3_DAT")}

    def assert_bad(self, tool, *args):
        run = subprocess.run([sys.executable, str(TOOLS / tool), *map(str, args)],
                             cwd=self.root, env=self.env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(run.returncode, 0, run.stdout)
        output = run.stderr or run.stdout
        self.assertNotIn("Traceback", run.stdout + run.stderr)
        self.assertEqual(len(output.strip().splitlines()), 1, output)

    def bad_files(self, name, short, tool, *args):
        file = self.data / name
        for kind, content in (("empty", b""), ("short", short)):
            with self.subTest(tool=tool, input=kind):
                file.write_bytes(content)
                self.assert_bad(tool, *args)

    def test_missing_data_folder(self):
        self.assert_bad("check_all.py", "--data", self.root / "missing")
        self.assert_bad("lol2_level_report.py", "--data", self.root / "missing")

    def test_archive(self):
        short = struct.pack("<H4I", 1, 4, 0x1234, 0, 4) + b"x"
        self.bad_files("A.MIX", short, "lol2_mix_parser.py", "--data", self.data, "A.MIX")

    def test_aud(self):
        short = struct.pack("<HIIBB", 22050, 10, 2, 2, 99) + b"x"
        self.bad_files("A.AUD", short, "lol2_aud_decode.py", "--raw", "--info", self.data / "A.AUD")

    def test_vqa(self):
        self.bad_files("A.VQA", b"FORM\0\0\0\x2fWVQA", "lol2_vqa_v2_decode.py", self.data / "A.VQA")

    def test_level_script(self):
        self.bad_files("L1_DC.MIX", struct.pack("<HI", 1, 5),
                       "lol2_disassemble_scripts.py", "--data", self.data, "L1_DC")

    def test_texture_container(self):
        self.bad_files("L1_DC.MIX", struct.pack("<HI", 1, 5),
                       "lol2_texture_container.py", "info", "--mix", self.data / "L1_DC.MIX")

    def test_localized_text(self):
        path = self.root / "LOCALLNG.MIX"
        for content in (b"", struct.pack("<HI", 1, 12)):
            path.write_bytes(content)
            with self.subTest(size=len(content)):
                self.assert_bad("lol2_inspect.py", "--data", self.data, "trr", "help")

    def test_cave_geometry_pipeline(self):
        tool = "draracle/run_geometry_pipeline.py"
        args = ("--game-root", self.root, "--out", self.root / "output")
        self.assert_bad(tool, *args)
        dat = self.root / "DAT"
        dat.mkdir()
        (self.root / "LOLG.DAT").write_bytes(b"MZ")
        for content in (b"", struct.pack("<HI", 1, 12)):
            (dat / "L1_DC.MIX").write_bytes(content)
            with self.subTest(size=len(content)):
                self.assert_bad(tool, *args)

    def test_save(self):
        self.bad_files("SAVE.000", b"short", "lol2_save_header.py", self.data / "SAVE.000")
