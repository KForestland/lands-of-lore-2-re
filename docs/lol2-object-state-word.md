# LoL2 Object State Word At `[+80] + 0xB4`

Date: 2026-03-23

## Scope

This note isolates the external object word at `[+80] + 0xB4` for the compact `L1` `B_HUMAN 0001` witness and records the strongest safe ownership/behavior read after direct-address tracing and suppression testing.

## Proven Pre/Post State

Direct-address tracing on W3 proved:

- pre-`A00F`: `00018000`
- post-`A00F`: `04018000`

This means `A00F` does not create the whole dword. It adds byte `0` on top of a prebuilt word.

## Observed Byte Ownership

Safest current ownership read:

- byte `0`
  - baseline: `A00F` contributes `0x04`
  - this is the only non-zero contribution observed on byte `0`
- byte `1`
  - `122A` sets `0x01`
  - observed once during setup
- byte `2`
  - `91E4` sets `0x80`
  - observed repeatedly during the loading-phase trace window
- byte `3`
  - `8F91` enforces `0x00`
  - observed as an idempotent zero write for this witness

Practical read:

- bytes `1-3` belong to prepared/prebuilt object state more than to `A00F`
- `A00F` contributes the byte-`0` stamp layered onto that prepared word

## What The Word Does Not Do

The following models are no longer supported by the tested witness set:

- byte `0` alone gates `A0C3` reachability
- byte `2` alone gates `A0C3` reachability
- `+0xB4` as the sole immediate gate for reaching `A0C3`
- byte `2 = 0x80` being sufficient by itself to recover the fast `A396` path

## What The Word Does Support

Safest promoted read:

- `[+80] + 0xB4` is a multi-byte loading-phase state word
- the word influences downstream branch shape
- the word is not a one-byte magic activation register

Most important promoted result:

- byte `0` is the strongest known loading-phase branch-steering field in the word
- byte `0` does not gate `A0C3` reachability
- byte `0` does strongly covary with:
  - fast `A396` path
  - versus alternate `E854 / E861 -> A40A / A44B` path

## Byte 0 Safe Read

What is supported:

- `A00F` applies byte `0 = 0x04` on the normal compact-path commit
- suppressing that write shifts the followed cascade into the alternate family
- allowing byte `2 = 0x80` while suppressing byte `0` does not restore the fast path

What is still unsafe:

- naming byte `0` as a universal activation flag
- claiming byte `0` is the sole branch input in all contexts
- assigning final gameplay semantics to `0x04`

Safest label:

- loading-phase branch-steering stamp

## Byte 2 Safe Read

What is supported:

- `91E4` contributes byte `2 = 0x80`
- this byte is repeatedly read later in the trace window
- suppressing byte `2` does not block `A0C3`
- suppressing byte `2` does not explain the fast/alternate branch split by itself

Safest label:

- prepared/prebuilt state bit with downstream significance still unresolved

## Remaining Unresolved Semantics

- exact safe name for byte `1 = 0x01`
- exact lifecycle meaning of byte `2 = 0x80`
- whether byte `0 = 0x04` is a pure equality-tested stamp, a bit flag, or one input among several inside `A0C3`
- the relationship between this state word and the deferred scalar target at `[+80] + 0x6C`
