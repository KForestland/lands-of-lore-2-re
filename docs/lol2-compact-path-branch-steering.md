# LoL2 Compact Path Branch Steering

Date: 2026-03-23

## Scope

This note promotes the compact `L1` `B_HUMAN 0001` loading-phase result that survived direct-address tracing, suppression testing, pivot-frame comparison, and bounded double-check review.

## Stable Compact Path

Proven compact control-frame path:

- `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

Practical read:

- `5570` stamps a fixed compact header/frame.
- `9BFC` fills the variable/linkage tail.
- `9C76` is the first proven downstream consumer.
- `+80` is the live object/base lane.
- `A00F` is the final compact-path commit step into external object state.

## Prebuilt External State At `[+80] + 0xB4`

Direct-address tracing on W3 proved:

- pre-`A00F`: `00018000`
- post-`A00F`: `04018000`

Observed byte ownership on that word:

- allocator / zeroing path establishes the baseline
- `122A` sets byte `+1 = 0x01`
- `91E4` sets byte `+2 = 0x80`
- `8F91` enforces byte `+3 = 0x00`
- `A00F` contributes byte `0`

This killed the earlier overstrong reading that `A00F` created the whole hot object word.

## Dead Models

The following models are no longer supported by the tested witness set:

- byte `0 = 0x04` gates `A0C3` reachability
- byte `2 = 0x80` gates `A0C3` reachability
- a simple one-byte activation-gate model
- `+0xB4` as the sole immediate gate for reaching `A0C3`
- byte `2` recovering the fast `A396` path by itself
- full convergence of baseline and alternate branch families within the observed loading-phase window

## Suppression Results

Single suppression:

- suppress `91E4` byte `+2 = 0x80`:
  - `A0C3` still fires
- suppress `A00F` dword write:
  - `A0C3` still fires

Dual suppression:

- suppress `91E4` byte `+2 = 0x80`
- suppress `A00F` dword write
- watched word stays `00010000`
- `A0C3` still fires

Practical result:

- `+0xB4` is not the sole reachability gate for `A0C3`

## Fast Path Versus Alternate Path

Baseline pivot trace (`commit1`) shows the fast family:

- `A0C3`
- `A2D5`
- `A6BA`
- heavy `A396`
- `6CC4`

Suppressed pivot traces show the alternate family:

- `A0C3`
- `A2D5`
- `A6BA`
- `6CC4`
- `E854 / E861`
- `A40A / A44B`
- no followed-chain `A396`

Most important isolation result:

- suppress `A00F` only, while still allowing byte `2 = 0x80`
- branch still matches the alternate family
- `A396` is still absent

This isolates byte `0` as the strongest known loading-phase branch-steering field.

## What Byte 0 Does And Does Not Do

What is supported:

- byte `0` does not gate `A0C3` reachability
- byte `0` strongly covaries with whether the followed cascade takes:
  - the fast `A396` path
  - or the alternate `E854 / E861 -> A40A / A44B` path
- byte `2 = 0x80` is not sufficient to recover the fast path by itself

What is still unsafe:

- naming byte `0` as a universal activation flag
- claiming byte `0` is the sole branch input in all contexts
- assigning final gameplay semantics to the alternate path outside the tested loading-phase witness

## Branch Boundary

Safest current boundary read:

- branch steering happens inside `A0C3` or immediately after it
- not at `A2D5`
- not at `A6BA`

Downstream safe role read:

- `A0C3`: unconditional loading-phase reader with branch-steering behavior under the tested compact-path states
- `A2D5`: downstream accessor whose `BX` differs across the two families
- `A6BA`: downstream pivot accessor/modifier whose behavior changes with the chosen family
- `A396`: fast-path loop body
- `6CC4`: branch-dependent pivot accessor seen in both families
- `E854 / E861 -> A40A / A44B`: alternate branch family, not a trace artifact

## Convergence Status

Full convergence is falsified.

Local pivot-frame comparison showed:

- `6 / 12` checked pivot offsets diverge between baseline and alternate traces
- `+92 = 8` in the alternate traces, not the later `100` state seen on the richer fast path
- `+88 = 0` in the alternate traces, so the post-loop `A6A8` handoff does not occur there

Safest current model:

- shared early setup
- partial convergence only
- different completion depth

## Current Safe Statement

The compact `L1` control frame is a live runtime structure with a class-stable consumer path, an instance-varying `+80` object/base lane, and a loading-phase branch-steering state word at `[+80] + 0xB4`. Within the tested witness, byte `0` is the strongest known steering field for fast `A396` versus alternate `E854 / E861 -> A40A / A44B` handling, while not serving as the sole reachability gate for `A0C3`.
