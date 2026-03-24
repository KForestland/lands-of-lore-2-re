# LoL2 Object State Word At `[+80] + 0xB4`

Date: 2026-03-23

## Scope

This note isolates the bit-field register at `[+80] + 0xB4` for the compact `L1` `B_HUMAN 0001` witness and records the strongest safe ownership/behavior read after direct-address tracing and suppression testing.

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

- `[+80] + 0xB4` is a bit-field register with independently controlled bits
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

## Disassembly-Proven Bit Layout (Update 2)

Native disassembly from live DOSBox memory proved `+0xB4` is a **bit-field register**, not a multi-value state word:

| Bit | Mask | Value | Writer | Proven role |
|-----|------|-------|--------|-------------|
| 2   | 0x04 | set   | A00F (`AND 0xFB` / `OR (val<<2)`) | entity activation flag |
| 6   | 0x40 | clear | A0C3 (`AND 0xBF`) | loading-complete cleanup |
| 7   | 0x80 | set   | 91E4 | prebuilt/allocated state |

A00F uses a classic Watcom C bit-field pattern: read byte, clear bit 2 with `AND 0xFB`, then `OR` in the new value shifted to bit 2. A0C3 clears bit 6 as a cleanup step and returns — it is NOT a branch-steering site (corrects earlier inference).

## Deferred Scalar +0x6C (Update 2)

Disassembly proved:
- `+0x6C` is loaded from **global address `0x101D0CB6`** by A00F: `MOV 0x101d0cb6,%eax ; MOV %eax,0x6c(%edx)`
- It is a global timer snapshot, NOT a per-entity computed value
- The W3/W4 delta (0x1E vs 0x14) was caused by loading at different game-time ticks

## Remaining Unresolved Semantics

- exact safe name for byte `1 = 0x01` (bit 8..15 of the dword)
- whether bits 0-1, 3-5 at `+0xB4` are used
- the actual branch point for the fast/alternate loading-phase split (not A0C3 — likely inside the `0x100B0F08` call)
