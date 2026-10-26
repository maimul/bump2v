# TRACKER

Working board for Claude Code and Codex sessions in this repo. Read it at session start; update it
when work starts, finishes or blocks. One line per item, linking out for detail. IDs are `T-NNN` and
never reused. Done means verified, not just written: tests pass (`pytest --tb=short -q`), and for a
release, the new version shows on PyPI.

Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md). Research behind it: [docs/research/](docs/research/).

## Board
None. Personal repo with no team board, so `/track-sync` does not apply.

## Now
- T-018 Remove the now-unused `BUMP2V` repo secret and `PYPI_API_TOKEN` environment from GitHub. Needs the user's OK (deletes credentials config).
- T-008 Audit the team pipelines that run bump2v (dev/stg/prod): why they break, what to fix in the pipelines and in bump2v. Running in the background. Details stay out of this public repo.

## Next
- T-009 Team pilot: one PR per pipeline pinning `bump2v>=1.6,<2`, plus the fixes T-008 finds. PRs only; the team merges.
- T-013 Roadmap Phase 2: structured JSON/TOML/YAML/XML edits, presets, schemes and build counters, prereleases, tag-only targets, monorepo, hooks.
- T-014 Roadmap Phase 3: GitHub Action, GitLab component, pre-commit hook, Docker image, docs site.
- T-015 Roadmap Phase 4: agent skill, Claude plugin marketplace, MCP server, agent eval.
- T-016 Roadmap Phase 5: team rollout on the Action, then Teh C Labs repos.
- T-017 Roadmap Phase 6: 2.0 (explicit push), name decision, README rewrite, launch, event CFPs (FOSSASIA closes ~Dec 2026, Docker KL 30 Dec 2026).
- T-003 The `testing` branch is stale (last commit at 1.1.16). Delete it once the user confirms.

## Blocked
- (none)

## Done
- T-012 2026-10-26 1.7.0 on PyPI (wheel + sdist, requires-python >=3.11): plan/release/show/check/init, `--json`, exit codes, `--no-push`, TOML config, safer file edits, `auto` by tag_name or version commit. Installed fresh on 3.15 and run. sync: —
- T-010 2026-10-26 Published 1.7.0 through Trusted Publishing (run 40291785502); PyPI shows a provenance attestation from `pypi-publish.yml`. sync: —
- T-007 2026-10-26 1.6.2 on PyPI: never pushes on `--dry-run`/no commit (`3cea284`), runs on Python 3.15 (`sre_constants` removed, `6e71693`). sync: —
- T-002 2026-10-26 `test.yml` green on 3.10–3.15 × ubuntu/macos/windows (run 40285273117); CLAUDE.md corrected. sync: —
- T-011 2026-10-26 Scratch notebook removed; local builds no longer ship the `bump2version/` clone (`b95315e`). sync: —
- T-001 2026-10-26 Version files synced to 1.6.1 (a251bc9); the core dry-run now previews 1.6.2. sync: —
- T-006 2026-10-26 Research notes in docs/research/, roadmap in docs/ROADMAP.md. sync: —
- T-004 2026-10-26 GitHub repo description, PyPI homepage link and topics set. sync: —
- T-005 2026-06-21 1.6.1 published on PyPI (confirmed via the PyPI API on 2026-10-26). sync: —
