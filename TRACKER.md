# TRACKER

Working board for Claude Code and Codex sessions in this repo. Read it at session start; update it
when work starts, finishes or blocks. One line per item, linking out for detail. IDs are `T-NNN` and
never reused. Done means verified, not just written: tests pass (`pytest --tb=short -q`), and for a
release, the new version shows on PyPI.

## Board
None. Personal repo with no team board, so `/track-sync` does not apply.

## Now
- (nothing in progress)

## Next
- T-001 Fix the version drift. `pyproject.toml` says 1.6.1, while `bump2v/__init__.py` and `.bumpversion.cfg` say 1.6.0. Tag `v1.6.1` (on PyPI) points at `8d31d5e`, which is not on `main` (`a92e5ec` has the same message). The next `bump2v patch` would try to create `v1.6.1` again. Set both files to 1.6.1 in one commit, with no tag.
- T-002 `CLAUDE.md` is out of date. It describes a `test.yml` CI workflow (Python 3.10–3.12) that doesn't exist; `pypi-publish.yml` is the only workflow and runs pytest on 3.x. It also names `checkout@v4`/`setup-python@v5`, but the workflow uses v6 of both. Add `test.yml` or correct the doc.
- T-003 The `testing` branch is stale (last commit at 1.1.16). Delete it unless something on it is still needed.

## Blocked
- (none)

## Done
- T-004 2026-10-26 GitHub repo description, PyPI homepage link and topics set. sync: —
- T-005 2026-06-21 1.6.1 published on PyPI (confirmed via the PyPI API on 2026-10-26). sync: —
