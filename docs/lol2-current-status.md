# LoL2 current status

Updated 2026-09-11. **Active reverse engineering and restoration; not complete.**

Read [Draracle restoration findings](draracle-restoration.md) for current evidence,
reproduction commands, supported source hashes and the remaining work.

The original cave's static geometry can now be extracted and reviewed in Godot.
Native instruction checks support slope corners, connector endpoints and wall
record indexing. Material extraction and binding have advanced beyond the earlier
LOCAL.MIX atlas hypothesis, but wall-span geometry, UVs, special openings,
interactive objects, hazards and native behavior still need work.

The historical compact entity/control-path results remain useful, with their
original scoped proof levels. They do not establish complete game RE. See
[lol2-compact-path-branch-steering.md](lol2-compact-path-branch-steering.md),
[lol2-entity-object-map.md](lol2-entity-object-map.md), and
[lol2-runtime-to-renderer-bridge.md](lol2-runtime-to-renderer-bridge.md).

[Godot implementation](https://github.com/KForestland/lands-of-lore-unified-godot)
is a separate repository. Its full-map walk view is experimental, and generated
game assets are not distributed with either source repository.
