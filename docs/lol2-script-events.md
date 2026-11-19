# LoL2 script records, timers and predicates

Evidence uses the retail 1.30 executable and the address convention in the
[opcode reference](lol2-script-opcodes.md). MIX offsets are absolute offsets
in each archive. A count below is a count of records visited, including reuse
through multiple object placements. Region lists are counted once per unique
descriptor-list offset within each archive.

## Event records

**CONFIRMED.** Byte +0 is the record length and +1 is the kind. For example,
`0xAD8B5–0xAD8D4` stops on zero length or kind and otherwise advances by
the length. Object group offsets are u16 +2 relative to `[0x2B514]`
(`0xAD89E–0xAD8AD`). Region group offsets are relative to `[0x2B51C]`
(`0xF2E98–0xF2EAC`). The common runner is `0x646EC`.

| List and kind | Records | Native interpretation and source |
|---|---:|---|
| Object 1 | 1369 | **CONFIRMED** as a 14-byte record in the framed corpus, e.g. `L10_DC.MIX+0xC8296B`. **CONFIRMED** kind-1 lookup and render-parameter update (`0xB4704`, `0xB4712`). See [kind-1 fields and producers](lol2-event-producers.md). |
| Object 2 | 616 | **CONFIRMED** periodic timer. The 10-byte row is indexed by `0xB47B4` and serviced by `0xB8BA0`. The timer details follow below. |
| Object 3 | 715 | **CONFIRMED** six-byte row. `0xAD7F4` compares u8 +4 with its second argument, checks the predicate and runs every matching group. The effective source event depends on the caller. |
| Object 4 | 1382 | **CONFIRMED** 10-byte held-item test. `0xADD36` dispatches mode +4 in 0–7 using a u32 argument at +6. The mode-3 arm compares item identity +0x18 (`0xADC84–0xADC8F`). Other arms test fields on +0x3D, +0x3F, +0x43 or +0x45. Zero at +5 leaves the test uninverted (`0xADC47`). |
| Object 5 | 403 | **CONFIRMED** `0xAD8E0` matches event u8 +4 and value u8 +5. A value of 0xFF on either side passes the value test. All predicate-qualified matches run. |
| Object 6 | 5153 | **CONFIRMED** `0xADDE0` compares u8 +4 with the supplied value and checks the predicate. Opcode 18 sends value 6 at `0xB5A0E`. Property 21 sends 20 at `0xB5448`. |
| Object 7 | 49 | **CONFIRMED** `0xAE134` evaluates a health threshold with u8 +4 mode and u8 +5 threshold. The table at object-2 offset `0x55100` maps modes 0–3 to `0xAE162`, `0xAE1B6`, `0xAE1CE`, `0xAE1E6`. See below. |
| Object 8 | 149 | **CONFIRMED** the six-byte row has a u16 match value +4 and 0xFFFF wildcard in the object-event walker at `0xAE510`. A corpus witness is `L10_DC.MIX+0xC82CC5`. The matcher checks the predicate trailer. |
| Object 9 | 1339 | **CONFIRMED** hit-filter row at `0xAE2C8`. Two u16 masks at +4/+6, threshold +8, and flags +9. The first qualifying match is queued. See [combat](lol2-combat-ai.md#scripted-hits-and-thresholds). |
| Object 10 | 110 | **CONFIRMED** `0xAE608` first compares u8 +4 with the signed low byte of the second argument. On equality it compares `[0x22D0C]+44*u16(+6)` with the third argument. The alternative branch requires event zero, record +4 = 7 and `u16(arg3+0x18) == u16(+6)` (`0xAE6E7–0xAE70F`). |
| Region 11 | 700 | **CONFIRMED** `0xF2FC0` checks u16 +4 against the supplied selector and u8 +6 against the supplied event, then checks the predicate and invokes stream 0. The descriptor-based entry near `0xF30FA` checks the event and already has its descriptor list. |
| Region 12 | 3241 | **CONFIRMED** the walker at `0xF2D87` compares region u16 +4 and event u8 +6. The switch at `0xF2E16` applies the event arms below before the predicate. |
| Region 15 | 18 | **CONFIRMED** `0xF37C8` matches region u16 +4 and evaluates the predicate. Mode +6 compares values from `0xF5094` to u16 +8 (byte +7 zero) or to a value computed for the region indexed by u16 +8. The eight arms at `0xF38E0–0xF396D` use unsigned >, <, = or ≠ on the callback sum or qualifying-object count. |
| Object or region 19 | 6009 / 1645 | **CONFIRMED** a four-byte trailer. After a match, e.g. at `0xAD863–0xAD88B`, the walker checks the immediately following record's kind for 0x13 and, if found, calls `0x66AB0(u16(+2))`. |

For kind 7, **CONFIRMED** at `0xAE162–0xAE1F7`: let `before` and
`after` be the hit-context dwords at +0x22 and +0x26. Mode 0 subtracts
`before-after` from the nonzero threshold byte, fires when that delta reaches
the threshold and clears the byte on success. Mode 1 tests
`after < threshold <= before`. Mode 2 tests
`before <= threshold < after`. Mode 3 tests `threshold == after`.
A passing trailer is required if present (`0xAE213–0xAE281)).

### Region event arms

**CONFIRMED.** Region kind 12 uses the switch at
`LOLG.DAT+0x129D04`. Let `a` be u8 record +7 and `v` the third
argument to `0xF2D2C`. All listed tests precede predicate evaluation.

| Event | Condition | VA |
|---:|---|---|
| 0, 7 | Pass | `0xF2DB7` |
| 1, 9 | `a << 2 <= v` using signed comparison | `0xF2DD1`, `0xF2DE7` |
| 2, 3, 4 | Pass if `a == 0` or `v != 0` | `0xF2DFD` |
| 5, 6 or above 9 | Test the incoming ESI value | `0xF2E1E`, range branch at `0xF2E10` |
| 8 | `a <= v` using signed comparison | `0xF2DBE` |

An adjacent special arm at `0xF2EB9` can dispatch a kind-12
record with stored event 6 when the caller requests event 2.
In the player's region transition path, the walker gets event 3
for the previous region at `0xD383C` and event 2 for the new
one at `0xD39BB`. Those calls establish two uses of the event
IDs. Other caller sequences remain **UNCONFIRMED**. At each entry to
`0xAD7F4`, recover the return address and the event byte, then follow
the last conditional branch at that caller.

## Object timers

**CONFIRMED.** At `0xB8BA0`, the timer service binds each object's pointer
from the parallel list to `[0xB7D80]` and skips records with +5 bit 0 set.
Flags are u8 +4, status is u8 +5, reload parameters are u8 +6/+7, and the
countdown is u16 +8. The service reads an elapsed quantity `D` from dword
`[0x22C5A]` when flags & 0x90 is nonzero, otherwise from sign-extended
word `[0x22C58]` (`0xB8BD3–0xB8C1C`). Let `C` be the stored
countdown. An unsigned `C > D` stores `C-D` without firing. Otherwise the
service obtains the low word `R` of a reload and stores the low word of
`C+R-D` when `R > D`, or zero. The predicate then gates dispatch of
`[0x2B514]+u16(+2)` (`0xB8C25–0xB8CE6)).

