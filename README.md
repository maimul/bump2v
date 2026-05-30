# bump2v

A CLI wrapper and native fork of [bump2version](https://github.com/c4urself/bump2version) for automated semantic versioning. Bumps version numbers across files, commits, tags, and pushes — all in one command.

```zsh
pip install bump2v
```

---

## How it works

bump2v reads your current version from a config file, increments it, rewrites it in every file you specify, commits the change, creates a git tag, and pushes — all in one command. The **source of truth for the version** lives in your project's main file:

| Stack | Source of truth |
|---|---|
| Node.js / React / JS | `package.json` → `"version": "1.0.0"` |
| Python | `appInfo.py` (or any `.py` file) → `__version__ = "1.0.0"` |
| Any other file | Configurable via `.bumpversion.cfg` |

The `.bumpversion.cfg` file tells bump2v where to find and update that version string. **You only need to run bump2v — never edit the version manually.**

---

## Quick Start

**Step 1:** Make your code change.

**Step 2:** Stage and commit.

```zsh
git add .
git commit -m "fix: describe your change here"
```

**Step 3:** Bump the version and push.

```zsh
bump2v patch   # 1.0.0 → 1.0.1  (bug fix)
bump2v minor   # 1.0.0 → 1.1.0  (new feature)
bump2v major   # 1.0.0 → 2.0.0  (breaking change)
```

That's it. bump2v bumps the version, commits, tags, and pushes in one step.

Alternative command aliases: `bumptydumpty`, `versionkaboom`

---

## Setup by project type

### Node.js / React

The version lives in `package.json`. bump2v finds and updates it there.

**`.bumpversion.cfg`:**
```ini
[bumpversion]
current_version = 1.0.0
commit = True
tag = True
message = Version Updated: {current_version} → {new_version} 🚀 [skip ci]

[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
```

The `current_version` in `.bumpversion.cfg` must always match the `"version"` field in `package.json`. bump2v keeps them in sync automatically — never edit either one by hand.

---

### Python

The version lives in `appInfo.py` (or wherever you store your app metadata).

**`app/appInfo.py`:**
```python
app_name = "Your App Name"
__version__ = "1.0.0"
description = "Describe your app here"
```

**`main.py`:**
```python
from appInfo import __version__, app_name, description

app = FastAPI(
    title=app_name,
    description=description,
    version=f"🏭 Prod:{__version__}",
)
```

**`.bumpversion.cfg`:**
```ini
[bumpversion]
current_version = 1.0.0
commit = True
tag = True
message = Version Updated: {current_version} → {new_version} 🚀 [skip ci]

[bumpversion:file:app/appInfo.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"
```

Again, `current_version` in `.bumpversion.cfg` must match `__version__` in `appInfo.py`. bump2v keeps them in sync.

---

### Multiple files

You can target as many files as needed:

```ini
[bumpversion]
current_version = 1.0.0
commit = True
tag = True

[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"

[bumpversion:file:app/appInfo.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"
```

---

## Semantic Versioning

| Command | Example | When to use |
|---|---|---|
| `bump2v patch` | `1.0.0 → 1.0.1` | Bug fixes, minor improvements |
| `bump2v minor` | `1.0.0 → 1.1.0` | New backward-compatible features |
| `bump2v major` | `1.0.0 → 2.0.0` | Breaking changes |

---

## Advanced Flags

### `--tag-only` — Tag without bumping

Tags the current HEAD using `current_version` from config, without bumping or committing. Useful when you need to commit a build artifact **between** the version bump commit and the release tag.

```zsh
bump2v patch --no-tag       # bump + commit, skip the tag
# ... build artifact, git add artifact, git commit ...
bumpversion --tag-only      # now tag HEAD with the bumped version
```

Fixes [#256](https://github.com/c4urself/bump2version/issues/256).

---

### `--ignore-missing-version` — Skip files where version string is not found

When using glob patterns, some matched files may not contain a version string. Instead of crashing, bump2v logs a warning and skips those files.

```zsh
bump2v patch --ignore-missing-version
```

Or set it permanently in config:

```ini
[bumpversion]
ignore_missing_version = True
```

Fixes [#267](https://github.com/c4urself/bump2version/issues/267).

---

### `--extra-files` — Include generated files in the bump commit

Stage additional files (e.g. build artifacts, generated docs) alongside the version bump commit, even if they were not modified by bumpversion. Files can be dirty or untracked.

```zsh
bump2v patch --extra-files docs/changelog.md dist/summary.txt
```

Or set them in config:

```ini
[bumpversion]
extra_files = docs/changelog.md dist/summary.txt
```

Fixes [#259](https://github.com/c4urself/bump2version/issues/259).

---

### `sign_tags` config fix

Setting `sign_tags = False` in `.bumpversion.cfg` now works correctly. Previously it was silently ignored, causing GPG signing attempts to fail.

```ini
[bumpversion]
sign_tags = False
```

Fixes [#269](https://github.com/c4urself/bump2version/issues/269).

---

## Full config reference

```ini
[bumpversion]
current_version = 1.0.0       # must match the version in your source of truth file
commit = True
tag = True
sign_tags = False
message = Version Updated: {current_version} → {new_version} 🚀 [skip ci]
tag_name = v{new_version}
tag_message = Release {new_version}
commit_args =
ignore_missing_version = False
extra_files =

[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
```

---

## Tips

Remove all local tags if you need to reset:

```zsh
git tag -l | xargs -n 1 git tag -d
```

---

## Contributors

Maintained and extended by [@maimul](https://github.com/maimul).

Built on top of [bump2version](https://github.com/c4urself/bump2version) by Christian Verkerk.
