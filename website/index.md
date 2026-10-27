# bump2v

**One command to version any repo:** every file that holds the version, the commit, the tag
and the push. It works the same on your laptop, in any CI and for AI coding agents, and it has
no dependencies beyond Python and git.

```console
$ bump2v plan auto
Analyzing commits since v1.4.2...

  feat: export to CSV                                                minor
  fix: retry the upload on a 503                                     patch

Auto-detected: minor

1.4.2 → 1.5.0  (minor)
  package.json                             1 match
  .bumpversion.cfg                         current_version
commit: Version Updated: 1.4.2 → 1.5.0
tag:    v1.5.0
push:   yes

$ bump2v release auto
```

## Install

=== "pipx"

    ```sh
    pipx install bump2v
    ```

=== "uv"

    ```sh
    uv tool install bump2v      # or run it once: uvx bump2v plan auto
    ```

=== "pip"

    ```sh
    pip install bump2v
    ```

=== "Container"

    ```sh
    docker run --rm -v "$PWD:/repo" ghcr.io/maimul/bump2v bump2v plan auto
    ```

Needs Python 3.11 or newer (older Pythons get 1.6.x). In CI you can skip the install:
there's a [GitHub Action](ci/github-actions.md), [GitLab templates](ci/gitlab.md) and a
[container image](ci/other.md).

## Start

```sh
bump2v init                 # finds your version (package.json, pyproject.toml, Cargo.toml, ...)
                            # and writes .bumpversion.cfg; review it
git add .bumpversion.cfg
git commit -m "chore: version with bump2v"

bump2v plan auto            # what the next release would be; changes nothing
bump2v release auto         # bump every file, commit, tag, push
```

`auto` reads the [Conventional Commits](https://www.conventionalcommits.org/) since the last
release: `feat:` bumps minor, `feat!:` or a `BREAKING CHANGE:` footer bumps major, anything
else bumps patch. Name the part yourself with `bump2v release patch|minor|major`.

## What a release does

1. Refuses to start when the working tree is dirty (exit 3) or the new tag already exists
   (exit 5), before it writes anything.
2. Rewrites the version in every file listed in `.bumpversion.cfg`.
3. Commits those files and tags the commit (`v1.5.0`, or your own `tag_name`).
4. Pushes the branch and the tag together (`git push --atomic`): both land, or neither does,
   so a rejected push never leaves a tag behind on the remote.

In CI, `--sync` first fast-forwards to the remote branch tip, and `--retry 3` catches up and
tries again when another run pushed first. `bump2v check` fails when a file has drifted from
the version in the config, for CI or [as a pre-commit hook](https://github.com/maimul/bump2v#pre-commit-hook).

## Next

- [Set it up for your stack](stacks.md): Node, Python, Rust, Helm, Expo, .NET, Go and plain files.
- Release from CI: [GitHub Actions](ci/github-actions.md), [GitLab](ci/gitlab.md),
  [anything else](ci/other.md).
- [Let AI coding agents release safely](agents.md).
- [Move from bump2version](migrate.md): bump2v reads the same `.bumpversion.cfg`.
- The full reference (every command, option, config key, exit code and the JSON output) is in
  the [README](https://github.com/maimul/bump2v#commands).
