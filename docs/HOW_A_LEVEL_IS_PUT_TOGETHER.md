# How a LoL2 level is put together

A level archive supplies a texture bank, an object-definition file and a map. The map contains both the traversable geometry and the records that make objects and regions respond to events. The L1_DC directory gives a concrete example. [Level sheets](levels/README.md)

## Pieces

| Piece | L1_DC witness | What the program uses |
|---|---|---|
| Geometry | MAP key `0xB1202500`, `L1_DC.MIX+0x6C370A` | Header +0x04 locates vertices and +0x0C locates the 44-byte region rows. The geometry-entry reader opens the named MAP through `0x9C538–0x9C54F`. [Geometry](formats/geometry.md) · [Header fields](lol2-level-script-format.md#header-fields-proven-by-consistent-reading-on-all-15-levels) |
| Textures | TE_ key `0xB12F2907`, `L1_DC.MIX+0x2A` | The loader requests .tex at `0x9C39E–0x9C3E8`. The expanded bank has descriptors, mip payloads and a surface animation table reached through header +0x20 at `0x9DC9D–0x9DCE2`. [Texture container](lol2-level-texture-container.md) |
| Definitions | ODF key `0xB1162802`, `L1_DC.MIX+0x70C150` | ODF includes surface presets read at `0x9E037–0x9E05B` and its 147-byte creature definition rows start at `L1_DC.MIX+0x712D9B`. Placed-item definitions come from the shared `GLOBAL.MIX` table. [Native definition and placement fields](lol2-save-field-witnesses.md#surface-presets-and-texture-animations) · [Item table](lol2-item-format.md) |
| Scripts and placements | The same MAP entry | MAP +0x3C/+0x44 are the two command offsets. Predicates and event lists occupy their own spans. Prop, control, actor, item and mover placement tables start at header offsets +0x14 through +0x24. The item path at `0x9D43A–0x9D450` gives a concrete join from a placement to a definition. [MAP scripts](lol2-level-script-format.md) · [Item join](lol2-save-field-witnesses.md#from-placement-row-to-item-definition) |
| Text | `LOCALLNG.MIX` and loose TRR files | Message tables have an ID directory followed by record boundaries. Automap text is requested at `0x145C49` through the shared reader `0xCF014`. [Message tables](lol2-text-tables.md) |
| Sound | `LOCALLNG.MIX`, key `0x5D9AD8B8` for the sound bank | `0xA0196–0xA01A0` supplies the shared EFX name to `0xE3608`. An opcode-20 command passes a cue word to `0xE3924` at dispatch `0xB5BDC`. [Sound bank and cues](lol2-sound-cues.md) |

## Load order

1. **CONFIRMED.** The transition stores the destination index at `0xD87AE`. The level loader formats a name from the row at `LOLG.DAT+0x1CDA44+8×index` at `0x9BE08–0x9BE14`. The archive path reaches the open call at `0x9BE85`. The resource-loading path is forwarded at `0x9C0CF`. [Level names and transition index](lol2-level-graph.md#matching-a-recorded-segment-to-an-archive)
2. **CONFIRMED.** On its normal resource route the loader calls the .tex reader at `0x9C3E8`, the .odf reader at `0x9C486` and the .map reader at `0x9C54F`, in that order. The suffix cells at `LOLG.DAT+0x1C1C23`, `+0x1C1C28` and `+0x1C1C2D` match those three calls. The MAP reader asks for `0x244` bytes at `0x9CCCE–0x9CCDB` (file `LOLG.DAT+0xD3CCE–0xD3CDB`), then tests the tag and region count at `0x9CCE3–0x9CCEE` before consuming the tables. [MAP entry](lol2-level-script-format.md#finding-the-geometry-entry)
3. **CONFIRMED.** In the MAP reader the predicate copy at `0x9CECC` precedes loading the region script pair at `0x9CF06/0x9CF4B` and the object script pair at `0x9CF90/0x9CFD5`. It installs these before calling the prop, control, actor, mover and item readers at `0x9D3A4`, `0x9D3CF`, `0x9D3FA`, `0x9D425` and `0x9D450`. The offsets those readers use are independent of their call order. [Saved sections and producers](lol2-save-field-witnesses.md)
4. The shared text and sound readers run through their own call paths. A concrete sound path is opcode 20 dispatching a bank cue after an event selects its command group. The event matcher resolves a command offset and the queue dispatches it. [Event records and command queues](lol2-script-events.md) · [Sound dispatch](lol2-sound-cues.md)

**UNCONFIRMED.** A single top-level order covering every shared text, music and sound resource is still open. Follow the callers of `0xCF014` and `0xE3608` back to the shared initialization paths and compare each with `0x9BDC4` and the documented level resource route. [Text readers](lol2-text-tables.md#the-reader)
