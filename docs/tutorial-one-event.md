# Follow one interaction in level 1

This example follows a level-1 command group for an empty-hand
interaction on prop 1050 in the original DOS level L1_DC. A prop is a placed object. A predicate is a
test the engine applies before it runs a command. File offsets below are
absolute within the named archive. Code addresses use the
[executable's address convention](lol2-executable-tables.md).

## From the interaction to the command list

1. **CONFIRMED.** Prop 1050's placement at `L1_DC.MIX+0x6F4F23`
   has event-list offset `0x14D4` in its word at +0xC. For an
   in-range interaction with prop +0x15 bit 0x80 clear (tested by both
   `0x5DA54` and `0xB5004`), the prop handler `0x5DA48–0x5DAAD` calls
   `0xB5000` with the prop and request. The range check compares
   request +0x28 with `0x01000000`. The prop event-list virtual at
   `0x5DA20` reads the live offset at prop +0x36, and `0xB5013–0xB501D`
   passes the list to the matcher. The slots +0x24 and +0xB8 of the vtable at
   `LOLG.DAT+0x1C64E8` (file `+0x1C650C`, `+0x1C65A0`) hold these routines.
   **UNCONFIRMED:** that prop 1050's class installs this vtable at prop
   +0x28, and the link from placement word +0xC to prop +0x36 through
   `[0x273E4]`; no constructor is cited here (see the test below).
2. **CONFIRMED.** The ten-byte kind-4 record at
   `L1_DC.MIX+0x6EAB81` names command group `0x228E` in stream 1.
   Its mode and inversion bytes are both zero. The matcher accepts
   this arm when request +0xC is null, meaning the player is interacting
   with an empty hand (`0xADBDD–0xADC04`, `0xADC41–0xADC59`).
3. **CONFIRMED.** The four bytes at `L1_DC.MIX+0x6EAB8B` give
   predicate 4. The predicate row at `+0x7061D1` has left type 5,
   right literal 0 and operation 0 (equality). Type 5 reads the byte
   at +0x25 of the object bound in `[0xB7D80]`
   (`0x66B3B–0x66B45`, `0x66B77`, `0x66C43–0x66C4F`).
   The binding slot in the candidate vtable at `LOLG.DAT+0x1C6560`
   points to a routine that binds its object at
   `0xB71B2` when prop +0x15 bit 0x10 is clear. With prop 1050
   bound and its byte still zero, `0xADD80–0xADDB0` admits the
   event and runs the group at `L1_DC.MIX+0x6E7FF5`.

**UNCONFIRMED.** The screen coordinate that picks prop 1050 and the
input call sequence that leads to its binding virtual are open. The
static trace starts where the world interaction supplies the prop and
request. **Test:** a breakpoint at `0x5DA48` conditioned on `[esp+4]` = prop
1050's object (the routine is a shared class method), on an in-game
click, can establish
the calling sequence and confirm that `[0xB7D80]` equals that prop before
`0xADD8A` evaluates predicate 4.

## The three commands

**CONFIRMED.** The `F0` header at `L1_DC.MIX+0x6E7FF5` gives a
count of three. The native runner (entry `0x646EC`) reads that count at `0x64715`.

| File offset | Opcode and operands | Result |
|---|---|---|
| `+0x6E7FFB` | 9, prop 1050, property 16 | Stops any audio owned by prop 1050. The call at `0xB540E` passes the prop to `0xE416C`, which matches the audio owner and stops matching channels at `0xE4193–0xE41C7`. |
| `+0x6E8001` | 3, player, identity `0xE0649CBA`, instance byte 1 | Resolves definition 68 at `GLOBAL.MIX+0x5B9115`. The player grant at `0xD78B8–0xD78D9` calls `0x95B68`. The constructor puts 1 in instance +4 and hands the instance to the player through vtable +0x6C (`0x95B8A–0x95BC5`, `0x95BF9–0x95C08`). |
| `+0x6E800D` | 16, prop 1050, state 1 | Writes 1 to prop +0x25 at `0xB5A44`. On a later empty-hand request with the same prop bound, predicate 4 now fails unless another action has reset the byte. |

**CONFIRMED.** The grant stores an item in the cursor slot. `0xD78C4` passes 1
as the fourth argument, so `0xD259C` takes mode 1 and skips the first
swap; when `[0x23C46]` bit 0 is set, `0x8FD40` runs again afterwards
(effect UNCONFIRMED). The player receive routine calls `0x77ACC` at
`0xD25EA`. It stores the pointer in the cursor item slot
`[0x23C57]` at `0x77AEA`. When the cursor override is clear,
`0x77B00–0x77B2C` takes the sprite ID from definition +0x39
and submits it with hotspot 12,12 to `0xACA44` on object `0x22518`
(INTERPRETATION: the mouse cursor). That ID is 310 in the word
at `GLOBAL.MIX+0x5B914E`.

The expected visible result is sprite 310 appearing at the pointer.
Neither the click nor the cursor change has been observed in a running
game; the [runtime procedure](NEEDS_A_RUNNING_GAME.md) covers the click.
[Item grant](lol2-item-effects.md#script-grants) ·
[Definition fields](lol2-item-format.md)

To find the record and group in your own installation, give the
[disassembler](lol2-script-opcodes.md) the original installation's
DAT directory.

```sh
python3 tools/lol2_disassemble_scripts.py --data "$LOL2_DAT" L1_DC |
  grep -iE '6e7ff5|6e7ffb|6e8001|6e800d|6eab81|7061d1'
```
