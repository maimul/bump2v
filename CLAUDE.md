# bump2v — Claude Code Instructions

## What this repo is

`bump2v` is a PyPI package that wraps and extends bump2version. The bump2version source is **vendored** (copied) into `bump2v/bumpversion/` so we own all the code and can modify it freely. The `bump2v/__main__.py` is the CLI entry point that adds guards, dry-run preview, and git push on top of the core logic.

## Repo structure

```
bump2v/
  __main__.py           # CLI entry point — subcommands, auto, guards, push; calls bumpversion.cli
  output.py             # Messages vs data, --json shape, exit codes
  init.py               # `bump2v init`: detect where a project keeps its version
  bumpversion/          # Vendored bump2version source (our fork — edit freely)
    cli.py              # Core logic: argument parsing, file replacement, git commit/tag
    vcs.py              # Git and Mercurial VCS integration
    version_part.py     # Version parsing and serialization
    utils.py            # ConfiguredFile, file search/replace helpers
    functions.py        # NumericFunction, ValuesFunction for version part bumping
    exceptions.py       # All custom exceptions
    __init__.py         # Package version metadata
pyproject.toml          # Package metadata and dependencies (no external deps)
requirements.txt        # Empty — no dependencies
.bumpversion.cfg        # bump2v uses itself to version itself
action.yml              # The GitHub Action (composite): runs bump2v from its own checkout
.pre-commit-hooks.yaml  # The pre-commit hook `bump2v-check` (runs `bump2v check`)
Dockerfile              # The image ghcr.io/maimul/bump2v (.dockerignore keeps it to the package)
templates/              # GitLab CI/CD templates (component format): release.yml, check.yml
zensical.toml           # The docs site config; pages in website/, built into site/ (gitignored)
website/                # Docs site pages (guides per stack and CI); the reference stays in README
.github/workflows/
  test.yml              # Tests on every push to main and every PR (Python 3.11–3.15, Linux/macOS/Windows),
                        # the pre-commit hook, and the image running the GitLab templates
  action.yml            # Runs the GitHub Action against a throwaway repo on all three OSes
  pypi-publish.yml      # On a version tag (v1.10.0): tests, PyPI, then the GitHub Release, the v1 tag
                        # and the container image
  docs.yml              # Builds the docs site (--strict) on PRs and main; deploys it to Pages from main
tests/                  # pytest suite (see Tests below)
docs/
  ROADMAP.md            # Where the project is going and why
  research/             # Research notes behind the roadmap (sourced, dated)
README.md               # GitHub-facing docs (Markdown)
README.rst              # PyPI-facing docs (reStructuredText — keep in sync with README.md)
TRACKER.md              # Working board: what is in progress, next, blocked, done
AGENTS.md               # Pointer for Codex and other agents to this file and TRACKER.md
```

This repo is **public**. Never commit details of private repos that use bump2v (team pipelines,
failure logs, repo names); keep those in the tracker of the repo they belong to.

## Source of truth for versions — critical concept

When setting up `.bumpversion.cfg` for a project, the version source of truth depends on the stack:

| Stack | Source of truth file | Field |
|---|---|---|
| Node.js / React / JS | `package.json` | `"version": "1.0.0"` |
| Python | `appInfo.py` (or similar) | `__version__ = "1.0.0"` |

The `current_version` in `.bumpversion.cfg` **must always match** the version in the source of truth file. bump2v keeps them in sync on every run — never edit either one manually.

Example for Node.js/React:
```ini
[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
```

Example for Python:
```ini
[bumpversion:file:app/appInfo.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"
```

## Standard workflow for every change

1. **Make the code change** in `bump2v/bumpversion/` or `bump2v/__main__.py`

2. **Verify the import chain works** before committing:
   ```zsh
   python3 -c "from bump2v.bumpversion.cli import main; print('OK')"
   ```

3. **Commit** with a clear descriptive message (no Co-Authored-By):
   ```zsh
   git add <files>
   git commit -m "fix: describe what you fixed"
   ```

4. **Update README.md and README.rst** if any user-facing behaviour changed (new flag, new config option, bug fix that changes behaviour). Both files must stay in sync.

5. **Run the tests** (`pytest --tb=short -q`) and preview the release. Since 1.6.2 a dry run
   writes, commits and pushes nothing:
   ```zsh
   bump2v patch --dry-run
   ```

6. **Bump and publish** using bump2v itself (we dogfood our own tool):
   ```zsh
   bump2v patch    # bug fix or doc update
   bump2v minor    # new feature or flag added
   bump2v major    # breaking change to CLI or config format
   bump2v auto     # let commit messages decide (Conventional Commits)
   ```
   This updates `pyproject.toml`, commits, creates a `v*` tag, and pushes. GitHub Actions picks up the tag and publishes to PyPI automatically.

**Do NOT** run `git push` manually — `bump2v` handles it.
**Do NOT** edit the version in `pyproject.toml` manually — `bump2v` handles it.
**Do NOT** add Co-Authored-By to commit messages.

## Version bump level guide

| Change type | Command |
|---|---|
| Fix a bug in existing behaviour | `bump2v patch` |
| Add a new CLI flag or config option | `bump2v minor` |
| Change how an existing flag works (breaking) | `bump2v major` |
| Update README, CLAUDE.md, or docs only | `bump2v patch` |
| Vendor a new upstream bump2version version | `bump2v minor` |
| Remove or rename an existing flag | `bump2v major` |

## When adding a new CLI flag or config option

1. Add the argument to the appropriate parse phase in `bump2v/bumpversion/cli.py`:
   - `_parse_arguments_phase_1` — early flags evaluated before the full config is loaded (e.g. `--tag-only`)
   - `_parse_arguments_phase_3` — standard flags (e.g. `--ignore-missing-version`, `--extra-files`)
