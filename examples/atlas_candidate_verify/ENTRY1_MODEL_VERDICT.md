# LOCAL.MIX Entry 1 Model Verdict

> **Superseded (2026-10-31).** A runtime witness traced a drawn wall
> material to the per-level `.TE_` texture container (L20_BB descriptor
> `556`), not to `LOCAL.MIX` entry `1`. Entry 1 is no longer a wall-texture
> candidate. See
> [lol2-wall-material-provenance.md](../../docs/lol2-wall-material-provenance.md).
> The note below is kept as history.

Date: 2026-04-02

This note records the current repo-safe verdict for `LOCAL.MIX` entry
`1` after the atlas verifier was cross-checked against the repo's
existing Sphere room-section parser.

## Short Verdict

`LOCAL.MIX` entry `1` should **not** currently be treated as a solved
"wall texture atlas with 39 sub-textures".

The safer read is:

- record `0` is a strong reproducible raw witness
- records `1..38` are at least as well explained by the repo's existing
  Sphere room-section model as by the older atlas/sub-texture model

So the old atlas interpretation survives only in a narrow form.

## What Is Still Strong

### 1. Record `0` is real and reproducible

The atlas verifier reproduces the repo example exactly:

- raw texture count: `1`
- compressed record count: `38`
- texture `0`: `128x128`
- setup-palette render matches:
  [L1_wall_texture_000.png](../../examples/L1_wall_texture_000.png)

Artifacts:

- [lol2_verify_wall_atlas_candidate.py](../../tools/lol2_verify_wall_atlas_candidate.py)
- [report.json](../../examples/atlas_candidate_verify/report.json)
- [tex0_setup.png](../../examples/atlas_candidate_verify/tex0_setup.png)
- [tex0_local.png](../../examples/atlas_candidate_verify/tex0_local.png)
- [ENTRY1_RUNTIME_BUFFER_CHECK_2026-04-02.md](../../examples/atlas_candidate_verify/ENTRY1_RUNTIME_BUFFER_CHECK_2026-04-02.md)
- [entry1_runtime_witness_check.json](../../examples/atlas_candidate_verify/entry1_runtime_witness_check.json)

### 2. Entry 1 is definitely structured

The old atlas parse is not random:

- `39` records
- stable offsets
- stable per-record sub-headers
- one raw record and many wrapped/compressed records

That part remains useful as a structural witness.

## What Is No Longer The Best Default Read

### Records `1..38` as independent texture sub-images

The new cross-check shows:

- atlas parser record count = `39`
- Sphere parser section count = `39`
- widths/heights match for all records
- `total_size` matches for all records

This means the same bytes also parse cleanly as the repo's known Sphere
room-section structure.

That is not a minor coincidence. It directly weakens the old
"these are 39 compressed texture sub-records" reading.

## Best Current Interpretation Split

### Keep

- `entry 1 record 0` as a reproducible raw image witness
- `entry 1` as a structured serialized runtime-oriented container
- the fact that the compressed records are wrapped records, not plain
  byte-0 `Format80` payloads

### Demote

- "records `1..38` are mipmaps/sub-textures by default"
- "skip-based `Format80` probing of records `24..38` is a primary path
  to texture closure"
- "the `16x16` later family is best understood first as image data"

## Why The Earlier Skip/Seed Results Matter Less Now

The `24..38` range that produced the most confusing `skip 4` and seeded
decode behavior is exactly the same range that the Sphere decoder treats
as chained `16x16` room sections.

That explains:

- why direct `Format80` from byte `0` failed
- why body-start classes seemed record-dependent
- why some streams looked self-seeding and others dependent

Those observations are still useful as evidence that the records are
wrapped and runtime-oriented, but they are no longer good evidence that
the records are texture sub-images.

## Practical Effect On The Texture Hunt

Do **not** use `LOCAL.MIX` entry `1` records `1..38` as the main texture
closure lane unless they first beat the Sphere interpretation with
stronger evidence.

Better current usage:

- keep record `0` as a witness
- treat records `1..38` as Sphere/room-structure data by default
- continue texture closure on a lane that is not already better explained
  by chained room-section decoding

Follow-up on 2026-04-02:

- a direct check against preserved runtime wall buffers found no full
  match, no substring reuse, and no exact `8x8` or `16x16` patch reuse
  for record `0`
- this does not kill Entry `1` record `0` as a witness, but it does
  weaken the simplest "captured runtime wall buffer == raw tex0" story

## Best Next Repo-Safe Step

If work continues on entry `1`, it should now answer one of these
questions explicitly:

1. Is record `0` a true wall-surface source, a staging surface, or just
   one convenient raw witness?
2. Are any bytes from entry `1` consumed by the wall renderer in a way
   that the Sphere room-section model cannot explain?
3. Is the actual wall-texture source somewhere else entirely, with entry
   `1` serving only map/room composition roles?

Until one of those is answered, the repo-safe verdict is:

`entry 1 is partially useful, but not texture-closure-safe beyond record 0`.
