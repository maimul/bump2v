# bump2v — Claude Code Instructions

## What this repo is

`bump2v` is a PyPI package that wraps and extends bump2version. The bump2version source is **vendored** (copied) into `bump2v/bumpversion/` so we own all the code and can modify it freely. The `bump2v/__main__.py` is the CLI entry point that adds guards, dry-run preview, and git push on top of the core logic.

## Repo structure

```
bump2v/
  __main__.py           # CLI entry point — guards, dry-run preview, calls bumpversion.cli.main
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
.github/workflows/
  pypi-publish.yml      # Publishes to PyPI on every git tag push (v*)
README.md               # GitHub-facing docs (Markdown)
README.rst              # PyPI-facing docs (reStructuredText — keep in sync with README.md)
```

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

5. **Bump and publish** using bump2v itself (we dogfood our own tool):
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

Tests are automatically run in two places:
1. **Before every push** — `bump2v` detects the `tests/` directory and runs pytest before `git push`. If tests fail, the push is blocked.
2. **In CI** — `test.yml` runs on every push and PR against main, across Python 3.10, 3.11, 3.12. `pypi-publish.yml` also runs tests as a required step before building and publishing.

When adding a new feature or fixing a bug, add a corresponding test:

| Changed file | Test file |
|---|---|
| `bumpversion/functions.py` | `tests/test_functions.py` |
| `bumpversion/version_part.py` | `tests/test_version_part.py` |
| `bumpversion/cli.py` | `tests/test_cli.py` |
| `bumpversion/vcs.py` | `tests/test_vcs.py` |
| `bump2v/__main__.py` | `tests/test_auto.py` |

## Publishing checklist

Before running `bump2v minor` or `bump2v major`:
- [ ] `pytest --tb=short -q` passes
- [ ] README.md updated with new flags or changed behaviour
- [ ] README.rst updated to match README.md
- [ ] Commit message is descriptive

## GitHub Actions — how PyPI publish works

`.github/workflows/pypi-publish.yml` triggers on any tag matching `v*`. It:
1. Checks out the repo (`actions/checkout@v4`)
2. Sets up Python (`actions/setup-python@v5`)
3. Builds the wheel: `python -m build --wheel`
4. Uploads to PyPI via `twine` using repo secrets `PYPI_USERNAME` and `BUMP2V`

If a publish fails, check the Actions tab on GitHub. Fix the issue, commit, then re-run `bump2v patch` to create a new tag and trigger a fresh publish.

## Things to never do

- Do not add `bump2version` back as a dependency — we vendor the source in `bump2v/bumpversion/`
- Do not add Co-Authored-By to commit messages
- Do not edit the version in `pyproject.toml` manually
- Do not run `git push` manually before bumping — the version commit won't be included
- Do not let `README.md` and `README.rst` get out of sync — both are read by users (GitHub vs PyPI)
