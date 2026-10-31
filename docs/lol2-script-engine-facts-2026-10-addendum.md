# LoL2 script engine facts: addendum (late October 2026)

Date: 2026-10-31

This adds to [`lol2-script-engine-facts-2026-10.md`](lol2-script-engine-facts-2026-10.md) and uses the same
conventions: `LOLG.DAT` 1.30 (sha256 `b27a3534...`), VA = file offset - 0x37000, relocated jump tables
decoded from LE fixup records (an object-2 target offset + 0x59024 is the handler VA). The data layout is in
[`lol2-level-script-format.md`](lol2-level-script-format.md).

Sources: static disassembly checkpoints written during the Godot rebuild (byte-cited, read-only), checked
against the retail level archives. Labels are kept as the sources give them: PROVEN (bytes read),
LIKELY / INTERPRETATION (a reading of proven calls), UNKNOWN.

## Predicate table and evaluator 0x66AB0

- Geometry header +0xBC is the offset of a table of 5-byte entries and +0xB8 its count. The loader passes
  them to 0x669D4, which reads count x 5 bytes and stores the count at 0x2B544 and the pointer at 0x2B548.
  (PROVEN) Every retail level has 255 entries.
- `0x66AB0(index)` evaluates entry `index`. Byte 0 = operator, byte 1 = left operand type, byte 2 = left
  operand argument, byte 3 = right operand type, byte 4 = literal used by right type 0. The three type /
  operator jump tables are relocated; their targets come from fixups, not from the raw dwords. (PROVEN)
- Decoded cases (PROVEN):
  - operator 0 = equality;
  - right type 0 = the literal in byte 4;
  - left type 5 = the byte at `[[0xB7D80] + 0x25]` (byte 2 is not read). So `00 05 00 00 NN` is true when
    that byte equals NN. Opcode 16 writes this same object byte (+0x25), but which object 0xB7D80 holds
    during a given walk is UNKNOWN;
  - left type 3 = the byte at `[cell 0x26E54 + byte 2]`. The cell's name stays LIKELY at most.
- Other operators and operand types are not decoded (UNKNOWN).

## Kind-19 trailer

A record of kind 19 (`04 13 pp pp`) directly after an event record is that record's predicate; word +2 is
the index. It is not a command group. The matchers for record kinds 4, 5, 6, 8, 9 and region kind 12
compare the next record's kind byte with 0x13 and, if equal, call 0x66AB0 with the zero-extended word; the
record only runs when the predicate is true. A record without a trailer has no predicate. (PROVEN) Whether
other, unentered kinds test a trailer is UNKNOWN.

## Record kinds and their runners

Event-record lists are walked as `rec += [rec+0]`, kind = `[rec+1]`, kind 0 ends (PROVEN). Groups run
through `0x646EC(group + [0x2B514])`.

| Kind | Layout | Runner | Rule |
|---|---|---|---|
| 2 | timer rows | 0xB47B4 | op14 timer operations (see the facts doc) |
| 4 | `0a 04 gggg mode inv dword` | 0xADC76 | byte +4 is a mode index 0-7 (held-item tests: identity +0x18, class +0x3F bits, word +0x3D bits, byte +0x43 bits, byte +0x45 equal); byte +5 = 0 leaves the result uninverted; mode 0 does not use the dword at +6. (PROVEN) |
| 5 | `06 05 gggg event value` | 0xAD8E0 | runs every record with `[rec+4] == event` and (`value == 0xFF` or `[rec+5] == 0xFF` or `[rec+5] == value`), predicate checked; all matches run. (PROVEN) |
| 6 | `06 06 gggg value` | 0xADDE0 | `[rec+4] == value` (byte compare). (PROVEN) |
| 7 | `06 07 gggg mode thr` | 0xAE134 | health thresholds over hit points before / after; all matches run. Four blocks are proven (countdown, crossed down, crossed up, equal); which mode number selects which block is UNKNOWN. No Act 1 level has a kind-7 record. |
| 8 | `06 08 gggg wwww` | (matcher entered) | u16 at +4 compared with the argument, 0xFFFF = wildcard. (PROVEN) |
| 9 | `0a 09 gggg m0m0 m2m2 thr flags` | 0xAE2C8 | the hit filter, below. |
| 12 | `08 0c gggg rrrr ev val` (region lists) | region matcher | u16 +4 = region index, byte +6 = event; for event 2, byte +7 must be 0. (PROVEN) |
| 0x13 | `04 13 pppp` | - | predicate of the previous record. |

Matcher widths at +4 are not one field: kinds 5 and 6 compare a byte, kind 4 uses a byte as a mode index,
kind 8 compares a u16 with a wildcard, kind 9 tests a u16 mask, region kind 12 compares a u16. (PROVEN)

The take-hit entry `0xB4298(object, ctx)` runs the kind-7 pass, then the kind-9 pass, then, if the attacker
is the player, a kind-5 event chosen by the hit kind: 1 -> event 2 value 0xFF, 2 -> event 3 value
`ctx+0x15`, 5 -> event 0x14 value 0xFF. Only objects with `[obj+0x14] & 0x400` dispatch. (PROVEN)

### Kind 9 (hit filter 0xAE2C8)

