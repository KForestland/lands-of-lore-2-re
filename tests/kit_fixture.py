"""Make a tiny synthetic MIX installation with editable LoL2 records."""
import struct

from tests.test_modkit import make_game
from tests.test_save_edit import GROUP, source_slot
from lol2_mix_writer import write_mix

DATA = "DAT"
LEVEL = "L1_DC"
ARCHIVE = "DAT/GLOBAL.MIX"
JOBS = ("level", "text", "translate", "music", "movie", "sound", "save", "patch", "mod")
TRANSLATE_FROM = "Main Menu"
SAVE_FIELD = "heading"
SAVE_AT = GROUP + 8


def geometry():
    vertices, region = 5300, 5332
    prop, item, events = region + 44, region + 81, region + 118
    raw = bytearray(events + 2)
    fields = {0: 18, 4: vertices, 0x50: 4, 0x0C: region, 0x58: 1,
              0x14: prop, 0x60: 1, 0x20: item, 0x6C: 1, 0x40: events, 0x88: 2}
    for offset, value in fields.items():
        struct.pack_into("<I", raw, offset, value)
    for index, (x, y) in enumerate(((0, 0), (10, 0), (10, 10), (0, 10))):
        struct.pack_into("<ii", raw, vertices + 8 * index, x << 16, y << 16)
    struct.pack_into("<8H", raw, region + 4, *([0xFFFF] * 4), 0, 1, 2, 3)
    struct.pack_into("<hh", raw, prop, 2, 3)
    struct.pack_into("<hh", raw, item, 3, 4)
    return bytes(raw)


def make_fixture(game):
    game.mkdir()
    make_game(game)
    payload = geometry()
    (game / DATA / "L1_DC.MIX").write_bytes(write_mix([(1, 0, payload)], len(payload)))
    return source_slot()


def media_files(game):
    """Independent fixture for the jobs that read the music-name table."""
    data = game / DATA
    data.mkdir(parents=True)
    (data / "L1_DC.MIX").write_bytes(write_mix([], 0))
    movie = b"FORM" + struct.pack(">I", 4) + b"WVQA"
    aud = struct.pack("<HIIBBHHI", 22050, 10, 2, 2, 99, 2, 2, 0xDEAF) + b"yz"
    (data / "TEST.MIX").write_bytes(write_mix([(1, 0, movie), (2, len(movie), aud)], len(movie) + len(aud)))
    image = bytearray(0x1CE10C + 35 * 4)
    for at, value in {0x1691: b"MUSIC\0", 0x1697: b"\\\0", 0x1699: b"CREDITS.AUD\0",
                      0x16A5: b"CREDITS.HMI\0"}.items():
        start = 0x1C1024 + at
        image[start:start + len(value)] = value
    (game / "LOLG.DAT").write_bytes(image)
    song = bytearray(0xEC)
    song[:12] = b"HMI-MIDISONG"
    struct.pack_into("<II", song, 0xE4, 1, len(song))
    track = bytearray(0x80)
    track[:13] = b"HMI-MIDITRACK"
    struct.pack_into("<I", track, 0x57, len(track))
    hmi = song + struct.pack("<I", len(song) + 4) + track + bytes.fromhex("00ff2f00")
    (game / "LOCAL.MIX").write_bytes(write_mix([(1, 0, hmi)], len(hmi)))
    return data


def foreign_level_edit():
    from level_edit import document

    return document(LEVEL, b"a different map", [])


def inspect_jobs(test):
    test.assertIn(TRANSLATE_FROM, test.job("text", "--data", test.game, "loose-options", "--id", "1"))
    game = test.root / "Media fixture"
    data = media_files(game)
    if test.lowercase:
        lowercase(game)
    test.assertIn("1 movie entry", test.job("movie", "--data", data, "--list", "--file", "TEST.MIX"))
    wav = test.root / "wave"
    test.job("sound", "--data", data, "--file", "TEST.MIX", "--entry", "1", "--out", wav)
    test.assertEqual((wav / ("test-1.wav" if test.lowercase else "TEST-1.wav")).read_bytes()[-2:], b"yz")
    out = test.root / "midi files"
    test.job("music", "--data", data, "--out", out)
    test.assertEqual((out / "unnamed_00000001.mid").read_bytes()[:4], b"MThd")


def lowercase(root):
    """Rename a generated installation as a lower-case filesystem copy."""
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        lower = path.with_name(path.name.lower())
        if lower.name != path.name:
            # The intermediate name also makes a case-only rename portable.
            temporary = path.with_name(path.name + ".renaming")
            path.rename(temporary)
            temporary.rename(lower)
