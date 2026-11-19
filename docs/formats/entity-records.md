# 147-byte entity records

**CONFIRMED.** A level's ODF entry holds a table of 147-byte creature
definitions. Its 135-byte record body is followed by a 12-byte type tag.
The file tag resolves to a runtime profile pointer. These are separate
from the geometry entry's placed actor records.

## Identify the table

**CONFIRMED.** At `0x9C43C–0x9C468` the level loader appends the
suffix `.odf` from `LOLG.DAT+0x1C1C28` to the level resource stem
before calling `0x9DFB8` at `0x9C486`. In all 15 MIX directories,
the corresponding key is the original rotate/add hash of
`SPHERE<n>\<LEVEL>\<LEVEL>.ODF`, with sphere 1, 2 or 3 as shown below.

The reader opens that stream at `0x9DFEF`, reads its 0x204-byte header
and checks dword +0 against 18 (`0x9DFF9–0x9E012`). Header u32 +0x10
is the absolute seek relative to the ODF stream (`0x9E152–0x9E15A`).
Header u32 +0x48 is the count passed into the record loader
(`0x9E162–0x9E16E`). At `0xA1C61–0xA1C82` the loader reads 135
body bytes and 12 tag bytes once per row. It resolves the tag through
`0x5A268` at `0xA1C94`, writes the profile pointer to the runtime
record at +0x87 (`0xA1CAF`) and advances memory by 139 bytes
(`0xA1D4D`). The disk stride remains 147.

| MIX | Sphere | Entry / key | ODF file offset | Table offset in ODF | Record count |
|---|---:|---|---:|---:|---:|
| `L1_DC.MIX` | 1 | 0 / `0xB1162802` | `0x70C150` | `0x6C4B` | 11 |
| `L3_DH.MIX` | 1 | 0 / `0xB9203816` | `0x5A51D9` | `0x67BF` | 5 |
| `L4_HJ.MIX` | 1 | 0 / `0xDD24481E` | `0xCA0BD7` | `0xB8B6` | 13 |
| `L5_HC.MIX` | 1 | 0 / `0xE1165002` | `0x5B8CA2` | `0x6525` | 6 |
| `L7_DH.MIX` | 1 | 0 / `0xC9205816` | `0x4CB7CD` | `0x67DC` | 5 |
| `L8_SJ.MIX` | 2 | 0 / `0x45347E1D` | `0xD21458` | `0x9DD7` | 18 |
| `L9_DR.MIX` | 2 | 0 / `0xD144683E` | `0x1673D89` | `0xE706` | 8 |
| `L10_DC.MIX` | 2 | 1 / `0xC85D0B86` | `0xD1F0A9` | `0xC671` | 6 |
| `L12_CM.MIX` | 2 | 1 / `0xC47D6392` | `0x992F5B` | `0x37AF` | 10 |
| `L13_RC.MIX` | 2 | 1 / `0x008D17F7` | `0x6A77FB` | `0x27CA` | 4 |
| `L14_HT.MIX` | 2 | 1 / `0xD89DA3C8` | `0xB526CF` | `0x8620` | 6 |
| `L16_CA.MIX` | 3 | 1 / `0xC4DD137A` | `0x122BC60` | `0xB8E0` | 6 |
| `L17_HC.MIX` | 3 | 1 / `0xD8ED27A6` | `0x4A1060` | `0x23B4` | 4 |
| `L19_BC.MIX` | 3 | 1 / `0xC10D2F76` | `0x6063EF` | `0x217B` | 7 |
| `L20_BB.MIX` | 3 | 1 / `0xC07D1378` | `0xEFD7D1` | `0x3617` | 19 |

## Worked example

**CONFIRMED.** `L1_DC.MIX+0x70C150` begins the ODF stream. The two
header values are `0x6C4B` at file `+0x70C160` and 11 at
`+0x70C198`. This yields 11 records in
`[0x712D9B, 0x7133EC)`. The first record's tag starts at
`0x712E22`. The table bounds and count are read directly by the
entity and level-sheet tools.

```bash
python3 tools/lol2_entity_field_analyzer.py --data DAT --check
```

The check reads 128 definitions in the 15 original ODF tables.
The older [body field notes](../lol2-entity-object-map.md) include
**UNCONFIRMED** field names. For another body field, follow the row selected by the placement at `0xA22AF–0xA22BE` through actor initialization, and match a read of the same displacement before assigning a role.