**CONFIRMED.** Reload at `0xB8AC4` uses `a=u8(+6)`, `b=u8(+7)`,
`S=u16([0x223A8])` and `v = a` if flags & 0x20, otherwise a random
integer in the inclusive interval between `a` and `b` from `0x12415C`.
Bit 0x10 takes precedence over bit 0x80.

| Flags condition | Reload before low-word store |
|---|---|
| Bit 0x10 set | `v * S` |
| Bit 0x10 clear, bit 0x80 set | `a * S * 60` |
| Both clear | `v << 8` |

The original writes 60 into `[0x223A8]` at `0x14E7F1`. **CONFIRMED**
from the 616 kind-2 placement rows, the initial word lies in the range of
the above formula for `S=60` in all 616, including fixed cases. **CONFIRMED.** The frame routine writes the 8.8 and whole-tick elapsed cells at `0xE0C82` and `0xE0CD2`. The [timer clock](lol2-timer-clock.md#live-write-and-conversion) gives the original formulas and a runtime writer witness. The scale constant and elapsed cells play distinct roles.

**CONFIRMED.** The load scan at `0xAEC74` adds enabled timer records to the
parallel lists at `0xB7DA4` and `0xB7DB0`. Status +5 bit 0 disables, bit
0x80 tracks membership, and bit 1 makes admission depend on region +0x28 bit
0x04. The action selector at `0xB47B4` takes the zero-based kind-2 index
from command +6 and falls back to the last kind-2 record when the index is too
large (`0xB4808–0xB4815`).

| Action byte +4 | Confirmed effect |
|---:|---|
| 0, 1, 2 | Copy command +5 into record +4, +6, +7 respectively (switch after `0xB4815`). |
| 3 | Start, if disabled. Clears the disabled bit, optionally reloads if command +5 is nonzero, and applies list admission at `0xB485C`. |
| 4 | Stop, if enabled. Removes the record and its object when registered, disables the timer and optionally reloads if command +5 is nonzero (`0xB494B`). |
| 5 | Reload with the record's stored operands (`0xB49BA`). |
| 6 | Temporarily replace record +6 by command +5 for this reload, store the result, then restore record +6 (`0xB49D1 → 0xB8B24`). |

See [timer clocks](lol2-timer-clock.md) for the original 60 Hz registration,
the reload census and an elapsed-cell witness in a native save.

### Worked timer

**CONFIRMED.** `L3_DH.MIX+0x593C70` has the row
`0A 02 A0 06 30 01 05 00 2C 01`. It targets group 0x06A0. Status 1
makes it initially disabled. Flags 0x30 and parameter 5 select the fixed
reload `5*60=300`, matching u16 +8 = 0x012C (`0xB8AC4`).

## Predicates and shared bytes

**CONFIRMED.** The geometry loader `0x669D4` reads 5-byte predicate
entries using geometry header offset +0xBC and count +0xB8. All 15 levels
have 255. Runtime pointer/count are at `0x2B548` and `0x2B544`. The
operator is u8 +0. Each operand is a two-byte type/index pair (+1/+2 left,
+3/+4 right). The evaluator `0x66AB0` resolves both operands before
dispatching the operator.

| Type | Left VA | Right VA | Confirmed source |
|---:|---|---|---|
| 0 | `0x66AE6` | `0x66B77` | Literal argument byte. |
| 2 | `0x66B2A` | `0x66BAF` | Indexed byte from `[0x26E58]` (slot-wide shared bytes). |
| 3 | `0x66B15` | `0x66B8C` | Indexed byte from `[0x26E54]` (level-local bytes). |
| 4 | `0x66B47` | `0x66BEC` | Recursive predicate at the argument index. |
| 5 | `0x66B3B` | `0x66BD2` | u8 at `[0xB7D80]+0x25`, independent of the index. Opcode 16 writes the same field at `0xB5A44`. |
| 7 | `0x66B5C` | — | Left returns false for predicate index ≥ 1. At index 0, entry `0xBBB8` passes inherited ESI through `0x66A48`. [Type 7 evidence](lol2-shared-predicates.md#type-7). |
| 1, 6 (and right 7) | `0x66AEB` | `0x66B7B` | **CONFIRMED.** Those slots are the continuation that does not load the operand. Across the 255 rows in each of the 15 levels, the left types are only 0, 2, 3, 4 and 5 and the right types are only 0, 3, 4 and 5. The loader `0x669D4` copies those rows; its only later store into the copy is the operator of row 15 (`[base+0x4B] = 3` when `[0x23331]` is 14). The other uses of the table pointer read it, or free and zero it (`0x9D848`, `[0x2B548]=0` at `0x9D852`). |

Operator IDs 0–7 are equality (`0x66C43`), inequality (`0x66C57`),
signed ≤ (`0x66C6B`), ≥ (`0x66C7F`), > (`0x66C8F`),
< (`0x66CA3`), logical AND (`0x66C10`) and OR (`0x66C2B`).
**CONFIRMED** by the relocated switch and comparison instructions.

**CONFIRMED.** Opcode 198 writes the `0x26E54` buffer at `0x64887`. Opcodes
201 and 207 randomize/add at `0x64906` and `0x648AF`. Opcodes
199, 200 and 206 change the `0x26E58` buffer through `0x64A8C`,
`0x64BB4` and `0x64B1C`. These are the same pointer cells used by
the evaluator. The per-level save switch `0xE8914` uses `0x26E54` in
section 24, and the global save switch `0xE867C` uses `0x26E58` in
section 1. Object binding is explicit in the timer service at `0xB8BD3`. Binding at each other dispatch caller needs a separate check.

**CONFIRMED.** The native name lookups for shared and local slots are
`0x61514` and `0x61560`. They step 41-byte name rows at
`[0x2B4C0]` or `[0x2B4BC]` and return the zero-based index.
The first shared name in the retail archive is `GV_LUTHERS_SOUL`
(`GLOBAL.MIX+0x667C18`, second row starts 41 bytes later).
The caller at `0x9F17B–0x9F193` looks up the same identifier from
`LOLG.DAT+0x1C1D0A` and caches the result. See [shared aliases and guarded branches](lol2-shared-predicates.md#shared-indexes-with-native-names).

### Worked predicate

**CONFIRMED.** `L1_DC.MIX+0x70621C` has `06 04 12 04 0F`. Both
operand types recurse, to predicate 18 on the left and 15 on the right.
Operator 6 then returns 1 only when both results are nonzero. At
`L1_DC.MIX+0x7061BD`, the bytes `00 03 1E 00 00` instead compare
level-local byte 30 to zero.

**UNCONFIRMED.** Some [event producers](lol2-event-producers.md) still need caller-by-caller
tracing. For a computed value, trace
the argument to `0xADDE0` or `0xF2D2C` backward through the first
selecting branch and match its width to the stored record. The [shared predicate page](lol2-shared-predicates.md) maps the type-7 fallback and original branch witnesses.
