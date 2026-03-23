# Tools

This folder is for reusable LoL2 analysis helpers and tool notes.

Current state:

- the public-facing catalog of tooling is currently documented in:
  - `../docs/tooling-catalog.md`
- the actual helper scripts used during the current closure pass still live in the wider local workspace and need cleanup before publication

First curated public subset:

- `lol2_guest_trace_summary.py`
  - summarizes one guest-trace run into a short markdown report
- `lol2_l9dr_census.py`
  - static census tool for `L9_DR.MIX`
- `run_lol2_l9_watch.sh`
  - baked wrapper for the `L9_DR.MIX` watch configuration used in the parser-side trace work

Expected future contents:

- cleaned trace summarizers
- small extraction helpers
- setup notes for patched DOSBox workflows
- examples of how to run the reusable scripts

Keep one-off scratch scripts out unless they are useful beyond a single test.
