# LoL2 creature observation and mode 2

Addresses use the DOS 1.30 [analysis convention](lol2-executable-tables.md).
The [transition page](lol2-creature-transitions.md) maps the behavior and
animation dispatchers.

## Observation records

**CONFIRMED.** `0xAA208` calls `0xA9A94(actor, player, actor+0x9C, 1)`
at `0xAA22E`. When actor target +0x38 is the player, it copies +0x9C
to +0x9E (`0xAA238–0xAA24F`). For another non-null +0x38 target it
recomputes into +0x9E and clears the target pointer if the call returns
zero (`0xAA257–0xAA279`). Target +0x34 has the same special case and
recompute path for +0x9D (`0xAA27F–0xAA2C9`). Consequently +0x9C
holds the player observation, and +0x9D/+0x9E belong to the paired
+0x34/+0x38 targets. An equal target can use the same observation byte
in more than one field.

**CONFIRMED.** The shared calculation at `0xA9A94` writes mask bits to
its third argument. The first range uses the two unsigned profile words
at +0x59 and +0x5B (`0xA9B80–0xA9B8D`). Let `d` be the distance at
`[EBP-8]`. It is the horizontal result from `0x136594 >> 16`, plus the
absolute Z difference shifted right 16 only when the previous mask & 7 is zero (`0xA9B26–0xA9B5C`).
Let `r` and `e` be those two words. Once the angle and range gates pass,
`d <= r` sets bit `0x40` and uses strength 255. When `r < d <= r+e`, the
code sets `0x80` and uses `255 - trunc(256*(d-r)/e)`
(`0xA9C0C–0xA9C56`). The angle compares the wrapped unsigned bearing
with half of profile word +0x5D (`0xA9BB1–0xA9BF8`). A nonzero previous mask & 7 bypasses the angle gate (`0xA9C00–0xA9C06`).

The path checks a region traversal through `0xE2958` at `0xA9D27`.
On success it sets bit `0x02`, and it also sets `0x01` when the strength
is 255 (`0xA9D36–0xA9D49`). With fourth argument nonzero it copies the
strength's low byte to actor +0x61 (`0xA9D4F–0xA9D52`). A separate
range test against words +0x55 and +0x57 and a source-value call to
`0xD8EC4` start at `0xA9E28–0xA9E58`. The code writes additional mask bits
`0x20`, `0x04|0x40`, `0x08` and `0x10` at `0xA9E25`, `0xA9F85`,
`0xA9FA8` and `0xAA040` respectively. A second `0x80` write occurs at `0xA9E95`. With fourth argument zero, `0xA9D65` reaches `0xAA0E7–0xAA134` and sets `0x20`, `0x44`, `0x08` and `0x10` using distance thresholds.

## Mode 2 branch conditions

**CONFIRMED.** For target +0x34 equal to the player and actor +0xB4 bit
0x20 set, the dispatch branch at `0xA32B4–0xA32D9` checks observation
byte +0x9D. When mask `0x05` is nonzero, it copies target XYZ to actor
+0x40/+0x44/+0x48, sets +0xB8 bits 4–5 to binary `10`, calls
`0xA9720(actor, 2, 1)`, selects secondary action 1, and sets +0xB4 bit 2
and +0xB9 bit 1 (`0xA32DB–0xA3337`). When `0x05` is zero and `0x0A`
is nonzero, a previous +0xB9 bit 1 permits the same helper arguments and
secondary action (`0xA3344–0xA336E`). Without that bit the branch selects
secondary action 9 and clears the two update bytes at `0xA337D–0xA3392`.

For the other mode-2 path at `0xA34B8`, +0xB9 bit 2 set invokes the
horizontal difference check `0x1365C4` against definition u16 +0x4D in
16.16 units (`0xA34C7–0xA34F9`). The near branch selects secondary action
9 (`0xA3503`). The other branch at `0xA3586` calls `0xA9720(actor, 2, 0)`.

**UNCONFIRMED.** Full producers for actor +0xA3 and the remaining
mode- and flag-specific semantics are still open. A bounded operand check
looked for byte and wider stores spanning +0xA3 in the actor code range
`0xA0000–0xADE00`. It found the decrement at `0xAB64D`, and the nearby
constructor writes at `0xA213E`, `0xA2145` and `0xA215A` set +0xA0,
+0xA1 and +0xA2 separately. The first positive value may originate in a
whole-record initialization or a computed write. Observe the first
change before the decrement, recording the actor definition and job mode.
For modes 3–5 and 7–10, trace each tested observation bit through the
setter above before assigning gameplay names to all branches.
