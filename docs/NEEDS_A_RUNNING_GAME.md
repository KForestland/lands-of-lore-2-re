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

## Q7. Which live writer supplies the timer service?

Question: [Q7 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** The timer reads the signed word at object-5
`0x22C58` at `0xB8C0D` and the dword at `0x22C5A`
at `0xB8BE5`. The saved witness (one save written by the game during play, not shipped) has 225280, 880 and 4
at `0x22C54/58/5A` respectively. Restore has a known
path through section 67. [Timer witness and inspected callers](lol2-timer-clock.md#saved-frame-witness-and-open-producer)

**UNCONFIRMED.** The actual live writer and its rounding.
In L1_DC without loading a save, set write watches on all
three cells. Open and close the menu, break at the restart
`0xA0457`, and run until the timer service `0xA055B`. Log the
first write to each cell, the producing counter's previous and
current values, and the next timer decrement. Repeat after a
long frame, then load a save as a separate restore control.
If the cells use 16.16 and 8.8 views of one elapsed quantity,
a fixed-point pair should satisfy `u32(0x22C54) >> 8 =
u16(0x22C58)` in range. A half-tick or near-boundary example
distinguishes floor, ceiling and round-to-nearest for the
whole-tick cell. A write only during restore identifies that
path without explaining the live source.

## Q9. What starts the timed message 0x26?

Question: [Q9 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** Player initialization clears +0x185 at
`0xCFB8B`. The update subtracts the elapsed quantity when
that field is nonzero and clears it at `0xD2E57` before
sending message 0x26. [Spell and timer consumers](lol2-spell-dispatch.md)

**UNCONFIRMED.** Which gameplay action arms the timer. Arm a
write watch at player +0x185 after initialization and note the
player pointer from the executing update at `0xD2E30`. In
separate trials use one lesson item, cast one spell and let the
character change form. Wait in each trial until the next update.
Record the first nonzero value and stack, then whether the
same object reaches `0xD2E57` and sends 0x26. A nonzero write
and matching expiry identify that trial's producer. Zero stores
at initialization or expiry are controls.

## Q10. Which observation path a live mode-2 creature takes

Question: [Q10 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** When a mode-2 creature's target +0x34 is the
player and +0xB4 bit 0x20 is set, the engine checks observation
byte +0x9D at `0xA32B4–0xA32D9`. Mask 0x05 selects action 1;
with mask 0x05 clear and mask 0x0A set, prior +0xB9 mask 0x02
chooses between action 1 and action 9
(`0xA32DB–0xA3392`). [Creature observation trace](lol2-creature-observation.md#mode-2-branch-conditions)

**UNCONFIRMED.** Which state is reached as the player approaches
and breaks contact in a particular encounter. Break at
`0xA32B4` and retain one actor whose target +0x34 is the player.
Record +0x9D, +0xB4 and +0xB9 before the update, then approach
in line of sight and move behind a portal boundary. On each
update record the target and secondary action. With 0x05
clear and 0x0A set, action 1 and 9 distinguish the remembered
bit's two settings. A transition to a different mode calls for
a trace of that actor's mode store with the same target snapshot.

## Q11. Which saved rows change on a known pickup?

Question: [Q11 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** Sections 2/3 describe the player item pool and
occupancy; level sections 31/32 cover the other item pool and
occupancy. [Save section tables](lol2-save-sections.md#items-and-occupancy)

**UNCONFIRMED.** A same-version pair tying one pickup to the
exact changed rows. In L1_DC, place the cursor over one ordinary
loose item, note the live instance and identity at the
`0x95B68` definition-lookup path if the action allocates a
new instance, and save before picking it up. Pick up only that
item, put it in an empty inventory slot, and save again. At each
save watch the four section descriptors and record occupancy and
row identity after pointer adjustment. A cleared level row with
a newly occupied player row of the same definition proves that
transfer. An unchanged level row and an additional player row
would show duplication or a grant. If the same pool row stays
occupied and only references change, report the reference change.
Save changes elsewhere are outside this comparison.

## Q12. Which history do two exceptional VQA frames read?

Question: [Q12 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** Two movies have one exceptional short-copy token
each. `L20_BBI.MIX` entry 25 frame 115 contains distance 0 at
input 23,847 with 30,400 bytes already written.
`SPKSTON2.MIX` entry 4 frame 492 contains distance 674 with
564 bytes already written. [Byte witnesses and framing](formats/vqa.md)
Static decoding leaves both frames unresolved; only the running game
shows what the original decoder puts on screen for them.

**UNCONFIRMED.** The original destination history at those
copies. Break at the pointer LCW invocation `0x172838`
during the corresponding original cutscenes. Identify the
source entry and count frames from the seek table. On the
target frame, step into each exceptional token and log its
actual source, destination, destination capacity and previous
contents. For frame 115, reading the current destination implies
an operation on existing bytes, while skipping the copy leaves
the output position unchanged. For frame 492, a valid source
before the current frame's start indicates a retained history
buffer; an ignored or rejected command follows a different arm.
Log the active codebook and the final destination offset so the
result can be repeated.

## Q17. What on-screen action reaches these records?

Question: [Q17 in OPEN_QUESTIONS](OPEN_QUESTIONS.md).

**CONFIRMED.** In L8_SJ, control 69 queues a destination of
X −1004, Y 2590, Z 100 and orientation `0x4FA4` at
`0x65C3C–0x65CC5`. Control 114 instead sends events to props
115 and 1014 and links control 116 as it unlinks itself.
[L8 controls and placement offsets](lol2-l8-controls.md)

**UNCONFIRMED.** Which visible face invokes each control and
what geometry the destination displays. In L8_SJ approach the
two placements from the positions recorded in the level archive.
Interact with an empty hand while breaking at `0xB5000` and
`0xADDB0`. Identify the record from its group word and record
the first visible before/after result and the player transform
at `0xB2A96`. Group 12668 identifies control 69 and the exact
destination above. Group 13090 identifies control 114 and
should change the linked objects. Capture a failed click with
an item held as a comparison.

## Level-1 tutorial: which click binds prop 1050?

In L1_DC, use the same approach for prop 1050 ([tutorial](tutorial-one-event.md)). Break at
`0x5DA48` (a shared class method); at `0x5DA51` the prop object is in `ebx`, so condition on `word [ebx+0x36] == 0x14D4`, prop 1050's event-list offset (this assumes the placement link the tutorial marks UNCONFIRMED), record the caller and input action, compare the
selected prop to `[0xB7D80]` at `0xADD8A`, and read its
+0x25. Binding to prop 1050 with byte zero reaches group
`0x228E` and the cursor grant. A different pointer establishes
that the test uses another object's state.
[The three original commands](tutorial-one-event.md)
