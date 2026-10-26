# bump2v roadmap

Written 26 October 2026 from the notes in [research/](research/). Work items and their status live
in [../TRACKER.md](../TRACKER.md); this page says where the project is going and why.

## Positioning

> **One command to version any repo — every file, commit, tag, push — with a JSON plan agents can
> read and a zero-dependency install that drops into any CI.**

- **Wedge.** bump2version is unmaintained, yet it and `bumpversion` still get about 1.87M PyPI
  downloads a month, against about 963k for its successor, bump-my-version. bump2v reads the same
  `.bumpversion.cfg`, so it is a drop-in upgrade that adds `auto`, push, and an agent contract.
- **Gap.** No tool combines language-agnostic, zero runtime dependencies, one command locally and
  in CI, and safe for AI agents. Commitizen (closest) needs dependencies and doesn't push;
  bump-my-version has no Conventional-Commits bumps and doesn't push; release-please is GitHub-only;
  semantic-release needs Node; uv, npm and Poetry each bump one manifest.
- **Security.** A semantic-release GitHub Action was compromised in June 2026. A zero-dependency
  tool with an Action users pin by commit SHA is a concrete answer.
- **Honest weak spots.** It still needs a Python interpreter, and it has little traction yet.

Decisions: keep the Python codebase (reach comes from packaging, not a rewrite); keep the 1.x line
backward compatible; make push explicit in 2.0; the name is open to change before the external
launch, with `bump2v` kept as an alias.

## Phases

### Phase 0: housekeeping (1.6.x patches)
- Sync the version files (pyproject.toml was ahead of `.bumpversion.cfg` and `__init__.py`).
- Fix: `bump2v <part> --dry-run` still ran `git push`.
- CI test matrix on every push and PR; correct CLAUDE.md.
- Publish with PyPI Trusted Publishing (attestations).

### Phase 1: core hardening (1.7.0)
- Split the vendored `cli.main()` into load, plan and apply steps that return values instead of
  only logging. Everything below builds on it.
- New subcommands: `plan` (read-only), `release` (bump, commit, tag, push), `show`, `check`
  (drift between files), `init` (detect the stack, write the config, optionally add a Releasing
  section to CLAUDE.md or AGENTS.md). Bare `bump2v <part>` behaves as before.
- `--json` output with a `format_version`; documented exit codes; plain output when not on a
  terminal, or when `NO_COLOR`, `CI` or `CLAUDECODE` is set; `--no-push` and a `push` config key.
- `auto`: respects `tag_name` patterns, works when tagging is off, stops on shallow clones.
- File edits: first match only (no more bumping dependency entries), no silent bare-version
  fallback, line endings and BOM preserved, no partial bumps.
- Reads `.bumpversion.toml` and `[tool.bumpversion]` in `pyproject.toml`.

### Phase 2: universal formats (1.8–1.9)
- Key-path edits for JSON, TOML, YAML, XML and plist, with presets (npm, pyproject, cargo, helm,
  expo, flutter, maven, dotnet, gradle, plist, docker label, go tag).
- Version schemes (SemVer, PEP 440, CalVer), build counters that never reset (Android
  `versionCode`, iOS `buildNumber`, Flutter `+N`), per-target rendering (OCI tags, integer-only
  fields), prereleases.
- Tag-only targets (Go, Terraform, GitHub Actions) and an opt-in moving major tag.
- Monorepo packages with fixed or independent versions; hooks for lockfiles and changelog tools.

### Phase 3: distribution
- A composite GitHub Action (`pipx run`, outputs `version`, checks fetch depth and tags), a GitLab
  CI/CD component, a pre-commit hook (`bump2v check`), a container image, a docs site.
- Standalone binaries, Homebrew, npm and Scoop only when demand shows up.

### Phase 4: AI agents
- An Agent Skill (`check` → `plan --json` → confirm → `release`), a Claude Code plugin
  marketplace in this repo, a Codex skill, an MCP server (`bump2v mcp`).
- An eval: fixture repos where agents are asked to cut a release, with and without the
  instructions snippet; score file consistency, the tag, and no unrequested push.

### Phase 5: team rollout
- Move the team's pipelines from hand-written glue to the Action, add `bump2v check` to CI, add
  Releasing instructions to each repo's agent file, measure the result.

### Phase 6: 2.0 and launch
- 2.0: only `release` pushes.
- Name decision; README rewrite (demo GIF, comparison table, migration guide, AI-agents section).
- Launch: blog post with real numbers, Show HN, r/Python, newsletters; talks and demos at regional
  events (FOSSASIA, DevFest KL, Docker KL, PyCon MY, Claude community meetups).
