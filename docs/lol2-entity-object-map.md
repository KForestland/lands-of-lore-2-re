# LoL2 Entity Object Map

Date: 2026-03-23
Source: live DOSBox code dumps + read-monitoring traces

Complete proven field layout of the `[+80]` entity object from live DOSBox disassembly and read-monitoring.

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
| +0xB4  | 1    | 0x04       | **bit-field: bit2=activated** (A00F sets), **bit6=loading-phase** (A0C3 clears) | disassembly |
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

## On-Disk Entity Record Field Map (135-byte body, 24 u16 LE words)

Proof levels: fields marked **PROVEN** have direct runtime evidence (disassembly or trace). Fields marked **INFERRED** are derived from cross-level statistical analysis of 128 records across 62 types — they are strong hypotheses, not runtime-confirmed.

Source: statistical analysis of 128 entity records across 62 types in all 15 level MIX files.
Tool: `tools/lol2_entity_field_analyzer.py`

### Fields f0–f9: Entity Class Configuration (INFERRED)

These 10 words are invariant within each entity type (same value for all instances of GGUARD, all instances of HIVEW, etc.) but differ between types. They define the entity's class-level properties: AI behavior, animation, combat style, rendering, and capabilities.

| Field | Byte Offset | Classification | Notes |
|-------|-------------|---------------|-------|
| f0    | 0–1   | class config (packed byte pair) | AI/behavior parameters. B_HUMAN=0x0000, GGUARD=0x0202, HIVEW=0x0207, Rat=0x0702 |
| f1    | 2–3   | class config (packed byte pair) | Animation/movement. Often 0x0000 for humanoids, non-zero for monsters |
| f2    | 4–5   | class config (capability flags) | Bitfield. 0x1FFF for SWARMER (max flags), 0x0000 for B_HUMAN |
| f3    | 6–7   | class config (AI mode flags)    | Bitfield: bit1=guard, bit2=ranged, bit5=patrol, bit6=aggressive. 0x60=boss AI (EXEC, SHADE, StSquid, RULOI) |
| f4    | 8–9   | class config (combat style)     | Bitfield encoding weapon/attack type. SSAR=0x1040, GGUARD=0x0801 |
| f5    | 10–11 | class config (special abilities) | Usually 0x0000. Non-zero: 0x0004=shield/block (Roach, STIGER, skel, HL), 0x0060=magic (RIX) |
| f6    | 12–13 | class config (auxiliary)         | SSAR=0x01A6, SHADE=0x0F0E, RULOI=0x1400 — entity-specific parameters |
| f7    | 14–15 | class config (extended)          | Usually 0x0000. Non-zero for DRACOID=0x0078, IMP_BEL=0x0060, RULOI=0x0080 |
| f8    | 16–17 | class config (rendering/LOD)     | VISC/bacl16/HL3/IMP_BEL=0x1000, SSAR=0x0800, STIGER=0x0010 |
| f9    | 18–19 | class config (AI extension)      | Usually 0x0000. HIVEW=0x0004, EXEC=0x0003, SEWER=0x0060 |

### Fields f10–f11: Reserved Padding

| Field | Byte Offset | Classification | Notes |
|-------|-------------|---------------|-------|
| f10   | 20–21 | always zero | Zero across all 62 entity types, all 128 instances |
| f11   | 22–23 | always zero | Zero across all 62 entity types, all 128 instances |

### Fields f12–f13: Global Entity ID (PROVEN — cross-level verified + runtime trace)

| Field | Byte Offset | Classification | Notes |
|-------|-------------|---------------|-------|
| f12   | 24–25 | global entity ID (low word)  | Cross-level stable. Same B_HUMAN (Luther) has f12=0xEB7A in all 12 levels |
| f13   | 26–27 | global entity ID (high word) | Cross-level stable. Luther's f13=0x1B28 in 11/12 levels (0x1BA8 in L14) |

Previously proven by cross-level comparison (session 4). f12:f13 as a u32 uniquely identifies each entity globally.

### Fields f14–f16: Combat Stats and Flags (f14: STRONGLY INFERRED — 95.3% match with f20_hi)

| Field | Byte Offset | Classification | Notes |
|-------|-------------|---------------|-------|
| f14   | 28–29 | **hit points (HP)** | 0=non-combat NPC, 24=Rat/Swarmer, 86=GGUARD, 159=HL1/HL2 boss. Strongly inferred from f20_hi duplicate (95.3% match). |
| f15   | 30–31 | behavior flags | Observed values: 0x0000=passive, 0x0008=combat-ready (L1), 0x00DD=berserker (APE/STIGER/TIG_ROG), 0x00E5=ambush (L3 skel/Rat), 0x00F0=scripted (L16 B_HUMAN) |
| f16   | 32–33 | auxiliary flags | Usually 0x0000. B_HUMAN in L1 has 0x000C (NPC dialogue), SKEL has 0x0025 |

### Fields f17–f18: Reserved Padding

| Field | Byte Offset | Classification | Notes |
|-------|-------------|---------------|-------|
| f17   | 34–35 | always zero | Zero across all 62 entity types, all 128 instances |
| f18   | 36–37 | always zero | Zero across all 62 entity types, all 128 instances |

### Fields f19–f23: Spawn Placement and Packed Combat Stats (INFERRED)

These fields use byte-packing — the high and low bytes of each u16 word carry separate values.

| Field | Byte Offset | Hi Byte | Lo Byte | Notes |
|-------|-------------|---------|---------|-------|
| f19   | 38–39 | spawn coordinate | zone/layer | Per-level spawn position |
| f20   | 40–41 | **HP duplicate** | variant flag | Hi byte = f14 value (95.3% match). Lo byte non-zero for companions |
| f21   | 42–43 | defense/speed | attack power | Combat stat pair. GGUARD: DEF=30, ATK=140. HL1: DEF=97, ATK=255 |
| f22   | 44–45 | armor/resistance | max damage | Combat stat pair. HIVEW L14: ARM=168, DMG=200 |
| f23   | 46–47 | tier/quest flag | slot index | Hi byte non-zero for quest-important entities |

### HP Duplicate Proof (f20_hi == f14)

Verified across 128 entity records in 15 levels: 122 exact matches (95.3%). The 6 non-matches are non-combat B_HUMAN with f14=0 where f20 carries spawn data instead.

### Remaining Gaps

- The exact byte-level mapping from on-disk f0–f9 through the `0E6C` parser to runtime offsets +0x4D–+0x64 has not been traced instruction-by-instruction
- f19 spawn coordinate interpretation needs DOSBox map position verification
- The `[+0x2C]` secondary descriptor remains only partially mapped (3 of its fields proven)
