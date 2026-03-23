#!/usr/bin/env python3
import collections
import json
import os
from pathlib import Path


def main() -> int:
    trace_dir = Path(os.environ.get("TRACE_DIR", "/home/bob/lol2_out/dosbox_guest_trace"))
    trace_path = trace_dir / "guest_trace.jsonl"
    out_path = trace_dir / "guest_trace_summary.md"

    if not trace_path.exists() or trace_path.stat().st_size == 0:
        out_path.write_text("# DOSBox Guest Trace Summary\n\nNo guest trace events captured.\n", encoding="utf-8")
        return 0

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

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
