import pytest
from bump2v.bumpversion.cli import _check_files_contain_version
from bump2v.bumpversion.exceptions import VersionNotFoundException
from bump2v.bumpversion.utils import ConfiguredFile
from bump2v.bumpversion.version_part import VersionConfig


@pytest.fixture
def semver_config():
    return VersionConfig(
        parse=r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        serialize=["{major}.{minor}.{patch}"],
        search="{current_version}",
        replace="{new_version}",
    )


@pytest.fixture
def context():
    return {"current_version": "1.0.0"}


class TestCheckFilesContainVersion:
    def test_raises_when_version_missing(self, tmp_path, semver_config, context):
        f = tmp_path / "test.txt"
        f.write_text("no version here", encoding="utf-8")
        cf = ConfiguredFile(str(f), semver_config)
        version = semver_config.parse("1.0.0")

        with pytest.raises(VersionNotFoundException):
            _check_files_contain_version([cf], version, context)

    def test_ignore_missing_does_not_raise(self, tmp_path, semver_config, context):
        f = tmp_path / "test.txt"
        f.write_text("no version here", encoding="utf-8")
        cf = ConfiguredFile(str(f), semver_config)
        version = semver_config.parse("1.0.0")

        # Must not raise with ignore_missing=True
        _check_files_contain_version([cf], version, context, ignore_missing=True)

    def test_passes_when_version_present(self, tmp_path, semver_config, context):
        f = tmp_path / "test.txt"
        f.write_text("current version is 1.0.0 here", encoding="utf-8")
        cf = ConfiguredFile(str(f), semver_config)
        version = semver_config.parse("1.0.0")

        # Must not raise
        _check_files_contain_version([cf], version, context)

    def test_ignore_missing_still_passes_found_files(self, tmp_path, semver_config, context):
        found = tmp_path / "found.txt"
        found.write_text("version is 1.0.0", encoding="utf-8")
        missing = tmp_path / "missing.txt"
        missing.write_text("no version here", encoding="utf-8")

        cf_found = ConfiguredFile(str(found), semver_config)
        cf_missing = ConfiguredFile(str(missing), semver_config)
        version = semver_config.parse("1.0.0")

        # Mixed: one found, one missing — should not raise with ignore_missing=True
        _check_files_contain_version([cf_found, cf_missing], version, context, ignore_missing=True)

    def test_empty_file_list_is_noop(self, semver_config, context):
        version = semver_config.parse("1.0.0")
        _check_files_contain_version([], version, context)


# --- file edits: line endings, BOM, match count, no partial bumps ---

from bump2v.bumpversion import cli
from bump2v.bumpversion.utils import FileChange


