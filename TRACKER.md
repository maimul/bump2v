# TRACKER

Working board for Claude Code and Codex sessions in this repo. Read it at session start; update it
when work starts, finishes or blocks. One line per item, linking out for detail. IDs are `T-NNN` and
never reused. Done means verified, not just written: tests pass (`pytest --tb=short -q`), and for a
release, the new version shows on PyPI.

Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md). Research behind it: [docs/research/](docs/research/).

## Board
None. Personal repo with no team board, so `/track-sync` does not apply.

## Now
- (none)

## Next
- T-013 Roadmap Phase 2: structured JSON/TOML/YAML/XML edits, presets, schemes and build counters, prereleases and environment-suffixed versions (`{version}-dev.{run}`, OCI-safe), tag-only targets, monorepo, hooks.
- T-020 `check --unreleased` (refuse a version that is already published, for promotion to prod) and `check --branches dev,staging,main` (version drift across branches).
- T-021 Decision: no stricter "HEAD is already a version commit" guard in 1.x. It would turn a green pipeline red when someone pushes a locally made version commit; the Action skips instead (bumped=false), and 2.0 can make it the default.
- T-015 Roadmap Phase 4: agent skill, Claude plugin marketplace, MCP server, agent eval.
- T-016 Roadmap Phase 5, rest: `bump2v check` in team CI, the Releasing section in team repos' agent docs, a demo for the team, then Teh C Labs repos.
- T-017 Roadmap Phase 6: 2.0 (explicit push), name decision, README rewrite, launch, event CFPs (FOSSASIA closes ~Dec 2026, Docker KL 30 Dec 2026).
- T-003 The `testing` branch is stale (last commit at 1.1.16). Delete it once the user confirms.

## Blocked
- T-031 Try the GitLab templates on a real GitLab project, then publish them to the CI/CD Catalog (a GitLab project whose pipeline creates releases with the `release` keyword). Unblocks: the user (a GitLab project).
- T-030 List the Action on GitHub Marketplace: edit the newest release, tick "Publish this Action to the GitHub Marketplace", category Continuous integration. Web UI with 2FA only. Unblocks: the user.
- T-027 Team pilot, last repo: its audit gate blocks the first bump; fix PR open 2026-10-27 (lockfile + zod 4, Verify green on Node 20 locally; no PR CI there). Unblocks: the repo owner (merge; bump-once decision); then check the first bump.
- T-028 A team repo's second dev branch couldn't deploy: 15 orphan tags from pre-1.7.1 non-atomic pushes collided with its next version. Tags deleted 2026-10-27 (0 left on the remote). Unblocks: the team's next push to that branch (none since mid-September); then check it builds the next version.
- T-024 Revoke the old PyPI API token on pypi.org (removed from GitHub, still valid until revoked). Unblocks: the user.

## Done
The last three; older items are in [TRACKER-ARCHIVE.md](TRACKER-ARCHIVE.md).
- T-029 2026-10-27 1.11.0 on PyPI: image ghcr.io/maimul/bump2v (amd64+arm64, public, tags 1.11.0/1.11/1/latest), GitLab templates `release` and `check` (11 emulated-runner checks green on Linux CI), docs site live with llms.txt. sync: —
- T-014 2026-10-27 1.10.0 on PyPI: pre-commit hook `bump2v-check` (CI job; run from GitHub, autoupdate picks v1.10.0), GitHub Release per version, `v1` tag at v1.10.0 (moved by the publish workflow). sync: —
- T-023 2026-10-26 Team pilot, round 2: 12 pipelines on the Action (1.9.2); 11 first runs green end to end. Detail: [TRACKER-NOTES.md](TRACKER-NOTES.md#t-023) sync: —
