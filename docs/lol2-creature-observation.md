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

### Live mode-2 distance branch

**CONFIRMED.** In DOS 1.30, a run loaded a player save written by the game
(not shipped; SHA-256 prefix `9a46a2bdecb4`) in L8_SJ and used the forward key. A bounded trace in the instrumented DOSBox build (see the [timer clock](lol2-timer-clock.md#live-write-and-conversion) setup)
followed one creature at guest pointer `0x1130680C` for that run.
Its target +0x34 was the live player `0x101D0574`, +0xA8/+0xA9 both held 2,
and +0x9D/+0xB4/+0xB9 held `00/04/04`. The actor used `0xA34B8`.

| Same actor sample | Horizontal difference in EAX | Threshold in EDX | Native instruction reached |
|---|---:|---:|---|
| Farther | `0x017E27E5` | `0x00BE0000` (190) | `0xA3586`, starts `0xA9720(actor, 2, 0)` |
| Nearer | `0x00B8E254` | `0x00BE0000` (190) | `0xA3503`, stores action 9 at +0xAA |

At entry to `0xA3503` the previous action was 1. In the same trial
another actor at `0x11306A40` took the farther branch with observation
`0x4C`, +0xB4=`0x04`, and +0xB9=`0x04`.

**UNCONFIRMED.** The portal crossing and the branch with +0xB4 mask
0x20 set remain open. The live witness followed the distance branch
with that bit clear. Set breakpoints on `0xA32B4`, `0xA3362` and
`0xA337D` to capture a qualifying actor with the same target on both
sides of a portal.

## Other mode branches

**CONFIRMED.** Mode 3 jumps to the waypoint path when +0xB5 bit 0x10
is set or +0x34 is null (`0xA26AD–0xA26C5`). Otherwise it tests the
target’s type (`0xA28FA–0xA291C`). Type 1 is copied from +0x34
to +0x38 and evaluated through a temporary behavior 4 call. The
original behavior byte is restored immediately after the call
(`0xA26CA–0xA26F4`). Type 4 goes to `0xA276A`. Other types
clear +0x34 and rejoin the waypoint path.

**CONFIRMED.** In modes 4 and 5, zero observation +0x9E with
+B8 bit 0x40 clear enters `0xA3B88–0xA3BA7`, sets +0xB9 bits
5–6 to binary `10` and calls `0xA9720(actor, 1, 3)`. The
continuation at `0xA36AB–0xA36FB` refreshes target XYZ and sets
+B8 bits 4–5 to binary `01` if observation & 7 is nonzero or
that field is not already `01`. Mode 10 uses the same XYZ
and +B8 writes when +0x9E & 7 is nonzero, then calls
`0xA9720(actor, 1, 1)` regardless of whether it refreshed the
target (`0xA3168–0xA31A6`). In that helper, selector 1 uses
target +0x38 and the actor's own observation byte +0x9E, and also tests
the third argument (`bl == 1` at `0xA9785`) (`0xA972F–0xA9788`).

**CONFIRMED.** Mode 7 uses mode 6's handler when path byte +0xA4 is
0xFF (`0xA3BCC–0xA3BD9`, `0xA3DBD–0xA3DC2`). The direct
path at `0xA3C27–0xA3C67` uses +0xA4 to select a 4-byte row
from `[0x22D20]`, then adds the absolute value of signed byte +0xA5 (`movsx; jge; neg; movsx`
at `0xA3C27–0xA3C3D`, so −128 stays −128) to that row’s starting
word to index the 8-byte point table at `[0x22D1C]`. Mode 9 can
skip the secondary-action-9 branch when actor +0xB9 bit 0 is
set, observation +0x9E & 5 is nonzero, actor +0xB4 bit 0x20
is set and its secondary action differs from 13
(`0xA2F2A–0xA2F5C`).

### Mode 3 item target, mode 8 and mode 13

**CONFIRMED.** Mode 3 target type 4 enters `0xA276A`, copies the
target coordinates and sets +0xB8 bits 4–5 to binary `10`. The
distance check at `0xA27B1–0xA27D3` requires a result strictly
below the creature's vtable +0x14 result shifted left 16. The
slot at `LOLG.DAT+0x1C6908` resolves to `0xF2A68`, which returns
`u8(definition+0x2B) >> 1`. At or beyond that distance the branch
calls `0xA9720(actor, 2, 0)` at `0xA28ED`. Inside that distance,
mode 3 clears the target and calls the placed-item transfer routine
`0x95A64` at `0xA27ED`. That routine uses the non-player recipient
pool at `[0x9691C]` and the source's item record +0x2C
(`0x95A8B–0x95AA5`). The near branch selects +0xAA=9 and requests
animation action `0x17` (`0xA2800`, `0xA2843`).

**CONFIRMED.** Placement u16 +0x21 copies into live +0x70 at
`0xA2455–0xA2459`. On load, its `0x20` bit selects object
+0x17 mask `0x80` versus `0x40` (`0xA245C–0xA246A`, `0xA210C`).
Low nibble 5 sets +0xB5 bit 0 (`0xA2110–0xA2121`, `0xA224E`),
which blocks the animation-request helper at `0xA7E0D`. With
placement mask `0x10` set, mode 3's near continuation writes +0x64
according to whether +0x34 remains non-null and clears +0xB5
bit `0x10` and +0xB8 bit 1 (`0xA2890–0xA28C4`). When
that mask is clear, it sets +0x64 to `0xFF` and sets +0xB8
bit 1 (`0xA28C9–0xA28DB`). The flags coexist in
`L13_RC.MIX+0x68EFEA`, actor placement 27 (u16 +0x21 = `0x0035`,
initial behavior 14). This record proves the original values at load.

**CONFIRMED.** The same placement mask 0x10 also selects actor +0x64
on mode 3's other item continuation. After the request at `0xA2A6F`,
the continuation clears actor +0xB5 bit 0x10 and writes +0x64 = 0 with
the placement bit set, or 0xFE if clear (`0xA2A8D–0xA2AB0`). This
path also selects secondary state 9. Across the actor rows read by
`0xA2283`, 86 carry mask 0x10, 373 carry mask 0x20, and 57 carry both.
The census uses u16 +0x21 of the 1,028 rows in the 15 geometry entries.

**CONFIRMED.** Modes 4 and 5 use two derived definition thresholds
in the branch requiring actor +0xB9 bit 0x10 (`0xA3681–0xA3688`,
`0xA36FB–0xA372A`). With unsigned definition words +0x55 and
+0x59, the loader sets +0x6B to `floor(7*max(+0x55,+0x59)/8)`
(`0xA1CC6–0xA1D04`). Let `T` be that result and `R` the signed
live word +0x61 after `0xA1CB5–0xA1CC0` adds 0x80. It sets +0x69
to `floor(T/2)` if `R > T`, otherwise `R + floor((T-R)/2)`
(`0xA1D08–0xA1D24`). The mode path reads these two words and
compares them with the current horizontal distance shifted right
16, from `0xA4E4C–0xA4E5A`. Its substate at actor +0xB9 bits
5–6 selects the branch at `0xA3941–0xA396A`. For the EXEC definition
at `L5_HC.MIX+0x5BF25A`, the three stored input words are 0, 400 and
0, giving `R=128`, `T=350` and a shorter threshold of 239.
The nearby alternative branch at `0xA39AB–0xA39E9` compares definition
u8 +0x74 (75 in that row) shifted left 16 with the distance after
subtracting both object radii (`0xA4EFA–0xA4F20`). These reads establish
the numeric gates. Which original encounter sets the live flags for
each gate remains open; record +0xB4/+0xB7/+0xB9 at `0xA36FB`
and check the dispatch against the definition installed at `0xA22DB`.

**CONFIRMED.** In mode 8's zero-observation continuation at `0xA2DEE`,
a set +0xB9 bit 0 refreshes the +0x40 coordinate triplet from the target at +0x38,
sets +0xB8 bit 4 and clears its bit 5 and the +0xB9 bit. It calls
`0xA9720(actor, 1, 3)` at `0xA2E2D`. With the +0xB9 bit clear,
+B8 & `0x30` equal to `0x30` calls
`0xA9720(actor, 3, 0)` at `0xA2E4F`. If the distance to the
stored point is then below the same definition radius via vtable
+0x14, it selects +0xAA=9, sets +0xB9 bit 0, and clears both update
bytes at `0xA2E84–0xA2EAA`.

**CONFIRMED.** Mode 13 refreshes the target and calls
`0xA9720(actor, 1, 1)` with observation & 7 nonzero
(`0xA31C2–0xA3200`). With that mask zero, it selects +0xAA=9,
clears update bytes and requests action 0 only with +0xB5 bit 0
clear and a successful animation lookup (`0xA320F–0xA328B`).
Mode 10 calls the navigation helper even on its zero-mask path
(`0xA316F` -> `0xA31A6`).

## Creature byte +0xA3

**CONFIRMED.** Two hit paths write 15. The area-hit helper at
`0x94DDC`, called at `0x945BD`, walks candidates returned by
`0xB23BC` with a 0x200000 radius argument. After the target
hit call at `0x94F0F`, it writes +0xA3 at `0x94F29` when
target vtable +0 returns type 2. Item handler 106 repeats this
for a single mode-17 target at `0x9B87E–0x9B89A`.
The creature table's type and hit entries at file
`LOLG.DAT+0x1C68F4` and `+0x1C6974` resolve to
`0xA6ACC` (returns 2) and `0xA6AE0` via fixups
`+0x7F03C` and `+0x7F15C`. The update decrements this
byte whenever it is nonzero at `0xAB63F–0xAB64D`.

**CONFIRMED.** Three consumers treat any nonzero value alike.
After computing actor +0xA6 and +0xA7 from definition +0x81
and the inputs to `0xA1F2C`, they replace each byte `v`
with `v - floor(v/4)`, independently
(`0xA2351–0xA2399`, `0xAA42D–0xAA478`,
`0xAB093–0xAB0E1`). This establishes the update count and
the reduced values. Which visible movement or action is
modified by each +0xA6/+0xA7 consumer remains
**UNCONFIRMED**. Trace the next read of each byte after
`0xAA478`, comparing the same definition with +0xA3=0 and 15.

**UNCONFIRMED.** Other branches in modes 3–5 and 7–10 remain open.
To settle which original situation takes mode 8's stored-point path,
record +0x9E, +0xB8 and +0xB9 on entry at `0xA2C63`, then check the
requested action at `0xA2E84` against the animation install at
`0xA7DC4`. Trace other placement and definition masks from their first
caller to establish their uses.
