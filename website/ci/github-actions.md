# GitHub Actions

The bump2v Action runs from its own commit: nothing to install, nothing downloaded at run time.

```yaml
on:
  push:
    branches: [main]

concurrency:                         # one release at a time per branch
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    outputs:
      version: ${{ steps.bump.outputs.version }}
      sha: ${{ steps.bump.outputs.sha }}
      bumped: ${{ steps.bump.outputs.bumped }}
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0             # auto reads the commits since the last release
      - id: bump
        uses: maimul/bump2v@v1       # or a commit SHA, see Pinning
        with:
          part: auto

  build:
    needs: release
    if: needs.release.outputs.bumped == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ needs.release.outputs.sha }}   # the version commit itself
      - run: docker build -t "app:${{ needs.release.outputs.version }}" .
```

## What the Action takes care of

- **A stale checkout.** CI checks out the commit that started the run. If another run pushed
  since, the Action fast-forwards to the branch tip before bumping.
- **A lost race.** If another run still pushes first, it drops its own version commit and tag,
  catches up and bumps again (`retry`, default 3).
- **A tip that's already released.** When the branch tip is a version commit, the step succeeds
  with `bumped=false` and the current version, so later steps still have a version.
- **Orphan tags.** The branch and the tag are pushed together or not at all.

| Input | Default | |
|---|---|---|
| `part` | `auto` | `major`, `minor`, `patch`, a part from your config, or `auto` |
| `push` | `true` | `false` commits and tags in the job only |
| `retry` | `3` | More tries when another run pushed first |
| `working-directory` | `.` | Where the bump2v config is |
| `args` | | Extra bump2v options, for example `--config-file release.cfg` |

| Output | |
|---|---|
| `version` | The version after this step (the current one when nothing was released) |
| `previous-version` | The version before |
| `tag` | The tag created, or empty |
| `sha` | The commit to build: the version commit, or HEAD when nothing was released |
| `bumped` | `true` when a new version was committed |
| `pushed` | `true` when the commit and tag were pushed |

The Action needs Python 3.11 or newer on the runner; GitHub-hosted runners have it. On a
self-hosted runner without it, add `actions/setup-python` first.

## Pinning

`@v1` follows the newest 1.x release. It moves only after that version has passed the tests on
Linux, macOS and Windows and reached PyPI, and it never moves to 2.0. A tag can still be moved,
so for a pipeline that must run exactly the code you reviewed, pin the commit, as GitHub
recommends for third-party actions:

```yaml
        uses: maimul/bump2v@27d7a8829ed3b0c5ae465f5d3dfc8d83e6e37736  # v1.9.2
```

`git ls-remote https://github.com/maimul/bump2v 'refs/tags/v1.9.2^{}'` prints the commit for a
version, and Dependabot (`package-ecosystem: github-actions`) keeps SHA pins up to date.

## Protected branches

Pushes made with the default `GITHUB_TOKEN` are refused by a branch rule that requires pull
requests or status checks. Let a GitHub App bypass the rule, and push with its token:

```yaml
    steps:
      - id: app-token
        uses: actions/create-github-app-token@v3
        with:
          client-id: ${{ vars.RELEASE_APP_CLIENT_ID }}
          private-key: ${{ secrets.RELEASE_APP_KEY }}
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          token: ${{ steps.app-token.outputs.token }}   # the Action pushes with this
      - id: bump
        uses: maimul/bump2v@v1
```

Unlike `GITHUB_TOKEN` pushes, an App token's push starts new workflow runs. The run for the
version commit finds the tip already released and reports `bumped=false`, so gate the jobs
after it on `bumped`, as in the example at the top.

## Without the Action

```yaml
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - id: bump
        run: |
          pip install "bump2v>=1.11,<2"
          bump2v release auto --sync --retry 3 --github-output
```

`--github-output` writes the same outputs as the Action (`version`, `previous_version`, `tag`,
`sha`, `bumped`, `pushed`) to `$GITHUB_OUTPUT`. Exit code 7 means the tip is already released.
