# Provenance

This note explains where the current LoL2 repo claims come from.

## Primary Sources

The current public LoL2 claims come from three source types:

### 1. Local Runtime Tracing

Used for:

- parser-site confirmation
- staged-block confirmation
- object-state watches
- suppression tests
- pivot-frame follow-write tracing

This is the strongest source type for the current compact-path branch claims.

### 2. Local Static / File Analysis

Used for:

- `L*_DC.MIX` record structure work
- `L9_DR.MIX` tag census
- texture/map and geometry output cataloging
- workspace inventory building

This is the strongest source type for the current inventory and record-family claims.

### 3. Live Memory Disassembly

Used for:

- native code analysis at runtime EIP addresses via DOSBox code dumps
- A0C3 correction (cleanup epilogue, not branch-steering)
- bit-field register layout at `+0xB4`
- `+0x6C` global timer resolution
- entity render function (6A50) decode
- wall texture renderer format confirmation

This is the strongest source type for the entity pipeline, bit-field layout, and renderer format claims.

### 4. Bounded Advisory AI Review

Used for:

- contradiction-hunting
- memo review
- dead-model cleanup
- ranked hypothesis support

Rule used in this repo:

- advisory output was never promoted directly
- only locally confirmed parts were folded into public docs

## What This Repo Avoids

This repo does not treat the following as public proof by themselves:

- private conversational history
- unconfirmed AI interpretations
- one-off speculative labels
- broad internal workspace clutter

## Best Reading Rule

When in doubt, trust:

1. the promoted docs in `docs/`
2. the inventories in `data/`
3. the witness/evidence maps in `evidence/`

Do not treat older private working notes outside this repo as cleaner truth than the promoted repo surface.
