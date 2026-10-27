# GitLab CI/CD

bump2v ships two GitLab templates in the CI/CD component format, in
[`templates/`](https://github.com/maimul/bump2v/tree/main/templates): `release` bumps, commits,
tags and pushes; `check` fails when a version file has drifted. Include them by URL, pinned to
a release:

```yaml
include:
  - remote: https://raw.githubusercontent.com/maimul/bump2v/v1.11.1/templates/release.yml
    inputs:
      branches: /^(development|main)$/
  - remote: https://raw.githubusercontent.com/maimul/bump2v/v1.11.1/templates/check.yml

stages: [test, release, build]

build:
  stage: build
  needs: [bump2v-release]
  script:
    - |
      if [ "$BUMP2V_BUMPED" != "true" ]; then echo "Nothing new to build."; exit 0; fi
    - git fetch --quiet origin "$CI_COMMIT_BRANCH"
    - git checkout --quiet "$BUMP2V_SHA"              # the version commit itself
    - ./build.sh "$BUMP2V_VERSION"                     # your build, with the new version
  rules:
    - if: $CI_COMMIT_BRANCH =~ /^(development|main)$/
```

Each template runs in the [bump2v image](other.md#the-container-image) of the same version, so
there's nothing to install. For a URL that can never change, use a commit SHA instead of the tag
in the path.

## Let the job push

The release job pushes the version commit and tag back to the branch. Pick one:

- **The job token** (simplest, GitLab 18.4 and later): in **Settings > CI/CD > Job token
  permissions**, turn on **Allow Git push requests to the repository**. The job pushes with the
  rights of whoever started the pipeline, so they need push access to the branch, and a push
  made with the job token starts no pipeline.
- **An access token**: a project access token (Premium on GitLab.com; any tier on Self-Managed)
  or a bot user's personal access token, with the `write_repository` scope and a role that may
  push to the branch and create tags. Store it as a masked CI/CD variable named `BUMP2V_TOKEN`
  (or pass another variable as the `token` input). A protected variable is only given to
  protected branches.

## What the release job does

1. Runs only on branches matching `branches` (default `/^(main|master)$/`), with the full
   history (`GIT_DEPTH: 0`) and a fresh clone.
2. Waits its turn: `resource_group` lets one release run at a time per branch.
3. Checks out the branch (GitLab starts jobs on a detached commit), fast-forwards to the
   branch tip, bumps, and pushes commit and tag together, retrying when another pipeline
   pushed first.
4. Pushes with `-o ci.skip`, so the version commit doesn't start another branch pipeline.
   GitLab's documentation doesn't say whether that also skips a pipeline for the tag; if you
   rely on tag pipelines, set `skip-pipeline: false`. The pipeline for the version commit then
   finds the tip already released and succeeds without bumping.
5. Hands the result to later jobs as variables:

| Variable | |
|---|---|
| `BUMP2V_VERSION` | The version after the job (the current one when nothing was released) |
| `BUMP2V_PREVIOUS_VERSION` | The version before |
| `BUMP2V_TAG` | The tag created; unset when none was |
| `BUMP2V_SHA` | The commit to build: the version commit, or HEAD when nothing was released |
| `BUMP2V_BUMPED` | `true` when a new version was committed |
| `BUMP2V_PUSHED` | `true` when the commit and tag were pushed |

These come from a `dotenv` report, so they exist in `script`, not in `rules`: decide in the
script whether there's anything to do, as the build job above does.

## Inputs

`release`:

| Input | Default | |
|---|---|---|
| `branches` | `main` and `master` | A regex of the branches to release from |
| `part` | `auto` | `major`, `minor`, `patch`, a part from your config, or `auto` |
| `token` | `$BUMP2V_TOKEN` | Token to push with; empty means the job token |
| `push` | `true` | `false` commits and tags in the job only |
| `skip-pipeline` | `true` | Push with `ci.skip` |
| `retry` | `3` | More tries when another pipeline pushed first |
| `args` | | Extra bump2v options, for example `--config-file release.cfg` |
| `stage` | `release` | |
| `image` | `ghcr.io/maimul/bump2v:<this version>` | |

`check`: `stage` (`test`), `args`, `image`.

## How it's tested

GitLab itself doesn't run in this project's CI. Every change runs both templates in the image
the way a runner does: the inputs filled in from the spec, a detached checkout, the `CI_*`
variables, a remote that another pipeline pushed to in the meantime, and the `dotenv` output
checked against GitLab's rules
([`tests/ci/gitlab_templates.py`](https://github.com/maimul/bump2v/blob/main/tests/ci/gitlab_templates.py)).
If something behaves differently on your GitLab, please
[open an issue](https://github.com/maimul/bump2v/issues).
