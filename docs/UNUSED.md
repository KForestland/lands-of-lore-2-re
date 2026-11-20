# Unused content and development leftovers

This page covers the measured [English DOS 1.30 files](EDITIONS.md). Stored commands, skipped pool bytes and startup options have different evidence.

## Script commands and stored event bytes

- **CONFIRMED.** The two streams in each of 15 level MIXes contain 42,594 commands, using 32 opcode numbers. A separate 9,678 `0xF0` group headers are framing records. Four size-known command values are absent from the streams. The length routine starts at `LOLG.DAT` VA `0x645E0`. [Full count and native dispatch](lol2-script-opcodes.md)

  | Absent command | Native destination or check |
  |---|---|
  | `0x00` | The range guard at `0xB6B6E` rejects it even though the length reader knows its size. |
  | `0x0B` | The low dispatch slot at file `+0xEC8C4` reaches `0xB5C6E`. Its only saved pointer besides the slot is the fixup at `+0x51CBB`. The group walker supplies stored commands to the queue on all 21 direct callers examined. With zero stored `0x0B` rows, this path does not call the handler from the shipped scripts. |
  | `0xC8` | `0x64999 → 0x64BB4` would write a bounded random value to the shared array. No framed record requests it. |
  | `0xCD` | `0x6497D` returns zero. The read of size eight at `0x64642` is the only explicit opcode-byte comparison found, and there is no direct call to the return arm. |

- **CONFIRMED.** The stored event-list pointers in the 15 MIXes leave exactly two bytes untouched by the event-list walk. They are in the region event pool at `L12_CM.MIX+0x967D14–0x967D15`. `tools/lol2_level_writer.py --check` retains them and reproduces every archive. [Level writer coverage](ROUND_TRIP.md)
- **CONFIRMED.** One room archive, `ARENA.MIX`, is outside the 46-name table at `LOLG.DAT+0x1CFA90`. Its module is the 47th. **UNCONFIRMED.** Whether another native route opens it. Neither the missing table entry nor the measured open calls establishes it is unused. [Room archive evidence](lol2-room-archives.md)

## Startup options and debug text

| File location | Stored option or development text |
|---|---|
| `LOLG.DAT+0x1C5278, +0x1C527F, +0x1C5285` | **CONFIRMED.** `-NOMIX`, `-PATH` and `-CD` respectively. The conditional startup write at analysis address `0x14E5E0` sets the optional-archive gate only without the former two. The `-CD` and `-PATH` uses are documented separately. [Optional archive gate](formats/vqa.md#scene-probes-from-edited-copies) · [Startup gate and save format](lol2-save-format.md) · [Other startup options](../patches/RUNNING.md) |
| `LOLG.DAT+0x1C53CD` | **CONFIRMED.** `-LOWMEM`. Native code at `0x14EBDD` looks for it and sets three startup cells, including the flag read at `0x9F1D8`. [Low-memory branch](../patches/README.md) |
| `LOLG.DAT+0x33753, +0x349D6` | **CONFIRMED.** Two debugger messages embedded in the DOS extender. They are present as text. **UNCONFIRMED.** Whether the shipped game supplies a game command-line option that reaches those messages. |
