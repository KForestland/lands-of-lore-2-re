import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from lol2_decompress_westwood import decompress_westwood
from lol2_export_scripts import SourceError, frame, group, walk
from lol2_save_header import HEADER_SIZE, parse_header
from lol2_save_inspect import LEVEL_HEADER, decode_chunks, inspect, level_sections
from lol2_source_format import parse_mix


class ReaderTests(unittest.TestCase):
    def test_mix_directory(self):
        archive = struct.pack("<HIIII", 1, 3, 0xFFFFFFFF, 0, 3) + b"abc"
        self.assertEqual(parse_mix(archive), [dict(index=0, key=0xFFFFFFFF, offset=18, size=3)])
        with self.assertRaises(ValueError):
            parse_mix(archive[:-1])

    def test_lz77_absolute_and_relative(self):
        literal = b"\x83abc"
        for stream in (literal + b"\xc0\0\0\x80", b"\0" + literal + b"\xc0\x03\0\x80"):
            with self.subTest(stream=stream):
                self.assertEqual(decompress_westwood(stream, 16), (b"abcabc", 0, len(stream)))

    def test_event_and_command_group(self):
        records, end = walk(bytes((6, 3, 0, 0, 1, 0, 0, 0)), 0)
        self.assertEqual((len(records), end), (1, 6))
        head = bytes((240, 0, 0, 0, 1, 0))
        child = bytes((198, 0, 0, 0, 4, 5))
        commands, error = frame(head + child)
        self.assertIsNone(error)
        self.assertEqual(group(commands), [(0, head, [(len(head), child)])])
        self.assertIsNotNone(frame(head + child[:-1])[1])
        with self.assertRaises(SourceError):
            group(commands[:1])

    def test_save_directory(self):
        header = bytearray(HEADER_SIZE)
        end = HEADER_SIZE + 12
        struct.pack_into("<3I", header, 0x2C, end, 18, 102)
        struct.pack_into("<3I", header, 0x9C, 8, 4, HEADER_SIZE)
        struct.pack_into("<31I", header, 0x18E, HEADER_SIZE + 3, *([end] * 30))
        parsed = parse_header(header, end)
        self.assertEqual(parsed["preview"], (HEADER_SIZE, 3))
        self.assertEqual(parsed["sections"][0], (HEADER_SIZE + 3, 9))
        self.assertEqual(parsed["levels"], [(end, 0)] * 20)
        struct.pack_into("<I", header, 0x1BA, end + 1)
        with self.assertRaises(ValueError):
            parse_header(header, end)

    def test_save_inspector_labels_fields_and_retains_unknown_bytes(self):
        header = bytearray(HEADER_SIZE)
        block = bytearray(LEVEL_HEADER + 4)
        struct.pack_into("<3I", header, 0x2C, len(header) + len(block), 18, 102)
        struct.pack_into("<3I", header, 0x9C, 0, 0, HEADER_SIZE)
        struct.pack_into("<31I", header, 0x18E, *([HEADER_SIZE] * 12), *([HEADER_SIZE + len(block)] * 19))
        struct.pack_into("<iI", header, 0x17C, 1, 0xFA)
        header[0x94] = 0xAA
        struct.pack_into("<I", header, 0x20A, len(block))
        struct.pack_into("<I", block, 0, len(block))
        struct.pack_into("<68I", block, 0xD8, *([LEVEL_HEADER] * 29), *([len(block)] * 39))
        struct.pack_into("<I", block, 0x1E8 + 28 * 4, 4)
        struct.pack_into("<I", block, LEVEL_HEADER, 0x1234)

        slot = header + block
        overview = "\n".join(inspect(slot, level=1))
        self.assertIn("Slot+0x0094  unknown = aa 00 00 00", overview)
        self.assertIn("Slot+0x0180  player position dword 0 = 250", overview)
        selected = "\n".join(inspect(slot, section=28, row=0))
        self.assertIn("first list head pointer = 4660 (0x00001234)", selected)
        struct.pack_into("<I", block, 0xD8, 0)
        with self.assertRaises(ValueError):
            level_sections(block)
        with self.assertRaises(ValueError):
            decode_chunks(struct.pack("<2I", 8, 100))