2. If it is a **boolean** config option, add it to the `boolvaluename` loop in `_load_configuration`
3. If it is a **list** config option, add string→list splitting after that loop
4. Wire the new flag into the relevant function(s) in `cli.py`
5. Update `README.md` and `README.rst` with a usage example
6. Commit, then `bump2v minor`

## When fixing a bug in bumpversion logic

All the core logic lives in `bump2v/bumpversion/`. Edit it directly — there is no upstream to sync with. File responsibilities:

| File | What to edit here |
|---|---|
| `cli.py` | Argument parsing, main flow, config loading, git commit/tag orchestration |
| `vcs.py` | Git/Mercurial commands, dirty-check logic, tag creation, file staging |
| `version_part.py` | Version parsing regex, serialization formats, part bumping |
| `utils.py` | File search/replace, version-in-file existence checks |
| `functions.py` | Numeric and values-based version part increment logic |
| `exceptions.py` | Add new exception types here |

## Tests

Tests live in `tests/` and use pytest. Run them with:

```zsh
pytest --tb=short -q
```

bump2v does **not** run the tests for you before it pushes (that was removed in `a92e5ec`), so run
them yourself before `bump2v patch|minor|major`. CI runs them in two places:
1. **`test.yml`** on every push to main and every PR, across Python 3.11–3.15 on Linux, macOS and Windows.
2. **`pypi-publish.yml`** as a required job before building and publishing, on Linux, macOS and
   Windows (Python 3.11 and the latest 3.x). Windows-only bugs (path separators, the console
   codepage) reached PyPI once when this job ran on Linux alone.

Always pass `encoding="utf-8"` when code or tests read or write text (`open`, `read_text`,
`write_text`, `subprocess(..., text=True)`): Windows otherwise uses the console codepage and
breaks on `→`. CI's "Explicit text encodings" job fails on any default-encoding access; run it
locally with `python -X warn_default_encoding -m pytest -q -W error::EncodingWarning`.

Integration tests that commit, tag and push use a throwaway repo and a bare remote under
`tmp_path`, with `GIT_CONFIG_GLOBAL` pointed at an empty file (see the `repo` fixture in
`tests/test_auto.py`). Never let a test touch this repo's own git state.

When adding a new feature or fixing a bug, add a corresponding test:

| Changed file | Test file |
|---|---|
| `bumpversion/functions.py` | `tests/test_functions.py` |
| `bumpversion/version_part.py` | `tests/test_version_part.py` |
| `bumpversion/cli.py` | `tests/test_cli.py` |
| `bumpversion/vcs.py` | `tests/test_vcs.py` |
| `bump2v/__main__.py` | `tests/test_auto.py` |
| `bump2v/output.py` | `tests/test_output.py` |
| `bump2v/init.py` | `tests/test_init.py` |
| `Dockerfile`, `templates/*.yml` | `tests/ci/gitlab_templates.py` (needs Docker and PyYAML; CI job `container`) |
| `bumpversion/utils.py` (file edits) | `tests/test_cli.py` |

## Publishing checklist

Before running `bump2v minor` or `bump2v major`:
- [ ] `pytest --tb=short -q` passes
- [ ] README.md updated with new flags or changed behaviour
- [ ] README.rst updated to match README.md
- [ ] Commit message is descriptive

## GitHub Actions — how PyPI publish works

`.github/workflows/pypi-publish.yml` triggers on version tags (`v[0-9]+.[0-9]+.[0-9]+`), not on the
moving `v1` tag. It:
1. Runs the tests (job `test`); the publish job needs it to pass
2. Checks out the repo (`actions/checkout@v6`) and sets up Python (`actions/setup-python@v6`)
3. Builds the wheel and sdist: `python -m build`
4. Uploads with `pypa/gh-action-pypi-publish` (pinned to a commit SHA) through PyPI Trusted
   Publishing: the `deploy` job runs in the `pypi` environment with `id-token: write`, so there is
   no stored API token, and PyPI records attestations. The trusted publisher on PyPI must name
   owner `maimul`, repo `bump2v`, workflow `pypi-publish.yml`, environment `pypi`.
5. After the upload (job `github-release`): force-moves the major tag (`v1`) to this version unless a
   newer 1.x exists (a backport leaves it), and creates the GitHub Release with the commits since
   the previous version. Never move `v1` by hand to a version that isn't on PyPI.
6. After the upload (job `image`): builds the image for amd64 and arm64 and pushes it to
   `ghcr.io/maimul/bump2v` as `X.Y.Z`, plus `X.Y`, `X` and `latest` when no newer version holds them.

Each release also bumps the version pins in the GitLab templates (their default image), both
READMEs and the docs site (`.bumpversion.cfg` lists them), so `bump2v check` covers them too.

The GitHub Marketplace listing is the owner's step in the web UI (2FA): edit the release, tick
"Publish this Action to the GitHub Marketplace", pick the categories. A release made by the
workflow isn't listed until someone ticks that box, so the listing shows the last ticked version.

A release is done only when the new version shows on PyPI
(`curl -s https://pypi.org/pypi/bump2v/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"`).

If a publish fails, check the Actions tab on GitHub. Fix the issue, commit, then re-run `bump2v patch` to create a new tag and trigger a fresh publish.

## Things to never do

- Do not add `bump2version` back as a dependency — we vendor the source in `bump2v/bumpversion/`
- Do not add Co-Authored-By to commit messages
- Do not edit the version in `pyproject.toml` manually
- Do not run `git push` manually before bumping — the version commit won't be included
- Do not let `README.md` and `README.rst` get out of sync — both are read by users (GitHub vs PyPI)
