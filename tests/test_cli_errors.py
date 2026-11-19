"""File reader commands report bad inputs without Python tracebacks."""
import json
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
        tool = "history/draracle/run_geometry_pipeline.py"
        game = self.root / "game"
        game.mkdir()
        args = ("--game-root", game, "--out", self.root / "output")
        self.assert_bad(tool, *args)
        dat = game / "DAT"
        dat.mkdir()
        (game / "LOLG.DAT").write_bytes(b"MZ")
        for content in (b"", struct.pack("<HI", 1, 12)):
            (dat / "L1_DC.MIX").write_bytes(content)
            with self.subTest(size=len(content)):
                self.assert_bad(tool, *args)

    def test_save(self):
        self.bad_files("SAVE.000", b"short", "lol2_save_header.py", self.data / "SAVE.000")

    def test_aud_only_writes_with_out(self):
        source = self.data / "A.AUD"
        source.write_bytes(struct.pack("<HIIBBHHIh", 22050, 10, 2, 2, 99, 2, 2, 0xDEAF, -123))
        reader = [sys.executable, str(TOOLS / "lol2_aud_decode.py"), "--raw", str(source)]
        for destination in ([], ["--out", str(self.root / "sample.wav")]):
            result = subprocess.run(reader + destination, cwd=self.root, env=self.env, capture_output=True,
                                    text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            if not destination:
                self.assertEqual(list(self.root.glob("*.wav")), [])
        self.assertTrue((self.root / "sample.wav").read_bytes().startswith(b"RIFF"))


class OutputGuard(unittest.TestCase):
    """No tool writes into the game data (the --data folder, a folder holding a MIX archive or
    LOLG.DAT, or anything below one); tools that extract game bytes also refuse the repository."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.game = self.root / "GAME"
        self.data = self.game / "DAT"
        self.data.mkdir(parents=True)
        (self.game / "LOLG.DAT").write_bytes(b"MZ")
        (self.data / "A.MIX").write_bytes(struct.pack("<HI3I", 1, 4, 0x1234, 0, 4) + b"abcd")
        self.loose = self.root / "LOOSE"
        (self.loose / "SUB").mkdir(parents=True)
        (self.loose / "fake.mix").write_bytes(b"")
        self.repo = TOOLS.parent
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ("LOL1_DATA", "LOL2_DAT", "LOL3_DAT")}

    def run_tool(self, tool, *args):
        return subprocess.run([sys.executable, str(TOOLS / tool), *map(str, args)], cwd=self.root,
                              env=self.env, capture_output=True, text=True, timeout=20)

    def assert_refused(self, targets, tool, *args):
        for target in targets:
            with self.subTest(tool=tool, target=target):
                run = self.run_tool(tool, *[target if a is None else a for a in args])
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                self.assertIn("give an output path outside", run.stderr)
                self.assertNotIn("Traceback", run.stderr)
                self.assertFalse(target.exists())

    def game_targets(self, name):
        return (self.loose / name, self.loose / "SUB" / name, self.data / name,
                self.game / name, self.game / "SAVES" / name)

    def test_output_refusal(self):
        sys.path.insert(0, str(TOOLS))
        try:
            from cli_errors import output_refusal
        finally:
            sys.path.remove(str(TOOLS))
        outside = self.root / "out" / "x.png"
        for target in self.game_targets("x.png"):
            with self.subTest(target=target):
                self.assertIsNotNone(output_refusal(target, self.data))
        self.assertIsNotNone(output_refusal(self.root / "elsewhere", [None, self.root / "elsewhere"]))
        self.assertIsNone(output_refusal(outside, self.data))
        self.assertIsNone(output_refusal(self.repo / "docs" / "x.md", self.data))
        self.assertIsNotNone(output_refusal(self.repo / "docs" / "x.md", self.data, repository=True))
        self.assertIsNone(output_refusal(outside, self.data, repository=True))

    def test_shared_parser_refuses_game_folders(self):
        trace = self.root / "trace.jsonl"
        trace.write_text(json.dumps({"event": "read", "guest_name": "LOLG.DAT", "actual": 1}) + "\n")
        self.assert_refused(self.game_targets("summary.md"), "lol2_guest_trace_summary.py",
                            "--trace", trace, "--out", None)
        fine = self.root / "summary.md"
        run = self.run_tool("lol2_guest_trace_summary.py", "--trace", trace, "--out", fine)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(fine.is_file())

    def test_subcommand_and_historical_parsers(self):
        self.assert_refused(self.game_targets("blob"), "lol2_texture_container.py",
                            "blob", "--mix", self.data / "A.MIX", "--out", None)
        self.assert_refused(self.game_targets("clip.ogv"), "history/convert_cave_video_review.py",
                            self.root / "missing.vqa", None)
        self.assert_refused(self.game_targets("frames"), "history/draracle/build_creature_group_review.py",
                            "--game-root", self.game, "--frames", None)

    def test_extracted_entry_refuses_game_and_repository(self):
        targets = (*self.game_targets("e0.bin"), self.repo / "no-such-folder" / "e0.bin")
        self.assert_refused(targets, "lol2_mix_parser.py", "--data", self.data, "A.MIX", "0", "--out", None)
        fine = self.root / "e0.bin"
        run = self.run_tool("lol2_mix_parser.py", "--data", self.data, "A.MIX", "0", "--out", fine)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(fine.read_bytes(), b"abcd")

    def test_relative_default_output_refuses_repository(self):
        self.assert_refused((self.repo / "no-such-folder", *self.game_targets("walls")),
                            "history/lol2_wall_texture_extract.py", "--lol2-root", self.game, "--output", None)
