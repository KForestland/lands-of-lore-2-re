"""Mod kit on synthetic files: unpack, edit, build and verify, refusals and errors."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import struct

from lol2_item_labels import ITEMS_KEY, STRIDE
from lol2_mix_writer import write_mix
from lol2_source_format import parse_mix
from lol2_text_writer import write_trr

ARCHIVE = ".MIX"
START = 0x40


def make_game(folder):
    (folder / "OPTTEXT.TRR").write_bytes(write_trr([(1, b"Main Menu"), (2, b"Save Game")]))
    items = bytearray(START + 2 * STRIDE)
    struct.pack_into("<I", items, 4, START)
    struct.pack_into("<I", items, 0x34, 2)
    items[START + 0x44] = items[START + STRIDE + 0x44] = 45
    text = write_trr([(7, b"Test Jungle")])
    (folder / "DAT").mkdir()
    (folder / "DAT" / "GLOBAL.MIX").write_bytes(
        write_mix([(0x1234, 0, text), (ITEMS_KEY, len(text), bytes(items))], len(text) + len(items)))


def edit(edits):
    name, document = next((n, d) for n, d in edits.items() if d["kind"] == "items")
    assert [row["strike_ticks"] for row in document["value"]] == [45, 45]
    document["value"][1]["strike_ticks"] = 46
    return name, document


def check_edit(test, game, out):
    old, new = ((path / "DAT" / "GLOBAL.MIX").read_bytes() for path in (game, out))
    test.assertEqual([i for i in range(len(old)) if old[i] != new[i]], [len(new) - STRIDE + 0x44])
    rows = {row["key"]: new[row["offset"]:row["offset"] + row["size"]] for row in parse_mix(new)}
    test.assertEqual(rows[ITEMS_KEY][START + STRIDE + 0x44], 46)



class ModKit(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="mod kit ")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.game = self.root / "my game"
        self.game.mkdir()
        make_game(self.game)
        self.before = {p: p.read_bytes() for p in self.game.rglob("*") if p.is_file()}
        self.work = self.root / "work"
        self.run_kit("unpack", self.game, self.work)

    def tearDown(self):
        self.assertEqual({p: p.read_bytes() for p in self.game.rglob("*") if p.is_file()}, self.before)

    def run_kit(self, *args, ok=True):
        run = subprocess.run([sys.executable, str(TOOLS / "modkit.py"), *map(str, args)],
                             capture_output=True, text=True, cwd=self.root)
        self.assertEqual(run.returncode == 0, ok, run.stdout + run.stderr)
        if not ok:
            self.assertNotIn("Traceback", run.stderr)
            self.assertEqual(len(run.stderr.strip().splitlines()), 1, run.stderr)
        return run.stdout + run.stderr

    def edits(self):
        return {path.name: json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((self.work / "edits").iterdir())}

    def save(self, name, document):
        (self.work / "edits" / name).write_text(json.dumps(document), encoding="utf-8")

    def test_unchanged_build_is_byte_identical(self):
        out = self.root / "out"
        self.assertIn("0 changed", self.run_kit("build", self.game, self.work, out))
        self.assertIn("0 changed", self.run_kit("verify", self.game, self.work, out))
        for path in out.rglob("*"):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (self.game / path.relative_to(out)).read_bytes())

    def test_edit_builds_and_reads_back(self):
        name, document = edit(self.edits())
        self.save(name, document)
        out = self.root / "out"
        self.assertIn("1 changed", self.run_kit("build", self.game, self.work, out))
        self.assertIn("1 changed", self.run_kit("verify", self.game, self.work, out))
        check_edit(self, self.game, out)
        target = out / document["file"]
        damaged = bytearray(target.read_bytes())
        damaged[-1] ^= 0xFF
        target.write_bytes(bytes(damaged))
        self.assertIn("differs", self.run_kit("verify", self.game, self.work, out, ok=False))

    def test_refused_outputs(self):
        archives = self.root / "archives"
        archives.mkdir()
        shutil.copy(next(p for p in self.game.rglob("*") if p.suffix.upper() == ARCHIVE), archives)
        for place in (self.game, self.game / "out", self.work, self.work / "out", archives / "out",
                      TOOLS.parent / "out"):
            self.assertIn("outside", self.run_kit("build", self.game, self.work, place, ok=False))
            self.assertFalse((self.game / "out").exists() or (archives / "out").exists())
        self.assertIn("outside", self.run_kit("unpack", self.game, self.game / "work", ok=False))

    def test_errors_are_one_line(self):
        out = self.root / "out"
        self.assertIn("not found", self.run_kit("unpack", self.root / "missing", self.root / "w", ok=False))
        empty = self.root / "empty"
        empty.mkdir()
        self.assertIn("nothing to unpack", self.run_kit("unpack", empty, self.root / "w", ok=False))
        name = sorted(self.edits())[0]
        (self.work / "edits" / name).write_text("{", encoding="utf-8")
        self.assertIn("not valid JSON", self.run_kit("build", self.game, self.work, out, ok=False))
        (self.work / "edits" / name).unlink()
        self.assertIn("is missing", self.run_kit("build", self.game, self.work, out, ok=False))
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
