# LoL2 script engine facts: addendum (late October 2026)

Date: 2026-10-31

For the current checks and corrected matcher arms, see the [opcode table](lol2-script-opcodes.md),
[event reference](lol2-script-events.md) and [combat rules](lol2-combat-ai.md).

This adds to [`lol2-script-engine-facts-2026-10.md`](lol2-script-engine-facts-2026-10.md) and uses the same
conventions: `LOLG.DAT` 1.30 (sha256 `b27a3534...`), VA = file offset - 0x37000, relocated jump tables
decoded from LE fixup records (an object-2 target offset + 0x59024 is the handler VA). The data layout is in
[`lol2-level-script-format.md`](lol2-level-script-format.md).

Sources: static disassembly notes (byte-cited, read-only), checked
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
    during a given walk depends on its binding call. Timer walkers store the object at `0xB8BD3`. The +0xB8 slot of every class vtable (`0x5484`, `0x573C`, `0x58D0`, `0x59C8`, `0x5AD8`, `0xA848`) is `0xB71A0`, which stores it at `0xB71B2` when object +0x15 bit 0x10 is clear. **CONFIRMED.** The LE direct-fixup census for `0xB7D80` gives these two stores and five readers at `0x5FD29`, `0x66BD2`, `0x66B3B`, `0xADEB9` and `0xAE3D4`.
  - left type 3 = the byte at `[cell 0x26E54 + byte 2]`. The cell's name stays LIKELY at most.
- **CONFIRMED.** The [predicate reference](lol2-script-events.md#predicates-and-shared-bytes) verifies all eight operator arms at `0x66C10–0x66CA3`, the two array readers and recursive operands. Operand types 1 and 6 (and right type 7) assign nothing; that row keeps their use **UNCONFIRMED** and gives the archive search that would settle it. No producer test exists yet.

## Kind-19 trailer

A record of kind 19 (`04 13 pp pp`) directly after an event record is that record's predicate; word +2 is
the index. It is not a command group. The matchers for record kinds 4, 5, 6, 8, 9 and region kind 12
compare the next record's kind byte with 0x13 and, if equal, call 0x66AB0 with the zero-extended word; the
record only runs when the predicate is true. A record without a trailer has no predicate. (PROVEN) Whether
other, unentered kinds test a trailer is UNKNOWN. To settle these, locate each kind’s native matcher and verify a comparison of the next row’s kind with 0x13.

## Record kinds and their runners

Event-record lists are walked as `rec += [rec+0]`, kind = `[rec+1]`, kind 0 ends (PROVEN). Groups run
through `0x646EC(group + [0x2B514])`.

| Kind | Layout | Runner | Rule |
|---|---|---|---|
| 2 | timer rows | 0xB47B4 | op14 timer operations (see the facts doc) |
| 4 | `0a 04 gggg mode inv dword` | `0xADBCC` entry, `0xADD36` mode dispatch | Byte +4 indexes modes 0–7. Mode 3 compares held-item identity +0x18 (`0xADC84–0xADC8F`). Other tests use class +0x3F bits, word +0x3D bits, byte +0x43 bits or byte +0x45 equality. Byte +5 = 0 leaves the result uninverted (`0xADC47`). Mode 0 tests for absence of the held item without using the dword at +6 (`0xADC01`, `0xADC41`). (PROVEN) |
| 5 | `06 05 gggg event value` | 0xAD8E0 | runs every record with `[rec+4] == event` and (`value == 0xFF` or `[rec+5] == 0xFF` or `[rec+5] == value`), predicate checked; all matches run. (PROVEN) |
| 6 | `06 06 gggg value` | 0xADDE0 | `[rec+4] == value` (byte compare). (PROVEN) |
| 7 | `06 07 gggg mode thr` | 0xAE134 | health thresholds over hit points before / after; all matches run. Modes 0 through 3 are countdown, crossed down, crossed up and equal respectively (`0xAE162–0xAE1F7`, **CONFIRMED**). |
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
  natively, entry 0 of the mode table at `0xAE2B4`, used by the jump at `0xAE44E`, is `0xAE369`, which does not admit the record and moves on to the next one).
- One hit enqueues at most one kind-9 record of a list, in list order: the scanner stops at the first record
  that fires, so later records and their predicates are not consulted. (PROVEN)
