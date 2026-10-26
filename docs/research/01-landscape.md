# Competitive landscape: version-bumping and release-automation tools (as of 2026-10-26)

Stars, archive flags and latest releases come from the live GitHub REST API (`gh api repos/<repo>`). Downloads come from the pypistats, npm and crates.io APIs, all pulled on 2026-10-26. Links marked † point to the right page, but the particular feature wasn't re-checked that session.

## Q1. Status of bump2version, and what bump-my-version has that bump2v lacks

### Takeaway
bump2version is unmaintained but still downloaded heavily. Its README tells users to switch to bump-my-version, which is active, TOML-first and does more than bump2v. bump-my-version does not pick bumps from Conventional Commits and does not push. Those are the two things bump2v does that it doesn't.

### Cited Findings
- **bump2version's README:** "`bump2version` is **no longer maintained**. You should **switch to `bump-my-version`**." The repo is **not archived**. Its last push was 2025-02-20, it has no GitHub Releases and it has 1,120 stars. — [github.com/c4urself/bump2version](https://github.com/c4urself/bump2version)
- **bump2version's legacy base is still large:** about 1.23M PyPI downloads a month for `bump2version` and 638k for `bumpversion`, which "now installs the latest bump2version". — [pypistats bump2version](https://pypistats.org/packages/bump2version), [pypistats bumpversion](https://pypistats.org/packages/bumpversion), [README](https://github.com/c4urself/bump2version)
- **bump-my-version adoption:** 633 stars, v1.6.7 released 2026-10-25, and about 963k downloads a month. It is actively maintained, with 12 releases since June 2026. — [repo](https://github.com/callowayproject/bump-my-version), [pypistats](https://pypistats.org/packages/bump-my-version), [CHANGELOG](https://github.com/callowayproject/bump-my-version/blob/master/CHANGELOG.md)
- **Its stated goals:** pyproject.toml config, a click + rich CLI, and Pydantic validation. So unlike bump2v it has runtime dependencies. It recommends installing with `uv tool install`. — [README](https://github.com/callowayproject/bump-my-version)
- **Config:** a `[tool.bumpversion]` table in `pyproject.toml` or `.bumpversion.toml`. `sample-config` generates one. In v1.6.7 it also falls back to PEP 621 `project.version`. — [README](https://github.com/callowayproject/bump-my-version), [CHANGELOG](https://github.com/callowayproject/bump-my-version/blob/master/CHANGELOG.md)
- **Subcommands:** `bump`, `show`, `replace`, `sample-config` and `show-bump`. `show-bump` draws the tree of possible next versions. — [cli.py L61-65](https://github.com/callowayproject/bump-my-version/blob/master/bumpversion/cli.py), [README](https://github.com/callowayproject/bump-my-version)
- **Machine-readable output:** `bump-my-version show --format json|yaml`. — [show-subcommand.md](https://github.com/callowayproject/bump-my-version/blob/master/docs/explanation/show-subcommand.md)
- **Hooks:** `setup_hooks`, `pre_commit_hooks` and `post_commit_hooks`. A safety option, `allow_shell_hooks`, was added in 1.3.0 (2026-03-22), and shell hooks have been off by default since 1.4.0 (2026-06-17). — [hooks.md](https://github.com/callowayproject/bump-my-version/blob/master/docs/reference/hooks.md), [CHANGELOG](https://github.com/callowayproject/bump-my-version/blob/master/CHANGELOG.md)
- **File targeting and other features:** per-file `glob`/`glob_exclude`, `{repo_root}` expansion and per-file `parse`/`serialize`/`regex`. Also movable version tags and CalVer. — [file.md](https://github.com/callowayproject/bump-my-version/blob/master/docs/reference/configuration/file.md), [docs tree](https://github.com/callowayproject/bump-my-version/tree/master/docs)
- **Push and commit-based bumps:** the README lists "Committing changes, Tagging releases, Reading version numbers from tags". It does not mention pushing or choosing a bump from commits. — [README](https://github.com/callowayproject/bump-my-version)
- **Agent docs are for contributors only:** it ships an `AGENTS.md` and a `docs/agents/` folder, but these guide contributors' coding agents. They are not a feature for users. — [CHANGELOG 1.3.0](https://github.com/callowayproject/bump-my-version/blob/master/CHANGELOG.md)

### Inferences
- About 1.87M downloads a month still go to unmaintained bump2version/bumpversion, against about 963k for its successor. That means a large `.bumpversion.cfg` (INI) user base hasn't migrated. bump2v reads that same INI format, so it can be a drop-in, zero-dependency upgrade that adds `auto` and push. Much of this traffic is probably pinned CI installs, though.
- Things bump-my-version has that bump2v lacks: TOML/pyproject config, JSON/YAML `show`, `show-bump`, `replace`, hooks, globs, movable tags, PEP 621 fallback, and active upkeep.

### Gaps
- No user complaint thread found specifically about bump-my-version's config complexity. The only evidence is its own README, where pre-release support needs a verbose `(?x)` regex `parse` plus `serialize` lists and part definitions.

## Q2. Tool-by-tool comparison

### Takeaway
The market splits into two groups:
- **Ecosystem-bound release orchestrators:** semantic-release, changesets, release-please, release-plz, Nx. They dominate downloads.
- **Generic file bumpers:** bump-my-version, tbump, bump2v. They don't use Conventional Commits (bump2v's `auto` is the exception).

The few single-binary tools that use Conventional Commits either only print or tag a version (svu), lean on hooks to edit files (cocogitto), or are small (knope, sampo).

### Cited Findings

Glossary: CC = Conventional Commits. Downloads are per week (wk), month (mo) or the last 90 days (90d), as labelled.

| Tool | Runtime / install | Config | Edits files? | CC | Changelog | Monorepo | Stars | Downloads | Latest release / status |
|---|---|---|---|---|---|---|---|---|---|
| [bump2v](https://github.com/maimul/bump2v) | Python, no dependencies | INI `.bumpversion.cfg` | Yes (regex) | Yes (`auto`) | No | No | 1 | [313/mo](https://pypistats.org/packages/bump2v) | — |
| [bump-my-version](https://github.com/callowayproject/bump-my-version) | Python (click, rich, pydantic) | TOML | Yes (regex, glob) | No | No | Partial (globs) | 633 | [963k/mo](https://pypistats.org/packages/bump-my-version) | 1.6.7, 2026-10-25 |
| [tbump](https://github.com/your-tools/tbump) | Python | TOML | Yes, plus hooks | No | No | No | 173 | [125k/mo](https://pypistats.org/packages/tbump) | **GitHub repo archived**, moved to [Codeberg](https://codeberg.org/your-tools/tbump) (1 star, no releases there); last release v6.11.0, 2023-09 |
| [commitizen](https://github.com/commitizen-tools/commitizen) | Python | pyproject / `.cz.toml` | Yes, via [providers](https://github.com/commitizen-tools/commitizen/blob/master/docs/config/version_provider.md) (pep621, poetry, uv, cargo, npm, composer, scm) + `version_files` | Yes | Yes | Limited† | 3,541 | [2.97M/mo](https://pypistats.org/packages/commitizen) | v4.19.3, 2026-10-24 |
| [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) | Python | pyproject | Yes (`version_variables`, `version_toml`) | Yes | Yes | Limited† | 1,074 | [1.28M/mo](https://pypistats.org/packages/python-semantic-release) | v10.7.0, 2026-09-22; has a GitHub Action |
| [semantic-release](https://github.com/semantic-release/semantic-release) | Node required in CI | `.releaserc` | Via plugins | Yes | Via plugins | No (native) | 24,126 | [1.98M/wk](https://www.npmjs.com/package/semantic-release) | v25.0.9, 2026-08-05 |
| [release-please](https://github.com/googleapis/release-please) | Node / GitHub Action | JSON config + manifest | Yes (language files) | Required | Yes | Yes (manifest) | 7,677 | [236k/wk](https://www.npmjs.com/package/release-please) | v17.11.2, 2026-08-24; GitHub only |
| [changesets](https://github.com/changesets/changesets) | Node | `.changeset/` | package.json | No (intent files) | Yes | Core focus | 12,510 | [3.66M/wk](https://www.npmjs.com/package/@changesets/cli) | cli 3.0.3, 2026-09-14 |
| [commit-and-tag-version](https://github.com/absolute-version/commit-and-tag-version) | Node | `.versionrc` | Yes | Yes | Yes | No | 658 | [155k/wk](https://www.npmjs.com/package/commit-and-tag-version) | v13.3.0, 2026-10-15 |
| [standard-version](https://github.com/conventional-changelog/standard-version) | Node | — | Yes | Yes | Yes | No | 7,987 | [348k/wk](https://www.npmjs.com/package/standard-version) | **Deprecated**; last release 2022-05 |
| [Lerna](https://github.com/lerna/lerna) `version` | Node, maintained by the Nx team | lerna.json | Yes | Yes | Yes | Yes | 36,038 | [997k/wk](https://www.npmjs.com/package/lerna) | v10.1.1, 2026-10-12 |
| [Nx release](https://nx.dev/docs/guides/nx-release) | Node / Nx | nx.json | Yes (JS, Rust, Docker) | Opt-in | Yes | Release groups | [29,428](https://github.com/nrwl/nx) | [6.28M/wk](https://www.npmjs.com/package/nx) (all of Nx) | 24.0.1, 2026-10-23 |
| [release-it](https://github.com/release-it/release-it) | Node | `.release-it.json` | Yes | Via plugin | Via plugin | No | 9,079 | [528k/wk](https://www.npmjs.com/package/release-it) | 21.1.1, 2026-10-07 |
| [cocogitto](https://github.com/cocogitto/cocogitto) | Rust single binary (libgit2) | cog.toml | Via hooks | Yes | Yes | Yes† | 1,220 | [8k/90d](https://crates.io/crates/cocogitto) | 7.0.0, 2026-03-04; **last push 2026-04-22** |
| [git-cliff](https://github.com/orhun/git-cliff) | Rust (cargo, PyPI, npm) | cliff.toml | Changelog only | Yes | Yes (core) | Partial | 12,335 | [179k/mo PyPI](https://pypistats.org/packages/git-cliff), [91k/wk npm](https://www.npmjs.com/package/git-cliff) | v2.14.2, 2026-09-18 |
| [knope](https://github.com/knope-dev/knope) | Rust binary + [Action](https://github.com/knope-dev/knope) | knope.toml | Yes, multiple manifest types† | Yes, plus changesets | Yes | Yes | 201 | [2k/90d](https://crates.io/crates/knope) | 0.23.2, 2026-10-22 |
| [release-plz](https://github.com/release-plz/release-plz) | Rust only | release-plz.toml | Cargo.toml | Yes, plus semver checks | Yes (git-cliff) | Cargo workspaces | 1,512 | [41k/90d](https://crates.io/crates/release-plz) | 0.4.1, 2026-10-24; GitHub, Gitea and GitLab releases |
| [cargo-release](https://github.com/crate-ci/cargo-release) | Rust only | release.toml | Cargo.toml + replacements | No | No† | Workspaces | 1,595 | [17k/90d](https://crates.io/crates/cargo-release) | v1.1.7, 2026-10-21; tags, pushes and publishes |
| [GitVersion](https://github.com/GitTools/GitVersion) | .NET; Docker, GitHub Action, Azure task | GitVersion.yml | No; calculates the version only† | Commit hints† | No | — | 3,146 | — | 6.8.2, 2026-07-10 |
| [svu](https://github.com/caarlos0/svu) | Go single binary | `.svu.yml` | No; prints the next version | Yes | No | Prefixes | 877 | — | v3.4.1, 2026-05-01 |
| [goreleaser](https://github.com/goreleaser/goreleaser) | Go | `.goreleaser.yml` | No; reads the existing tag† | No | Release notes | — | 16,124 | — | v2.19.0, 2026-10-22 |
| [JReleaser](https://github.com/jreleaser/jreleaser) | Java | jreleaser.yml | Release orchestration† | Yes† | Yes | Yes† | 1,245 | — | v1.26.0, 2026-08-31 |
| [uv](https://docs.astral.sh/uv/guides/package/) `version --bump` | Rust binary | pyproject.toml | pyproject.toml only, plus lock/sync | No | No | Workspace member (from a [third-party page](https://skills.sh/kjanat/skills/uv-versioning) only) | [91,186](https://github.com/astral-sh/uv) | [127.8M/mo](https://pypistats.org/packages/uv) | Added in [0.7.x](https://github.com/astral-sh/uv/blob/main/changelogs/0.7.x.md); uv is now at 0.13.5 |
| [Poetry](https://python-poetry.org/docs/cli/#version)† `version` | Python | pyproject.toml | pyproject.toml only | No | No | No | 34,320 | [40.4M/mo](https://pypistats.org/packages/poetry) | 2.5.1, 2026-09-20 |
| [npm version](https://docs.npmjs.com/cli/commands/npm-version)† | Built into npm | package.json | Yes; commits and tags | No | No | Workspaces | — | — | Built in |
| **New:** [sampo](https://github.com/bruits/sampo) | Rust | changesets | crates, npm, Hex, PyPI, Packagist, Maven | No (changesets) | Yes | Multi-ecosystem | 235 | [1.1k/90d](https://crates.io/crates/sampo) | 0.23.0, 2026-10-24 |

More facts behind the table:
- **uv:** documents `--bump` for major, minor, patch, stable, alpha, beta, rc, post and dev, plus `--dry-run`. The page says nothing about git commits or tags. — [uv docs](https://docs.astral.sh/uv/guides/package/)
- **release-please:** its README says it "does not handle publication to package managers". A community PR adding GitLab support (#2631) was **closed unmerged on 2026-04-09**. — [README](https://github.com/googleapis/release-please), [PR #2631](https://github.com/googleapis/release-please/pull/2631)
- **standard-version:** its README says "`standard-version` is deprecated" and recommends release-please, or the commit-and-tag-version fork. — [README](https://github.com/conventional-changelog/standard-version)
- **svu:** its README suggests `alias gtn='git tag $(svu next)'`, so it doesn't tag by itself. — [README](https://github.com/caarlos0/svu)
- **Lerna:** "changed stewardship to Nx". — [README](https://github.com/lerna/lerna)
- **cocogitto:** "one standalone binary, the only system dependency is libgit2". — [README](https://github.com/cocogitto/cocogitto)
- **Other active tools worth knowing:** [changie](https://github.com/miniscruff/changie) (Go changelog fragments, 920 stars, v1.26.0, 2026-08) and [bumpp](https://github.com/antfu-collective/bumpp) (Node, [112k/wk](https://www.npmjs.com/package/bumpp)). [intuit/auto](https://github.com/intuit/auto) has had no release since 2025-11-14.

### Inferences
- Commitizen (about 3M downloads a month, multi-ecosystem providers, CC plus changelog) is bump2v's closest real competitor for a language-agnostic tool that uses Conventional Commits. Its weakness is that it needs Python and does not push.
- uv's `version --bump` makes the "just bump pyproject.toml" job a free built-in. That squeezes simple Python-only bumpers.

### Gaps
- No download numbers for GitHub Actions themselves, so release-please's real usage is undercounted.
- Monorepo depth for commitizen, python-semantic-release and cocogitto was not checked.

## Q3. Common user complaints

### Takeaway
The main complaints are:
- semantic-release is too eager, opaque and Node-bound.
- release-please only works on GitHub and is heavy to set up.
- Conventional Commits themselves face a strong 2026 backlash.
- Action-based release tools now carry supply-chain risk.

### Cited Findings
- **semantic-release:** "If you push five small fixes in an hour, you get five new versions." It is called a "black box", and non-Node plugins "often feel like second-class citizens". — [hazya.dev](https://blog.hazya.dev/why-i-swapped-semantic-release-for-release-please) (undated)
- **semantic-release needs Node:** "A Node.js version that meets our version requirement installed in your Continuous Integration environment". — [README](https://github.com/semantic-release/semantic-release)
- **release-please setup:** needs an Action, a config file, a manifest, a token with repo scope, and sometimes a `bootstrap-sha`. — [hazya.dev](https://blog.hazya.dev/why-i-swapped-semantic-release-for-release-please)
- **release-please platform:** GitHub only, and GitLab support was not merged. — [PR #2631](https://github.com/googleapis/release-please/pull/2631)
- **HN "Conventional Commits encourages focus on the wrong things"** (2026-06-05, 372 points, 276 comments):
  - Commenters say generated changelogs serve the wrong audience.
  - Reverting a breaking change can trigger an unwanted major bump.
  - Some prefer `git describe` or tags decided by people.
  - One commenter writes: "I've seen Claude Code aggressively use Conventional Commits, even when the project its working on doesn't use them."
  - Source: [HN 48414027](https://news.ycombinator.com/item?id=48414027)
- **Changesets' own framing:** it exists to solve "monorepos, keeping packages that rely on each other up to date", and it is JS/npm-centred. — [README](https://github.com/changesets/changesets)
- **Supply-chain compromise, 2026-06-24:** `codfish/semantic-release-action`, which is "referenced by thousands of workflows", had 23 tags repointed to malicious code.
  - The payload stole OIDC and GitHub tokens.
  - It committed AI-assistant and editor config files (`.claude/settings.json`, `.vscode/tasks.json`) into repos and "hijacks configurations for 13 AI coding assistants".
  - The advice was to "Pin actions to full-length commit SHA."
  - Sources: [StepSecurity](https://www.stepsecurity.io/blog/supply-chain-compromise-codfish-semantic-release-action), [HN](https://news.ycombinator.com/item?id=48663112). StepSecurity's write-up contradicts itself in places (7 vs 23 tags, two different commit SHAs).

### Inferences
- Coding agents already write Conventional Commits by default. That makes CC-driven `auto` a natural fit for agent workflows, even while human developers push back on CC.
- Zero dependencies plus a SHA-pinned or self-contained Action is now a selling point you can argue for on security grounds.

### Gaps
- No Reddit threads were retrieved.
- Several complaint sources are search-summary blogs that weren't fully read, such as [oleksiipopov.com](https://oleksiipopov.com/blog/npm-release-automation/) and [pkgpulse](https://www.pkgpulse.com/guides/semantic-release-vs-changesets-vs-release-it-release-2026). Treat them as secondary.

## Q4. Underserved gaps: does anything own "language-agnostic + zero runtime dependency + one command locally and in CI + agent-friendly"?

### Takeaway
No tool owns that position. Each candidate misses at least one of the criteria:

| Tool | What it misses |
|---|---|
| cocogitto | Edits files only through hooks; activity has stalled since April 2026 |
| knope | Small (201 stars) |
| svu | Only prints a version |
| commitizen | Needs Python; doesn't push |
| bump-my-version | No Conventional Commits; has dependencies |

No versioning tool with an official MCP server was found.

### Cited Findings
- The only MCP server found for this area is [changelog-ai-mcp](https://github.com/CSOAI-ORG/changelog-ai-mcp). It has 0 stars and was created on 2026-04-13. [ReleasePad's MCP server](https://www.releasepad.io/blog/releasepad-mcp-server/) is a hosted changelog product with no version numbers.
- bump-my-version's `show --format json` is the closest thing to agent-readable output among the bumpers. — [docs](https://github.com/callowayproject/bump-my-version/blob/master/docs/explanation/show-subcommand.md)
- Single-binary tools that use Conventional Commits: [svu](https://github.com/caarlos0/svu), [cocogitto](https://github.com/cocogitto/cocogitto), [git-cliff](https://github.com/orhun/git-cliff) and [knope](https://github.com/knope-dev/knope).
- Multi-ecosystem newcomer: [sampo](https://github.com/bruits/sampo), which is changeset-based rather than commit-based.

### Inferences (where bump2v can win)
1. **Migration wedge:** about 1.87M downloads a month still run unmaintained bump2version code with INI config. bump2v could offer "same config, zero deps, plus `auto` and push", and could also read `[tool.bumpversion]` TOML.
2. **Agent surface:** a JSON plan/dry-run output, stable exit codes, a no-prompt mode, an `AGENTS.md`/skill snippet and an MCP server. Nobody serious ships these yet.
3. **CI:** a self-contained, SHA-pinnable Action, pitched explicitly against the 2026 Action compromise.
4. **Built-in bumpers:** structured edits for pyproject, package.json and Cargo.toml would beat uv's, Poetry's and npm's single-ecosystem bumpers.
5. **Honest weak spots:** bump2v still needs a Python interpreter, so it is not a single binary. It has no changelog, monorepo support, TOML config, hooks or traction yet (1 star, 313 downloads a month).

### Gaps
- npm version, Poetry, GitVersion, goreleaser and JReleaser behaviour were not verified on their docs pages (marked †).
- No 2025–2026 survey of tool market share was found.