def _bump(tmp_path, monkeypatch, config, files, *args):
    """Run the core in a directory without version control and return the files' bytes."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".bumpversion.cfg").write_bytes(config)
    for name, data in files.items():
        (tmp_path / name).write_bytes(data)
    cli.main(["patch", *args])
    return {name: (tmp_path / name).read_bytes() for name in files}


CFG = b"[bumpversion]\ncurrent_version = 1.0.0\n\n[bumpversion:file:v.txt]\n"


class TestFileEdits:
    def test_crlf_file_keeps_crlf(self, tmp_path, monkeypatch):
        out = _bump(tmp_path, monkeypatch, CFG, {"v.txt": b"a\r\nversion 1.0.0\r\nb\r\n"})
        assert out["v.txt"] == b"a\r\nversion 1.0.1\r\nb\r\n"

    def test_mixed_line_endings_kept_per_line(self, tmp_path, monkeypatch):
        out = _bump(tmp_path, monkeypatch, CFG, {"v.txt": b"a\r\nversion 1.0.0\nb\r\n"})
        assert out["v.txt"] == b"a\r\nversion 1.0.1\nb\r\n"

    def test_bom_kept_and_line_start_search_matches(self, tmp_path, monkeypatch):
        cfg = CFG + b'search = __version__ = "{current_version}"\nreplace = __version__ = "{new_version}"\n'
        out = _bump(tmp_path, monkeypatch, cfg, {"v.txt": b'\xef\xbb\xbf__version__ = "1.0.0"\n'})
        assert out["v.txt"] == b'\xef\xbb\xbf__version__ = "1.0.1"\n'

    def test_multiline_search_matches_crlf(self, tmp_path, monkeypatch):
        cfg = CFG + b"search = [app]\n  version = {current_version}\nreplace = [app]\n  version = {new_version}\n"
        data = b"[lib]\r\nversion = 1.0.0\r\n[app]\r\nversion = 1.0.0\r\n"
        out = _bump(tmp_path, monkeypatch, cfg, {"v.txt": data})
        assert out["v.txt"] == b"[lib]\r\nversion = 1.0.0\r\n[app]\r\nversion = 1.0.1\r\n"

    def test_replace_all_is_the_default(self, tmp_path, monkeypatch):
        out = _bump(tmp_path, monkeypatch, CFG, {"v.txt": b"1.0.0\ndep==1.0.0\n"})
        assert out["v.txt"] == b"1.0.1\ndep==1.0.1\n"

    def test_replace_all_false_bumps_first_match_only(self, tmp_path, monkeypatch):
        cfg = CFG + b"replace_all = False\n"
        out = _bump(tmp_path, monkeypatch, cfg, {"v.txt": b"1.0.0\ndep==1.0.0\n"})
        assert out["v.txt"] == b"1.0.1\ndep==1.0.0\n"

    def test_replace_all_false_as_global_default(self, tmp_path, monkeypatch):
        cfg = CFG.replace(b"current_version = 1.0.0\n", b"current_version = 1.0.0\nreplace_all = False\n")
        out = _bump(tmp_path, monkeypatch, cfg, {"v.txt": b"1.0.0\ndep==1.0.0\n"})
        assert out["v.txt"] == b"1.0.1\ndep==1.0.0\n"

    def test_custom_search_never_falls_back_to_bare_version(self, tmp_path, monkeypatch):
        cfg = CFG + b'search = "version": "{current_version}"\nreplace = "version": "{new_version}"\n'
        data = b'{"name": "x", "dep": "1.0.0"}\n'
        out = _bump(tmp_path, monkeypatch, cfg, {"v.txt": data}, "--ignore-missing-version")
        assert out["v.txt"] == data

    def test_config_with_bom_and_mixed_newlines(self, tmp_path, monkeypatch):
        cfg = b"\xef\xbb\xbf[bumpversion]\r\ncurrent_version = 1.0.0\n\n[bumpversion:file:v.txt]\r\n"
        _bump(tmp_path, monkeypatch, cfg, {"v.txt": b"1.0.0\n"})
        written = (tmp_path / ".bumpversion.cfg").read_bytes()
        assert b"current_version = 1.0.1" in written
        assert b"\r" not in written

    def test_failed_write_restores_files_already_written(self, tmp_path, monkeypatch):
        cfg = CFG + b"\n[bumpversion:file:w.txt]\n"
        original_write = FileChange.write

        def write(self):
            if self.path == "w.txt":
                raise OSError("disk full")
            original_write(self)

        monkeypatch.setattr(FileChange, "write", write)
        with pytest.raises(OSError):
            _bump(tmp_path, monkeypatch, cfg, {"v.txt": b"1.0.0\n", "w.txt": b"1.0.0\n"})
        assert (tmp_path / "v.txt").read_bytes() == b"1.0.0\n"
        assert b"current_version = 1.0.0" in (tmp_path / ".bumpversion.cfg").read_bytes()


# --- TOML config ([tool.bumpversion], bump-my-version's format) ---

def _run_core(tmp_path, monkeypatch, files, *args):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    cli.main(list(args))
    return {name: (tmp_path / name).read_text(encoding="utf-8") for name in files}


PYPROJECT = '''[project]
name = "demo"
version = "1.0.0"  # keep this comment
dependencies = ["other==1.0.0"]

[tool.bumpversion]
# release settings
current_version = "1.0.0"
commit = false

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'

[[tool.bumpversion.files]]
filename = "src.py"
'''


class TestTomlConfig:
    def test_pyproject_is_config_and_bumped_file(self, tmp_path, monkeypatch):
        out = _run_core(tmp_path, monkeypatch,
                        {"pyproject.toml": PYPROJECT, "src.py": '__version__ = "1.0.0"\n'}, "minor")
        assert out["pyproject.toml"] == (
            PYPROJECT.replace('version = "1.0.0"  #', 'version = "1.1.0"  #')
            .replace('current_version = "1.0.0"', 'current_version = "1.1.0"')
        )
        assert '"other==1.0.0"' in out["pyproject.toml"]
        assert out["src.py"] == '__version__ = "1.1.0"\n'

    def test_bumpversion_toml_with_parts_and_serialize(self, tmp_path, monkeypatch):
        config = '''[tool.bumpversion]
current_version = "1.0.0-dev"
parse = "(?P<major>\\\\d+)\\\\.(?P<minor>\\\\d+)\\\\.(?P<patch>\\\\d+)(-(?P<release>\\\\w+))?"
serialize = ["{major}.{minor}.{patch}-{release}", "{major}.{minor}.{patch}"]

[tool.bumpversion.parts.release]
optional_value = "final"
values = ["dev", "final"]

[[tool.bumpversion.files]]
filename = "VERSION"
'''
        out = _run_core(tmp_path, monkeypatch,
                        {".bumpversion.toml": config, "VERSION": "1.0.0-dev\n"}, "release")
        assert out["VERSION"] == "1.0.0\n"
        assert 'current_version = "1.0.0"' in out[".bumpversion.toml"]

    def test_same_file_listed_twice_with_different_searches(self, tmp_path, monkeypatch):
        config = '''[tool.bumpversion]
current_version = "1.0.0"

[[tool.bumpversion.files]]
filename = "app.json"
search = '"version": "{current_version}"'
replace = '"version": "{new_version}"'

[[tool.bumpversion.files]]
filename = "app.json"
search = '"runtimeVersion": "{current_version}"'
replace = '"runtimeVersion": "{new_version}"'
'''
        app = '{"version": "1.0.0", "runtimeVersion": "1.0.0", "sdk": "1.0.0"}\n'
        out = _run_core(tmp_path, monkeypatch, {".bumpversion.toml": config, "app.json": app}, "patch")
        assert out["app.json"] == '{"version": "1.0.1", "runtimeVersion": "1.0.1", "sdk": "1.0.0"}\n'

    def test_unsupported_option_is_ignored_with_a_warning(self, tmp_path, monkeypatch, caplog):
        config = '[tool.bumpversion]\ncurrent_version = "1.0.0"\nsetup_hooks = ["echo hi"]\n\n' \
                 '[[tool.bumpversion.files]]\nfilename = "VERSION"\nregex = true\n'
        out = _run_core(tmp_path, monkeypatch, {".bumpversion.toml": config, "VERSION": "1.0.0\n"}, "patch")
        assert out["VERSION"] == "1.0.1\n"
        assert "setup_hooks" in caplog.text and "regex" in caplog.text


class TestConfigDiscovery:
    def test_order(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
        assert cli._determine_config_file(None) == ".bumpversion.cfg"
        (tmp_path / "setup.cfg").write_text("[metadata]\n", encoding="utf-8")
        assert cli._determine_config_file(None) == "setup.cfg"
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
        assert cli._determine_config_file(None) == "setup.cfg"
        (tmp_path / "pyproject.toml").write_text('[tool.bumpversion]\ncurrent_version = "1.0.0"\n', encoding="utf-8")
        assert cli._determine_config_file(None) == "pyproject.toml"
        (tmp_path / ".bumpversion.toml").write_text("", encoding="utf-8")
        assert cli._determine_config_file(None) == ".bumpversion.toml"
        (tmp_path / ".bumpversion.cfg").write_text("", encoding="utf-8")
        assert cli._determine_config_file(None) == ".bumpversion.cfg"
        monkeypatch.setenv("BUMP2V_CONFIG", "custom.cfg")
        assert cli._determine_config_file(None) == "custom.cfg"
        assert cli._determine_config_file("explicit.cfg") == "explicit.cfg"


class TestSameFileTwice:
    def test_ini_file_sections_with_suffix_both_apply(self, tmp_path, monkeypatch):
        cfg = (b'[bumpversion]\ncurrent_version = 1.0.0\n\n'
               b'[bumpversion:file:app.json]\nsearch = "version": "{current_version}"\nreplace = "version": "{new_version}"\n\n'
               b'[bumpversion:file(2):app.json]\nsearch = "runtimeVersion": "{current_version}"\n'
               b'replace = "runtimeVersion": "{new_version}"\n')
        out = _bump(tmp_path, monkeypatch, cfg,
                    {"app.json": b'{"version": "1.0.0", "runtimeVersion": "1.0.0", "sdk": "1.0.0"}\n'})
        assert out["app.json"] == b'{"version": "1.0.1", "runtimeVersion": "1.0.1", "sdk": "1.0.0"}\n'
