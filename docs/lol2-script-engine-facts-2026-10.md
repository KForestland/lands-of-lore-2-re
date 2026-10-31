# LoL2 script engine and runtime facts (2026-10)

Date: 2026-10-31

These facts came out of the Godot rebuild work (September-October 2026), where the
game's own script records are executed by a host that follows the original code.
Each was settled by disassembly of `LOLG.DAT` (sha256 prefix `b27a3534`, version 1.30),
and most were also checked by running the original routine in a small native harness.
They are published here because they answer open questions from the March closure
notes. Addresses are virtual addresses in the flattened LE image.

## Address conventions

- VA = file offset - 0x37000.
- Relocated jump tables decode from 9-byte fixup records `07 10 <srcoff16> 02 <target32>`;
  handler VA = target + 0x59024.

## Script opcodes (dispatch at 0xB6B8D)

| Opcode | Handler | Meaning |
|--------|---------|---------|
| 5 | B5970 | object vtable+0xB0 (obj, byte4, byte5); byte5 = 1 means relative |
| 6 | B598B -> B3EC8 | sub-table at 0x5AE70; sub 1 = animation restart (9F584) |
| 9 | B59B3 -> B50C0 | property set; see below |
| 14 | B47B4 | timer; sub 3 start (no-op if running, arg != 0 reloads), sub 4 stop (keeps the counter) |
| 16 | B5A3C | state byte at object +0x25 |
| 17 | - | add a signed byte to owner state, clamped |
| 19 | B6B5F -> 66130 | hit/damage record; see below |

op9 properties: 2 unlink, 3 link, 16 stop sound, 17/18 set/clear flag 0x4000,
19 durability byte +0x26 = byte5, 21 raise event 20.

op19: target masks are command bytes 4-7 (mask bit 0x10 = fire). Damage by byte 9:
0 -> byte 8 as a value, 1/2 -> percent via vtable 0x8C/0x88. Delivered through the
target's vtable+0x80, gated by flag 0x400, then the hit filter AE2C8.

## Timers

- Timer records are periodic: start enables without resetting the counter, stop keeps it,
  expiry reloads with carry.
- The clock runs at 60 ticks per second. Duration flags: 0x20 fixed byte6, otherwise a random
  value between byte7 and byte6; 0x10 = seconds (x60); 0x80 = minutes (x60x60); otherwise
  1/256-tick units.

## Record kinds and events

- Record kind 9 is the hit filter (AE2C8), not event 9. It enqueues at most one record per hit;
  a record whose byte +9 was cleared after enqueue admits nothing.
- Event 9 is a kind-6 record with byte4 = 9 (ADF34). Kind-6 value 3 = animation end.
- Region kind-11 records are movement events (F2FC0): start events 0-3, end events 4-7. In the
  Hive this drives the ceiling-collapse chain once read as a "pit trap".
- Object lifecycle: link sets 0x10000 and adds to the active list (0x20000000); unlink sets 0x1000;
  destroy (B6B98) sets 0x800000. The per-frame loop B30AC calls B286C for each active object.

## Transformation curse

- No global timer. Script subs 0x13 random, 0x15 lizard, 0x16 beast, 0x17 human.
- Duration byte5 gives 15*lo to 15*(lo+hi) seconds. Zone curses run from prop timer records.
- The morph animations are 22-frame WSAs in LOCAL.MIX.

## Static object collision

- The base initializer AE990 copies placement word 8 to object +0x14; bit 0x80 = solid.
- The shape comes from the template (stride 60): byte 0x2D & 3 selects none / special /
  oriented box; half-sizes at template bytes 0x2F (x) and 0x30 (depth), rotated by the object
  heading at +0x1E and grown by the mover radius.
- Player movement itself is region-based; drawn interior walls are not all colliders.

## Still open

- The caller paths for control and prop events.
- Opcodes 196/204 (heavy in Acts 2-3): now partly decoded, see the
  [addendum](lol2-script-engine-facts-2026-10-addendum.md).
- Wall-source provenance is closed for one traced span
  ([wall material provenance](lol2-wall-material-provenance.md)); texture flags other than 0xA9
  and HMI-MIDI conversion remain open.
