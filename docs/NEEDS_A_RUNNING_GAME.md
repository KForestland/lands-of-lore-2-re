# LoL2 questions to test in the original DOS game

Launch `LOLG.EXE` from a disposable copy of your own original DOS 1.30
installation (`LOLG.DAT` SHA-256 starting `b27a3534`) in a
debugger-enabled DOS emulator. Breakpoints below use
the [LOLG.DAT analysis addresses](lol2-executable-tables.md). Within
the loaded LE code object (object 2), a breakpoint at analysis address
`A` is at offset `A − 0x59024`. Data addresses name displacements from
the loaded object-5 base. To find the linear bases under DOS/4GW, search memory for the
fixup-free bytes `C7 83 85 01 00 00 00 00 00 00 C7 83` (analysis address
`0xCFB8B`; the first ten bytes alone also match at `0xD2E57`): object-2 base = match − (`0xCFB8B` − `0x59024`).
Object-5 base = the relocated operand of the `mov ax,[…]` at
`0xB8C0D`, minus `0x22C58`. Record the release, save slot,
level, action, native instruction and values for each observation.

## Remaining probes

### Q9. What starts the timed message 0x26?

Question: [Q9 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** Player initialization clears +0x185 at
`0xCFB8B`. The update subtracts the elapsed quantity when
that field is nonzero and clears it at `0xD2E57` before
sending message 0x26. [Spell and timer consumers](lol2-spell-dispatch.md)

**CONFIRMED, two runtime controls.** One level-20 cast reached
`0xD24B1` with effect `0x0A` and the watched player field stayed zero.
In a separate restore of the same slot, taking the handler-34 lesson
and pressing W reached acquisition ID 4 at `0x96FEC`. Its return
of zero at `0x96FF4` shows that ID 4 was already known. This
path spawned the feedback effect at `0x97028`.
Player +0x185 stayed zero at the traced sites and through the
20-second watch. The expiry call at `0xD2E61` did not run.
[Lesson, feedback and slot evidence](lol2-spell-dispatch.md#controlled-use-of-the-level-20-lesson)

**UNCONFIRMED.** Which gameplay action arms the timer. Arm a write
watch at player +0x185 after initialization and note the player
pointer from `0xD2E30`. First observe a lesson with an absent
acquisition ID (for ID 4, message 0x23 at `0x86230`). Separately,
let the character change form and verify
a transition at player +0x1AB. Record the first nonzero timer
write and stack if it occurs, then whether the same object reaches
`0xD2E57` and sends 0x26. A nonzero write and matching expiry
identify that trial's producer. The already-known lesson and
effect-0x0A cast provide zero-valued controls.

### Q10. Which observation path a live mode-2 creature takes

Question: [Q10 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** When a mode-2 creature's target +0x34 is the
player and +0xB4 bit 0x20 is set, the engine checks observation
byte +0x9D at `0xA32B4–0xA32D9`. Mask 0x05 selects action 1;
with mask 0x05 clear and mask 0x0A set, prior +0xB9 mask 0x02
chooses between action 1 and action 9
(`0xA32DB–0xA3392`). [Creature observation trace](lol2-creature-observation.md#mode-2-branch-conditions)

**CONFIRMED, partial runtime result.** One L8_SJ actor with +0xB4=`0x04`
used the alternate distance path. It reached the farther helper at
`0xA3586`, then the near action-9 store at `0xA3503` when its distance
fell below the 190-unit threshold.
[Live mode-2 samples](lol2-creature-observation.md#live-mode-2-distance-branch)

**UNCONFIRMED.** Which state is reached as the player approaches
and breaks contact in a particular encounter. Break at
`0xA32B4` and retain one actor whose target +0x34 is the player.
Record +0x9D, +0xB4 and +0xB9 before the update, then approach
in line of sight and move behind a portal boundary. On each
update record the target and secondary action. With 0x05
clear and 0x0A set, action 1 and 9 distinguish the remembered
bit's two settings. A transition to a different mode calls for
a trace of that actor's mode store with the same target snapshot.

### Q12. Which history do two exceptional VQA frames read?

Question: [Q12 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** Two movies have one exceptional short-copy token
each. `L20_BBI.MIX` entry 25 frame 115 contains distance 0 at
input 23,847 with 30,400 bytes already written.
`SPKSTON2.MIX` entry 4 frame 492 contains distance 674 with
564 bytes already written. [Byte witnesses and framing](formats/vqa.md)
Static decoding leaves both frames unresolved; only the running game
shows what the original decoder puts on screen for them.

**BLOCKED (partial runtime result).** An intro frame hit `0x172838`
with a bounded destination. The two target VPTZ payloads now have exact
MIX offsets and predicted short-copy source positions. The Extras menu
did not provide a route to the target movies: the `L20_BBI.MIX` read reached only its directory (offsets 0, 4 and 6), and the slot lacked item 139 for `SPKSTON2` entry 4. Both scene and item paths also skip the `SPKSTON` open while `[0xB860]` is zero (`0x95E60`).
[Decoder control and target offsets](formats/vqa.md#native-short-copy-runtime-control)

**CONFIRMED.** Original commands now identify two playback routes.
L20_BB prop 87 can play scene 65, and L9_DR prop 967 can play
scene 42. L5_HC placement 9 and an L9_DR grant supply the item
handled by `0x99EF4` for scene 42.
[Original trigger routes and offsets](formats/vqa.md#original-trigger-routes-for-the-two-frames)

**UNCONFIRMED.** The original destination history at those
copies. Break at the pointer LCW invocation `0x172838`
during the corresponding original cutscenes. Identify the
source entry and count frames from the seek table. On the
target frame, step into each exceptional token and log its
actual source, destination, destination capacity and previous
contents. At `0x158DB2` frame 115 predicts a short self-copy
from the current destination. Frame 492 predicts a source 110
bytes before the destination base. Log the active codebook and
the final destination offset to identify how those bytes become
tile references in the frame.

### Q17. What on-screen action reaches these records?

Question: [Q17 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** In L8_SJ, control 69 queues a destination of
X −1004, Y 2590, Z 100 and orientation `0x4FA4` at
`0x65C3C–0x65CC5`. Control 114 instead sends events to props
115 and 1014 and links control 116 as it unlinks itself.
[L8 controls and placement offsets](lol2-l8-controls.md)

**CONFIRMED, partial runtime result.** Both live controls resolve to
the expected event groups through vtable `0x5484`. The interaction entry
`0x5DA48` calls `0xB5000` at `0x5DAAD`. The loaded slot placed the
player away from both targets, so the test left the visible results open.
[Live placement and breakpoint conditions](lol2-l8-controls.md#live-binding-of-both-l8-controls)

**UNCONFIRMED.** Which visible face invokes each control and
what geometry the destination displays. In L8_SJ approach the
two placements from the positions recorded in the level archive.
Interact with an empty hand while breaking at `0x110ACD` (log request
+0x32 kind, +0x20 object and +0x28 distance), `0xB5000` and `0xADDB0`;
this needs a save close to the controls (one from the owner, see the
saves list). Identify the record from its group word and record
the first visible before/after result and the player transform
at `0xB2A96`. Group 12668 identifies control 69 and the exact
destination above. Group 13090 identifies control 114 and
should change the linked objects. Capture a failed click with
an item held as a comparison.

### Level-1 tutorial: which click binds prop 1050?

In L1_DC, break at `0xB5000` for [prop 1050](tutorial-one-event.md)
with vtable `0xA848` and word at prop +0x18 equal to `0x14D4`.
The first stack argument identifies the prop. Record the caller
and input, compare the target to `[0xB7D80]` at `0xADD8A`, and read
prop +0x25. Binding to prop 1050 with byte zero reaches group
`0x228E` and its cursor grant. A different pointer identifies
the object supplying the predicate's state.

## Answered probes

### Q7. Which live writer supplies the timer service?

Question: [Q7 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** The timer reads the signed word at object-5
`0x22C58` at `0xB8C0D` and the dword at `0x22C5A`
at `0xB8BE5`. The saved witness (one save written by the game during play, not shipped) has 225280, 880 and 4
at `0x22C54/58/5A` respectively. Restore has a known
path through section 67. [Timer witness and inspected callers](lol2-timer-clock.md#saved-frame-witness-and-live-producer)

**ANSWERED, CONFIRMED.** A fresh DOS 1.30 L1_DC run wrote the
three cells at `0xE0C5C`, `0xE0C82` and `0xE0CD2`. The 480 Hz
counter feeds the four-sample average and the separate fractional
carries feed the 8.8 and whole-tick outputs. The same triplet's first
two values `0x34000` and `0x340` yielded whole ticks 4 and 3 on
adjacent frames. A slowed frame supplied `0x7B000`, `0x7B0`, and 7 to
the service before the subtraction at `0xB8CE4`.
[Live trace and conversion formulas](lol2-timer-clock.md#live-write-and-conversion)

### Q7 (save-load and menu). What does the first resumed countdown use?

Question: [Q7 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**ANSWERED, CONFIRMED.** The same kind-2 L20_BB event first
used 3 restored whole ticks after load (`0x0A0B` → `0x0A08`).
In a separate normal-menu trial it stayed at `0x0A05` for
eight seconds, then used 4 retained whole ticks on resume
(`0x0A05` → `0x0A01`). Both first debits at `0xB8CE4`
preceded the first new sample at `0xE0BE9`. In the pause
trial that new sample was 24, with the marker advancing only
`0x0F31` → `0x0F49` since `0xA034A` restarted the clock.
[Slot offsets and native trace sequence](lol2-timer-clock.md#first-countdown-after-save-load-and-menu-pause)

### Q11. Which saved rows change on a known pickup?

Question: [Q11 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** Sections 2/3 describe the player item pool and
occupancy; level sections 31/32 cover the other item pool and
occupancy. [Save section tables](lol2-save-sections.md#items-and-occupancy)

**ANSWERED for a dropped item, CONFIRMED.** The controlled trial used a dropped item in
L20_BB. The live transfer made placement row 4 reusable via `0x9412C`
and allocated player inventory row 17 at `0x95A99`. The decoded
before/after slots differ at that player's occupancy bit and the
matching placement row in level section 25. Global section 2 and level
sections 31/32 agree across the pair.
[Original slot offsets and observed changes](lol2-save-sections.md#controlled-pickup-in-l20_bb)

**ANSWERED for an original loose item, CONFIRMED.** The opening-cave
placement at `L1_DC.MIX+0x6FBFCE` has definition `0xA4C5CBD3`.
A left click allocated player row 0 at `0x95A99` and released placement
row 16 at `0x9412C`. With position fixed, the saves show row 16's
reusable bit, the new player occupancy bit, and four new definition-pointer
XOR bytes in global section 2. Level sections 31/32 agree.
[Save inspector comparison and native calls](lol2-save-sections.md#original-opening-cave-pickup-in-l1_dc)

### Q18. Which gesture reaches an original placed-item group?

Question: [Q18 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**ANSWERED, CONFIRMED.** An empty-hand left click on L1_DC row
16 (`L1_DC.MIX+0x6FBFCE`) reached the placed-item virtual call
at `0x110ACD`, dispatched its kind-4 record and entered stream-1
group `0x3648` at `0x646EC`. The click was replayed with xdotool
on private Xvfb display :74, using the Q11 before slot in a separate
DOS instance. The empty cursor passed the gate at
`0xADBDB–0xADC59`. The click also allocated a player item and
released the floor row.
[Native calls, predicate and group offsets](lol2-event-producers.md#empty-hand-left-click-on-l1_dc-placement-16)
