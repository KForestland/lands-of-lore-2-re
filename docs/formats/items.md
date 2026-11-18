# Item definition table

**What:** the 170 item types: one 91-byte record each, plus the tables the game uses to pick each item's icon. Full field notes and the item-use dispatcher: [lol2-item-format.md](../lol2-item-format.md).

**Read:** `DAT/GLOBAL.MIX`, entry key 3984507021 (0xED7EC08D). Tool: `tools/lol2_mix_parser.py` to extract the entry.

## Layout

| Where | Type | Meaning |
|---|---|---|
| entry +4 | uint32 | offset of the definition table (496) |
| entry +0x34 | uint32 | number of definitions (170) |
| table | 170 x 91 bytes | definition records |
| after the table | uint32 + rows | count and 16-byte selector rows, then a count and 12-byte view rows, then 30-byte name rows |

Record fields known so far (from [lol2-item-format.md](../lol2-item-format.md#record-fields)): +0x18 identity (u32), +0x37 strike sound, +0x3B mask word, +0x3D flags word, +0x3F class byte, +0x42 handler index into the item-use table, +0x43 magic bits, +0x44 post-hit addend, +0x47 four 5-byte descriptor rows; the rest UNCONFIRMED.

## Worked example (re-run 2026-11-18)

Reproduce (prints base, count, the count after the table, record 1's identity, class and handler, and the handler-0 count and highest handler):

```bash
python3 -c "import sys,struct; sys.path.insert(0,'tools'); import lol2_source_format as S; b=open(sys.argv[1],'rb').read(); r=[x for x in S.parse_mix(b) if x['key']==0xED7EC08D][0]; e=b[r['offset']:r['offset']+r['size']]; u=lambda o: struct.unpack_from('<I',e,o)[0]; base,n=u(4),u(0x34); rec=lambda i: e[base+91*i:base+91*(i+1)]; h=[rec(i)[0x42] for i in range(n)]; print(base, n, u(base+91*n), hex(struct.unpack_from('<I',rec(1),0x18)[0]), hex(rec(1)[0x3F]), rec(1)[0x42], h.count(0), max(h))" "$LOL2_DAT/GLOBAL.MIX"
```

- Entry +4 = 496, entry +0x34 = 170, and the uint32 right after 170 x 91 bytes is again 170 (the selector-table count). CONFIRMED.
- Record 1 (bytes 587-677 of the entry): identity 0x8FCB4F6D, class byte 0x44 (hand weapon group), handler index 0 (no use handler).
- Over all 170 records: 47 have handler index 0, the highest is 107. CONFIRMED.

## Open

Grants: [grant census](../lol2-item-effects.md); handlers: [handler catalog](../lol2-item-handlers.md); the dispatcher reads +0x42 and calls the table at `0x9584E–0x95865`. Remaining handler details: [Q8](../OPEN_QUESTIONS.md).
