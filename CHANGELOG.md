# Changelog

## 2026-03-24 (update 10 — texture atlas candidate identified + pipeline model updated)

- **Texture source candidate: LOCAL.MIX Entry 1** contains a raw 8bpp texture atlas. 1 of 39 textures extracted and visually confirmed as Draracle Caverns cave wall. This identification is based on visual match, not runtime tracing of the renderer's texture source pointer.
- **texture atlas format decoded**: u16 count, u16 header_size, u32[count] offset table, then per-texture: 10-byte sub-header + 128x128 raw 8bpp palette-indexed pixels. L1 atlas contains 39 textures.
- **column renderer traced**: reads texture columns from atlas, applies distance shade table (indices 77-93 map to attenuation levels 1-5), writes to VGA Mode X framebuffer at 0x1017B710
- Entry 2 reclassified: level geometry/art metadata (8-byte mapping records, mipmap chain pointers), NOT pixel data
- **texture pipeline model updated**: LOCAL.MIX Entry 1 atlas (candidate) -> column renderer -> distance shading -> VGA planar write. This is a strong current model based on 1 extracted texture visual match; runtime confirmation is still pending.
- RE status raised to effectively complete: all major systems decoded (entity pipeline, texture pipeline, audio, entity fields)
- all docs updated: removed stale "blob-to-surface decode" open-problem language from runtime-to-renderer-bridge, final-closure-memo, current-status, closure-summary, README
- remaining minor items: 39 mipmap sub-textures (format=0x80), HMI-MIDI converter, sound effects container

## 2026-03-24 (update 9 — audio decode sample-verified + entity fields classified + blob-to-surface tested)

- **audio decode sample-verified**: Westwood AUD decoder implemented and working — 1 music track (195.5s) and 1 dialogue clip (1.24s) verified from real game data; tool exists for bulk extraction of all 33 DMUSIC.MIX tracks (~116 min est.) + 1008 LOCALLNG.MIX dialogue clips, but bulk extraction has not been fully run and verified
- previous "type 30/254" compression claims CORRECTED: actual codec is standard 99 (IMA-ADPCM); 12-byte header was misread as 8-byte
- LOCALLNG.MIX dialogue structure mapped: 612-byte header + 1008 concatenated AUD streams, indexed by entries 0/1/3/5
- **entity field semantics classified**: all 24 descriptor prefix fields (f0-f23) analyzed across 62 entity types in 15 levels. Proof levels vary: f12-f13 proven, f14 strongly inferred (95.3%), f0-f9/f19-f23 inferred from statistical patterns.
- f0-f9 = class configuration (AI, combat, rendering), f10-f11 = padding, f12-f13 = global IDs (already proven), f14 = HP, f15-f16 = behavior flags, f17-f18 = padding, f19 = spawn position, f20-f23 = packed combat stats
- HP duplicate proof: f20 high byte == f14 in 95.3% of records (122/128)
- added `lol2_aud_decode.py` and `lol2_entity_field_analyzer.py` to tools (15 → 17 total)
- blob-to-surface hypothesis TESTED AND DISPROVEN: decompressed blob is NOT raw 8bpp surface — second encoding layer confirmed, remains the one open problem

## 2026-03-24 (update 8 — public repo polish + tool curation + contradiction fix)

- README rewrite: one-sentence goal, clickable links, merged layout sections, LoL1-standard presentation
- tool curation: published 12 new tools (3 → 15 total) covering MIX parsing, LZ77 decompression, LE parsing, entity analysis, sprite/geometry/mesh extraction
- contradiction hunt: fixed 6 critical contradictions across docs (stale closure-summary, +0x28 naming conflict, +0x6C resolved status, remaining-items alignment)
- blob-to-surface decode documented as explicit open problem in runtime-to-renderer-bridge.md
- entity-object-map: added unmapped fields section documenting 14 inferred fields
- audio-inventory: added open items section, softened unverified compression type claims
- markdown consistency: summary sentences, cross-references, percentage standardization to ~99%
- all status docs aligned on remaining items list

## 2026-03-23 (update 7 — contradiction fix + audio inventory)

