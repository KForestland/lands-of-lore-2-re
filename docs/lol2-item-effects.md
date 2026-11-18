# LoL2 item grants and use effects

The original DOS 1.30 executable is identified in
[executable addresses](lol2-executable-tables.md). Item definition indexes
in this page are zero-based. Item identities are little-endian u32 values.

## Definition and object

**CONFIRMED.** Entry `0xED7EC08D` of `GLOBAL.MIX` starts at
`0x5B76F9`. Entry +4 contains 0x1F0 and +0x34 contains 170. Therefore
definition `i` starts at `MIX+0x5B78E9+91*i`. Native identity lookup
`0x9EB5C` steps 0x5B bytes and compares definition dword +0x18.
The [item format](lol2-item-format.md) documents the remaining definition
fields and the archive's following tables.

The native item instance begins with a definition pointer and byte fields
+4/+5. The copy at `0x95804` preserves both bytes. The constructor path
at `0x9B8D4–0x9B8E7` calls that copy and zeroes instance dword +8.
The use dispatcher `0x95840` reads the handler index from definition
byte +0x42 and dispatches through object-5 `0xC860` (file `0x1CD884`).
Handler 0 at `0x95874` returns zero.

## Script grants

**CONFIRMED.** The player table's +0xAC slot at
`LOLG.DAT+0x1C6CF0` resolves to `0xD7890` via the fixup at `LOLG.DAT+0x7EADF`. A command with
opcode 3 reaches that slot through `0xB5937`. The player arm requires
`[0x223D4] == 0` and calls
`0x95B68(player, u32(command+4), u8(command+8), 1)`
at `0xD78B8–0xD78D9`. A null result leaves the command unhandled.
The item helper performs the following operations.

| Operation | Native evidence |
|---|---|
| Look up the 91-byte definition by identity | `0x95B80 → 0x9EB5C` |
| Copy command +8 into the temporary instance's byte +4 and initialize +5 to zero | `0x95B91–0x95B99`, copied to the new item by `0x9B8DF → 0x95804` |
| Allocate a 12-byte payload from the player item pool `[0x96918]` when the recipient is the player | `0x95BA4–0x95BC7` |
| When the fourth argument differs from 2, call recipient vtable +0x6C and notify `0xA98F8` with the identity | `0x95BF4–0x95C12` |
| Player +0x6C uses the hand-slot helper and inventory routine, then keeps a nonzero pending pointer under an additional condition | `0xD259C`, calls `0x77ACC` and `0x8FD40`, conditional store at `0xD25FD` |

The copied byte's meaning can depend on the item. **UNCONFIRMED.** The
grant path establishes where the raw byte goes. The interpretation of each
observed value, such as whether it becomes a charge count for a particular
handler, requires that handler's read of instance +4.

**CONFIRMED.** Across the 15 original level archives, opcode 3 with
selector 1 occurs 876 times. All 876 identities resolve to the 170
definitions. Arguments at command +8 are 0 (34 occurrences), 1 (129),
3 (17), 4 (695) and 5 (1). The count comes from both framed streams
using the [script disassembler](lol2-script-opcodes.md#worked-disassembly-and-corpus-check).
It counts command sites. Each site's event and predicate determine
admission, as described in [script records](lol2-script-events.md).

### Reproduce the grant census

Set `LOL2_DAT` to the original game's `DAT` directory. The adjacent
`GLOBAL.MIX` must contain the item definition entry described above.

```bash
PYTHONPATH=tools python3 - "$LOL2_DAT" <<'PYTHON'
from pathlib import Path
from struct import unpack_from
from sys import argv

from lol2_disassemble_scripts import EXPECTED_LEVELS, select_archive
from lol2_export_scripts import export
from lol2_source_format import parse_mix

dat = Path(argv[1])
global_mix = (dat.parent / "GLOBAL.MIX").read_bytes()
entry = next(row for row in parse_mix(global_mix) if row["key"] == 0xED7EC08D)
offset = entry["offset"]
base = offset + unpack_from("<I", global_mix, offset + 4)[0]
count = unpack_from("<I", global_mix, offset + 0x34)[0]
identities = {unpack_from("<I", global_mix, base + 91*i + 0x18)[0]
              for i in range(count)}
grants = 0
for level in EXPECTED_LEVELS:
    result = export(select_archive(dat, level))
    for group in result["groups"]:
        for command in group["commands"]:
            if (command["opcode"], command["kind"]) == (3, 1):
                raw = bytes.fromhex(command["raw_hex"])
                assert unpack_from("<I", raw, 4)[0] in identities
                grants += 1
print(f"{grants} grants checked against {len(identities)} identities")
PYTHON
```

Expected output is `876 grants checked against 170 identities`.

### Worked grant

**CONFIRMED.** `L9_DR.MIX+0x16291DE` has bytes
`03 01 00 00 01 5D 47 D9 01 00 00 00` in stream 1 group 16722.
The identity 0xD9475D01 resolves to definition 168 at
`GLOBAL.MIX+0x5BB4A1`. The command's +8 value is 1, which the above
arm copies to the new instance's +4. To learn which event reaches the
group, search the same listing for `S1:4152`, the hexadecimal group offset.
For example, kind-4 record `L9_DR.MIX+0x162C24C` points to that group
and has predicate trailer index 5.

## Selected item-use handlers

**CONFIRMED.** These cases follow the dispatch table, the definition bytes,
and the original handler. Mappings for other items can be read from the same
definition byte and dispatch table.

| Definition and archive offset | Handler | Mode and effect |
|---|---|---|
| 8, `GLOBAL.MIX+0x5B7BC1` | 1 → `0x95FF0` | Mode 5 plays the strike sound, then draws through `0x15CB4B` at `0x96026` and checks `(rng & 0x11) == 0x11` at `0x9602B–0x96031`. On success and a successful template 0x6E lookup it calls `0x102EA4`. The handler returns zero even after the call, so the normal strike can continue at `0x88F8F`. |
| 75, `GLOBAL.MIX+0x5B9392` | 32 → `0x96CC8` | Mode 1 frees a held instance through the pool that contains it (`0x96CDD–0x96D40`), checks acquired-school ID 1, and calls `0x10A9D0` at `0x96DA6` when a target context and template 0xC2 resolve. |
| 148, `GLOBAL.MIX+0x5BAD85` | 31 → `0x96C08` | Mode 1 checks acquired-school ID 2. The known-school branch clears byte `0x22729` and calls `0x7C7DC` and `0x7EB40`, the latter with 50 (`0x96CA1–0x96CB5`). |
| 149, `GLOBAL.MIX+0x5BADE0` | 12 → `0x96DB8` | Mode 1 checks acquired-school ID 0. The known-school branch calls `0x10C6BC(1, player)` at `0x96E52`. |
| 151, `GLOBAL.MIX+0x5BAE96` | 33 → `0x96E7C` | Mode 1 checks acquired-school ID 3. If player byte `0x2271F` equals 1, the known-school branch resolves template 0x5E and calls `0x1028A4` at `0x96F41`. The alternative calls `0xDD260`. |

For the scrolls, the common school check at `0x8619C` can permit the
effect or dispatch a lesson. The item removal is earlier in the handler.
See [spell acquisition](lol2-spells.md#acquisition).

**UNCONFIRMED.** The broad mechanics of most handler indices and all
per-item descriptor operations still need decoding. The table offsets
and dispatcher call at `0x95865` locate each handler. Each handler
tests its own mode byte, for example `0x95FFA` in handler 1.
