# LoL2 item definitions and the item-use dispatcher

Date: 2026-10-31

Field layout only. No item names, text or icons are reproduced here; read them from your own
`GLOBAL.MIX`. Addresses follow [`lol2-script-engine-facts-2026-10.md`](lol2-script-engine-facts-2026-10.md):
`LOLG.DAT` 1.30 (sha256 `b27a3534...`), VA = file offset - 0x37000. Labels: PROVEN (bytes read),
INTERPRETATION (a reading of proven calls), UNKNOWN.

## Where the table is

- Archive `GLOBAL.MIX` (retail sha256 prefix `1e3e2a46`), entry key **3984507021** (0xED7EC08D).
- Entry header: dword +4 = offset of the definition table (496 in retail), dword +0x34 = count (**170**).
- Records are **91 bytes**, back to back. After the table comes a u32 count and a table of 16-byte selector
  rows, then a u32 count and 12-byte view rows, then 30-byte name rows (24-byte name field). The selector
  and view walk is the one the port's icon producer uses; it yields 165 decodable icons with matching sizes.

Verified by running on retail files (2026-10-31): count 170 at +0x34, base 496, the selector-table count
after the last record, 47 records with handler index 0, highest handler index 107, and 37 records with
class byte 0x44 or 0x48.

## Record fields

| Offset | Size | Field | Status |
|---|---|---|---|
| +0x18 | u32 | identity (unique per record; kind-4 mode test) | PROVEN |
| +0x2E, +0x2F (46, 47) | u8, u8 | selector counts used to walk the selector table | PROVEN by use (icon producer) |
| +0x37 | u16 | strike sound id; read at 0x88F91 and passed to 0xE3924 when nonzero | PROVEN |
| +0x3B | u16 | mask word, copied to hit context +0 (matched by kind-9 word +4) | PROVEN |
| +0x3D | u16 | flags word, copied to hit context +2 (matched by kind-9 word +6) | PROVEN |
| +0x3F | u8 | class byte; kind-4 tests its bits | PROVEN read; slot meaning below is INTERPRETATION |
| +0x41 | s8 | read as a defence value by the Godot port | native reader not traced (UNKNOWN) |
| +0x42 | u8 | handler index into the item-use table (0 = no handler) | PROVEN |
| +0x43 | u8 | bit 0 = "magic" class, bit 1 tested by kind-4 matcher 0xADCDB | PROVEN reads; names INTERPRETATION |
| +0x44 | u8 | post-hit addend: after a strike, `[0x22C5A] + addend` is returned (halved when `[0x2270E] & 0x400`) | PROVEN value; meaning (speed/recovery) UNKNOWN |
| +0x45 | u8 | compared whole by kind-4 mode 0xADCFB | PROVEN |
| +0x47 | 4 x 5 | descriptor rows (byte, u16, u16); all zero on the plain swords | layout PROVEN by use; ops UNKNOWN |
| others | | +0x1C, +0x20, +0x29..+0x2D, +0x39, +0x40, +0x46 and the rest | UNKNOWN |

Class byte values seen: 0x44 hand weapons, 0x48 thrown/ranged, 0x50/0x53 shields and bracers, 0x60 body
armour, 0x43 rings/amulets/gauntlets, 0x40 other (grouping by item, INTERPRETATION; the native reader of
the class byte as an equipment slot is not traced).

## Item-use dispatcher 0x95840 (PROVEN)

```
95840  push ebx
95841  edx = request, eax = item object; eax = [eax]   ; the definition record
9584e  al = definition byte +0x42                       ; handler index
95851  if [edx+1] == 0: [edx+1] = 0x22574              ; default actor = the player object
95864  call [0xC860 + 4*index](item object, request)   ; nonzero = handled / consumed
```

- The handler table at 0xC860 holds 107 handlers (indexes 1-107); index 0 is a stub. Its dwords are relocated; the handler VA comes
  from the LE fixup at slot `0xC860 + 4*index` (object-2 target + 0x59024). Handler 0 resolves to a stub at
  0x95874 (`xor eax, eax; ret`), so items with index 0 always take the ordinary path. (PROVEN)
