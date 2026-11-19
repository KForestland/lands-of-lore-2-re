"""Reader and history listings stay in sync with the files."""
from pathlib import Path
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"


class ToolInventory(unittest.TestCase):
    def test_active_tools_listed(self):
        index = (TOOLS / "README.md").read_text(encoding="utf-8")
        for source in sorted(TOOLS.glob("*.py")):
            with self.subTest(tool=source.name):
                self.assertIn(f"`{source.name}`", index)

    def test_historical_tools_listed(self):
        history = TOOLS / "history"
        index = (history / "README.md").read_text(encoding="utf-8")
        self.assertIn("> **Historical.**", index)
        for source in sorted(history.rglob("*")):
            if source.suffix in {".py", ".c"}:
                path = source.relative_to(history).as_posix()
                with self.subTest(tool=path):
                    self.assertIn(f"]({path})", index)
