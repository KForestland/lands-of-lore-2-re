# Contributing

Thanks for contributing to the public *Lands of Lore II* reverse-engineering repo.

## Scope

Good contributions for this repo:

- wording and clarity fixes in promoted docs
- evidence-backed corrections
- public-safe tooling cleanup
- output examples that improve reviewability
- machine-readable summary updates that match promoted docs

Out of scope for this repo:

- retail game files
- full asset dumps
- raw private trace ledgers
- speculative claims presented as settled truth

## Working Rules

- Prefer narrower claims over attractive overreach.
- Keep runtime proof, static proof, and interpretation distinct.
- Update existing promoted docs before adding new scattered notes.
- If a result is witness-local or phase-local, say so directly.

## Repo Shape

- `docs/` holds promoted writeups.
- `evidence/` holds witness maps and short evidence indexes.
- `data/` holds machine-readable summaries.
- `examples/` holds public-safe screenshots and outputs.
- `tools/` holds public-safe analysis and extraction helpers.

## Pull Requests

Small, focused PRs are preferred:

- one doc cleanup pass
- one tooling cleanup pass
- one evidence/example addition

If something is not clean enough for the public repo yet, keep it out until it is reduced and verified.
