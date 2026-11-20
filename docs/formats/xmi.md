# XMIDI scores in LOCAL.MIX

**CONFIRMED.** The 33 members beginning with `FORM` are XMIDI scores.
Both MIX hashes of `MUSIC\<stem>.XMI` reproduce their keys for every
nonempty, non-placeholder stem in the original table at
`LOLG.DAT+0x1CE10C` and for CREDITS. Each name also has a corresponding
HMI member. The key is the rolling hash on the [MIX page](mix.md):
4-byte little-endian words, rotate left by 1, add. The table holds 35
pointers relative to `LOLG.DAT+0x1C1024`. Slot 0 points to an empty
string and slots 3 and 13 to `badfile`. The 32 other stems run from
`ARENBAT1` at `LOLG.DAT+0x1C2283` to `SAVAGE` at `+0x1C23A0`. The
credits stem comes from the literals `music`, `\` and `credits.hmi` at
`+0x1C26B5`, `+0x1C26BB` and `+0x1C26C9`. The `.XMI` extension is
supplied by this page, not read from the program: the stems and the
directory are the game's, and all 33 keys match with none left over. For example, `LOCAL.MIX+0x195CA8E` is entry 0, key
`0x80E64013` (`MUSIC\CEMWNDR1.XMI`). `MUSIC\CREDITS.XMI` has key
`0x1325A4F0` and starts at `LOCAL.MIX+0x1993716`.

**CONFIRMED.** Entry 0 is 30,874 bytes. The following offsets are
relative to its start. The same chunk order holds in all 33 entries.

| Offset | Fields |
|---:|---|
| +0x00 | `FORM`, big-endian payload length 14, type `XDIR` |
| +0x0C | `INFO`, length 2, little-endian sequence count 1 |
| +0x16 | `CAT `, length 30,844, type `XMID` |
| +0x22 | `FORM`, length 30,832, type `XMID` |
| +0x2E | `TIMB`, length 30. At +0x36, a little-endian u16 count of 14, then 14 pairs of bytes. |
| +0x54 | `EVNT`, length 30,782, with the first event bytes at +0x5C. |

A chunk length covers its payload and excludes the one alignment byte
after an odd payload. The score reader checks these extents, the INFO
sequence count and the TIMB array length. **CONFIRMED.** In the 33 EVNT
sequences it reads 109,623 events and 80,067 note-ons with duration.
The first member's stream ends in the meta event `FF 2F 00` at
member +0x7897. Delays are sums of successive bytes below 0x80.
A channel event starts with its own status. A note-on adds a duration
encoded as a MIDI variable-length integer after its key and velocity.
The tool checks system and meta lengths and accepts a single stored
zero after the end marker. The TIMB arrays hold 559 pairs in total.

```sh
python3 tools/lol2_xmi_reader.py --data /path/to/DAT --check
python3 tools/lol2_xmi_reader.py --data /path/to/DAT --list
```

**UNCONFIRMED.** Which original build or configuration plays these
entries. The inspected DOS 1.30 paths build AUD and HMI names, including
the direct credits builder at `0xCA8E0`. The literal strings `XDIR`,
`XMID`, `EVNT` and `.XMI` were absent in that original `LOLG.DAT`.
A resource-open call supplying one of the 33 XMI keys would establish
a playback path. [HMI music and native paths](../lol2-music-2026-11.md)