- Request struct (0x19 bytes, zeroed by every caller): `+0` mode byte, `+1` actor (u32, default 0x22574),
  `+5` target/context object (u32). (PROVEN layout; `+5` always being the world target is UNKNOWN)
- Every handler begins with a compare on the mode byte and returns 0 for modes it does not accept.

### Modes (callers of 0x95840)

| Mode | Called from | Meaning |
|---|---|---|
| 1 | interface click handler 0x7DB54; inventory-slot routine 0x8AA60 | use / consume (PROVEN for handlers 2, 6, 8, 9, 10, 11, 12, 16) |
| 5 | melee strike 0x88D2C, with the equipped weapon | on-strike hook; a nonzero return skips the ordinary hit (PROVEN) |
| 6 / 13 | same strike function; 13 when a poison-coat counter is nonzero | swing notification, plain or coated (INTERPRETATION) |
| 8 | 0x797A4 | timer maintenance for one handler (PORT-documented) |
| 10 / 11 | equipment slot routines | slot in / slot out for passive items (INTERPRETATION) |
| 12 | 0x7DB54, after the weapon-ring hit test | item dropped on the weapon circle (PROVEN for the coat handlers) |
| 16 | several world-interaction routines, always with the hand item | hand item applied to a world object (INTERPRETATION) |
| 18 | 0x942A8 and the player update 0xD0F2C | periodic tick for carried items (INTERPRETATION) |
| 0, 9, 14, 15, 17 | various | UNKNOWN |

Handlers read by hand so far: the two poison-coat handlers (mode 12 adds one coat, up to 9; mode 1 hits
the player with the coat flag), the on-strike handlers for two weapons (modes 5), the passive slot
handlers (modes 10/11, writing player flag words 0x2270E / 0x22712), and the consumables the port hosts.
The other handlers are listed only by their head compares and calls. (Source: an automated per-handler scan
plus hand reads; effects not read stay UNKNOWN.)

## Weapon damage path (vertical slice, PROVEN where marked)

Traced for two plain swords (handler 0, mask 0x0002, flags 0x0004) and the empty hand (mask 0x000A, flags
0x000C):

1. UI sites call the strike `0x88D2C(0x23348, 0)`. Reach does not read the weapon (0x136594 distance;
   limit 0x40 or 0x80 << 16 depending on byte 0x2271F). Byte 0x23C2D must be 1, 8 or 9. (PROVEN)
2. Mode 5 goes through 0x95840; handler 0 returns 0, so the ordinary hit runs. (PROVEN)
3. The attack amount at hit context +0x16 is `[0x236DC] + [0x236E4] + [0x236EC] + [0x236F4] + sar([0x2372C], 24)`.
   (PROVEN; the names of these terms are UNKNOWN. One handler adds 20 to `[0x236E4]` while active.)
4. The target's `vtable+0x80` runs the damage function 0x62728; the final damage is stored at context +0x1E
   by 0x62EC9. Before the creature-side descriptor loop, the amount is scaled by byte 0xB7FB2 (0: x2, 1:
   unchanged, 2: halved above 2), then by a ratio against the target's scalar unless flag bit 0x08 is set or
   the mask is zero, then divided by the number of mask bits (and of `flags & 0xE7` when that is above 1).
   (PROVEN)
5. Damage is clamped to current hit points: `ctx+0x1E = min(damage, ctx+0x22)`, `ctx+0x26 = max(0, hp - damage)`.
   (PROVEN)

Consequence: two weapons with the same +0x3B / +0x3D words get the same damage from this path; the bytes
that differ between them (+0x1C, +0x20, +0x29..+0x2D, +0x39, +0x40, +0x46) are not read on it. (PROVEN for
the slice)

UNKNOWN: the relocated descriptor-op table at 0x96E0 used by `jmp [ecx*4 + 0x96E0]` at 0x62E6B (the
creature-side loop that runs for live targets), the writer of creature byte +0xA7 (the scalar), the names
of the attack-sum terms and of byte 0xB7FB2, what `[0x22C5A]` counts, and the runtime value of 0x23C2D.
No random-number call appears on this path before the descriptor callbacks.

## Still open

- Descriptor ops (+0x47 rows and the 0x96E0 table).
- Effects of most of the 107 handlers.
- The remaining undecoded record bytes.
