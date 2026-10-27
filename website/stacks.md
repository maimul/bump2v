# Your stack

`bump2v init` writes the config for you when it finds `package.json`, `pyproject.toml`,
`Cargo.toml`, `Chart.yaml`, `pubspec.yaml`, `app.json`, a `__version__` in a Python file, or a
`VERSION` file. Below is what it writes, and what to add by hand. After any change to the
config, `bump2v plan patch` shows every file and how many places match, without changing anything.

Each `[bumpversion:file:...]` section names one file. `search` is the text to find, with
`{current_version}` where the version goes; `replace` is what it becomes. Without `search`,
bump2v looks for the bare version string. By default every match in the file is replaced;
`replace_all = False` replaces only the first, and `bump2v plan` warns when a search matches
more than once.

## Node.js, React, TypeScript

```ini
[bumpversion]
current_version = 1.4.2
commit = True
tag = True
tag_name = v{new_version}
message = Version Updated: {current_version} → {new_version}

[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
```

The search includes `"version":`, so a dependency that happens to be at the same version
(`"left-pad": "1.4.2"`) is left alone.

Leave `package-lock.json` out: its own version also appears in nested packages, and npm
rewrites the root entry the next time it writes the lockfile. `npm ci` doesn't check it.

## Python

```ini
[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
replace_all = False

[bumpversion:file:src/app/__init__.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"
```

`replace_all = False` bumps only the first `version = "..."`, which is the project's own in a
usual `pyproject.toml`, and leaves any later table alone. If `pyproject.toml` has `dynamic = ["version"]`, there's
nothing to edit there: list only the file your build backend reads the version from.

## Rust

```ini
[bumpversion:file:Cargo.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
replace_all = False

[bumpversion:file:Cargo.lock]
search = name = "tool"
	version = "{current_version}"
replace = name = "tool"
	version = "{new_version}"
```

`Cargo.lock` lists every crate with a `version` line, so the search names your crate on the
line before. Indent the second line of `search` and `replace` (a tab or spaces); the config
file reads it as the next line of the same value. Keep `Cargo.lock` in the config if you build
with `--locked`, which fails when the lockfile is out of date.

## Helm charts

```ini
[bumpversion:file:Chart.yaml]
```

With no `search`, bump2v replaces the bare version everywhere in the file, so `version` and
`appVersion` move together when they're the same. `bump2v plan` says how many places matched.
If the chart's version and the app's version differ, use `search = version: {current_version}`
and keep `appVersion` in the app's own config.

## Expo and React Native

```ini
[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"

[bumpversion:file:app.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
```

Store build numbers (`ios.buildNumber`, `android.versionCode`) count up and never reset, which
version parts can't do yet; keep incrementing those in your build (EAS's `autoIncrement`, for
example). The same goes for Flutter's `version: 1.2.3+45`: `bump2v init` warns that it isn't
`MAJOR.MINOR.PATCH`.

## .NET

```ini
[bumpversion:file:src/App/App.csproj]
search = <Version>{current_version}</Version>
replace = <Version>{new_version}</Version>
```

The search includes the element, so `<PackageReference ... Version="1.2.3" />` is left alone.

## Go, Terraform modules, GitHub Actions: the tag is the version

```ini
[bumpversion]
current_version = 0.4.0
commit = True
tag = True
tag_name = v{new_version}
```

With no file sections, a release commits the new `current_version` in `.bumpversion.cfg` and
tags it `v0.5.0`. For Go modules at v2 and later, the module path in `go.mod` also changes
(`/v2`); make that change in the commit that breaks the API, before `bump2v release major`.

## A plain VERSION file

```ini
[bumpversion:file:VERSION]
```

## Several files

List as many sections as you need, one per file; a release updates all of them in one commit,
and `bump2v check` (in CI or [as a pre-commit hook](https://github.com/maimul/bump2v#pre-commit-hook))
fails when any of them drifts from `current_version`. The full list of config keys is in the
[README](https://github.com/maimul/bump2v#full-config-reference).
