# Next steps for tool makers

## Map viewer

`tools/lol2_source_format.py` finds a level's geometry member in its MIX.
`tools/lol2_level_schematic.py` already reads 16.16 vertex pairs, 44-byte
regions and placements. Use the region boundary and neighbour indices
to draw an overhead view. The wall and texture pages give the stored
records for adding materials. Region height interpolation and layered
regions need a separate view or floor control.
[Geometry rows and native offsets](formats/geometry.md) ·
[Wall references](formats/walls.md) · [Texture container](formats/texture-container.md)

## Map editor

`tools/lol2_mix_writer.py` writes archive directories and
`tools/lol2_level_writer.py` writes the supported command, event and
predicate fields back into their spans. The latter retains opaque bytes
and the geometry as stored. A map editor still needs a typed geometry and
placement writer with cross-checks for vertices, neighbour links,
subdivisions, wall spans and the script references to region indices.
Start with a fixed-size edit and read it back. Adding rows will also need
a relocation pass over offsets, counts and references in both command
flavours. On 22 November 2026 the mod kit edits the level's ODF numbers and TRRs.
[Level sections and their offsets](formats/level-data.md) ·
[Script framing](lol2-level-script-format.md) · [Writer checks](ROUND_TRIP.md)
