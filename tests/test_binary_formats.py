"""Small file layouts exercising readers independently of a game install."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from draracle.lol2_cache_named_wall_fixture import parse_records
from lol2_aud_decode import CHUNK_MAGIC, decode_aud
from lol2_decompress_sphere import parse_entry1
from lol2_disassemble_scripts import operands
from lol2_entity_field_analyzer import BODY_SIZE, RECORD_SIZE, extract_entities, locate_entity_table
from lol2_hmi_midi import convert_song, read_vlq, write_vlq
from lol2_item_labels import ITEMS_KEY, STRIDE, item_layout
from lol2_lcw import decompress_f80
from lol2_level_report import geometry_stats, wall_stats
from lol2_loose import describe_wave
from lol2_media_check import mix_dir
from lol2_mix_parser import read_mix_with_hashes
from lol2_parse_le import find_le_header, segment_type
from lol2_sound_bank import parse_rows
from lol2_source_format import level_geometry
from lol2_text_tables import parse_trr
from lol2_texture_container import DESCRIPTOR_FORMAT, descriptor
from lol2_vqa_v2_decode import VQAError, header
from lol2_westwood_hash import ww_hash_v1


def mix(key, payload):
    return struct.pack("<HIIII", 1, len(payload), key, 0, len(payload)) + payload


def chunk(tag, payload, order):
    return tag + struct.pack(order + "I", len(payload)) + payload + bytes(len(payload) % 2)


def stored_aud():
    return (struct.pack("<HIIBB", 22050, 10, 2, 2, 99)
            + struct.pack("<HHIh", 2, 2, CHUNK_MAGIC, -123))


class BinaryFormats(unittest.TestCase):
    def test_file_archive_readers(self):
        blob = mix(0x90781234, b"end")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mini.mix"
            path.write_bytes(blob)
            source, rows, begin = read_mix_with_hashes(path)
            self.assertEqual(rows, [(0x90781234, 0, 3)])
            self.assertEqual(source[begin:], b"end")
            self.assertEqual(mix_dir(path)[-1][-1]["size"], 3)

    def test_level_geometry_member_and_wall_row(self):
        raw = bytearray(0x244 + 8 + 44)
        for field, value in ((0, 18), (4, 5300), (8, 0x244), (0x0C, 0x24C),
                             (0x54, 1), (0x58, 1)):
            struct.pack_into("<I", raw, field, value)
        raw[0x249] = 0x15
        struct.pack_into("<4H", raw, 0x250, *([0xFFFF] * 4))
        raw[0x24C + 30] = 1
        archive = mix(42, raw)
        row, payload = level_geometry(archive)
        self.assertEqual(row["offset"] + row["size"], len(archive))
        self.assertEqual(geometry_stats(payload)["walls"], 4)
        self.assertTrue(wall_stats(payload))
        with self.assertRaises(ValueError):
            level_geometry(archive[:-1])

    def test_sphere_shape(self):
        record = struct.pack("<HBHBHH", 2, 1, 1, 1, 11, 1) + b"\x0f"
        blob = struct.pack("<HI", 1, 4) + record
        self.assertEqual(parse_entry1(blob)[0]["grid"], [[15]])
        with self.assertRaises(ValueError):
            parse_entry1(blob[:-1])

    def test_named_cache_slot_at_end_of_file(self):
        raw = bytearray(8 + 256)
        struct.pack_into("<I", raw, 0, 8)
        raw[16:24] = b"Test.Te_"
        struct.pack_into("<II", raw, 8 + 0xD8, 2, 28)
        struct.pack_into("<I", raw, 8 + 0xE8, 4096)
        row, = parse_records(raw)
        self.assertEqual((row["canonical_name"], row["pointer"]), ("test.tex", 4096))
        with self.assertRaises(ValueError):
            parse_records(raw[:-1])

    def test_placed_entity_at_end_of_odf(self):
        model = bytearray(0x204 + RECORD_SIZE)
        for offset, value in ((0, 18), (0x10, 0x204), (0x48, 1)):
            struct.pack_into("<I", model, offset, value)
        struct.pack_into("<H", model, 0x204, 42)
        model[0x204 + BODY_SIZE:0x208 + BODY_SIZE] = b"TEST"
        archive = mix(ww_hash_v1(r"SPHERE1\TEST\TEST.ODF"), model)
        _, start, count = locate_entity_table(archive, "TEST")
        row, = extract_entities(archive, start, count)
        self.assertEqual((row["tag"], row["words"][0]), ("TEST", 42))
        self.assertEqual(start + RECORD_SIZE, len(archive))
        with self.assertRaises(ValueError):
            locate_entity_table(archive[:-1], "TEST")

    def test_script_operand_signed_value(self):
        self.assertEqual(operands({"opcode": 206, "raw_hex": "ce00000003ff"}), "index=3 value=-1")

    def test_format80_literal_and_end(self):
        self.assertEqual(decompress_f80(b"\x83abc\0"), b"abc")

    def test_aud_one_stored_sample(self):
        hdr, pcm, count = decode_aud(stored_aud())
        self.assertEqual((hdr["sample_rate"], pcm, count), (22050, b"\x85\xff", 1))

    def test_sound_bank_clip_and_directory(self):
        audio = stored_aud()
        bank = bytearray(0x260)
        start = len(bank)
        bank.extend(audio)
        table = len(bank)
        struct.pack_into("<II", bank, 0x258, 1, table)
        bank.extend(struct.pack("<4I44s", start, len(audio), 0, 0, b"test.aud"))
        count, position, rows = parse_rows(bank)
        self.assertEqual((count, position + 60), (1, len(bank)))
        self.assertEqual((rows[0]["name"], rows[0]["chunks"]), ("test.aud", 1))
        with self.assertRaises(ValueError):
            parse_rows(bank[:-1])

    def test_hmi_end_of_track(self):
        self.assertEqual(read_vlq(write_vlq(128), 0, 2), (128, 2))
        song = bytearray(0x170)
        struct.pack_into("<II", song, 0xE4, 1, 0xEC)
        struct.pack_into("<I", song, 0xEC, 0xF0)
        song[0xF0:0xFD] = b"HMI-MIDITRACK"
        struct.pack_into("<I", song, 0xF0 + 0x57, 0x80)
        song.extend(b"\0\xff\x2f\0")
        smf, events, tails = convert_song(song)
        self.assertEqual((smf[:4], smf[-4:], len(events), tails), (b"MThd", b"\0\xff\x2f\0", 1, [0]))
        with self.assertRaises(ValueError):
            convert_song(song[:-1])

    def test_item_definition_at_end_of_mix(self):
        table = bytearray(0x38 + STRIDE)
        struct.pack_into("<I", table, 4, 0x38)
        struct.pack_into("<I", table, 0x34, 1)
        struct.pack_into("<I", table, 0x38 + 0x18, 0x12345678)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "GLOBAL.MIX"
            blob = mix(ITEMS_KEY, table)
            path.write_bytes(blob)
            at, rows = item_layout(directory)
            self.assertEqual(at + len(rows[0]), len(blob))
            self.assertEqual(struct.unpack_from("<I", rows[0], 0x18)[0], 0x12345678)
            path.write_bytes(blob[:-1])
            with self.assertRaises(ValueError):
                item_layout(directory)

    def test_texture_descriptor_and_terminal_payload(self):
        fmt = DESCRIPTOR_FORMAT
        row = struct.pack(fmt, 3, 4, 2, 8, 0, 0, *([0] * 11))
        payload = struct.pack("<6I", 4, 0, 0, 0, 24, 24 + len(row)) + row + b"\0"
        parsed = descriptor(payload, 0)
        self.assertEqual((parsed["identifier"], parsed["width"], parsed["height"]), (3, 4, 2))
        with self.assertRaises(ValueError):
            descriptor(payload[:-2], 0)

    def test_vqa_form_and_frame_boundary(self):
        fields = struct.pack("<5H4B", 2, 0, 1, 4, 4, 4, 4, 15, 0).ljust(42, b"\0")
        movie = chunk(b"FORM", b"WVQA" + chunk(b"VQHD", fields, ">")
                      + chunk(b"VQFR", b"", ">"), ">")
        records, fields = header(movie)
        self.assertEqual((fields["frames"], fields["width"], records[-1]), (1, 4, (b"VQFR", b"")))
        with self.assertRaises(VQAError):
            header(movie[:-1])

    def test_trr_record_and_end_offset(self):
        data = struct.pack("<4I", 1, 9, 12, 14) + b"z\0"
        self.assertEqual(parse_trr(data, "fixture"), (1, [9], [12, 14]))
        with self.assertRaises(ValueError):
            parse_trr(data[:-1], "fixture")

    def test_pcm_wave_and_riff_length(self):
        fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
        wave = chunk(b"RIFF", b"WAVE" + chunk(b"fmt ", fmt, "<") + chunk(b"data", b"\x32\0", "<"), "<")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            path.write_bytes(wave)
            self.assertEqual(describe_wave(path)["fmt"], (1, 8000, 16))
            path.write_bytes(wave[:-1])
            with self.assertRaises(ValueError):
                describe_wave(path)

    def test_le_header_candidate(self):
        header = bytearray(32)
        header[4:6] = b"LE"
        struct.pack_into("<H", header, 12, 3)
        self.assertEqual(find_le_header(header), 4)
        self.assertIsNone(find_le_header(header[:12]))
        self.assertEqual(segment_type(4), "CODE")
