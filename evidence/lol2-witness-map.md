# LoL2 Witness Map

Date: 2026-03-23

This map summarizes the key local witnesses behind the promoted compact-path branch result.

## Primary Witness

- compact witness:
  - `L1_DC.MIX`
  - `B_HUMAN 0001`
  - first pivoted control often referred to as `W3`

Core stable path:

- `0E6C -> 0D53 -> 1A44 -> 5570 / 9BFC -> 9C76 -> 9C89 / 91D0 / A00F`

## Important Addresses

- live object/base lane:
  - `+80`
- external object state word:
  - `[+80] + 0xB4`
- deferred scalar target:
  - `[+80] + 0x6C`

Direct-address W3 target used in the main proof:

- `[+80] + 0xB4 = 287872820`

## Core Trace Set

### Baseline

- `commit1`
  - path used as the main fast-path baseline
  - followed-chain `A396` heavily present

### Direct Object Watch

- `directb4`
  - direct watch on `[+80] + 0xB4`
  - proved:
    - pre-`A00F`: `00018000`
    - post-`A00F`: `04018000`
  - exposed byte ownership:
    - `122A`
    - `91E4`
    - `8F91`
    - `A00F`

### Single Suppressions

- `suppress91e4`
  - suppresses byte `2 = 0x80`
  - `A0C3` still fires

- `suppress_a00f_b0`
  - suppresses `A00F` dword stamp
  - `A0C3` still fires

### Dual Suppression

- `dual_suppress_fix`
  - suppresses both:
    - `91E4` byte `2`
    - `A00F` dword stamp
  - `A0C3` still fires
  - killed the simple one-byte gate model

### Pivot Branch Family Traces

- `dual_suppress_pivot`
- `dual_suppress_pivot_deep`
  - proved:
    - `A0C3`, `A6BA`, `6CC4` still appear
    - followed-chain `A396` absent
    - alternate family appears:
      - `E854 / E861`
      - `A40A / A44B`

- `suppress_a00f_pivot`
  - allows byte `2 = 0x80`
  - suppresses byte `0`
  - branch still matches the alternate family
  - isolated byte `0` as the strongest known branch-steering field

## Practical Witness Conclusions

- W3 is sufficient to prove:
  - `+0xB4` is not the sole reachability gate for `A0C3`
  - byte `0` is the strongest known loading-phase branch-steering field
  - byte `2` is not sufficient to recover the fast path by itself

- W3 is not sufficient to safely prove:
  - universal semantics for byte `0`
  - universal semantics for byte `2`
  - final gameplay-phase meaning of the alternate branch family
