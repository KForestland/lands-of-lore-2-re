# Lands of Lore II RE

Focused reverse-engineering workspace for `Lands of Lore II`.

## Status

- RE closure: near-final
- Current strongest local result:
  - compact `L1_DC.MIX` control path is traced through stable downstream consumers/writers
  - byte `0` at `[+80] + 0xB4` is the strongest known loading-phase branch-steering field
  - byte `0` does not gate `A0C3` reachability
  - byte `2 = 0x80` is not sufficient to recover the fast `A396` path by itself

## Repo Layout

- `docs/`
  - promoted writeups and closure notes
- `evidence/`
  - trace references, artifact maps, and evidence indexes
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
