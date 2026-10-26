"""`bump2v init`: find where a project keeps its version and write a config for it.

Detection only records a file when the version sits in a tight, recognisable string,
so the generated search can't match anything else in the file by accident.
"""
import glob
import json
import os
import re
import tomllib
from collections import Counter

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

_DUNDER_VERSION = re.compile(r"""__version__\s*=\s*(["'])([^"']+)\1""")
_YAML_VERSION = re.compile(r"""^version:[ \t]*(["']?)([^"'\s#]+)\1[ \t]*(#.*)?$""", re.MULTILINE)
_JSON_VERSION = re.compile(r'"version"\s*:\s*"([^"]+)"')
_TOML_VERSION = re.compile(r"""^version\s*=\s*(["'])([^"']+)\1""", re.MULTILINE)

_DUNDER_CANDIDATES = (
    "appInfo.py", "*/appInfo.py", "*/*/appInfo.py",
    "version.py", "_version.py", "*/__init__.py", "*/_version.py", "*/version.py",
    "src/*/__init__.py", "src/*/_version.py", "src/*/version.py",
)


class Source:
    """One place a version lives: the file, the version found, and the search for it."""

    def __init__(self, path, version, search, replace_all=True, note=None):
        self.path = path
        self.version = version
        self.search = search
        self.replace_all = replace_all
        self.note = note

    def as_dict(self):
        return {"path": self.path, "version": self.version, "search": self.search}


def _read(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def _template(matched_text, version):
    """Turn the text that matched into a search template: the version becomes a placeholder."""
    return matched_text.replace(version, "{current_version}", 1)


def _from_json(path):
    try:
        data = json.loads(_read(path))
    except (OSError, ValueError):
        return None
    version = data.get("version") if isinstance(data, dict) else None
    if path.endswith("app.json") and isinstance(data, dict) and isinstance(data.get("expo"), dict):
        version = data["expo"].get("version")
    if not isinstance(version, str):
        return None
    match = next((m for m in _JSON_VERSION.finditer(_read(path)) if m.group(1) == version), None)
    if not match:
        return None
    return Source(path, version, _template(match.group(0), version))


def _from_toml(path, tables):
    """pyproject.toml / Cargo.toml: a static version in one of `tables`."""
    try:
        text = _read(path)
        data = tomllib.loads(text)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    for dotted in tables:
        table = data
        for key in dotted.split("."):
            table = table.get(key, {}) if isinstance(table, dict) else {}
        if "version" in table.get("dynamic", []):
            return Source(path, None, None, note="version is dynamic (set from git tags); not edited")
        version = table.get("version")
        if isinstance(version, str):
            match = next((m for m in _TOML_VERSION.finditer(text) if m.group(2) == version), None)
            if match:
                # Dependency pins can repeat the same string, so only bump the first match.
                return Source(path, version, _template(match.group(0), version), replace_all=False)
    return None


def _from_yaml(path):
    try:
        match = _YAML_VERSION.search(_read(path))
    except OSError:
        return None
    if not match:
        return None
    version = match.group(2)
    return Source(path, version, _template(match.group(0).split("#")[0].rstrip(), version))


def _from_dunder(path):
    try:
        match = _DUNDER_VERSION.search(_read(path))
    except OSError:
        return None
    if not match:
        return None
    return Source(path, match.group(2), _template(match.group(0), match.group(2)))


def _from_plain(path):
    try:
        text = _read(path).strip()
    except OSError:
        return None
    if "\n" in text or not re.match(r"^\d+(\.\d+)*([\-+.][\w.\-+]*)?$", text):
        return None
    return Source(path, text, "{current_version}")


def detect(root="."):
    """Every version source under root (paths relative to root), most authoritative first."""
    def exists(name):
        return os.path.isfile(os.path.join(root, name))

    found = []

    def add(source):
        if source is not None and source.path not in {s.path for s in found}:
            # Config paths use "/" on every OS, so a config written on Windows works elsewhere.
            source.path = source.path.replace(os.sep, "/")
            found.append(source)

    cwd = os.getcwd()
    os.chdir(root)
    try:
        if exists("package.json"):
            add(_from_json("package.json"))
        if exists("pyproject.toml"):
            add(_from_toml("pyproject.toml", ("project", "tool.poetry")))
        if exists("Cargo.toml"):
            add(_from_toml("Cargo.toml", ("package", "workspace.package")))
        for name in ("Chart.yaml", "pubspec.yaml"):
            if exists(name):
                add(_from_yaml(name))
        if exists("app.json"):
            add(_from_json("app.json"))
        for pattern in _DUNDER_CANDIDATES:
            for path in sorted(glob.glob(pattern)):
                if "site-packages" not in path and not path.startswith((".", "node_modules")):
                    add(_from_dunder(path))
        for name in ("VERSION", "VERSION.txt", "version.txt"):
            if exists(name):
                add(_from_plain(name))
    finally:
        os.chdir(cwd)
    return found


def choose(sources):
    """Pick current_version: the most common version, ties going to the earlier source.

    Returns (version, used, skipped): the sources that hold it, and the ones that don't.
    """
    usable = [s for s in sources if s.version]
    if not usable:
        return None, [], sources
    counts = Counter(s.version for s in usable)
    best = max(counts.values())
    version = next(s.version for s in usable if counts[s.version] == best)
    used = [s for s in usable if s.version == version]
    skipped = [s for s in sources if s not in used]
    return version, used, skipped


def render_config(version, sources):
    lines = [
        "[bumpversion]",
        f"current_version = {version}",
        "commit = True",
        "tag = True",
        "tag_name = v{new_version}",
        "message = Version Updated: {current_version} → {new_version}",
        "",
    ]
    for source in sources:
        lines.append(f"[bumpversion:file:{source.path}]")
        if source.search != "{current_version}":
            lines.append(f"search = {source.search}")
            lines.append(f"replace = {source.search.replace('{current_version}', '{new_version}')}")
        if not source.replace_all:
            lines.append("replace_all = False")
        lines.append("")
    return "\n".join(lines)


RELEASING = """\
## Releasing

Versions are managed by bump2v ({config}). Never edit version numbers by hand.

- Preview: `bump2v plan auto` (add `--json` for a machine-readable plan). Changes nothing.
- Release: `bump2v release auto` bumps every configured file, commits, tags and pushes.
  Add `--no-push` to keep it local. Commit your work first: a dirty tree is refused.
- Check: `bump2v check` fails with exit 4 when a file has drifted from the current version.
- Exit codes: 0 ok, 3 dirty tree, 4 version not found, 5 tag exists, 6 push failed,
  7 nothing to release.
"""


def agents_file(root="."):
    """CLAUDE.md if the repo has one (Claude Code reads it instead of AGENTS.md), else AGENTS.md."""
    return "CLAUDE.md" if os.path.isfile(os.path.join(root, "CLAUDE.md")) else "AGENTS.md"


def add_releasing_section(path, config_file):
    """Append the Releasing section unless the file already has one. Returns True if added."""
    existing = _read(path) if os.path.isfile(path) else ""
    if re.search(r"^#+\s*Releasing\b", existing, re.MULTILINE) and "bump2v" in existing:
        return False
    if not existing:
        separator = ""
    elif existing.endswith("\n"):
        separator = "\n"
    else:
        separator = "\n\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(separator + RELEASING.format(config=config_file))
    return True
