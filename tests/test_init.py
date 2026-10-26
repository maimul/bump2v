import json
import sys

import pytest

from bump2v import __main__ as bump2v_main
from bump2v import init as setup
from bump2v.bumpversion import cli


def _write(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _init(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["bump2v", "init", *args, "--json"])
    code = 0
    try:
        bump2v_main.main()
    except SystemExit as e:
        code = e.code
    return code, json.loads(capsys.readouterr().out)


class TestDetect:
    def test_finds_each_kind_of_source(self, tmp_path):
        _write(tmp_path, {
            "package.json": '{"name": "x", "version": "1.2.3", "dependencies": {"y": "1.2.3"}}',
            "Cargo.toml": '[package]\nname = "x"\nversion = "1.2.3"\n\n[dependencies]\nz = { version = "1.2.3" }\n',
            "Chart.yaml": 'apiVersion: v2\nversion: "1.2.3"\nappVersion: "1.2.3"\n',
            "pkg/__init__.py": "__version__ = '1.2.3'\n",
            "VERSION": "1.2.3\n",
        })
        found = {s.path: s for s in setup.detect(str(tmp_path))}
        assert found["package.json"].search == '"version": "{current_version}"'
        assert found["Cargo.toml"].search == 'version = "{current_version}"'
        assert not found["Cargo.toml"].replace_all
        assert found["Chart.yaml"].search == 'version: "{current_version}"'
        assert found["pkg/__init__.py"].search == "__version__ = '{current_version}'"
        assert found["VERSION"].search == "{current_version}"

    def test_dynamic_pyproject_version_is_not_edited(self, tmp_path):
        _write(tmp_path, {"pyproject.toml": '[project]\nname = "x"\ndynamic = ["version"]\n'})
        (source,) = setup.detect(str(tmp_path))
        assert source.version is None and "dynamic" in source.note

    def test_expo_app_json(self, tmp_path):
        _write(tmp_path, {"app.json": '{"expo": {"name": "a", "version": "2.0.0", "runtimeVersion": "2.0.0"}}'})
        (source,) = setup.detect(str(tmp_path))
        assert source.version == "2.0.0" and source.search == '"version": "{current_version}"'

    def test_choose_takes_the_most_common_version(self, tmp_path):
        _write(tmp_path, {"package.json": '{"version": "1.0.0"}', "VERSION": "1.0.1\n",
                          "pkg/__init__.py": '__version__ = "1.0.1"\n'})
        version, used, skipped = setup.choose(setup.detect(str(tmp_path)))
        assert version == "1.0.1"
        assert [s.path for s in skipped] == ["package.json"]


class TestInitCommand:
    def test_generated_config_bumps_only_the_project_version(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
        pyproject = '[project]\nname = "x"\nversion = "1.0.0"\ndependencies = ["dep==1.0.0"]\n'
        _write(tmp_path, {"pyproject.toml": pyproject, "x/__init__.py": '__version__ = "1.0.0"\n'})
        code, result = _init(monkeypatch, capsys)
        assert code == 0 and result["created"] and result["current_version"] == "1.0.0"
        cli.main(["minor"])
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == pyproject.replace(
            'version = "1.0.0"', 'version = "1.1.0"', 1)
        assert (tmp_path / "x/__init__.py").read_text(encoding="utf-8") == '__version__ = "1.1.0"\n'

    def test_existing_config_is_left_alone(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
        _write(tmp_path, {".bumpversion.cfg": "[bumpversion]\ncurrent_version = 9.9.9\n", "VERSION": "1.0.0\n"})
        code, result = _init(monkeypatch, capsys)
        assert code == 0 and not result["created"]
        assert (tmp_path / ".bumpversion.cfg").read_text(encoding="utf-8") == "[bumpversion]\ncurrent_version = 9.9.9\n"

    def test_nothing_to_manage_exits_4(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
        code, result = _init(monkeypatch, capsys)
        assert code == 4 and result["error"]["code"] == "nothing_detected"
        assert not (tmp_path / ".bumpversion.cfg").exists()

    def test_agents_section_goes_to_claude_md_when_present(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
        _write(tmp_path, {"VERSION": "1.0.0\n", "CLAUDE.md": "# Project\n"})
        code, result = _init(monkeypatch, capsys, "--agents")
        assert result["agents"] == {"file": "CLAUDE.md", "added": True}
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert text.startswith("# Project\n\n## Releasing") and "bump2v release auto" in text
        assert not (tmp_path / "AGENTS.md").exists()
        code, result = _init(monkeypatch, capsys, "--agents")
        assert result["agents"]["added"] is False
        assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == text

    def test_agents_section_creates_agents_md_otherwise(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
        _write(tmp_path, {"VERSION": "1.0.0\n"})
        _init(monkeypatch, capsys, "--agents")
        assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8").startswith("## Releasing")

    def test_unknown_argument_is_a_usage_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        code, result = _init(monkeypatch, capsys, "--force")
        assert code == 2
