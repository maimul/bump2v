# Any other CI

Any CI that can run a shell can release with bump2v: install it (`pip install "bump2v>=1.11,<2"`)
or run the job in the [container image](#the-container-image). A release job needs five things.

1. **The full history and the tags**, so `auto` can find the last release. A shallow clone
   makes `auto` fail (exit 1) instead of guessing.
2. **A branch checked out, tracking the remote branch.** Many CIs start on a detached commit.
3. **Credentials that can push** the branch and tags.
4. **One release at a time per branch**: your CI's concurrency, lock or queue setting.
5. **No loop.** The version commit's own pipeline finds the tip already released (`--sync`
   exits 7) and does nothing; to skip that pipeline, add `[skip ci]` to `message` in the config.

The release step, with `BRANCH` and `COMMIT` taken from your CI's variables:

```sh
git checkout -B "$BRANCH" "$COMMIT"
git config "branch.$BRANCH.remote" origin
git config "branch.$BRANCH.merge" "refs/heads/$BRANCH"

code=0
bump2v release auto --sync --retry 3 || code=$?
if [ "$code" -ne 0 ] && [ "$code" -ne 7 ]; then exit "$code"; fi   # 7: already released

VERSION=$(bump2v show current_version)
```

`--sync` fast-forwards to the remote branch tip first; `--retry 3` catches up and tries again
when another run pushed in between. The branch and tag are pushed together or not at all.
For everything the run did as one JSON object, add `--json`; the exit codes are in the
[README](https://github.com/maimul/bump2v#exit-codes-and-json-output).

When git has no user configured and `CI` is set, bump2v commits as
`bump2v <bump2v@users.noreply.github.com>`. To choose the author, set `GIT_AUTHOR_NAME`,
`GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL`, or run `git config user.name`
and `user.email` in the job.

## Bitbucket Pipelines

```yaml
image: ghcr.io/maimul/bump2v:1.11.1

pipelines:
  branches:
    main:
      - step:
          name: Release
          clone:
            depth: full    # auto reads the commits since the last release
          script:
            - git checkout -B "$BITBUCKET_BRANCH" "$BITBUCKET_COMMIT"
            - git config "branch.$BITBUCKET_BRANCH.remote" origin
            - git config "branch.$BITBUCKET_BRANCH.merge" "refs/heads/$BITBUCKET_BRANCH"
            - bump2v release auto --sync --retry 3 || [ $? -eq 7 ]
```

Bitbucket sets up an origin that steps can push back to. A branch with restrictions needs its
own credentials (an access token, or a Pipelines SSH key that's allowed to push); see
Atlassian's [push back to your repository](https://support.atlassian.com/bitbucket-cloud/docs/push-back-to-your-repository/).
Bitbucket starts a pipeline for the version commit unless its message has `[skip ci]`.

## The container image

`ghcr.io/maimul/bump2v` is Python, git, openssh-client and bump2v, for `linux/amd64` and
`linux/arm64`.

| Tag | |
|---|---|
| `1.11.0` | That version, never rebuilt |
| `1.11`, `1` | The newest release in that line |
| `latest` | The newest release |

It has no entrypoint, so CI runners can start their own shell in it, and it marks every
directory as safe for git, since the repository it works on usually belongs to another user.
Run it on your machine with the repo mounted:

```sh
docker run --rm -v "$PWD:/repo" ghcr.io/maimul/bump2v:1 bump2v plan auto
docker run --rm -v "$PWD:/repo" ghcr.io/maimul/bump2v:1 bump2v check
```
