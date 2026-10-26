# TRACKER

Working board for Claude Code and Codex sessions in this repo. Read it at session start; update it
when work starts, finishes or blocks. One line per item, linking out for detail. IDs are `T-NNN` and
never reused. Done means verified, not just written: tests pass (`pytest --tb=short -q`), and for a
release, the new version shows on PyPI.

Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md). Research behind it: [docs/research/](docs/research/).

## Board
None. Personal repo with no team board, so `/track-sync` does not apply.

## Now
- T-007 Fix: `bump2v <part> --dry-run` still runs `git push` (`__main__.py` never checks `--dry-run`); release 1.6.2.
- T-008 Audit the Coolriots pipelines that run bump2v (dev/stg/prod): why they break, and what to fix in the pipelines and in bump2v. Running in the background; findings stay out of this public repo.

## Next
- T-009 Coolriots: one PR per pipeline pinning `bump2v>=1.6,<2`, plus the fixes T-008 finds. PRs only; the team merges.
- T-002 `CLAUDE.md` is out of date: no `test.yml` exists, bump2v no longer runs pytest before push (`a92e5ec`), workflows use checkout/setup-python v6. Add `test.yml` (3.10–3.14, ubuntu/macos/windows) and correct the doc.
- T-010 Publish with PyPI Trusted Publishing (`pypa/gh-action-pypi-publish`, attestations). Needs the user to add the trusted publisher on PyPI before the next release.
- T-011 Clean-up: drop `bump2v/test.ipynb`; make sure `bump2v.egg-info/` is ignored.
- T-012 Roadmap Phase 1 → 1.7.0: split `cli.main()` into load/plan/apply; `plan`, `release`, `show`, `check`, `init`; `--json`, exit codes, `--no-push`; `auto` fixes; first-match replace, newline/BOM, no partial bumps; TOML config.
- T-013 Roadmap Phase 2: structured JSON/TOML/YAML/XML edits, presets, schemes and build counters, prereleases, tag-only targets, monorepo, hooks.
- T-014 Roadmap Phase 3: GitHub Action, GitLab component, pre-commit hook, Docker image, docs site.
- T-015 Roadmap Phase 4: agent skill, Claude plugin marketplace, MCP server, agent eval.
- T-016 Roadmap Phase 5: Coolriots rollout on the Action, then Teh C Labs repos.
- T-017 Roadmap Phase 6: 2.0 (explicit push), name decision, README rewrite, launch, event CFPs (FOSSASIA closes ~Dec 2026, Docker KL 30 Dec 2026).
- T-003 The `testing` branch is stale (last commit at 1.1.16). Delete it once the user confirms.

## Blocked
- (none)

## Done
- T-001 2026-10-26 Version files synced to 1.6.1 (a251bc9); the core dry-run now previews 1.6.2. sync: —
- T-006 2026-10-26 Research notes in docs/research/, roadmap in docs/ROADMAP.md. sync: —
- T-004 2026-10-26 GitHub repo description, PyPI homepage link and topics set. sync: —
- T-005 2026-06-21 1.6.1 published on PyPI (confirmed via the PyPI API on 2026-10-26). sync: —
