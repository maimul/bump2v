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

## Next
- T-013 Roadmap Phase 2: structured JSON/TOML/YAML/XML edits, presets, schemes and build counters, prereleases and environment-suffixed versions (`{version}-dev.{run}`, OCI-safe), tag-only targets, monorepo, hooks.
- T-014 Roadmap Phase 3: GitHub Action (fetch to the branch tip, skip when the tip is already a version commit, `--retry` on a lost push race, outputs version/tag/sha/bumped), GitLab component, pre-commit hook, Docker image, docs site.
- T-020 `check --unreleased` (refuse a version that is already published, for promotion to prod) and `check --branches dev,staging,main` (version drift across branches).
- T-021 Decision: no stricter "HEAD is already a version commit" guard in 1.x. It would turn a green pipeline red when someone pushes a locally made version commit; the Action skips instead (bumped=false), and 2.0 can make it the default.
- T-015 Roadmap Phase 4: agent skill, Claude plugin marketplace, MCP server, agent eval.
- T-016 Roadmap Phase 5: team rollout on the Action, then Teh C Labs repos.
- T-017 Roadmap Phase 6: 2.0 (explicit push), name decision, README rewrite, launch, event CFPs (FOSSASIA closes ~Dec 2026, Docker KL 30 Dec 2026).
- T-003 The `testing` branch is stale (last commit at 1.1.16). Delete it once the user confirms.

## Blocked
- T-009 Team pilot: one PR per repo pinning `bump2v>=1.6.2,<2` (approved). The 13 one-line changes are ready in local clones, but pushing to the team repos was blocked by the permission check. Unblocks: user (run the prepared script or allow the push). Further pipeline fixes and deleting stale tags need the user's OK.

## Done
- T-019 2026-10-26 1.7.1 on PyPI: branch and tag pushed atomically, so a rejected push leaves no orphan tag (`4572d22`; test fails on the old code). sync: —
- T-008 2026-10-26 Team pipeline audit (dev/stg/prod): failures came from how pipelines call bump2v (push races, non-atomic tag push, missing config, branch rules), not from bump2v; no pipeline parses its output. Report kept outside this public repo. sync: —
- T-012 2026-10-26 1.7.0 on PyPI (wheel + sdist, requires-python >=3.11): plan/release/show/check/init, `--json`, exit codes, `--no-push`, TOML config, safer file edits, `auto` by tag_name or version commit. Installed fresh on 3.15 and run. sync: —
- T-010 2026-10-26 Published 1.7.0 through Trusted Publishing (run 40291785502); PyPI shows a provenance attestation from `pypi-publish.yml`. sync: —
- T-007 2026-10-26 1.6.2 on PyPI: never pushes on `--dry-run`/no commit (`3cea284`), runs on Python 3.15 (`sre_constants` removed, `6e71693`). sync: —
- T-002 2026-10-26 `test.yml` green on 3.10–3.15 × ubuntu/macos/windows (run 40285273117); CLAUDE.md corrected. sync: —
- T-011 2026-10-26 Scratch notebook removed; local builds no longer ship the `bump2version/` clone (`b95315e`). sync: —
- T-001 2026-10-26 Version files synced to 1.6.1 (a251bc9); the core dry-run now previews 1.6.2. sync: —
- T-006 2026-10-26 Research notes in docs/research/, roadmap in docs/ROADMAP.md. sync: —
- T-004 2026-10-26 GitHub repo description, PyPI homepage link and topics set. sync: —
- T-005 2026-06-21 1.6.1 published on PyPI (confirmed via the PyPI API on 2026-10-26). sync: —
