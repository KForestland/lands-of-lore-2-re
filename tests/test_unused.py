"""Compare the unused-opcode summary with the measured opcode table."""
from pathlib import Path
import re
import unittest

DOCS = Path(__file__).resolve().parents[1] / "docs"


class UnusedClaims(unittest.TestCase):
    def test_opcode_summary(self):
        reference = (DOCS / "lol2-script-opcodes.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| \d+ \(([0-9A-F]+)\) \| (\d+) \| (\d+) \|", reference, re.M)
        counts = {int(code, 16): int(count) for code, _, count in rows}
        absent = {code for code, count in counts.items() if not count}
        summary = (DOCS / "UNUSED.md").read_text(encoding="utf-8").split("## Startup options")[0]
        documented = {int(code, 16) for code in re.findall(r"^\s*\| `0x([0-9A-F]+)` \|", summary, re.M)}
        commands, used = re.search(r"contain ([\d,]+) commands, using (\d+) opcode numbers", summary).groups()
        self.assertEqual(int(commands.replace(",", "")), sum(counts.values()))
        self.assertEqual(int(used), len(counts) - len(absent))
        self.assertEqual(documented, absent)
