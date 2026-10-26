# Distributing bump2v across language stacks and CI pipelines (research notes, October 2026)

Short answer: keep the Python codebase. GitHub-hosted runners already have pipx, so `pipx run bump2v` works there with no setup. A composite GitHub Action and a GitLab CI/CD component would reach most teams for the least work. Standalone binaries and npm/Homebrew packaging come second. No source was found saying a Python requirement blocks JS or Go teams.

## 1. Zero-setup Python paths (uvx, uv tool, pipx)

### Takeaway
On GitHub-hosted runners, pipx is preinstalled on every image checked and uv is not. So `pipx run bump2v` needs no setup, and `uvx` needs an `astral-sh/setup-uv` step first. On other CI systems, the uv Docker image avoids managing Python.

### Cited Findings
- Ubuntu 24.04 image 20261023: Pipx 1.16.7, system Python 3.12.3, no uv listed — [Ubuntu2404 readme](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md)
- Ubuntu 26.04: Pipx 1.17.10, Python 3.14.4. Windows 2025: Pipx 1.18.4. macOS 15 arm64: Pipx 1.17.2. macOS 26 arm64: Pipx 1.17.13. None of these readmes lists uv — [26.04](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2604-Readme.md), [Win2025](https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-Readme.md), [macOS 15](https://github.com/actions/runner-images/blob/main/images/macos/macos-15-arm64-Readme.md), [macOS 26](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md)
- On 2025-03-05 the maintainers declined to add uv. Their reasons: it "can be installed fairly easily and quickly (less than two minutes…)", and "we try to minimise the number of our dependencies". Requests to reconsider in 2026 got no reversal — [issue #10533](https://github.com/actions/runner-images/issues/10533); a 2025 repeat request was closed as a duplicate — [#13227](https://github.com/actions/runner-images/issues/13227)
- `ubuntu-latest` moves to 26.04 between Oct 19 and Nov 19, 2026 — [#14748](https://github.com/actions/runner-images/issues/14748)
- uv's docs recommend `astral-sh/setup-uv` with a pinned version (example `0.13.5`) and `enable-cache: true` — [uv GitHub guide](https://docs.astral.sh/uv/guides/integration/github/). setup-uv's latest release is v10.3.2 (2026-10-22) — [releases](https://github.com/astral-sh/setup-uv/releases)
- GitLab CI: use `image: ghcr.io/astral-sh/uv:$UV_VERSION-python$PYTHON_VERSION-$BASE_LAYER` (the example uses trixie-slim). The distroless image needs `entrypoint: [""]` — [uv GitLab guide](https://docs.astral.sh/uv/guides/integration/gitlab/)
- `uvx` runs tools "in temporary, isolated environments". You pin a version with `uvx tool@1.2.3`, and `--from` takes ranges — [uv tools guide](https://docs.astral.sh/uv/guides/tools/)

### Inferences
- `ubuntu-latest` will soon run Python 3.14 by default. `pyproject.toml` has no `requires-python`, and the test matrix stops at 3.12. Add 3.13 and 3.14 to the matrix before telling users to run `pipx run bump2v`.

### Gaps
- Startup-time benchmarks for pipx run, uvx or binaries: no citable source.
- Whether `pipx run` caches between runs, and whether uvx installs Python by itself: neither page read says.
- The mise PyPI backend: the page moved to [mise.jdx.dev/dev-tools/backends/pypi.html](https://mise.jdx.dev/dev-tools/backends/pypi.html) and was not read.

## 2. Standalone binaries built from Python

### Takeaway
PyInstaller and PyApp are both actively released. PyOxidizer has stalled. None of them cross-compiles easily, so each OS needs its own build job, and macOS signing and notarisation stay on us.

### Cited Findings
- PyOxidizer's last release was 0.24.0 on 2022-12-30 and its last push was 2024-12-24. It is not archived — [releases](https://github.com/indygreg/PyOxidizer/releases). A Pants maintainer said they moved away from it because it "was also pretty slow… sharp edges", and pointed to python-build-standalone instead — [Pants chat](https://chat.pantsbuild.org/t/16408126/status-of-pyozidizer-i-am-using-pyoxidizer-which-only-suppor)
- python-build-standalone is now maintained by Astral (astral-sh); latest release 20261021 — [releases](https://github.com/astral-sh/python-build-standalone/releases)
- PyApp describes itself as "a wrapper for Python applications that bootstrap themselves at runtime", with "standalone binaries for every platform" and optional self-update. Latest is v0.30.0 (2026-10-12) — [PyApp](https://github.com/ofek/pyapp)
- PyInstaller 6.22.3 (2026-09-12) — [releases](https://github.com/pyinstaller/pyinstaller/releases)
- PyInstaller says "install PyInstaller on each platform and bundle your app separately". Linux builds should be made on the *oldest* glibc you support. It has `--codesign-identity` and `--osx-entitlements-file`, and `--target-arch universal2` for macOS. Onefile app bundles "require unpacking on each run" — [PyInstaller usage](https://pyinstaller.org/en/stable/usage.html)
- Nuitka's repo was pushed 2026-10-26, but it publishes no GitHub Releases — [Nuitka](https://github.com/Nuitka/Nuitka)

### Gaps
- How PyApp works inside, its binary size, and real projects shipping with it: the README doesn't say.
- PyInstaller's notarisation steps (the docs only warn about sandboxing), and Windows signing: not covered.
- Size and startup numbers, and Nuitka's onefile and signing behaviour: no sources found.
- Real CLIs shipped as PyInstaller binaries: not researched.

## 3. Packaging for other ecosystems (npm, Homebrew, Scoop/winget, Docker, pre-commit, mise, Nix)

### Takeaway
The npm pattern needs a native binary for each platform. Homebrew core needs stable, immutable tagged releases. pre-commit is the cheapest way in because it already handles Python hooks.

### Cited Findings
- Biome's npm package lists ten platform packages as `optionalDependencies` (`@biomejs/cli-{win32,darwin,linux,linux-*-musl,android}-{x64,arm64}`), uses `bin: bin/biome`, and has **no postinstall** script — [package.json](https://github.com/biomejs/biome/blob/main/packages/@biomejs/biome/package.json)
- Homebrew core requires "a stable… immutable tag or release". Python formulae declare checksummed `resource` blocks. Other trade-offs "belong in a third-party tap" — [Acceptable Formulae](https://docs.brew.sh/Acceptable-Formulae)
- pre-commit is "a multi-language package manager". Python hooks "work without any system-level dependencies" and are installed with `pip install .`. There is a `docker_image` language. pre-commit itself runs from pip or a zipapp (`python pre-commit-#.#.#.pyz`) — [pre-commit.com](https://pre-commit.com/)

### Inferences — distribution comparison

| Option | Setup for a non-Python team | OS coverage | Our upkeep | Signing burden | Source |
|---|---|---|---|---|---|
| `pipx run bump2v` | none on GitHub-hosted runners | Linux/Win/macOS | none | none | [runner readme](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md) |
| setup-uv + `uvx` | one step | all | none | none | [uv](https://docs.astral.sh/uv/guides/integration/github/) |
| uv Docker image | one `image:` line | Linux CI | none | none | [uv GitLab](https://docs.astral.sh/uv/guides/integration/gitlab/) |
| PyApp binary | download | "every platform" | a build per target | ours (unverified) | [PyApp](https://github.com/ofek/pyapp) |
| PyInstaller binary | download | a build per OS | high | codesign on us | [usage](https://pyinstaller.org/en/stable/usage.html) |
| npm wrapper | `npx` | per-platform packages | high (needs binaries first) | inherits binary signing | [biome](https://github.com/biomejs/biome/blob/main/packages/@biomejs/biome/package.json) |
| pre-commit hook | `.pre-commit-config.yaml` | all | low | none | [pre-commit](https://pre-commit.com/) |

### Gaps
- Homebrew core's star/fork thresholds: not on the page read.
- Scoop and winget manifest rules, Nix, a mise registry entry, and npm trusted publishing/provenance: not researched.

## 4. CI integration surfaces

### Takeaway
A composite GitHub Action plus a GitLab CI/CD component give the most reach for the least work. Bitbucket Pipes, Azure DevOps tasks and CircleCI orbs each need their own packaging, so each costs more.

### Cited Findings
- Action types: Docker container actions run on Linux only and are "slower than JavaScript actions". Composite and JavaScript actions run on Linux, macOS and Windows — [custom actions](https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions)
- Marketplace rules: a public repo, "a single action metadata file… at the root", a unique name, 2FA. Actions that meet these are published without GitHub review — [Marketplace](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace)
- GitLab components: a `templates/` directory, README at the tagged commit, a release created with the `release` keyword in a job ("not the Releases API"), and a semver tag. Available on the Free tier. Components work only on the same instance; Self-Managed users must mirror them — [GitLab components](https://docs.gitlab.com/ci/components/)
- A Bitbucket pipe is a Docker image plus a script — [Atlassian](https://support.atlassian.com/bitbucket-cloud/docs/write-a-pipe-for-bitbucket-pipelines/). A third-party source says `pipe.yml` metadata is required for a complete pipe — [Octopus](https://octopus.com/blog/bitbucket-pipes-and-octopus-deploy)
- Azure DevOps: a TypeScript task packaged as an extension and published to the Visual Studio Marketplace — [Microsoft](https://learn.microsoft.com/en-us/azure/devops/extend/develop/add-build-task)
- CircleCI orbs are published to a public or private registry with the CLI. This comes from a 2019 post, so it may be dated — [orb concepts](https://circleci.com/docs/orbs/use/orb-concepts/index.md), [blog](https://circleci.com/blog/creating-automated-build-test-and-deploy-workflows-for-orbs)

### Inferences — CI surface comparison

| Surface | Packaging | Runners | Effort |
|---|---|---|---|
| GitHub composite action (`pipx run` or setup-uv) | `action.yml` | all three OSes | low |
| GitHub Docker action | image | Linux only | medium |
| GitLab component | `templates/*.yml` + release job | Linux images | low |
| Bitbucket pipe | Docker image (+`pipe.yml`) | Linux | medium |
| Azure DevOps task | TypeScript + VS Marketplace | all | high |
| CircleCI orb | orb.yml + CLI | — | medium |
| Jenkins | (not researched) | — | — |

### Gaps
- GitHub's guidance on a moving `v1` tag and immutable releases: the pages read don't mention either.
- Jenkins integration options: not researched.

## 5. CI pitfalls for a tool that commits, tags and pushes

### Takeaway
bump2v's `git push --follow-tags` quietly depends on several checkout defaults, and on GitHub and GitLab a push made with the built-in CI token does not trigger new pipelines.

### Cited Findings
- `actions/checkout` is now at v7. Defaults: `fetch-depth: 1`, `fetch-tags: false`, and `persist-credentials: true` (kept under `$RUNNER_TEMP` since v6). Pull requests are checked out in detached HEAD mode. The bot identity is `41898282+github-actions[bot]@users.noreply.github.com`, which does not work on GHES — [checkout](https://github.com/actions/checkout)
- "Events triggered by the `GITHUB_TOKEN` will not create a new workflow run." Exceptions: `workflow_dispatch` and `repository_dispatch`, plus `pull_request` runs that wait for approval. The suggested alternative is "a GitHub App installation access token or a personal access token" — [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token)
- Ruleset bypass can go to roles, teams or GitHub Apps. Rulesets can cover tags. When rules overlap, "the most restrictive version of the rule applies" — [rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- GitHub skip strings: `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, `[actions skip]`, plus a `skip-checks: true` trailer. They apply to `push` and `pull_request`; `pull_request_target` still runs. Skipped required checks stay "Pending" and block merging — [skip runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)
- GitLab: `[skip ci]` in any capitalisation, or `git push -o ci.skip`. The push option "does not skip merge request pipelines". Pipeline policies can disable skipping — [GitLab pipelines](https://docs.gitlab.com/ci/pipelines/)
- GitLab `CI_JOB_TOKEN` can push once "Allow Git push requests to the repository" is enabled (generally available in 18.4). Such a push "doesn't trigger any CI/CD pipelines". There is a known issue with semantic-release — [job token](https://docs.gitlab.com/ci/jobs/ci_job_token/)
- Concurrency: by default one run executes and at most one waits, and an older waiting run is cancelled. `queue: max` allows up to 100 waiting runs and cannot be combined with `cancel-in-progress: true` — [concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- GitHub marks a bot commit as verified only when it is created "as the GitHub App or bot" with "no custom author… committer". Commits made in the web UI are GPG-signed. SSH signing needs Git 2.34 or later — [signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)

### Inferences
- `bump2v auto` reads commit messages since the last tag, so it needs `fetch-depth: 0` and the tags fetched. The action should check for a shallow clone and stop with a clear error.
- On a detached HEAD, bump2v should stop with an error, or push to an explicit ref.
- A local `git commit` made in CI shows as unverified unless bump2v signs it itself (SSH key) or creates the commit through the API.
- Release jobs should use a concurrency group without `cancel-in-progress`.

### Gaps
- Can the GITHUB_TOKEN or the github-actions app be added to a ruleset bypass list? The page doesn't say.
- How GitLab job-token pushes interact with protected branches: not stated.
- Skip conventions for Bitbucket, Azure DevOps, CircleCI and Jenkins: not researched.
- gitsign / Sigstore commit signing: not researched.

## 6. Supply chain

### Takeaway
A credible dev tool in 2026 publishes with PyPI Trusted Publishing, which turns on PEP 740 attestations by default, and adds GitHub artifact attestations (SLSA Build L2) to any binaries. bump2v currently uploads with a long-lived token.

### Cited Findings
- Trusted Publishing tokens are valid for "15 minutes", compared with long-lived API tokens — [PyPI](https://docs.pypi.org/trusted-publishers/)
- Attestations can be produced from GitHub Actions, GitLab CI/CD and Google Cloud. `twine upload --attestations` also works — [PyPI attestations](https://docs.pypi.org/attestations/producing-attestations/)
- `pypa/gh-action-pypi-publish` turns attestations on by default when Trusted Publishing is used. It needs `id-token: write` and is Docker-based, so it runs only on Linux jobs — [action](https://github.com/pypa/gh-action-pypi-publish)
- GitHub artifact attestations give "SLSA v1.0 Build Level 2", or L3 when built in a shared reusable workflow. Users check them with `gh attestation verify` — [GitHub](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- This repo's workflow: `.github/workflows/pypi-publish.yml` runs `twine upload -u ${{ vars.PYPI_USERNAME }} -p ${{ secrets.BUMP2V }}` with `permissions: contents: read` and no `id-token`.

### Gaps
- Which actions name to use (`attest-build-provenance` vs `attest`) and which plans support attestations on private repos: not confirmed.

## 7. Evidence on a rewrite

### Takeaway
No versioning tool was found that moved from Python to Go or Rust to make distribution easier. The leading release tools are Node and Python, and the CI action hides their runtime from users.

### Cited Findings
- release-please is TypeScript and supports the `go`, `rust`, `java`, `maven`, `dart`, `python`, `node` and `simple` release types, among others. Its README says: "The easiest way to run Release Please is as a GitHub action" — [release-please](https://github.com/googleapis/release-please). Its action is at v5.0.0 (2026-04) — [releases](https://github.com/googleapis/release-please-action/releases)
- semantic-release is JavaScript, with about 24.1k stars and v25.0.9 — [repo](https://github.com/semantic-release/semantic-release)
- Python tools still actively released in October 2026: pre-commit v4.7.0 (about 15.7k stars) — [releases](https://github.com/pre-commit/pre-commit/releases); commitizen v4.19.3 — [releases](https://github.com/commitizen-tools/commitizen/releases); bump-my-version 1.6.7 — [releases](https://github.com/callowayproject/bump-my-version/releases)

### Inferences
- **Recommendation.** Keep Python and ship in this order:
  1. Move publishing to Trusted Publishing, which also gives attestations.
  2. A composite GitHub Action. It should run `pipx run bump2v==X` (or setup-uv), check fetch depth, tags and branch, accept an App token input, and recommend a release concurrency group.
  3. A GitLab component built on the uv image.
  4. A pre-commit hook.
  5. Only after that, PyApp or PyInstaller binaries for Homebrew, npm and Scoop.

  A rewrite is justified only if the binary route turns out too costly to run.

### Gaps
- No reliable data in either direction on whether "requires Python" blocks adoption by JS or Go teams.
- No example found of a versioning tool migrating from Python to Go or Rust.
