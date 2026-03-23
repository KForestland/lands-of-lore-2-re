# LoL2 Entity Object Map

Date: 2026-03-23
Source: live DOSBox code dumps + read-monitoring traces

## Overview

The `[+80]` entity object is part of a C++ polymorphic entity system. It contains chain pointers, type/config fields, a vtable pointer for virtual dispatch, animation state, and bit-field status flags.

All offsets are relative to the `[+80]` base (the live object pointer at compact-frame offset +80).

## Proven Field Layout

| Offset | Size | Value (W3) | Role | Source |
|--------|------|------------|------|--------|
| +0x0C  | 4    | ptr        | pointer (inferred) | read-monitoring |
| +0x10  | 4    | ptr        | pointer (inferred) | read-monitoring |
| +0x14  | 4    | ptr        | pointer (inferred) | read-monitoring |
| +0x15  | 1    | 0x71       | type/flags (inferred) | read-monitoring |
| +0x16  | 1    | 0x00       | type/flags (inferred) | read-monitoring |
| +0x17  | 1    | 0x60       | type/flags (inferred) | read-monitoring |
| +0x1E  | 2    | 0x0000     | index/counter (inferred) | read-monitoring |
| +0x28  | 4    | ptr        | **vtable pointer** (virtual dispatch) | disassembly: `call *0x8c(%eax)`, `call *0x9c(%eax)` |
| +0x2C  | 4    | ptr        | secondary descriptor pointer | disassembly: A00F reads `[+0x2C]` fields |
| +0x4D  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x51  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x52  | 1    | 0x01       | config flag (inferred) | read-monitoring |
| +0x5A  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x5F  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x60  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x61  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x64  | 1    | 0x00       | config flag (inferred) | read-monitoring |
| +0x65  | 1    | computed   | animation speed (A40A computes) | disassembly |
| +0x6C  | 4    | 0x1E (30)  | **global timer snapshot** from `0x101D0CB6` | disassembly: A00F `mov 0x101d0cb6,%eax; mov %eax,0x6c(%edx)` |
| +0x88  | 2    | 0x0064     | dimension X (100) | disassembly: A396 reads, 6A50 clears for type 0xF |
| +0x8A  | 2    | 0x0000     | dimension Y | disassembly: A396/A40A read |
| +0x90  | 4    | 0x00       | frame count | disassembly: A40A loop bound |
| +0x94+ | 2/ea | —          | per-frame config entries | disassembly: A40A loop body |
| +0xA3  | 1    | 0x00       | animation-path flag (controls A044 → A0C3 jump) | disassembly: `test %bh,%bh; je A0C3` |
| +0xA6  | 1    | —          | sprite frame index (from 0F08 call result) | disassembly: A044 stores |
| +0xA7  | 1    | —          | frame delta (`secondary[0x81] - obj[0xA6]`) | disassembly: A044 computes |
| +0xA8  | 1    | 0x06       | **entity type** (0x06=standard, 0x0F=invisible) | disassembly: 6A50 `cmp $0xf` |
| +0xAA  | 1    | 0x00       | entity sub-type (inferred) | read-monitoring |
| +0xB0  | 2    | 0x1388     | sprite/animation reference (5000) | read-monitoring |
| +0xB2  | 2    | 0x0000     | sprite state/frame | read-monitoring |
| +0xB4  | 1    | 0x04       | **bit-field: bit2=activated** (A00F sets), **bit6=loading** (A0C3 clears) | disassembly |
| +0xB5  | 1    | 0x01       | **bit-field: bit0=render-skip** (6A50 tests) | disassembly: `testb $0x1,0xb5(%ebx)` |
| +0xB6  | 1    | 0x80       | **bit-field: bit7=allocated** (91E4 sets) | suppression tests + disassembly |

## Virtual Method Table at +0x28

The pointer at `+0x28` is a vtable pointer for a polymorphic entity class. Observed virtual method calls:

| Vtable offset | Method # | Callers | Purpose |
|--------------|----------|---------|---------|
| +0x8C        | ~35      | A396, 6A50 | get frame count / animation length |
| +0x9C        | ~39      | A396, A40A | get current state / next tick |

## Secondary Descriptor at +0x2C

The pointer at `+0x2C` points to a descriptor record with at least:

| Offset | Size | Readers | Purpose |
|--------|------|---------|---------|
| +0x3C  | 1    | 6A50    | descriptor flags (bit 4 tested) |
| +0x81  | 1    | 0F08, A044 | total frame count |
| +0x82  | 1    | 0F08    | minimum frame value |

## Bit-Field Register Layout (+0xB4 dword)

```
Byte 0 (+0xB4): [....x.x.]  bit 2 = activated (A00F), bit 6 = loading (A0C3 clears)
Byte 1 (+0xB5): [.......x]  bit 0 = render-skip (6A50 tests)
Byte 2 (+0xB6): [x.......]  bit 7 = allocated/prebuilt (91E4 sets)
Byte 3 (+0xB7): [........]  zero-enforced (8F91)
```
