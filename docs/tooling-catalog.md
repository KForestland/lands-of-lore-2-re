# Tooling Catalog

Date: 2026-03-23

## Purpose

This note explains what tooling was actually used during the current LoL2 closure pass and how it was used.

It is intentionally short. The goal is to make the workflow understandable, not to publish every scratch command ever run.

## Main Tool Families

### 1. Patched DOSBox Guest Tracing

Used for:

- guest-side file I/O tracing
- targeted watch runs on `L*_DC.MIX` records
- direct-address watches on external object state
- suppression tests on specific writes
- pivot-frame follow-write tracing

What it enabled:

- proving `0070:0E6C` as a live parser site
- proving the compact runtime path through `A00F`
- proving pre/post state at `[+80] + 0xB4`
- proving the fast-versus-alternate branch split

Typical local wrappers used in the workspace:

- `/home/bob/lol2_dosbox_guest_trace.sh`
- `/home/bob/run_lol2_l9_watch.sh`

These wrappers are not yet copied into this repo because they still need cleanup before publication.

### 2. Local Trace Inspection

Used for:

- `jsonl` trace review
- event counting
- direct witness comparison
- pivot-state comparison

Typical shell tools:

- `rg`
- `sed`
- `find`
- `git`

Typical task shape:

- isolate one witness
- isolate one exact field or branch question
- compare baseline versus suppression traces

### 3. Bounded Advisory AI Review

Used for:

- contradiction-hunting
- ranking surviving explanations
- memo review and self-deception checks

Rule used during this pass:

- advisory output never became canon by itself
- only locally confirmed parts were promoted into repo docs

## How The Workflow Was Used

The working method during the compact-path closure pass was:

1. find one narrow ambiguity
2. design one exact trace or suppression check
3. confirm locally
4. reduce dead models
5. promote only the cleaned result

This is why the repo contains promoted notes rather than raw conversational history.

## Current Gap

The repo still lacks cleaned, publication-ready versions of the DOSBox helper scripts. That is intentional for now.

The current repo priority is:

- clean closure documentation first
- reusable public-facing tooling second