- Word +4 is a mask against hit context word +0 (the weapon definition's word +0x3B), word +6 a mask against
  context word +2 (definition word +0x3D plus coat bits 0x20/0x40). A zero mask is a wildcard; otherwise a
  shared bit is required. (PROVEN)
- Byte +8 is a threshold, the low 3 bits of byte +9 select a mode (above 4 rejects), bit 7 of byte +9 makes
  the record one-shot (byte +9 is cleared after it fires). (PROVEN)
- Mode 1: fires when the threshold <= the hit's final damage (`ctx+0x1E`). Mode 4: fires when hit points
  after the hit (`ctx+0x26`) <= the threshold. (PROVEN) Mode 3 = cumulative damage, remainder stored back
  in byte +8 (INTERPRETATION from the record series). Mode 2 = hit points crossed the threshold downward
  (INTERPRETATION). A cleared mode byte (0) does not admit (stated as PROVEN in the 2026-10-31 walk rule;
  an earlier contract left mode 0 UNKNOWN).
- One hit enqueues at most one kind-9 record of a list, in list order: the scanner stops at the first record
  that fires, so later records and their predicates are not consulted. (PROVEN)
- When the byte at 0x23331 is 5 (read as the level index, i.e. the Hive) and the attacker is in pool 0xDB590, a
  mode-4 record is disabled instead of firing. (PROVEN bytes; the pool's identity is UNKNOWN.)
- The names of context fields beyond those above, and whether kind 9 is a "bash", are UNKNOWN.

## Opcode 196 (PARTIAL)

Length 12. Not in the low table. `0x64770` compares the opcode byte down a branch tree and, for 0xC4, jumps
to an arm that pushes the dispatcher's second argument and the command pointer and calls `0x64DDC`; the arm
stores nothing itself and returns the callee's result. (PROVEN)

- `0x64DDC` zero-extends the word at command +2 and computes `word * 44 + [0x22D0C]`: a 44-byte record
  in a table whose base dword is at 0x22D0C. (PROVEN) No bound check on the word. The table's name is
  UNKNOWN (44 is also the geometry region stride, but that link is not proven).
- It uses command bytes +4 (signed word), +6 (flag bits 0, 2, 3, 4), +7, +8 (word) and +0xA (signed word),
  and the word at record +0x28 (bits 0x40 / 0x80), +0x12..+0x16 and byte +0x27. It also scans other
  queued opcode-196 commands (through 0x664E4 over a list at 0x26E88) with the same record index. (PROVEN)
- There are 45 memory stores in `0x64DDC`. 37 have a proven condition and value. 8 (S20, S22, S30, S34,
  S36, S37, S40, S43) take a value after a call that was not entered (0xF2FC0's callees, 0xF3A5C), so they
  are UNKNOWN. The checkpoint is therefore marked incomplete. (PROVEN count)
- It returns 1 or 0; every return path is PROVEN (for example, the tail returns 1 when the word at
  command +0xA is 0 and 0 when it is not).
- The gameplay meaning is not claimed. Names of 0x22D0C, 0x22C54, 0x26E88 and 0x26E6C are UNKNOWN.

Use: opcode 196 is heavy in L9_DR, L14_HT and L16_CA and nearly absent in Act 1.

## Opcode 204

Length 8. Handled in `0x64770` at 0x647B3, entered only for 0xCC; the second argument is not used.
(PROVEN) The signed word at command +4 picks one of three arms; each returns 1:

- -1 (`FF FF`): record = `word(+2) * 44 + [0x22D0C]` (same table as opcode 196). Calls `0xF44CC`, which
  stores command byte 6 at record +0x20 and the byte `[[0x22D44] + byte6 * 24 + 0x15]` at record +0x27, then
  calls 0xB861C. Further writes in 0xB6D98 / 0xF4FD0 are UNKNOWN. (PROVEN up to that point)
- -2 (`FE FF`): same record; stores command byte 6 at record +0x22. Its only store. (PROVEN)
- other: entry = `signed word(+4) * 8 + [0x22D08]`; stores the word at command +6 at entry +0 and ORs 0x40
  into entry byte +5. (PROVEN) No range test.

The tables at 0x22D08, 0x22D0C and 0x22D44 are unnamed (UNKNOWN). Opcode 204 has 1,348 uses across the 15
levels; opcode 13 has 1,452 and opcode 3 has 1,086. Opcodes 13 and 3 share the low-table handler 0xB5937,
which only calls the object's `vtable+0xAC` (callee UNKNOWN).

## Other opcode effects proven in the same pass

- Opcode 1 on mode 6 writes `(mode-6 angle word * byte 4) / 100` to the low word at object +0x50
  (percent 100 -> 21845).
- Opcode 5 stores the selector at object byte +0x3D when command byte 5 is 0.
- Opcode 16 stores command byte 4 at object byte +0x25 (the byte read by predicate left type 5).
- Opcode 20 calls 0xE3924 with the request u16 (a sound-bank request).
- Opcode 198 stores command byte 5 at `[0x26E54] + command byte 4` (bytes `a1546e0200 8a5304 01c2 8a4305 8802`).
  Predicate left type 3 also reads a byte addressed from cell 0x26E54 and an index byte; whether the two
  are the same array is not proven here.
- Command kind byte 0x20 selects object-5 cell 0x2B500.

## Still open

- Remaining predicate operators and operand types; kind-7 mode numbering; kind-9 mode 0/2/3 confirmation.
- The 8 open stores of opcode 196 and the tail of the opcode 204 -1 arm.
- The names of the 44-byte table at 0x22D0C and of the other unnamed globals above.
- The `vtable+0xAC` callee shared by opcodes 3 and 13.
