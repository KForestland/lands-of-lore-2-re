#!/usr/bin/env python3
import collections
import json
import os
from pathlib import Path


def summarize(trace_path) -> str:
    trace_path = Path(trace_path)
    if not trace_path.exists() or trace_path.stat().st_size == 0:
        return "# DOSBox Guest Trace Summary\n\nNo guest trace events captured.\n"

    counts = collections.Counter()
    file_reads = collections.Counter()
    first_events = []
    watch_counts = collections.Counter()

    with trace_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            counts[event.get("event", "unknown")] += 1
            if len(first_events) < 20:
                first_events.append(event)
            if event.get("event") == "read":
                key = event.get("guest_name") or event.get("system_name") or "<unknown>"
                file_reads[key] += int(event.get("actual", 0) or 0)
            if event.get("event") in {
                "watch_config",
                "watch_arm",
                "watch_write",
                "watch_read",
                "watch_disarm",
                "watch_derive",
                "watch_rearm",
                "watch_follow_arm",
                "watch_follow_write",
                "watch_follow_disarm",
                "watch_stage_rearm",
            }:
                key = event.get("watch_file") or "<unknown>"
                watch_counts[(event.get("event"), key)] += 1

    lines = [
        "# DOSBox Guest Trace Summary",
        "",
        f"Source: `{trace_path}`",
        "",
        "## Event Counts",
        "",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Top Read Sources", ""])
    for key, value in file_reads.most_common(15):
        lines.append(f"- `{key}`: {value} bytes")
    if not file_reads:
        lines.append("- No read events captured.")

    lines.extend(["", "## Watch Events", ""])
    if watch_counts:
        for (event_name, key), value in sorted(watch_counts.items()):
            lines.append(f"- `{event_name}` `{key}`: {value}")
    else:
        lines.append("- No watch events captured.")

    lines.extend(["", "## First Events", ""])
    for event in first_events:
        lines.append(f"- `{json.dumps(event, sort_keys=True)}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    """Summarize a DOSBox guest trace (guest_trace.jsonl from the patched tracer; none is included)."""
    import argparse, tempfile
    ap = argparse.ArgumentParser(description="""Summarize a DOSBox guest trace (JSON lines) as Markdown.

  lol2_guest_trace_summary.py --trace guest_trace.jsonl [--out summary.md]
  lol2_guest_trace_summary.py --check   # self-test on a synthetic trace (needs no game data)""",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trace")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--data", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.check:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "guest_trace.jsonl"
            p.write_text("\n".join(json.dumps(e) for e in [
                {"event": "read", "guest_name": "LOLG.DAT", "actual": 512},
                {"event": "read", "guest_name": "LOLG.DAT", "actual": 512},
                {"event": "watch_read", "watch_file": "L1_DC.MIX"}]) + "\n")
            md = summarize(p)
        ok = "`LOLG.DAT`: 1024 bytes" in md and "`watch_read` `L1_DC.MIX`: 1" in md
        print(f"CHECK guest_trace_summary: self-test on a synthetic trace {'passed' if ok else 'FAILED'} (no game data needed)")
        return 0 if ok else 1
    if not a.trace:
        ap.print_help(); return 2
    md = summarize(a.trace)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8"); print("wrote", a.out)
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