- When the byte at 0x23331 is 5 (read as the level index, i.e. the Hive) and the attacker is in pool 0xDB590, a
  mode-4 record is disabled instead of firing. (**CONFIRMED.** The pool is used for props. The selector at `0x5FC43` reads `0xDB590`; `0xF2128–0xF216D` builds the 37-byte placement rows into it.)
- The names of context fields beyond those above, and whether kind 9 is a "bash", are UNKNOWN. Compare the inputs to `0xAE2C8` after two distinct original attack actions and match context words to their producers.

## Opcode 196

The [motion page](lol2-script-motion.md#opcode-196) resolves the eight stores and traces the height update.

Length 12. Not in the low table. `0x64770` compares the opcode byte down a branch tree and, for 0xC4, jumps
to an arm that pushes the dispatcher's second argument and the command pointer and calls `0x64DDC`; the arm
stores nothing itself and returns the callee's result. (PROVEN)

- `0x64DDC` zero-extends the word at command +2 and computes `word * 44 + [0x22D0C]`: a 44-byte record
  in a table whose base dword is at 0x22D0C. (PROVEN) No bound check on the word. The selector and stride identify the geometry region table (`0x5FCE6`).
- It uses command bytes +4 (signed word), +6 (flag bits 0, 2, 3, 4), +7, +8 (word) and +0xA (signed word),
  and the word at record +0x28 (bits 0x40 / 0x80), +0x12..+0x16 and byte +0x27. It also scans other
  queued opcode-196 commands (through 0x664E4 over a list at 0x26E88; call site `0x64EDA–0x64EDF`) with the same record index. (PROVEN)
- It returns 1 or 0; every return path is PROVEN (for example, the tail returns 1 when the word at
  command +0xA is 0 and 0 when it is not).
- The gameplay meaning is open. **CONFIRMED.** `0x22D0C` is the region table (`0x5FCE6`), `0x22C54` holds the frame delta at `0xE0C5C–0xE0C73`, and `0x9CC23` initializes the list header at `0x26E6C`. Queue iteration at `0x664E4` consumes the header at `0x26E88`. To resolve the remaining queue element roles, compare the entry at `0x664E4` with the allocation written by the command buffer setup.

Use: opcode 196 is heavy in L9_DR, L14_HT and L16_CA and nearly absent in Act 1.

## Opcode 204

Length 8. Handled in `0x64770` at 0x647B3, entered only for 0xCC; the second argument is not used.
(PROVEN) The signed word at command +4 picks one of three arms; each returns 1:

- -1 (`FF FF`): record = `word(+2) * 44 + [0x22D0C]` (same table as opcode 196). Calls `0xF44CC`, which
  stores command byte 6 at record +0x20 and the byte `[[0x22D44] + byte6 * 24 + 0x15]` at record +0x27, then
  calls 0xB861C. Further writes in 0xB6D98 / 0xF4FD0 are UNKNOWN; follow arguments from `0xB861C` into those two callees and log writes to that exact region and its linked wall rows. (PROVEN up to that point)
- -2 (`FE FF`): same record; stores command byte 6 at record +0x22. Its only store. (PROVEN)
- other: entry = `signed word(+4) * 8 + [0x22D08]`; stores the word at command +6 at entry +0 and ORs 0x40
  into entry byte +5. (PROVEN) No range test.

**CONFIRMED.** `0x22D08` is the [8-byte wall table](formats/walls.md) selected at `0xF4370–0xF438E`; `0x22D0C` is the 44-byte region table (`0x5FCE6`). The 24-byte table at `0x22D44` provides the byte for region +0x27 and is updated at `0xA053E → 0x67460`. Its remaining fields are UNKNOWN; follow the active row after the bit-0 gate at `0x67489`. Opcode 204 has 1,348 uses across the 15
levels; opcode 13 has 1,452 and opcode 3 has 1,086. Opcodes 13 and 3 share the low-table handler 0xB5937,
which calls the object's `vtable+0xAC`. **CONFIRMED.** Props constructed by `0xF20C3` use `0xF22B4`, which returns immediately unless the command begins with byte 8. The [current opcode table](lol2-script-opcodes.md) covers the other named opcode-13 class slots. Follow command 3 through each +0xAC callee for its remaining encounters.

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
- The tail of the opcode 204 -1 arm.
- The names of the 44-byte table at 0x22D0C and of the other unnamed globals above.
- The `vtable+0xAC` callee shared by opcodes 3 and 13.
