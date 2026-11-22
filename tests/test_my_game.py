"""Use invented names and records to exercise the LoL2 guide."""
from importlib.util import find_spec
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest

from tests.kit_fixture import geometry, make_fixture
from lol2_entity_field_analyzer import BODY_SIZE, RECORD_SIZE
from lol2_item_labels import ITEMS_KEY, OBJ5, STRIDE
from lol2_mix_writer import write_mix
from lol2_text_writer import write_trr
from lol2_westwood_hash import ww_hash_v1
from my_game import app
from my_game_ui import GameFolderError


def make_my_game_fixture(game):
    make_fixture(game)
    data = game / "DAT"
    start = 0x40
    names_at = start + STRIDE + 8
    items = bytearray(names_at + 30)
    struct.pack_into("<II", items, 4, start, len(items))
    struct.pack_into("<I", items, 0x34, 1)
    struct.pack_into("<I", items, start + 0x18, 123)
    name = b"100-Test Compass"
    items[names_at:names_at + len(name)] = name
    (data / "GLOBAL.MIX").write_bytes(write_mix([(ITEMS_KEY, 0, items)], len(items)))
    titles = write_trr([(1, b"Test Cavern")])
    credits = write_trr([(17, b"^%Example cast:\r\r^%Test Drake\r^Test Actor")])
    language = [(ww_hash_v1("automap.trr"), 0, titles), (ww_hash_v1("credits.trr"), len(titles), credits)]
    (game / "LOCALLNG.MIX").write_bytes(write_mix(language, len(titles) + len(credits)))

    image = bytearray(0x1CFC08)
    image[:2] = b"MZ"
    struct.pack_into("<II", image, 0x1CFB90, 64, 0)
    image[OBJ5 + 64:OBJ5 + 74] = b"Test Flash"
    (game / "LOLG.DAT").write_bytes(image)

    level = bytearray(geometry())
    struct.pack_into("<I", level, 0x3C, len(level))
    struct.pack_into("<I", level, 0x84, 6)
    level.extend(bytes((2, 1, 0, 0, 28, 33)))
    struct.pack_into("<I", level, 0xA4, len(level))
    struct.pack_into("<I", level, 0xAC, 1)
    level.extend(bytes(26))
    struct.pack_into("<I", level, 0x38, len(level))
    struct.pack_into("<I", level, 0x80, 10)
    level.extend(bytes((8, 12, 0, 0, 0, 0, 2, 0, 0, 0)))
    tags = (b"TEST DRAKE", b"APE", b"UNKNOWN12")
    odf = bytearray(0x204 + len(tags) * RECORD_SIZE)
    struct.pack_into("<I", odf, 0, 18)
    struct.pack_into("<I", odf, 0x10, 0x204)
    struct.pack_into("<I", odf, 0x48, len(tags))
    for number, tag in enumerate(tags):
        at = 0x204 + number * RECORD_SIZE + BODY_SIZE
        odf[at:at + len(tag)] = tag
    key = ww_hash_v1("SPHERE1\\L1_DC\\L1_DC.ODF")
    (data / "L1_DC.MIX").write_bytes(write_mix([(1, 0, level), (key, len(level), odf)], len(level) + len(odf)))


def check_page(page):
    assert page.count("data:image/png;base64,") == 1
    for label in ("<td>Test Compass</td>", "Test Flash", "<td>Test Drake</td><td>Test Cavern</td><td>TEST DRAKE</td>",
                  "<td>Ape</td><td>Test Cavern</td><td>APE</td>", "<td>—</td><td>Test Cavern</td><td>UNKNOWN12</td>",
                  "<td>Walk across the exit area.</td><td>No extra condition.</td><td>region 0</td>"):
        assert label in page, label


class MyGame(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Pillow not installed")
    def test_page_shows_named_original_records(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "fixture"
            make_my_game_fixture(game)
            original = {path: path.read_bytes() for path in game.rglob("*") if path.is_file()}
            out = app.write_page(game / "DAT", root / "page.html", open_page=False)
            check_page(out.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ValueError, "outside the game folder"):
                app.write_page(game, game / "page.html", open_page=False)
            self.assertEqual({path: path.read_bytes() for path in game.rglob("*") if path.is_file()}, original)

    def test_empty_folder_is_refused(self):
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(GameFolderError, app.wrong_folder):
                app.write_page(Path(temp), open_page=False)
