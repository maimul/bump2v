# Version schemes and where each ecosystem stores its version: requirements catalogue for bump2v (as of 2026-10-26)

Each source was fetched directly unless marked otherwise.

## 1. Version schemes

### Takeaway
The schemes disagree on four things: leading zeros, letter case, how pre-release tags sort, and whether `+` or a 4th number segment is allowed. One "version" in bump2v's model needs a different written form for each target.

### Cited Findings
- **SemVer 2.0.0**
  - Format is X.Y.Z, and no part may have leading zeros. Pre-release is `-` followed by dot-separated identifiers. Build metadata is `+…` and is ignored when comparing versions. [semver.org](https://semver.org/)
  - Example order: `1.0.0-alpha < -alpha.1 < -alpha.beta < -beta < -beta.2 < -beta.11 < -rc.1 < 1.0.0`. Numeric identifiers compare as numbers and sort before text identifiers. [semver.org](https://semver.org/)
  - `v1.2.3` is *not* a semver; the `v` is only a tag convention. `0.y.z` means "anything MAY change". The spec also publishes an official regex. [semver.org](https://semver.org/)
- **CalVer**
  - Tokens are `YYYY/YY/0Y/M/0M/W/0W/D/0D/MICRO/MODIFIER`. The doubled forms `MM/WW/DD` are deprecated. [calver.org](https://calver.org/)
  - Users listed on calver.org:
    - Ubuntu: `YY.0M.MICRO`
    - Twisted: `YY.M.MICRO`
    - pip: `YY.MINOR.MICRO`
    - yt-dlp: `YYYY.0M.0D[.MICRO]`
    - certifi: `YYYY.0M.0D`
    - Home Assistant: `YYYY.M.MICRO`
    - JetBrains: `YYYY.MINOR.MICRO`
    - Stripe API: `YYYY-0M-0D.MODIFIER`
    - tz database: `YYYY` plus a letter

    [calver.org](https://calver.org/)
  - Zero-padding breaks SemVer (Cargo and Go). PEP 440 strips it: PyPI shows yt-dlp's `2026.08.19` as `2026.8.19`. [calver.org](https://calver.org/)
  - Black: the docs describe a calendar-year stability policy, so pinning `black ~= 26.0` is stable for that year. This comes from a search summary of [Black docs](https://black.readthedocs.io/en/stable/the_black_code_style/); the version-string shape was not fetched. calver.org does not list Black or Unity.
- **PEP 440** (now the PyPA "version specifiers" spec)
  - Form: `[N!]N(.N)*[{a|b|rc}N][.postN][.devN][+local]`. [packaging.python.org](https://packaging.python.org/en/latest/specifications/version-specifiers/)
  - Order: dev < a < b < rc < final < post. [packaging.python.org](https://packaging.python.org/en/latest/specifications/version-specifiers/)
  - Normalisation:
    - Text is lowercased and leading zeros are dropped.
    - `alpha→a`, `beta→b`, and `c/pre/preview→rc`.
    - `1.2a→1.2a0`, `1.0-1→1.0.post1`, and `r/rev→post`.
    - A leading `v` is ignored.

    [packaging.python.org](https://packaging.python.org/en/latest/specifications/version-specifiers/)
  - PyPI must reject local versions (`+label`). [packaging.python.org](https://packaging.python.org/en/latest/specifications/version-specifiers/)
- **Maven**
  - Versions are split at `.`, `-`, `_` and at digit/letter boundaries. Trailing `0`, `ga` and `final` are trimmed, so `1.ga = 1-0 = 1.0 = 1`. [maven.apache.org](https://maven.apache.org/pom.html)
  - Qualifier order: `alpha < beta < milestone < rc=cr < snapshot < final=ga=release < sp`. [maven.apache.org](https://maven.apache.org/pom.html)
  - Comparison is case-insensitive, unlike SemVer. "Snapshots are not treated differently" when ordering. [maven.apache.org](https://maven.apache.org/pom.html)
- **NuGet**
  - Allows `Major.Minor.Patch[.Revision]`. A zero 4th part is dropped, leading zeros are removed, `+metadata` is stripped, and `1 = 1.0 = 1.0.0 = 1.0.0.0`. [learn.microsoft.com](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning)
  - Pre-release labels are case-insensitive. Under SemVer 1 sorting, `alpha10 < alpha2`, so NuGet recommends zero-padding (`beta01`). [learn.microsoft.com](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning)
- **.NET assemblies**
  - There are four distinct versions: the NuGet `PackageVersion`, `AssemblyVersion`, `FileVersion` and `InformationalVersion`. [learn.microsoft.com](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning)
  - `AssemblyVersion`: Microsoft says to consider including only the major version (e.g. `2.0.0.0`) and never to keep it fixed. [learn.microsoft.com](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning)
  - `FileVersion` must be `Major.Minor.Build.Revision`, with the CI build number as Revision (e.g. `1.0.0.99`). [learn.microsoft.com](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning)
  - `InformationalVersion` is set by Source Link to the package version plus the commit, e.g. `1.0.0-beta1+204ff0a`, and the docs advise "AVOID setting [it] yourself". [learn.microsoft.com](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning)
- **Go**
  - A version is `v` plus a semver. `+build` is ignored. `+incompatible` must never appear on a tag. [go.dev/ref/mod](https://go.dev/ref/mod)
  - From v2 on, the module path must end in `/vN`; this is not allowed at v0 or v1. `gopkg.in` uses `.vN`. [go.dev/ref/mod](https://go.dev/ref/mod)
  - Pseudo-versions look like `vX.Y.(Z+1)-0.yyyymmddhhmmss-<12-char hash>`. [go.dev/ref/mod](https://go.dev/ref/mod)

### Inferences
- bump2v needs a separate "scheme" (parse, compare, render) for each target, not a single regex. The same release would be written `1.0.0rc1` (PEP 440), `1.0.0-rc.1` (SemVer), `1.0.0-RC1` (Maven) and `1.0.0.0` (`AssemblyVersion`).

### Gaps
- ZeroVer (0ver.org) and conventions for monotonic build numbers: not fetched.

## 2. Where the version lives

| Ecosystem | File | Field | Notes | Source |
|---|---|---|---|---|
| npm/pnpm/yarn | `package.json` (and `package-lock.json`) | `version`; the lockfile has top-level `version` and `packages[""]` | The lock's `version` "will match" `package.json`. lockfileVersion 1/2/3 = npm 5–6/7–8/9+. Dependency entries also carry `version`. | [npm](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json) |
| Python | `pyproject.toml` | `[project] version` *or* listed in `dynamic` | A field cannot be both static and dynamic. | [PyPA](https://packaging.python.org/en/latest/specifications/pyproject-toml/) |
| Python (scm) | git tag | `dynamic=["version"]` + setuptools-scm | Between tags it produces e.g. `1.2.4.dev3+g<hash>`. `version_file` should not be committed. | [setuptools-scm](https://setuptools-scm.readthedocs.io/en/latest/usage/) |
| Rust | `Cargo.toml` | `[package] version` or `[workspace.package] version` + `version.workspace = true` | Inheritance needs Rust 1.64+. | [Cargo](https://doc.rust-lang.org/cargo/reference/workspaces.html) |
| Go | git tag only | `vX.Y.Z`; in a subdirectory `sub/vX.Y.Z` | v2+ also needs the `/vN` suffix in the `go.mod` module line. | [go.dev](https://go.dev/ref/mod) |
| Maven | `pom.xml` | `<project><version>` | release-please's `java`/`maven` strategies write a SNAPSHOT version after each release. | [release-please](https://github.com/googleapis/release-please/blob/main/docs/customizing.md) |
| Android | `build.gradle(.kts)` | `defaultConfig { versionCode; versionName }` | `versionCode` is an integer, must always increase, max 2,100,000,000. Flavors can override. Gradle values override the manifest. | [Android](https://developer.android.com/studio/publish/versioning) |
| iOS/macOS | `Info.plist` | `CFBundleShortVersionString` (exactly 3 ints) / `CFBundleVersion` (1–3 ints, digits and periods only) | — | [Apple](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleshortversionstring), [Apple](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleversion) |
| Expo | `app.json` / `app.config` | `version`; `ios.buildNumber` (string); `android.versionCode` (integer); `runtimeVersion` (string, or `{policy}`) | `ios.version` and `android.version` override `version`. Bare React Native projects set these in the native files instead. | [Expo](https://docs.expo.dev/versions/latest/config/app/) |
| Flutter | `pubspec.yaml` | `version: 1.0.0+1` | The `+N` becomes Android `versionCode`. Split APKs add ABI×1000. | [Flutter](https://docs.flutter.dev/deployment/android) |
| .NET | `.csproj` / `Directory.Build.props` | `PackageVersion`, `AssemblyVersion`, `FileVersion`, `InformationalVersion` | See §1. | [MS](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning) |
| PHP | `composer.json` | `version` (optional) | Composer recommends omitting it; Packagist infers it from VCS tags. | [Composer](https://getcomposer.org/doc/04-schema.md) |
| Ruby / Elixir / Dart | `version.rb` / `mix.exs` / `pubspec.yaml` | — | Secondary source: these are the files release-please's strategies update. | [release-please](https://github.com/googleapis/release-please/blob/main/docs/customizing.md) |
| Helm | `Chart.yaml` | `version` (SemVer, required) vs `appVersion` (free-form, "quotes recommended") | The `.tgz` filename must match `version`. | [Helm](https://helm.sh/docs/topics/charts/) |
| Helm OCI | registry tag | chart version | "OCI registries don't support + as a tag character. Helm translates the + to _". Argo CD and Flux had bugs reversing it. | [Helm](https://helm.sh/docs/v3/topics/registries), [argo-cd#14097](https://github.com/argoproj/argo-cd/issues/14097), [flux#1102](https://github.com/fluxcd/helm-controller/pull/1102) |
| Docker/OCI | image tag; `LABEL` | `org.opencontainers.image.version` (+ `.revision`, `.created`) | Tag must match `[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}`, so `+` is not allowed. | [annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md), [dist-spec](https://github.com/opencontainers/distribution-spec/blob/main/spec.md) |
| Terraform modules | git tag only | semver, optional `v` | Non-version tags are ignored. | [HashiCorp](https://developer.hashicorp.com/terraform/registry/modules/publish) |
| GitHub Actions | git tags | `v1.0.1` + a moving major tag `v1` | Re-point `v1` on each release. Users can pin by full SHA. | [GitHub](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/manage-custom-actions) |
| VS Code extension | `package.json` | `version` | Only `major.minor.patch` (no semver pre-release). Convention: even minor = stable, odd minor = pre-release. | [VS Code](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) |
| Browser extension | `manifest.json` | `version` (1–4 ints, each 0–65535, no leading zeros, not all zeros); `version_name` for display | — | [Chrome](https://developer.chrome.com/docs/extensions/reference/manifest/version) |
| C/C++ | `CMakeLists.txt` | `project(... VERSION a[.b[.c[.d]]])` | Integers only; sets `PROJECT_VERSION_*`. | [CMake](https://cmake.org/cmake/help/latest/command/project.html) |
| Lerna | `lerna.json` | `version`, or the literal `"independent"` | — | [Lerna](https://lerna.js.org/docs/features/version-and-publish) |
| Changelog | `CHANGELOG.md` | `## [Unreleased]`, `## [1.1.2] - 2024-09-27`, compare links at the bottom, `[YANKED]` | — | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) |

### Inferences
- **Tag-only ecosystems** (Go, Terraform, Actions, Composer best practice, setuptools-scm): there is no file to edit. bump2v should support a "tag-only" target.
- **Go major bump**: going to v2+ means editing the `module` line and, by implication, every import path.
- **Dynamic Python versions**: if `version` is listed in `dynamic`, bump2v must not write a static `version` into `pyproject.toml`.
- **Cargo.lock**: probably holds a root `[[package]]` entry, since knope updates it. Not verified.

### Gaps
- No primary page fetched for:
  - Xcode `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` and agvtool
  - Apple upload-uniqueness rules
  - Flutter's iOS mapping
  - Expo `runtimeVersion` policy semantics and EAS `appVersionSource`
  - Gradle `gradle.properties` and Kotlin Multiplatform
  - Unity `bundleVersion`
  - SwiftPM tags
  - gemspec / Gemfile.lock
  - Kubernetes manifests and Kustomize `newTag`
- Not confirmed that `packages[""].version` duplicates the top-level `version` in `package-lock.json`; that is an inference.

## 3. Edge cases a regex bumper gets wrong

### Takeaway
bump2v's current code shows several of these failures, confirmed with in-memory Python tests.

### Cited Findings: bump2v code (this repo, as of commit `e94c1a8`)
- **Replace-all**: `bump2v/bumpversion/utils.py:117` uses `str.replace`, which rewrites *every* match. A test on `{"version":"1.2.3","dependencies":{"x":{"version":"1.2.3"}}}` bumped both entries. This is the lockfile/dependency collision.
- **Wide fallback**: `utils.py:119-123`. If the configured search string is missing, bump2v replaces the bare `current_version.original` anywhere in the file.
- **Loose "found" check**: `utils.py:89-91`. `contains()` is a per-line substring check, so a dependency line counts as "found" just as the root line does.
- **Mixed line endings crash**: `utils.py:107/144` and `cli.py:312/715`. With mixed CRLF/LF, `f.newlines` is a tuple, e.g. `('\n','\r\n')`, and passing it back to `open()` raises `TypeError: … 'newline' must be str or None, not tuple`. Python documents `newlines` as "a string, a tuple of strings, or None" ([Python io](https://docs.python.org/3/library/io.html)). The crash comes at write time, after earlier files may already have been written, so it can leave a partial bump.
- **UTF-8 BOM**: `encoding="utf-8"` (not `utf-8-sig`) keeps the BOM as `﻿` at the start of line 1. Searches anchored at the start of a line then fail.
  - Inference: UTF-16 files (Windows `.rc` and similar) will raise a decode error. Untested.

### Cited Findings: format traps
- **Typed fields**: Expo's `buildNumber` is a string but `versionCode` is an integer ([Expo](https://docs.expo.dev/versions/latest/config/app/)). Helm advises quoting `appVersion` because YAML reads `1.0` as a float ([Helm](https://helm.sh/docs/topics/charts/)).
- **Build numbers that must always increase**, independent of semver:
  - Android `versionCode`, max 2.1e9 ([Android](https://developer.android.com/studio/publish/versioning))
  - Flutter `+N`, with split APKs adding ABI×1000 ([Flutter](https://docs.flutter.dev/deployment/android))
  - .NET `FileVersion` Revision ([MS](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning))
- **Targets that cannot hold a SemVer pre-release or `+`**:
  - Chrome (integers only) ([Chrome](https://developer.chrome.com/docs/extensions/reference/manifest/version))
  - VS Code ([VS Code](https://code.visualstudio.com/api/working-with-extensions/publishing-extension))
  - `CFBundleShortVersionString` ([Apple](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleshortversionstring))
  - OCI tags (no `+`) ([dist-spec](https://github.com/opencontainers/distribution-spec/blob/main/spec.md))
- **Normalisation means the string in the file is not the canonical one**:
  - PEP 440: `1.0-1` = `1.0.post1` ([PyPA](https://packaging.python.org/en/latest/specifications/version-specifiers/))
  - NuGet: `1.0.0.0` = `1.0.0` ([NuGet](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning))
  - CalVer padding: `26.04` vs `26.4` ([calver.org](https://calver.org/))
- **Pre-release ordering differs by scheme**:
  - SemVer: `rc.10 > rc.2` ([semver.org](https://semver.org/))
  - NuGet SemVer 1: `alpha10 < alpha2` ([NuGet](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning))
  - Maven is case-insensitive; SemVer is case-sensitive ([Maven](https://maven.apache.org/pom.html))
- **Multiple versions in one file**: a .NET project has 4 version fields ([MS](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/versioning)). Helm has `version` and `appVersion` ([Helm](https://helm.sh/docs/topics/charts/)). Expo has `version`, `buildNumber`, `versionCode` and `runtimeVersion` ([Expo](https://docs.expo.dev/versions/latest/config/app/)).

### Inferences
Requirements for bump2v:
- Edit structured files by key path (JSON, TOML, YAML, XML, plist, Gradle).
- Replace only the first or nth match, or require exactly one match.
- Remove the bare-version fallback, or make it opt-in.
- Keep line endings per line rather than per file.
- Read with `utf-8-sig` and write the BOM back if it was there.
- Validate every file before writing any, so a failure cannot leave a partial bump.
- Support a separate integer build counter, and a per-target "render" step: `+` → `_` for OCI, integers only for Chrome.

## 4. Monorepo strategies

### Cited Findings
- **changesets**: `fixed` groups are bumped and published together even when unchanged. `linked` groups share a version but are not forced to publish. `updateInternalDependencies` is `patch` or `minor`. Private packages are not versioned or tagged by default. [changesets](https://github.com/changesets/changesets/blob/main/docs/config-file-options.md)
- **release-please**:
  - `.release-please-manifest.json` maps each path to its version. [manifest-releaser](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
  - Default tag is `<component>-v<version>`; with `include-component-in-tag:false` it becomes `v<version>`. [manifest-releaser](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
  - The `linked-versions` plugin applies the highest version across a group. [manifest-releaser](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
  - The `node-workspace` and `cargo-workspace` plugins patch-bump dependents, and the Cargo one also updates the lockfile. `separate-pull-requests` is an option. [manifest-releaser](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
- **Nx**: `projectsRelationship: "independent"` tags as `{projectName}@{version}` (e.g. `pkg-1@1.1.0`). The pattern is set by `release.releaseTag.pattern` in Nx 22+. Projects can be put in release groups. [Nx](https://nx.dev/docs/guides/nx-release/release-projects-independently)
- **Lerna**: fixed mode keeps the version in `lerna.json` and tags `v1.0.0`; setting the version to `"independent"` switches modes. [Lerna](https://lerna.js.org/docs/features/version-and-publish)
- **knope**: `[package]` for a single package, `[packages."name"]` for many, each with `versioned_files`. [knope](https://knope.tech/reference/config-file/packages/)
- **Go**: a module in a subdirectory *must* be tagged `sub/vX.Y.Z`. [go.dev](https://go.dev/ref/mod)

### Gaps
- Not confirmed: Nx's fixed-mode default tag, Lerna's independent-mode tag, changesets' tag format (`pkg@x.y.z`), and knope's multi-package tag naming.

## 5. What the best tools do

### Cited Findings
- **release-please**: picks an updater by file extension. It has structured updaters for json (jsonpath), xml (xpath), yaml and toml (jsonpath). It also supports inline markers `x-release-please-version|major|minor|patch` and blocks between `x-release-please-start-version` and `x-release-please-end`. It has `release-type` strategies for dart, elixir, go, helm, java, maven, node, expo, ocaml, php, python, ruby, rust, sfdx, simple and terraform-module. Versioning strategies include `always-bump-*`, `service-pack` (`1.2.3-sp.1`) and `prerelease`. [customizing.md](https://github.com/googleapis/release-please/blob/main/docs/customizing.md)
- **knope**: has a parser for each file format. It handles:
  - Cargo.toml, including `workspace.package` and the dependency tables
  - Cargo.lock
  - package.json and package-lock.json (lockfile format v2+)
  - deno.json and deno.lock
  - pyproject.toml (PEP 621 or Poetry)
  - pom.xml
  - pubspec.yaml, gleam.toml, go.mod and tauri.conf.json

  `dependency` targets dependents by name, and `regex` takes a named `version` group. For Go it reads a version comment in `go.mod` or the latest tag, honouring the major-version rule. [knope](https://knope.tech/reference/config-file/packages/)
- **bump-my-version** (successor to bump2version):
  - Per-file options: `filename`, `glob`, `glob_exclude`, `parse`, `serialize`, `search`, `replace`, `regex`, `ignore_missing_version`, `ignore_missing_file`, `include_bumps`, `exclude_bumps`. [file config](https://callowayproject.github.io/bump-my-version/reference/configuration/file/)
  - The per-file page as fetched shows no structured-key option. [file config](https://callowayproject.github.io/bump-my-version/reference/configuration/file/)
  - Config lookup order: `--config-file`, then `BUMPVERSION_CONFIG_FILE`, then `.bumpversion.cfg` (legacy), `.bumpversion.toml`, `setup.cfg`, `pyproject.toml`, nearest first up to the repo root. [config](https://callowayproject.github.io/bump-my-version/reference/configuration/)
  - With no config, it falls back to a static `project.version` and ignores a dynamic one. The INI format "will likely be dropped". [config](https://callowayproject.github.io/bump-my-version/reference/configuration/)

### Inferences
- The strongest model for bump2v combines three things: knope-style per-format, dependency-aware handlers; release-please-style key paths and inline markers as an escape hatch; and bump-my-version's `include_bumps`/`exclude_bumps` for build counters.
- Lockfiles are better regenerated by the package manager than edited by regex. This is a design judgement, not a sourced fact.