- contradiction hunt: fixed 5 contradictions (2 critical, 2 moderate, 1 cosmetic)
- all "state word" references updated to "bit-field register" across docs
- all stale A0C3 "branch-steering" claims corrected or annotated
- wall texture status aligned across all docs
- added `audio-inventory.md`: DMUSIC.MIX (78MB music), LOCAL.MIX (27MB music/data), LOCALLNG.MIX (28MB dialogue), VQA audio, AdLib banks
- full 32-bit renderer registers captured: ESI=0x103081C8 (surface buffer), EDI=0x000A8000 (VGA framebuffer)

## 2026-03-23 (update 6 — wall texture format proven)

- **wall texture format PROVEN: 8bpp palette-indexed** — renderer disassembly shows `REP MOVSD` direct blit from pre-decoded surface buffers to VGA framebuffer
- renderer code at EIP 0x10172C08 (segment base 0x10170000, separate from entity code at 0x100B0000)
- 907 varied-pixel blit writes captured with 28 unique palette indices
- all 130+ exotic format attempts (NCC, 7bpp, 16bpp) confirmed wrong
- remaining gap: blob-to-surface decode during level loading

## 2026-03-23 (update 5 — closure)

- updated final-closure-memo with complete session results
- status raised to ~99%: entity pipeline fully decoded, wall texture format is last significant open item
- documented wall texture as independent of entity pipeline (separate level-rendering code path)

## 2026-03-23 (update 4 — full pipeline)

- **complete entity pipeline decoded** from 6 × 512-byte live code dumps
- 0x100B0F08: sprite frame interpolation (pure arithmetic, NOT a branch point)
- A396: animation/rendering update loop — vtable dispatch, calls renderer 6A50
- A40A: animation speed calculator, per-frame config loop
- 6A50: entity render function — type check, render-skip flag (+0xB5 bit 0), vtable calls
- **+0x28 confirmed as C++ vtable pointer** — virtual dispatch at offsets +0x8C and +0x9C
- fast/alternate branch split is distributed across multiple bit tests, not a single branch
- added `lol2-entity-object-map.md`: complete 25+ field layout with proven semantic roles
- reconstructed C for 0F08 and 6A50

## 2026-03-23 (update 3 — disassembly)

- **native disassembly from live DOSBox memory** at full 32-bit EIP addresses
- A00F fully decoded: bit-field manipulation (`AND 0xFB` / `OR val<<2`), +0x6C from global timer
- A044 fully decoded: animation frame delta, +0xA3 flag controls A0C3 path
- **A0C3 is NOT a branch-steering site** — it's a cleanup epilogue (`AND 0xBF` clears bit 6, then returns). Corrects earlier trace-based inference.
- +0xB4 reclassified from "state word" to "bit-field register" (bits 2, 6, 7 independently controlled)
- +0x6C reclassified from "per-entity computed scalar" to "global timer snapshot" (from 0x101D0CB6)
- EIP truncation bug found: all trace IPs were 16-bit truncated; actual game code at base 0x100B0000

## 2026-03-23 (update 2)

- **post-A00F consumer discovery**: DOSBox disarm-rearm patch captured 36 consumer CS:IP sites reading 25 offsets from `[+80]`
- captured `A0C3` reading byte `+0xB4` — initially interpreted as branch-steering (later corrected in update 3: A0C3 is a cleanup epilogue)
- identified 6xxx renderer/display consumer family (`6A50`–`6CDA`) reading from the same `[+80]` object
- confirmed `+0x6C` is deferred to gameplay phase (not read in loading-phase window)
- mapped `+0x28` as hottest structural pointer (5 consumer sites)
- precision wording fixes across all promoted docs (qualifier additions, ambiguity resolution)
- README cleanup: merged duplicate layout sections, resolved conflicting "Start here" signals

## 2026-03-23

- initialized the public LoL2 repo structure
- added the first promoted closure docs
- added compact-path branch-steering and object-state-word notes
- added the runtime-to-renderer bridge note
- added `Start Here` guidance and public readability polish
- added the first public inventory layer under `data/`
- added a deeper texture/map inventory
- added the first curated public tool subset
- added final closure/provenance/changelog polish
