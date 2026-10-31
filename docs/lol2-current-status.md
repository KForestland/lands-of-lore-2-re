# LoL2 current status

Updated 2026-10-31. **Active reverse engineering and restoration; not complete.**

## October 2026 update

- **Sound bank found:** `LOCALLNG.MIX` entry 4 (key 1570429112) is a named AUD bank of
  1179 rows: 1008 real clips (22050 Hz mono, codec 99, creature sounds and speech) and
  171 one-byte placeholders. See [audio inventory](audio-inventory.md); tool
  `tools/lol2_sound_bank.py`.
- **Level texture containers decoded:** each level MIX holds an LZO1X-blocked
  `SPHERE<n>\<LEVEL>\<LEVEL>.TE_`; raw 0xA9 materials decode with
  `tools/lol2_texture_container.py`. See [level texture container](lol2-level-texture-container.md).
- **Wall-material source closed for one traced span:** L20_BB descriptor 556 pixels, shade row
  and palette are original file bytes, reproduced with zero mismatches. This supersedes the
  LOCAL.MIX Entry 1 atlas hypothesis. See [wall material provenance](lol2-wall-material-provenance.md).
- **Level scripts:** all 15 levels export with no unknown opcodes (42,594 commands, 32
  opcodes). See [level script format](lol2-level-script-format.md); tool `tools/lol2_export_scripts.py`.
- **Script engine:** [facts](lol2-script-engine-facts-2026-10.md) and
  [addendum](lol2-script-engine-facts-2026-10-addendum.md) (predicate table, record-kind runners,
  op196 PARTIAL, op204 arms).
- **Items:** [item format](lol2-item-format.md): 170 records of 91 bytes, 107-handler item-use table.
- **Movies:** [VQA v2 partial-codebook decoder](lol2-vqa-v2.md); tool `tools/lol2_vqa_v2_decode.py`.
- **Levels:** [level graph](lol2-level-graph.md): 15 levels, 48 room archives, the decoded exit graph.

Still open: the HMI-MIDI music converter, texture flags other than 0xA9 (including 0x80A9),
op196's remaining stores, and the control/prop event caller paths.

## September 2026 state

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
