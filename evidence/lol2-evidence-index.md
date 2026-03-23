# LoL2 Evidence Index

Date: 2026-03-23

This index points to the local workspace artifacts backing the first promoted LoL2 closure docs.

## Canonical Workspace Sources

- `/home/bob/AI_COMMS/LOL2_TQ001_TRACE_CHECKPOINT_2026-03-17.md`
- `/home/bob/AI_COMMS/CURRENT_STATE.md`

## Key Trace Artifacts

- baseline fast-path pivot trace:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_commit1/guest_trace.jsonl`
- direct-address pre/post `+0xB4` proof:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_directb4/guest_trace.jsonl`
- suppress `91E4` only:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_suppress91e4/guest_trace.jsonl`
- suppress `A00F` only:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_suppress_a00f_b0/guest_trace.jsonl`
- dual suppress:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_dual_suppress_fix/guest_trace.jsonl`
- dual suppress with pivot watch:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_dual_suppress_pivot/guest_trace.jsonl`
- dual suppress with deeper pivot follow budget:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_dual_suppress_pivot_deep/guest_trace.jsonl`
- suppress `A00F` with pivot watch:
  - `/home/bob/lol2_out/dosbox_guest_trace_l1_offset_7418566_suppress_a00f_pivot/guest_trace.jsonl`

## Promoted Repo Docs Backed By These Artifacts

- `docs/lol2-current-status.md`
- `docs/lol2-compact-path-branch-steering.md`
