# Lands of Lore II RE

Focused reverse-engineering workspace for `Lands of Lore II`.

## Start Here

If you are new to this repo, read these in order:

1. `docs/lol2-current-status.md`
   What is currently proven, what is still open, and where the LoL2 lane stands now.
2. `docs/lol2-compact-path-branch-steering.md`
   The main near-final LoL2 result: the compact `L1` control path and the loading-phase fast-vs-alternate branch split.
3. `docs/lol2-object-state-word.md`
   The clean breakdown of the external object state word at `[+80] + 0xB4` and what each byte is currently believed to do.
4. `docs/lol2-runtime-to-renderer-bridge.md`
   Explains why this runtime work matters for the old texture/renderer question and how the two lanes connect.
5. `evidence/lol2-witness-map.md`
   Short map of the main witnesses and trace variants, so the docs above are easier to follow.

## Status

- RE closure: near-final
- Current strongest local result:
  - compact `L1_DC.MIX` control path is traced through stable downstream consumers/writers
  - byte `0` at `[+80] + 0xB4` is the strongest known loading-phase branch-steering field
  - byte `0` does not gate `A0C3` reachability
  - byte `2 = 0x80` is not sufficient to recover the fast `A396` path by itself

## Repo Layout

- `docs/`
  - promoted writeups and closure notes for humans to read first
- `evidence/`
  - trace references, witness maps, and evidence indexes that back the docs
- `tools/`
  - reusable local analysis helpers and setup notes
- `future-patches/`
  - future patch planning only, kept separate from RE canon

## Scope Rules

- Keep promoted facts separate from hypotheses.
- Keep LoL2 RE canon separate from future patch planning.
- Do not mix advisory AI output into canon without local confirmation.

## Current Canon Source

Primary current checkpoint source in the workspace:

- `/home/bob/AI_COMMS/LOL2_TQ001_TRACE_CHECKPOINT_2026-03-17.md`

This repo will absorb the clean promoted LoL2 closure material from that working ledger.

## Promoted Docs

- `docs/lol2-current-status.md`
  - current status and strongest safe conclusions
- `docs/lol2-compact-path-branch-steering.md`
  - main compact-path closure note
- `docs/lol2-object-state-word.md`
  - focused note on `[+80] + 0xB4`
- `docs/lol2-runtime-to-renderer-bridge.md`
  - bridge from runtime object/control semantics back to renderer/texture work
- `evidence/lol2-evidence-index.md`
  - where the supporting local artifacts live
- `evidence/lol2-witness-map.md`
  - which trace witness proved which result
