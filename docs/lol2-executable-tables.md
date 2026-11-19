# LoL2 executable addresses and tables

**CONFIRMED.** This page covers the DOS retail 1.30 `LOLG.DAT` of size
`0x1E2AAF` and SHA-256
`b27a35341c6e877e40b1540b6482748e7a750c605fefe6452431b18a5d766775`.
File +0x100 is `bd 01 68 0c df 07 91 0f df 07 95 0f df 07 89 10`, in the part before the embedded MZ (below); this page does not interpret those bytes, they only pin the copy.
`lol2_cache_seed.py --check` re-reads those sixteen bytes.
The embedded MZ starts at file `0x39024`. Its LE header begins at
`0x3BCB4` with bytes `4C 45 00 00`. LE header +0x28 specifies a
0x1000-byte page. Header +0x80 gives the page-data start relative to the
embedded MZ, 0x56000. The first data page is therefore at file `0x8F024`.
The LE object table starts at `0x3BD78` (LE +0xC4), its page map at
`0x3BDF0` (LE +0x13C).

| Object | Header file offset | LE link base | Logical first page | File-backed pages |
|---:|---|---|---:|---:|
| 1 | `0x3BD78` | `0x010000` | 1 | 1 |
| 2 (main code) | `0x3BD90` | `0x020000` | 2 | 304 |
| 3 | `0x3BDA8` | `0x150000` | 306 | 1 |
| 4 | `0x3BDC0` | `0x160000` | 307 | 0 |
| 5 (data) | `0x3BDD8` | `0x180000` | 307 | 34 |

**CONFIRMED.** The 24-byte LE object records contain six little-endian
dwords. The fields at +0, +4, +8, +0xC and +0x10 give virtual byte size,
LE link base, flags, first logical page and page count. The original maps
logical pages 2 and 307 to physical pages 2 and 307 at `0x3BDF4` and
`0x3C2B8`. Their file starts are `0x90024` and `0x1C1024`.
The addresses in this documentation use three conventions.

| Form | Convert it as follows |
|---|---|
| Code analysis VA `A` | File `A + 0x37000` in the main object. An object-2 relocation target `T` is analysis VA `T + 0x59024`. |
| Object-5 cell `D` | Described relative to object 5. LE-linked address `0x180000 + D`. For a file-backed cell read file `0x1C1024 + D`. |
| MIX offset | Absolute byte position in the named archive. An entry offset is added to its in-entry offset. |

Object 5 has virtual size `0x11DFA0` (file `0x3BDD8`). Its end extends
past its file data. **CONFIRMED.** A reference to a cell such as `0xB7D80`
can identify runtime storage without being a location to seek inside the
executable.

## Selected executable tables

These locations and table roles are **CONFIRMED** by their consumers.

| Table | Disk start | Layout | Native consumer |
|---|---|---|---|
| Low script jump table | `0xEC89C` | 24 dwords starting at opcode 1 | `0xB6B8D` |
| Predicate left/right/operator | `0x9DA50`, `0x9DA70`, `0x9DA90` | Eight code offsets each | `0x66ADE`, `0x66B0D`, `0x66B84` |
| Item-use handlers | `0x1CD884` | 108 dwords, indices 0–107, object-5 +0xC860 | `0x95865` |
| Spell schools | `0x1CCB44` | Two bytes per row (first effect ID, candidate effect count (**UNCONFIRMED** per-row use)), object-5 +0xBB20 | `0xD0F4D` |
| Spell effects | `0x1CC980` | Four bytes per effect, object-5 +0xB95C | `0x7C1AB`, `0xD1060` |
| Damage descriptor switch | `0x99704` | Nine code dwords from object-2 +0x96E0 | `0x62E6B` |
| Global save sections | `0x11F64C` | Twelve dwords, last entry returns without supplying a section | `0xE869B` |
| Level save sections | `0x11F800` | 69 dwords, index 68 is the default and writer uses 0–67 | `0xE8938`, `0xE8390` |

Item definitions themselves are in `GLOBAL.MIX` at entry `0xED7EC08D`,
table file offset `0x5B78E9`. The entry offsets and gameplay dispatch are
described in the [item format](lol2-item-format.md) and
[item effects](lol2-item-effects.md).

## Worked relocation

**CONFIRMED.** The LE fixup page and record tables are at
`0x3C349` and `0x3C89D` (header +0x68 and +0x6C). For object 2 offset
`0x5C878`, add its page index `0x5C` to logical first page 2 to obtain
page 94. The offset within that 4 KiB page is 0x878. At file `0x51C5C`
the corresponding record is `07 10 78 08 02 13 C9 05 00`. In this
32-bit internal offset record, bytes +2/+3 give source offset 0x0878,
+4 is target object 2, and +5..+8 give target 0x5C913. Adding 0x59024
produces handler `0xB5937`. Its physical instruction bytes are at
`0xEC937`. The dispatcher operand has its own fixup at `0x52404`,
which points back to object 2 offset `0x5C878`.

The item dispatcher uses the same fixup format on an object-5 source.
Slot 1 at file `0x1CD888` has fixup `0x8BFEC` to object 2 offset
`0x3CFCC`, yielding `0x95FF0`.

**UNCONFIRMED.** The complete semantics of the damage descriptor switch and
spell effect record byte +2 and the remaining bits of +3 need consumer-specific maps. Follow the derived row pointer at `0xD1035`. The +1 byte is already read as the experience base at `0xD0CDF`. The
ordinary internal fixup examples here establish these table targets.
Other LE fixup record forms require separate decoding.
