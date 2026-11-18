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

## Release procedure (maintainers)

Every commit that reaches a public branch must carry the project's noreply identity as author and committer:

```bash
git -c user.name=KForestland -c user.email=261564562+KForestland@users.noreply.github.com commit ...
```

Before a release branch is pushed:

1. Work from contributor branches is squash-merged (`git merge --squash`), then committed with the identity above, so no contributor address enters the published history.
2. Never merge, cherry-pick or push from `refs/original`, a reflog entry or a commit hash from before a history rewrite.
3. In a fresh clone of the release branch, with `$LOL2_DAT` set to your game files, `python3 tools/check_all.py` must end with `ALL ... CHECKS PASSED`. It includes `tools/repo_guard.py`. The guard fails on game files and media, on machine paths and lane or agent names, and on any author or committer address in the branch history other than the allowed noreply ones (`ALLOWED_AUTHORS` in the guard; GitHub web merges may commit as `noreply@github.com`).
4. The tree must be clean after the checks, and the tools must write nothing into the repository.

## Pull Requests

Small, focused PRs are preferred:

- one doc cleanup pass
- one tooling cleanup pass
- one evidence/example addition

If something is not clean enough for the public repo yet, keep it out until it is reduced and verified.
