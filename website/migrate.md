# Coming from bump2version

bump2version is no longer maintained. bump2v carries its code (version 1.0.1) inside the
package, fixed and extended, with no dependencies, so the config you have keeps working.

## Switch

```sh
pip install bump2v        # or pipx install bump2v
bump2v plan patch         # reads your existing config; changes nothing
```

bump2v finds its config in this order: `--config-file`, `$BUMP2V_CONFIG`, `.bumpversion.cfg`,
`.bumpversion.toml`, `pyproject.toml` with a `[tool.bumpversion]` table, then `setup.cfg`. The
INI format is the same as bump2version's; the TOML tables follow bump-my-version's, and options
bump2v doesn't support there (hooks, `regex`, ...) are reported and ignored.

## The one difference to know first: bump2v pushes

| bump2version | bump2v |
|---|---|
| `bump2version patch` bumps, commits and tags | `bump2v patch` bumps, commits, tags **and pushes** |

To keep the old behaviour, set `push = False` in `[bumpversion]`, or run
`bump2v release patch --no-push`. bump2v only ever pushes what that run created: with
`--dry-run`, `--no-commit` or `commit = False` it pushes nothing.

## What else you get

- `bump2v plan <part>` shows the new version, every file and how many places match, the commit
  message and the tag, and changes nothing (`--json` for scripts).
- `bump2v release auto` picks major, minor or patch from Conventional Commits since the last release.
- `bump2v show current_version` prints just the version, instead of grepping the config.
- `bump2v check` fails (exit 4) when a file has drifted from `current_version`.
- The new tag is checked before any file is written, so a release that would fail on the tag
  changes nothing (exit 5).
- In CI: `--sync` and `--retry` for runs that overlap, and an atomic push of branch and tag.
- Documented exit codes and one JSON object per run, for scripts and AI agents.
- Fixes for long-standing bump2version issues: `sign_tags = False` works, `--ignore-missing-version`,
  `--extra-files`, `--tag-only`, and `replace_all = False` to bump only the first match.

Every option is in the [README](https://github.com/maimul/bump2v#advanced-flags).
