# TRACKER

Working board for Claude Code and Codex sessions in this repo. Read it at session start; update it
when work starts, finishes or blocks. One line per item, linking out for detail. IDs are `T-NNN` and
never reused. Done means verified, not just written: tests pass (`pytest --tb=short -q`), and for a
release, the new version shows on PyPI.

Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md). Research behind it: [docs/research/](docs/research/).

## Board
None. Personal repo with no team board, so `/track-sync` does not apply.

## Now
- T-014 Roadmap Phase 3, first part: pre-commit hook (`bump2v check`), a moving `v1` tag for the Action, a GitHub Release per version, Marketplace listing (the user ticks the box).

## Next
- T-029 Roadmap Phase 3, rest: GitLab CI/CD component, container image, docs site.
- T-013 Roadmap Phase 2: structured JSON/TOML/YAML/XML edits, presets, schemes and build counters, prereleases and environment-suffixed versions (`{version}-dev.{run}`, OCI-safe), tag-only targets, monorepo, hooks.
- T-020 `check --unreleased` (refuse a version that is already published, for promotion to prod) and `check --branches dev,staging,main` (version drift across branches).
- T-021 Decision: no stricter "HEAD is already a version commit" guard in 1.x. It would turn a green pipeline red when someone pushes a locally made version commit; the Action skips instead (bumped=false), and 2.0 can make it the default.
- T-015 Roadmap Phase 4: agent skill, Claude plugin marketplace, MCP server, agent eval.
- T-016 Roadmap Phase 5, rest: `bump2v check` in team CI, the Releasing section in team repos' agent docs, a demo for the team, then Teh C Labs repos.
- T-017 Roadmap Phase 6: 2.0 (explicit push), name decision, README rewrite, launch, event CFPs (FOSSASIA closes ~Dec 2026, Docker KL 30 Dec 2026).
- T-003 The `testing` branch is stale (last commit at 1.1.16). Delete it once the user confirms.

## Blocked
- T-027 Team pilot, last repo: its audit gate blocks the first bump; fix PR open 2026-10-27 (lockfile + zod 4, Verify green on Node 20 locally; no PR CI there). Unblocks: the repo owner (merge; bump-once decision); then check the first bump.
- T-028 A team repo's second dev branch couldn't deploy: 15 orphan tags from pre-1.7.1 non-atomic pushes collided with its next version. Tags deleted 2026-10-27 (0 left on the remote). Unblocks: the team's next push to that branch (none since mid-September); then check it builds the next version.
- T-024 Revoke the old PyPI API token on pypi.org (removed from GitHub, still valid until revoked). Unblocks: the user.

## Done
The last three; older items are in [TRACKER-ARCHIVE.md](TRACKER-ARCHIVE.md).
- T-023 2026-10-26 Team pilot, round 2: 12 pipelines on the Action (1.9.2); 11 first runs green end to end. Detail: [TRACKER-NOTES.md](TRACKER-NOTES.md#t-023) sync: —
- T-026 2026-10-26 1.9.0 (`auto` reads a merge commit's PR title) and 1.9.2 (outputs on a [skip ci] tip; explicit UTF-8). 1.9.1 never published. Detail: [TRACKER-NOTES.md](TRACKER-NOTES.md#t-026) sync: —
- T-025 2026-10-26 1.8.2 on PyPI: `auto` ignores tags when tag = False (it had counted from tags left over from before tagging was turned off and planned a major bump). Tests, Action (3 OSes) and publish green. sync: —
