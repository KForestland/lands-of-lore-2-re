# LoL2 Wall Material Provenance (Runtime Witness)

Date: 2026-10-31 (work done 2026-09-11)

## Short Verdict

For one wall material, the source of the pixels the renderer draws is now
traced end to end to original files: L20_BB texture container
(`SPHERE3\L20_BB\L20_BB.TE_`), material descriptor `556`. Pixels, shade row
and palette all come from that blob. One 64-pixel span drawn by the game was
reproduced from those file bytes with zero mismatches.

This supersedes the older hypothesis that `LOCAL.MIX` entry `1` is the wall
texture atlas.

## What Was Traced

1. **Cache identity.** A wall page read by the renderer in a DOSBox guest
   trace was located in the named cache blob `sphere3\l20_bb\l20_bb.te_`
   (`CDCACHE.MIX`). All `28,451,111` bytes match the reference copy (SHA-256
   `adf44e53...6c41ef21`). The same bytes are the LZO1X decode of the
   `.TE_` entry in `DAT/L20_BB.MIX`
   ([lol2-level-texture-container.md](lol2-level-texture-container.md)).
2. **Descriptor.** The page is mip 0 of section-2 descriptor `556`
   (id `2682`, 256 x 256, flag `0xA9`, five mips). Section 3 starts at
   `0x572660`; the descriptor's first mip offset `0xBCC223` lands on the
   page at blob `0x113E883`, whose header is `A9 00 00 01 00 01 00 00`.
3. **Consumer.** Code at `0x1013EEF1` reads the header width/height and
   stores `header + 8` as the source pointer. The trace covers the full
   `65544`-byte record. `4368` sampled source reads match the reference
   pixels with zero mismatches, each at `header_base + 8 + AX`.
4. **Shading.** The sampler at `0x1013F9EB` and related sites maps each
   source index through a 256-byte shade row (bank `0x2D`, live address
   `0x1019BD00`).
5. **Fresh context capture.** A gated hook logged full registers, the live
   shade row, renderer state and the live DAC palette at the three
   consumer sites (`128` events, `64` paired samples).

## Closure Against Original Files

| Input | Source in the L20 blob | Check |
|-------|------------------------|-------|
| Pixels | Descriptor 556 mip 0, `0x113E883 + 8` | `4368` traced reads, zero mismatches |
| Shade row | Section 4 (`0x9A2`) + `0x2D * 256` = `0x36A2` | `256/256` bytes equal the live row |
| Palette | Header `+4` -> `0x6A2`, 768 bytes | `764/768` bytes equal the live DAC |

The four differing palette bytes (indices 12, 14, 16, 55; one step each) are
not reached by descriptor 556 or 557 through row `0x2D` at any mip, so the
file palette fully covers this fixture. Their cause is OPEN.

## Native Span (PROVEN, one span)

From one captured initial sampler state (source index, U/V accumulators,
steps, masks), stepping with the captured F9DF/FA6B update order over the
file pixels reproduces all `64` consecutive source indices, accumulator
states, output indices and normalized RGB colours, zero mismatches. The
same file shade row also reproduces all `2184` source/output pairs in that
trace and `2184/2184` in an older, separate trace (over 32 source indices).

An older salvaged shade-table dump matched only `953/2184` pairs and must
not be used for this material.

## Exactly What Is Proven

- One descriptor (`556`) in one level (L20_BB), one shade row (`0x2D`),
  one 64-pixel span, from one trace.
- Pixel source, shade row and palette are original file bytes, not
  runtime-generated.
- Not proven: other descriptors (557 was checked statically only), other
  shade banks, how the renderer picks the bank, how a scene produces the
  span's initial state, world-space UV orientation, and final frame output
  (window scaling, gamma, overlays). The trace logged `1000` DOS-handler
  `Illegal read` diagnostics; the accepted samples are unaffected, but the
  run is not warning-free.

## Effect On The LOCAL.MIX Entry 1 Hypothesis

The older lane treated `LOCAL.MIX` entry `1` (39 records) as a wall texture
atlas. The [Entry 1 verdict](../examples/atlas_candidate_verify/ENTRY1_MODEL_VERDICT.md)
had already demoted records `1..38` to Sphere room-section data and found
no runtime buffer match for record `0`. This trace shows where a drawn wall's
pixels actually come from: the per-level `.TE_` container. Entry 1 is no
longer a candidate wall-texture source. Record `0` stays a valid raw image
witness, but nothing links it to rendered walls.

## Evidence

- 2026-09-11 cache-identity, wall-material and native-material-colour
  checkpoints in the project's AI coordination notes (private workspace).
- DOSBox guest trace with the material-context hook; trace SHA-256
  `824365cf90601d38366f5c2065600a1806750ed663d0b94115d67f0d791a5a92`.
- File-side reproduction: `tools/lol2_texture_container.py export --mix
  ./lol2_game/DAT/L20_BB.MIX --index 556 --shade-row 45`. Run on a GOG
  install, the blob, palette (`aee85cf7...`) and shade row 0x2D
  (`450e13dc...`) hashes match the checkpoint values. The span replay itself
  is not part of this repo.
