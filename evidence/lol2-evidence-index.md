# LoL2 Evidence Index

Date: 2026-03-23

This index lists the DOSBox trace captures behind the March 2026 notes. The captures themselves are not published; `<LOL2_OUT>` stands for the folder they were written to.

## Key Trace Artifacts

- baseline fast-path pivot trace:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_commit1/guest_trace.jsonl`
- direct-address pre/post `+0xB4` proof:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_directb4/guest_trace.jsonl`
- suppress `91E4` only:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_suppress91e4/guest_trace.jsonl`
- suppress `A00F` only:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_suppress_a00f_b0/guest_trace.jsonl`
- dual suppress:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_dual_suppress_fix/guest_trace.jsonl`
- dual suppress with pivot watch:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_dual_suppress_pivot/guest_trace.jsonl`
- dual suppress with deeper pivot follow budget:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_dual_suppress_pivot_deep/guest_trace.jsonl`
- suppress `A00F` with pivot watch:
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_suppress_a00f_pivot/guest_trace.jsonl`

- post-A00F consumer read-monitoring (disarm-rearm v2):
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_disarm_rearm/guest_trace.jsonl`
  - `<LOL2_OUT>/dosbox_guest_trace_l1_offset_7418566_disarm_rearm/consumer_summary.json`

## Promoted Repo Docs Backed By These Artifacts

- `docs/lol2-current-status.md`
- `docs/lol2-compact-path-branch-steering.md`
- `docs/lol2-runtime-to-renderer-bridge.md`
