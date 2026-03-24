#!/usr/bin/env python3
"""Analyze the disarm-rearm trace to identify post-A00F consumers.

Reads guest_trace.jsonl from the disarm-rearm trace run and extracts:
1. The disarm_rearm event (confirms patch fired)
2. All watch_read events after the rearm (the consumers)
3. Summary of which CS:IP reads which offset relative to [+80]

Usage:
    python lol2_analyze_disarm_rearm.py [TRACE_FILE]

The trace file path is resolved in order:
    1. CLI argument (if provided)
    2. TRACE_PATH environment variable
    3. Built-in default path
"""

import json
import os
import sys
from collections import defaultdict

DEFAULT_TRACE_PATH = "/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_disarm_rearm/guest_trace.jsonl"


def load_events(path):
    """Load JSONL trace events from the given path."""
    events = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    except FileNotFoundError:
        print(f"Trace file not found: {path}")
        print("Run the trace first: bash /home/bob/run_lol2_disarm_rearm_trace.sh")
        sys.exit(1)
    return events


def analyze_rearm_events(events):
    """Find and print disarm_rearm events. Returns (rearm_base, rearm_gen)."""
    rearm_events = [e for e in events if e.get("event") == "watch_disarm_rearm"]
    if not rearm_events:
        print("ERROR: No watch_disarm_rearm event found in trace.")
        print("The patch may not have triggered. Check:")
        print("  - Was the follow_write_budget high enough to reach A00F?")
        print("  - Did CS:IP match 02E0:A00F at disarm time?")

        disarms = [e for e in events if e.get("event") == "watch_follow_disarm"]
        if disarms:
            print(f"\nFound {len(disarms)} regular follow_disarm event(s):")
            for d in disarms:
                print(f"  CS:IP = {d.get('cs', '')}:{d.get('ip', '')}")
        sys.exit(1)

    print("=== DISARM-REARM EVENT ===")
    for re_evt in rearm_events:
        rearm_base = re_evt.get("rearm_base", 0)
        print(f"  CS:IP at disarm: {re_evt.get('cs', '')}:{re_evt.get('ip', '')}")
        print(f"  Last write addr: {re_evt.get('last_write_addr', 0)} (0x{re_evt.get('last_write_addr', 0):X})")
        print(f"  Rearm base:      {rearm_base} (0x{rearm_base:X})")
        print(f"  Rearm len:       {re_evt.get('rearm_len', 0)} (0x{re_evt.get('rearm_len', 0):X})")
        print(f"  Read budget:     {re_evt.get('watch_read_budget', 0)}")
        print(f"  Generation:      {re_evt.get('watch_generation', 0)}")

    rearm_gen = rearm_events[0].get("watch_generation", 0)
    rearm_base = rearm_events[0].get("rearm_base", 0)
    return rearm_base, rearm_gen


def collect_post_reads(events, rearm_gen, rearm_base):
    """Collect and group post-rearm read events by CS:IP."""
    post_reads = [e for e in events
                  if e.get("event") == "watch_read"
                  and e.get("watch_generation", 0) >= rearm_gen]

    if not post_reads:
        print("\nWARNING: No watch_read events found after rearm.")
        print("The consumer may not have executed during the trace window.")
        print("Consider increasing the trace duration or checking execution flow.")
        sys.exit(0)

    print(f"\n=== POST-A00F CONSUMER READS ({len(post_reads)} events) ===")

    readers = defaultdict(list)
    for r in post_reads:
        csip = f"{r.get('cs', '')}:{r.get('ip', '')}"
        offset = r.get("overlap_addr", 0) - rearm_base if rearm_base else 0
        readers[csip].append({
            "offset": offset,
            "hex_offset": f"+0x{offset:X}" if offset >= 0 else f"-0x{-offset:X}",
            "size": r.get("overlap_size", r.get("size", 0)),
            "addr": r.get("overlap_addr", r.get("addr", 0)),
            "ax": r.get("ax", ""),
            "bx": r.get("bx", ""),
            "preview": r.get("preview", ""),
        })

    return post_reads, readers


def print_consumer_analysis(readers, rearm_base, post_reads, trace_path):
    """Print consumer analysis and write machine-readable summary."""
    for csip, accesses in sorted(readers.items()):
        print(f"\n  Consumer CS:IP = {csip} ({len(accesses)} reads)")
        seen_offsets = set()
        for a in accesses:
            key = (a["hex_offset"], a["size"])
            if key not in seen_offsets:
                seen_offsets.add(key)
                print(f"    {a['hex_offset']} (size={a['size']}) preview={a['preview']}")

    # Highlight the critical offsets
    print("\n=== CRITICAL OFFSET COVERAGE ===")
    all_offsets = set()
    for accesses in readers.values():
        for a in accesses:
            all_offsets.add(a["offset"])

    b4_read = 0xB4 in all_offsets
    x6c_read = 0x6C in all_offsets
    print(f"  [+80]+0xB4 read: {'YES' if b4_read else 'NO'}")
    print(f"  [+80]+0x6C read: {'YES' if x6c_read else 'NO'}")

    if b4_read or x6c_read:
        print("\n=== CONSUMER IDENTITY ===")
        for csip, accesses in sorted(readers.items()):
            for a in accesses:
                if a["offset"] == 0xB4:
                    print(f"  +0xB4 reader: {csip} (preview={a['preview']})")
                if a["offset"] == 0x6C:
                    print(f"  +0x6C reader: {csip} (preview={a['preview']})")

    # Write machine-readable summary
    summary_path = trace_path.replace("guest_trace.jsonl", "consumer_summary.json")
    summary = {
        "rearm_base": rearm_base,
        "rearm_base_hex": f"0x{rearm_base:X}",
        "total_post_reads": len(post_reads),
        "unique_consumers": list(readers.keys()),
        "b4_read": b4_read,
        "x6c_read": x6c_read,
        "consumer_details": {
            csip: [{"offset_hex": a["hex_offset"], "size": a["size"]} for a in accesses]
            for csip, accesses in readers.items()
        }
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nMachine-readable summary: {summary_path}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TRACE_PATH", DEFAULT_TRACE_PATH)

    events = load_events(path)
    rearm_base, rearm_gen = analyze_rearm_events(events)
    post_reads, readers = collect_post_reads(events, rearm_gen, rearm_base)
    print_consumer_analysis(readers, rearm_base, post_reads, path)


if __name__ == "__main__":
    main()
