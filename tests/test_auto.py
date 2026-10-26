import pytest
from bump2v.__main__ import _classify_commits


class TestClassifyCommits:
    # --- level detection ---

    def test_feat_gives_minor(self):
        level, _, _ = _classify_commits(["feat: add new API"])
        assert level == "minor"

    def test_fix_gives_patch(self):
        level, _, _ = _classify_commits(["fix: correct null dereference"])
        assert level == "patch"

    def test_perf_gives_patch(self):
        level, _, _ = _classify_commits(["perf: optimise query"])
        assert level == "patch"

    def test_chore_gives_patch(self):
        level, _, _ = _classify_commits(["chore: update deps"])
        assert level == "patch"

    def test_breaking_bang_gives_major(self):
        level, _, _ = _classify_commits(["feat!: redesign auth API"])
        assert level == "major"

    def test_fix_breaking_bang_gives_major(self):
        level, _, _ = _classify_commits(["fix!: remove deprecated endpoint"])
        assert level == "major"

    def test_breaking_footer_gives_major(self):
        msg = "feat: redesign login\n\nBREAKING CHANGE: removes /v1/login endpoint"
        level, _, _ = _classify_commits([msg])
        assert level == "major"

    def test_breaking_hyphen_footer_gives_major(self):
        msg = "fix: overhaul config\n\nBREAKING-CHANGE: config file format changed"
        level, _, _ = _classify_commits([msg])
        assert level == "major"

    # --- precedence (highest wins) ---

    def test_major_beats_minor(self):
        level, _, _ = _classify_commits(["feat: new endpoint", "feat!: drop old API"])
        assert level == "major"

    def test_major_beats_patch(self):
        level, _, _ = _classify_commits(["fix: null pointer", "feat!: redesign"])
        assert level == "major"

    def test_minor_beats_patch(self):
        level, _, _ = _classify_commits(["feat: new endpoint", "fix: null pointer"])
        assert level == "minor"

    def test_order_does_not_matter_major(self):
        # major first
        a, _, _ = _classify_commits(["feat!: break", "feat: add", "fix: bug"])
        # major last
        b, _, _ = _classify_commits(["feat: add", "fix: bug", "feat!: break"])
        assert a == b == "major"

    # --- scoped commits ---

    def test_scoped_feat(self):
        level, _, _ = _classify_commits(["feat(auth): add OAuth support"])
        assert level == "minor"

    def test_scoped_breaking_bang(self):
        level, _, _ = _classify_commits(["fix(api)!: remove deprecated endpoint"])
        assert level == "major"

    def test_scoped_fix(self):
        level, _, _ = _classify_commits(["fix(db): handle connection timeout"])
        assert level == "patch"

    # --- non-conventional commits ---

    def test_non_conventional_defaults_to_patch(self):
        level, _, found = _classify_commits(["Updated readme", "WIP stuff"])
        assert level == "patch"
        assert not found

    def test_non_conventional_rows_have_none_level(self):
        _, rows, _ = _classify_commits(["Updated readme"])
        assert rows[0][1] is None

    def test_mixed_conventional_and_non_conventional(self):
        level, rows, found = _classify_commits(["feat: new thing", "WIP some stuff"])
        assert level == "minor"
        assert found
        non_cc = [r for r in rows if r[0] == "WIP some stuff"]
        assert non_cc[0][1] is None

    # --- empty / edge cases ---

    def test_empty_list_gives_patch(self):
        level, rows, found = _classify_commits([])
        assert level == "patch"
        assert rows == []
        assert not found

    def test_blank_strings_are_ignored(self):
        level, rows, _ = _classify_commits(["", "   ", "\n"])
        assert level == "patch"
        assert rows == []

    def test_single_patch_commit(self):
        level, rows, found = _classify_commits(["fix: one small thing"])
        assert level == "patch"
        assert len(rows) == 1
        assert rows[0] == ("fix: one small thing", "patch")
        assert found

    # --- rows content ---

    def test_rows_first_line_only(self):
        msg = "feat: add thing\n\nLonger description that should not appear in rows."
        _, rows, _ = _classify_commits([msg])
        assert rows[0][0] == "feat: add thing"

    def test_breaking_footer_row_shows_first_line(self):
        msg = "feat: redesign\n\nBREAKING CHANGE: changes everything"
        _, rows, _ = _classify_commits([msg])
        assert rows[0][0] == "feat: redesign"
        assert rows[0][1] == "major"

    # --- found_conventional flag ---

    def test_found_conventional_true_when_cc_present(self):
        _, _, found = _classify_commits(["fix: something"])
        assert found

    def test_found_conventional_false_when_no_cc(self):
        _, _, found = _classify_commits(["random commit message"])
        assert not found


# --- push behaviour: only push what this run created ---

import subprocess
import sys

from bump2v import __main__ as bump2v_main


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repo at 1.0.0 with a pushed first commit and one unpushed local commit."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    _git(tmp_path, "init", "-q", "-b", "main", str(work))
    _git(work, "config", "user.name", "Test")
    _git(work, "config", "user.email", "test@example.com")
    (work / "VERSION").write_text("1.0.0\n")
    (work / ".bumpversion.cfg").write_text(
        "[bumpversion]\ncurrent_version = 1.0.0\ncommit = True\ntag = True\n\n"
        "[bumpversion:file:VERSION]\n"
    )
    _git(work, "add", ".")
    _git(work, "commit", "-q", "-m", "initial")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-q", "-u", "origin", "main")
    (work / "notes.txt").write_text("local work\n")
    _git(work, "add", "notes.txt")
    _git(work, "commit", "-q", "-m", "local, not pushed")
    monkeypatch.chdir(work)
    return work, remote


def _run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["bump2v", *args])
    bump2v_main.main()


class TestPush:
    def test_dry_run_pushes_nothing(self, repo, monkeypatch):
        work, remote = repo
        remote_head = _git(remote, "rev-parse", "main")
        _run(monkeypatch, "patch", "--dry-run")
        assert _git(remote, "rev-parse", "main") == remote_head
        assert (work / "VERSION").read_text() == "1.0.0\n"

    def test_no_commit_pushes_nothing(self, repo, monkeypatch):
        work, remote = repo
        remote_head = _git(remote, "rev-parse", "main")
        _run(monkeypatch, "patch", "--no-commit", "--no-tag")
        assert _git(remote, "rev-parse", "main") == remote_head
        assert (work / "VERSION").read_text() == "1.0.1\n"

    def test_bump_pushes_commit_and_tag(self, repo, monkeypatch):
        work, remote = repo
        _run(monkeypatch, "patch")
        assert _git(remote, "rev-parse", "main") == _git(work, "rev-parse", "HEAD")
        assert _git(remote, "tag", "--list") == "v1.0.1"
