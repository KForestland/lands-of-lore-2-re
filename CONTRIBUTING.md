# Contributing

Thanks for contributing to the public *Lands of Lore II* reverse-engineering repo.

## Scope

Good contributions for this repo:

- wording and clarity fixes in the documentation
- evidence-backed corrections
- tool fixes and new readers (no game data in the repository)
- output examples that improve reviewability
- machine-readable summary updates that match the documentation

Out of scope for this repo:

- retail game files
- full asset dumps
- raw private trace ledgers
- speculative claims presented as settled truth

## Working Rules

- Prefer narrower claims over attractive overreach.
- Keep runtime proof, static proof, and interpretation distinct.
- Update the existing format page before adding a new note.
- If a result holds only for one sample or one phase of the game, say so directly.

## Repo Shape

- `docs/` holds the published pages.
- `evidence/` holds witness maps and short evidence indexes.
- `data/` holds machine-readable summaries.
- `examples/` holds small outputs made by the tools, without game pixels.
- `tools/` holds the readers and analysers.

## Checks without game files

Run `python3 -m unittest` and `python3 tools/repo_guard.py --check`
from the repository root. The tests build their own fixtures in memory or
in a temporary directory. GitHub Actions runs these same commands on
pushes and pull requests. CI uses the runner's Python (3.12); the minimum version in the README is not tested there.

## Release procedure (maintainers)

Every commit that reaches a public branch must carry the project's noreply identity as author and committer:

```bash
git -c user.name=KForestland -c user.email=261564562+KForestland@users.noreply.github.com commit ...
```

Before a release branch is pushed:

1. Contributor work is squash-merged and committed with the identity above.
2. In a fresh clone of the release branch, with `$LOL2_DAT` set to your game files, `python3 tools/check_all.py` must end with `ALL ... CHECKS PASSED` and `python3 -m unittest` must pass. It includes `tools/repo_guard.py`, which fails on game files and media, on files over 300 KB, and on machine paths and on the words in an optional local word list (`.git/info/private_words`, never tracked). Then run `python3 tools/repo_guard.py --check --release`: it also fails on any author or committer address in the branch history other than the allowed noreply ones (`ALLOWED_AUTHORS`; GitHub web merges may commit as `noreply@github.com`). Contributors do not need `--release`.
3. The tree must be clean after the checks, and the tools must write nothing into the repository.

## Pull Requests

Small, focused PRs are preferred:

- one doc cleanup pass
- one tooling cleanup pass
- one evidence/example addition

If something is not clean enough for the public repo yet, keep it out until it is reduced and verified.
