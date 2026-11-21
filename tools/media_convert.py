#!/usr/bin/env python3
"""Convert original LoL2 VQA movies to MKV and AUD sounds to WAV."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
from tempfile import TemporaryFile
import wave

from cli_errors import ReaderArgumentParser, run_cli
from level_html import counted, find_data, installation_root
from lol2_aud_decode import decode_aud, decode_ima_adpcm_block, is_aud, write_wav
from lol2_cli import DEFAULT_DATA
from lol2_media_check import mix_dir
from lol2_source_format import parse_mix
from lol2_vqa_v2_decode import chunks, decode, header
from modkit_core import output_folder


def locate(data, filename):
    supplied = Path(filename).expanduser()
    if supplied.is_absolute() or supplied.parent != Path("."):
        if supplied.is_file():
            return supplied.resolve()
        raise ValueError(f"Cannot find {supplied}. Check the full path after --file.")
    for folder in (data, data.parent):
        for item in folder.iterdir():
            if item.name.casefold() == supplied.name.casefold() and item.is_file():
                return item
    raise ValueError(f"Cannot find {filename}. Check --data and the file name.")


def members(path):
    blob = path.read_bytes()
    if path.suffix.upper() == ".MIX":
        for row in parse_mix(blob):
            at = row["offset"]
            yield row["index"], blob[at:at + row["size"]]
    else:
        yield None, blob


def looks_like(blob, mode):
    return (blob[:4] == b"FORM" and blob[8:12] == b"WVQA") if mode == "movie" else is_aud(blob)


def list_entries(path, mode):
    """Probe headers first so listing media never reads unrelated payloads."""
    _, _, rows = mix_dir(path)
    with path.open("rb") as source:
        for row in rows:
            source.seek(row["offset"])
            prefix = source.read(min(20, row["size"]))
            if mode == "movie":
                matching = looks_like(prefix, mode)
            elif len(prefix) == 20 and prefix[16:20] == b"\xaf\xde\0\0":
                size, = struct.unpack_from("<I", prefix, 2)
                matching = size + 12 == row["size"] and is_aud(prefix + source.read(size - 8))
            else:
                matching = False
            if matching:
                yield row["index"], row["size"]


def list_archives(data, mode):
    archives = sorted({item for folder in (data, data.parent) for item in folder.iterdir()
                       if item.is_file() and item.suffix.lower() == ".mix"
                       and not item.name.upper().startswith("CDCACHE")})
    total = with_media = 0
    for path in archives:
        count = sum(1 for _ in list_entries(path, mode))
        if count:
            print(f"{path}: {counted(count, mode + ' entry', mode + ' entries')}")
            with_media += 1
            total += count
    print(f"Found {counted(total, mode + ' entry', mode + ' entries')} in {counted(with_media, 'archive')}.")
    if with_media:
        print("Add --file with an archive path to list its entry numbers.")


def read_audio(top):
    stored = [(tag, payload) for tag, payload in top if tag.startswith(b"SND")]
    if not stored:
        return 0, b"", 0
    raw_header = next(body for tag, body in top if tag == b"VQHD")
    rate, channels, width = struct.unpack_from("<HBB", raw_header, 0x18)
    if not rate or (channels, width) != (1, 16):
        raise ValueError("The movie audio is outside the supported mono 16-bit layout.")
    pred = step = count = 0
    pcm = bytearray()
    for kind, payload in stored:
        if kind == b"SND2":
            samples, pred, step = decode_ima_adpcm_block(payload, pred, step, round_once=True)
            if len(samples) != 2 * len(payload):
                raise ValueError("Movie audio sample count differs from its SND2 packets.")
            pcm.extend(struct.pack(f"<{len(samples)}h", *samples))
            count += 2 * len(payload)
        elif kind == b"SND0" and len(payload) % 2 == 0:
            pcm.extend(payload)
            count += len(payload) // 2
        else:
            raise ValueError(f"The movie has an unsupported audio packet {kind.decode('ascii', errors='replace')}.")
    return rate, bytes(pcm), count


def vqa_frames(blob, top):
    import numpy as np

    palette = None
    kinds = set()
    packets = (body for tag, body in top if tag == b"VQFR")
    for kind, frame in decode(blob, pixels=True, stream_pixels=True):
        packet = next(packets)
        kinds.add(kind)
        if len(kinds) != 1:
            raise ValueError("The movie mixes pointer layouts. Choose a movie with one layout.")
        if kind == "vpt":
            yield frame.tobytes(), 0
            continue
        for tag, body in chunks(packet):
            if tag == b"CPL0":
                words = np.frombuffer(body, dtype=np.uint8).astype(np.uint16) & 63
                palette = ((words << 2) | (words >> 4)).astype(np.uint8).reshape(-1, 3)
        indices, known = frame
        rgb = palette[indices]
        rgb[~known] = 0
        yield rgb.tobytes(), int(known.size - np.count_nonzero(known))


def find_ffmpeg():
    paths = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if any(path is None for path in paths):
        raise ValueError("Movie export needs FFmpeg and FFprobe on PATH. Install FFmpeg and reopen your terminal.")
    return paths


def verify_movie(probe, path, expected_frames, expected_samples):
    common = [probe, "-v", "error", "-of", "json"]
    video = subprocess.run(common + ["-count_frames", "-select_streams", "v:0",
                                     "-show_entries", "stream=nb_read_frames", str(path)],
                           capture_output=True, text=True)
    audio = subprocess.run(common + ["-select_streams", "a:0", "-show_entries", "frame=nb_samples", str(path)],
                           capture_output=True, text=True)
    if video.returncode or audio.returncode:
        raise ValueError("FFprobe could not read the exported movie. Check the FFmpeg installation.")
    frames = json.loads(video.stdout).get("streams", [])
    count = sum(int(row["nb_samples"]) for row in json.loads(audio.stdout).get("frames", []))
    if len(frames) != 1 or int(frames[0]["nb_read_frames"]) != expected_frames or count != expected_samples:
        raise ValueError("Exported frame or sample count differs from the original movie.")


def movie(blob, out, stem):
    ffmpeg, ffprobe = find_ffmpeg()
    top, fields = header(blob)
    rate, pcm, expected = read_audio(top)
    if not fields["fps"]:
        raise ValueError("The original movie has no frame rate. Choose a valid VQA entry.")
    path = out / f"{stem}.mkv"
    args = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{fields['width']}x{fields['height']}", "-r", str(fields["fps"]), "-i", "pipe:0"]
    wav = out / "temporary-audio.wav"
    if pcm:
        write_wav(str(wav), pcm, rate, 1, 2)
        args += ["-i", str(wav), "-c:a", "pcm_s16le"]
    args += ["-c:v", "ffv1", "-pix_fmt", "bgr0", str(path)]
    count = unset = 0
    with TemporaryFile() as errors, subprocess.Popen(args, stdin=subprocess.PIPE, stderr=errors) as encoder:
        try:
            for frame, unknown in vqa_frames(blob, top):
                encoder.stdin.write(frame)
                count += 1
                unset += unknown
            encoder.stdin.close()
        except BrokenPipeError as error:
            raise ValueError("FFmpeg rejected the movie frames. Check that its FFV1 encoder is available.") from error
        except Exception:
            encoder.stdin.close()
            raise
        if encoder.wait():
            raise ValueError("FFmpeg could not encode the movie. Check its installation and the output drive.")
    if count != fields["frames"]:
        raise ValueError("Decoded frame count differs from the source VQA header.")
    verify_movie(ffprobe, path, count, expected)
    if pcm:
        wav.unlink()
    summary = f"{count:,} frames at {fields['fps']} fps, {expected:,} audio samples"
    if unset:
        summary += f", {unset:,} pixels without a stored background drawn black"
    return path.name, summary


def sound(blob, out, stem):
    info, pcm, _ = decode_aud(blob)
    if info["stereo"] or not info["is_16bit"]:
        raise ValueError("Choose a 16-bit mono LoL2 sound. This entry has a different layout.")
    if len(pcm) not in (info["output_size"], info["output_size"] - 2):
        raise ValueError("Decoded sample count differs from the original AUD header.")
    path = out / f"{stem}.wav"
    write_wav(str(path), pcm, info["sample_rate"], 1, 2)
    with wave.open(str(path), "rb") as loaded:
        count = loaded.getnframes()
        if (loaded.getframerate(), loaded.getnchannels(), loaded.getsampwidth()) != (info["sample_rate"], 1, 2):
            raise ValueError("WAV layout differs from the original AUD header.")
        if count != len(pcm) // 2 or loaded.readframes(count) != pcm:
            raise ValueError("WAV sample count or contents differ from decoded audio.")
    summary = f"{count:,} samples at {info['sample_rate']:,} Hz"
    if len(pcm) != info["output_size"]:
        summary += " (one sample fewer than the source header advertises)"
    return path.name, summary


def main(mode=None):
    description = {"movie": "Convert an original LoL2 movie to MKV.",
                   "sound": "Convert an original LoL2 sound to WAV."}
    parser = ReaderArgumentParser(description=description.get(mode, __doc__))
    if mode is None:
        parser.add_argument("mode", choices=("movie", "sound"))
    else:
        parser.set_defaults(mode=mode)
    parser.add_argument("--data", default=DEFAULT_DATA, required=DEFAULT_DATA is None,
                        help="your game folder or its DAT folder (default: $LOL2_DAT)")
    parser.add_argument("--file", help="MIX archive or loose file name or path")
    parser.add_argument("--entry", type=int, help="zero-based MIX entry number from --list")
    parser.add_argument("--list", action="store_true", help="list media archives or entries in the archive named by --file")
    parser.add_argument("--out", help="new folder for the converted file")
    args = parser.parse_args()
    data = find_data(args.data, "DAT", "L1_DC.MIX")
    if args.list:
        if args.out or args.entry is not None:
            parser.error("Use --list without --out or --entry.")
        if not args.file:
            list_archives(data, args.mode)
            return 0
        path = locate(data, args.file)
        if path.suffix.upper() != ".MIX":
            parser.error("Use --list with a MIX archive or omit --file to scan the game folder.")
        found = 0
        for index, size in list_entries(path, args.mode):
            found += 1
            print(f"Entry {index:>4}: {size:,} bytes")
        print(f"{path.name}: {counted(found, args.mode + ' entry', args.mode + ' entries')}")
        return 0
    if not args.file:
        parser.error("Give --file a file name or path, or use --list to find media archives.")
    path = locate(data, args.file)
    archive = path.suffix.upper() == ".MIX"
    if not args.out or archive != (args.entry is not None):
        parser.error("Give --out a new folder and use --entry only for a MIX archive.")
    raw = next((blob for index, blob in members(path) if index == args.entry), None)
    if raw is None or not looks_like(raw, args.mode):
        raise ValueError(f"The file or entry does not contain a {args.mode}. Use --list to find entries.")
    stem = path.stem + (f"-{args.entry}" if archive else "")
    convert = movie if args.mode == "movie" else sound
    with output_folder(args.out, installation_root(data), args.data, path.parent) as folder:
        name, counts = convert(raw, folder, stem)
    print(f"Wrote {name} to {args.out}: {counts}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
