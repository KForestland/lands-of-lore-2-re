#!/usr/bin/env python3
"""Read original LoL2 files and documentation to compute the rating.

  rating.py --data DAT          # print the rating lines
  rating.py --data DAT --check  # also require README.md and docs/STATUS.md to carry them
  rating.py --data DAT --labels # list pages with open labels, largest first

The lines are explained in docs/HOW_WE_RATE.md:
  Files read      DAT files whose every byte a reader here accounts for, by count and by bytes
  Rules traced    evidence labels on the current pages: CONFIRMED against UNCONFIRMED
  Running game    probes on docs/NEEDS_A_RUNNING_GAME.md answered, out of all probes there
                  and how many of the answered ones rest on edited saves only
  Open questions  the state words of the At-a-glance table in docs/OPEN_QUESTIONS.md
  Page facts      candidate literals covered by a registered byte witness
"""
from cli_errors import run_cli
import re
from pathlib import Path

import struct

import lol2_cli
import lol2_loose
from page_facts import coverage

ROOT = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- rating:begin -->", "<!-- rating:end -->"


def mix_covered(path):
    """A Westwood MIX counts when its body-size field matches the file and its entries tile the body
    from offset 0 to the end with no gap or overlap."""
    data = path.read_bytes()
    if len(data) < 6:
        return False
    count, body = struct.unpack_from("<HI", data)
    base = 6 + 12 * count
    if base > len(data) or base + body != len(data):
        return False
    position = 0
    for offset, size in sorted(struct.unpack_from("<II", data, 6 + 12 * i + 4) for i in range(count)):
        if offset != position:
            return False
        position = offset + size
    return position == body


def files_read(data_dir):
    """A MIX archive counts when mix_covered() holds. A loose WAVE or NE file counts when lol2_loose.covered()
    holds. Every other file in the folder counts as not read."""
    total = read = total_bytes = read_bytes = 0
    for path in sorted(p for p in Path(data_dir).iterdir() if p.is_file()):
        size = path.stat().st_size
        total += 1
        total_bytes += size
        if path.suffix.lower() == ".mix" and mix_covered(path):
            read += 1
            read_bytes += size
        elif lol2_loose.covered(path):
            read += 1
            read_bytes += size
    return read, total, read_bytes, total_bytes


def history(text):
    return any(line.startswith("> **History") for line in text.splitlines()[:6])


def label_counts():
    for page in sorted((ROOT / "docs").rglob("*.md")):
        text = page.read_text(encoding="utf-8")
        if history(text) or page.name == "HOW_WE_RATE.md":
            continue
        text = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), "", text, flags=re.S)  # the rating block itself
        if page.name == "GLOSSARY.md":
            text = ""  # the glossary only defines the label words; its page still counts
        confirmed = len(re.findall(r"(?<![A-Z])(?:CONFIRMED|PROVEN)\b", text))
        unconfirmed = len(re.findall(r"\b(?:UNCONFIRMED|UNKNOWN)\b", text))
        yield page.relative_to(ROOT), confirmed, unconfirmed


def labels():
    counts = list(label_counts())
    return sum(c for _, c, _ in counts), sum(u for _, _, u in counts), len(counts)


def edited_only(body):
    """An answered probe rests on edited saves only when its section says "edited-save run" and none of its
    bold labels says "answered" without "edited-save" (a run on a game-written save)."""
    if "edited-save run" not in "\n".join(body):
        return False
    labels = [line[2:].split("**", 1)[0].lower() for line in body if line.startswith("**")]
    return not any("answered" in label and "edited-save" not in label for label in labels)


def probes():
    """Probe headings under "Answered probes" and "Remaining probes", and how many answered ones rest on
    edited saves only (edited_only)."""
    text = (ROOT / "docs" / "NEEDS_A_RUNNING_GAME.md").read_text(encoding="utf-8")
    counts, section, bodies = {"answered": 0, "remaining": 0}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            low = line.lower()
            section = "answered" if "answered probes" in low else "remaining" if "remaining probes" in low else None
        elif line.startswith("### ") and section:
            counts[section] += 1
            if section == "answered":
                bodies.append([])
                continue
        if section == "answered" and bodies and not line.startswith("## "):
            bodies[-1].append(line)
    edited = sum(edited_only(body) for body in bodies)
    return counts["answered"], counts["answered"] + counts["remaining"], edited


def questions():
    text = (ROOT / "docs" / "OPEN_QUESTIONS.md").read_text(encoding="utf-8")
    table = text.split("## At a glance", 1)[1].split("\n## ", 1)[0]
    states = [row.split("|")[2].strip() for row in table.splitlines() if re.match(r"\| Q\d+[a-z]? \|", row)]
    answered = sum(s.startswith("Answered") for s in states)
    mostly = sum(s.startswith("Mostly") for s in states)
    partly = sum(s.startswith("Partly") for s in states)
    return answered, mostly, partly, len(states)


def rating(data_dir):
    read, total, read_bytes, total_bytes = files_read(data_dir)
    confirmed, unconfirmed, pages = labels()
    seen, needed, edited = probes()
    answered, mostly, partly, count = questions()
    return [
        f"- **Files read:** {read} of {total} files in `DAT` ({read_bytes / 2**20:,.1f} of {total_bytes / 2**20:,.1f} MiB) have their whole layout read by a tool here: every byte belongs to a known header, directory, entry, chunk, segment or resource, or to zero padding between them; the DOS part of `SETUP.EXE` is counted by its length (what is inside an entry may still be only partly understood).",
        f"- **Rules traced:** the pages mark {confirmed:,} statements CONFIRMED (proved from the program code or the files) and {unconfirmed:,} UNCONFIRMED (a reading not yet proved), on {pages} current pages; old notes kept as history are not counted.",
        f"- **Seen in the running game:** {seen} of {needed} probes that need the original game running are answered (a question can have more than one probe); {edited} of them rest on edited saves only.",
        f"- **Open questions:** {count} numbered questions: {answered} answered, {mostly} mostly answered, {partly} partly answered.",
        f"- **Page facts:** {coverage()} with byte witnesses. The other literals are inventoried as prose-only.",
    ]


def block_of(path):
    text = path.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return None
    return [line for line in text.split(BEGIN, 1)[1].split(END, 1)[0].splitlines() if line.strip()]


def main():
    parser = lol2_cli.tool_args(__doc__)
    parser.add_argument("--labels", action="store_true", help="list pages with open evidence labels")
    args = parser.parse_args()
    if args.out:
        parser.error("prints only")
    if args.labels and args.check:
        parser.error("--labels and --check are mutually exclusive")
    try:
        if args.labels:
            for page, _, count in sorted(label_counts(), key=lambda row: (-row[2], row[0])):
                if count:
                    print(f"{count}\t{page}")
            return 0
        lines = rating(args.data)
        if not args.check:
            print("\n".join(lines))
            return 0
        stale = [p.name for p in (ROOT / "README.md", ROOT / "docs" / "STATUS.md") if block_of(p) != lines]
        if stale:
            raise ValueError(f"rating block differs from the counts in {', '.join(stale)}; run rating.py and copy the lines")
        print("CHECK rating: README.md and docs/STATUS.md carry the counted rating (" +
              "; ".join(re.sub(r"[*`]", "", l[2:]).split(":", 1)[0] for l in lines) + ")")
        return 0
    except (OSError, ValueError, IndexError) as error:
        parser.exit(1, f"rating: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
