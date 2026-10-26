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


# --- subcommands, --json and exit codes ---

import json


def _cli(monkeypatch, capsys, *args):
    """Run bump2v with args; return (exit code, stdout, stderr)."""
    monkeypatch.setattr(sys, "argv", ["bump2v", *args])
    code = 0
    try:
        bump2v_main.main()
    except SystemExit as e:
        code = e.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _json(monkeypatch, capsys, *args):
    code, out, _ = _cli(monkeypatch, capsys, *args, "--json")
    return code, json.loads(out)


class TestPlan:
    def test_plan_json_describes_the_bump_and_writes_nothing(self, repo, monkeypatch, capsys):
        work, _ = repo
        code, result = _json(monkeypatch, capsys, "plan", "minor")
        assert code == 0
        assert result["ok"] and result["command"] == "plan" and result["format_version"] == "1.0"
        assert (result["current_version"], result["new_version"]) == ("1.0.0", "1.1.0")
        assert result["files"] == [{"path": "VERSION", "changed": True, "matches": 1}]
        assert result["tag"]["name"] == "v1.1.0"
        assert _git(work, "status", "--porcelain") == ""
        assert (work / "VERSION").read_text() == "1.0.0\n"

    def test_plan_on_dirty_tree_fails_like_release_would(self, repo, monkeypatch, capsys):
        work, _ = repo
        (work / "VERSION").write_text("1.0.0\nedited\n")
        code, result = _json(monkeypatch, capsys, "plan", "patch")
        assert code == 3
        assert not result["ok"] and result["error"]["code"] == "dirty_tree"

    def test_plan_auto_reports_the_commits(self, repo, monkeypatch, capsys):
        work, _ = repo
        _git(work, "tag", "v1.0.0", "HEAD~1")
        (work / "feature.txt").write_text("x\n")
        _git(work, "add", "feature.txt")
        _git(work, "commit", "-q", "-m", "feat: add a feature")
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 0
        assert result["auto"]["level"] == "minor" and result["auto"]["since"] == "v1.0.0"
        assert result["new_version"] == "1.1.0"

    def test_auto_with_nothing_since_the_tag_exits_7(self, repo, monkeypatch, capsys):
        work, _ = repo
        _git(work, "tag", "v1.0.0")
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 7 and result["error"]["code"] == "nothing_to_release"


class TestRelease:
    def test_release_no_push_commits_and_tags_locally(self, repo, monkeypatch, capsys):
        work, remote = repo
        remote_head = _git(remote, "rev-parse", "main")
        code, result = _json(monkeypatch, capsys, "release", "patch", "--no-push")
        assert code == 0 and result["command"] == "release"
        assert result["commit"]["sha"] == _git(work, "rev-parse", "HEAD")
        assert result["tag"] == {"enabled": True, "name": "v1.0.1", "created": True}
        assert result["push"] == {"enabled": False, "pushed": False}
        assert _git(remote, "rev-parse", "main") == remote_head

    def test_push_false_in_config_and_push_flag_override(self, repo, monkeypatch, capsys):
        work, remote = repo
        cfg = work / ".bumpversion.cfg"
        cfg.write_text(cfg.read_text().replace("tag = True\n", "tag = True\npush = False\n"))
        _git(work, "commit", "-q", "-am", "chore: no push")
        remote_head = _git(remote, "rev-parse", "main")
        code, result = _json(monkeypatch, capsys, "patch")
        assert code == 0 and not result["push"]["pushed"]
        assert _git(remote, "rev-parse", "main") == remote_head
        code, result = _json(monkeypatch, capsys, "patch", "--push")
        assert code == 0 and result["push"]["pushed"]
        assert _git(remote, "rev-parse", "main") == _git(work, "rev-parse", "HEAD")

    def test_existing_tag_fails_before_anything_is_written(self, repo, monkeypatch, capsys):
        work, _ = repo
        _git(work, "tag", "v1.0.1")
        head = _git(work, "rev-parse", "HEAD")
        code, result = _json(monkeypatch, capsys, "patch")
        assert code == 5 and result["error"]["code"] == "tag_exists"
        assert _git(work, "rev-parse", "HEAD") == head
        assert _git(work, "status", "--porcelain") == ""

    def test_detached_head_keeps_the_commit_and_exits_6(self, repo, monkeypatch, capsys):
        work, remote = repo
        _git(work, "checkout", "-q", "--detach")
        remote_head = _git(remote, "rev-parse", "main")
        code, result = _json(monkeypatch, capsys, "patch")
        assert code == 6 and result["error"]["code"] == "detached_head"
        assert _git(work, "log", "-1", "--format=%s").startswith("Bump version: 1.0.0")
        assert _git(remote, "rev-parse", "main") == remote_head

    def test_release_alone_still_bumps_a_part_named_release(self, repo, monkeypatch, capsys):
        work, _ = repo
        (work / "VERSION").write_text("1.0.0-dev\n")
        (work / ".bumpversion.cfg").write_text(
            "[bumpversion]\ncurrent_version = 1.0.0-dev\n"
            "parse = (?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(-(?P<release>\\w+))?\n"
            "serialize =\n\t{major}.{minor}.{patch}-{release}\n\t{major}.{minor}.{patch}\n\n"
            "[bumpversion:part:release]\noptional_value = final\nvalues =\n\tdev\n\tfinal\n\n"
            "[bumpversion:file:VERSION]\n"
        )
        _git(work, "commit", "-q", "-am", "chore: release part")
        code, result = _json(monkeypatch, capsys, "release", "--no-push", "--no-tag")
        assert code == 0 and result["command"] == "bump"
        assert result["new_version"] == "1.0.0"


class TestShowAndCheck:
    def test_show_prints_a_single_field(self, repo, monkeypatch, capsys):
        code, out, _ = _cli(monkeypatch, capsys, "show", "current_version")
        assert code == 0 and out == "1.0.0\n"
        code, out, _ = _cli(monkeypatch, capsys, "show", "next.minor")
        assert out == "1.1.0\n"

    def test_show_unknown_field_is_a_usage_error(self, repo, monkeypatch, capsys):
        code, _, err = _cli(monkeypatch, capsys, "show", "nope")
        assert code == 2 and "Unknown field" in err

    def test_check_passes_when_files_match(self, repo, monkeypatch, capsys):
        code, result = _json(monkeypatch, capsys, "check")
        assert code == 0 and result["files"][0]["found"]

    def test_check_reports_drift_with_exit_4(self, repo, monkeypatch, capsys):
        work, _ = repo
        (work / "VERSION").write_text("1.0.9\n")
        code, result = _json(monkeypatch, capsys, "check")
        assert code == 4 and result["error"]["code"] == "version_drift"
        assert result["files"] == [{"path": "VERSION", "found": False, "matches": 0, "ignored": False}]


class TestUsage:
    def test_no_arguments_prints_usage_and_exits_2(self, monkeypatch, capsys):
        code, _, err = _cli(monkeypatch, capsys)
        assert code == 2 and "usage: bump2v" in err

    def test_help_exits_0(self, monkeypatch, capsys):
        code, out, _ = _cli(monkeypatch, capsys, "--help")
        assert code == 0 and "exit codes" in out


# --- auto: which commits count as new ---

def _commit(work, name, message):
    (work / name).write_text(message + "\n")
    _git(work, "add", name)
    _git(work, "commit", "-q", "-m", message)


class TestAutoBoundary:
    def test_only_tags_that_tag_name_makes_count(self, repo, monkeypatch, capsys):
        work, _ = repo
        cfg = work / ".bumpversion.cfg"
        cfg.write_text(cfg.read_text().replace("tag = True\n", "tag = True\ntag_name = baseline-v{new_version}\n"))
        _git(work, "commit", "-q", "-am", "chore: baseline tags")
        _git(work, "tag", "baseline-v1.0.0")
        _commit(work, "a.txt", "feat: a feature")
        _git(work, "tag", "deploy-2026-10-26")  # someone else's tag, newer
        _commit(work, "b.txt", "fix: a fix")
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 0
        assert result["auto"]["since"] == "baseline-v1.0.0" and result["auto"]["level"] == "minor"

    def test_without_tags_the_last_version_commit_is_the_boundary(self, repo, monkeypatch, capsys):
        work, _ = repo
        cfg = work / ".bumpversion.cfg"
        cfg.write_text(cfg.read_text().replace("tag = True\n", "tag = False\n"))
        _git(work, "commit", "-q", "-am", "Bump version: 0.9.0 → 1.0.0")
        boundary = _git(work, "rev-parse", "HEAD")
        _commit(work, "a.txt", "feat: a feature")
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 0
        assert result["auto"]["since"] == boundary and result["auto"]["level"] == "minor"
        assert [c["subject"] for c in result["auto"]["commits"]] == ["feat: a feature"]

    def test_shallow_clone_without_the_last_release_fails(self, repo, tmp_path, monkeypatch, capsys):
        work, _ = repo
        _git(work, "tag", "v1.0.0", "HEAD~1")
        _commit(work, "a.txt", "feat: a feature")
        clone = tmp_path / "shallow"
        _git(tmp_path, "clone", "-q", "--depth", "1", "--no-tags", work.as_uri(), str(clone))
        monkeypatch.chdir(clone)
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 1 and result["error"]["code"] == "shallow_clone"
        assert "fetch-depth: 0" in result["error"]["hint"]


class TestCiIdentity:
    def test_commits_as_the_actions_bot_when_git_has_no_identity(self, repo, monkeypatch, capsys):
        work, _ = repo
        _git(work, "config", "--unset", "user.name")
        _git(work, "config", "--unset", "user.email")
        for key in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
            # setenv then delenv: monkeypatch records the key as absent, so whatever
            # bump2v sets with os.environ.setdefault is removed after the test.
            monkeypatch.setenv(key, "x")
            monkeypatch.delenv(key)
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        code, result = _json(monkeypatch, capsys, "patch", "--no-push")
        assert code == 0
        assert _git(work, "log", "-1", "--format=%an <%ae>") == \
            "github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"


class TestAtomicPush:
    def test_rejected_push_leaves_no_tag_on_the_remote(self, repo, tmp_path, monkeypatch, capsys):
        work, remote = repo
        other = tmp_path / "other"
        _git(tmp_path, "clone", "-q", str(remote), str(other))
        _git(other, "config", "user.name", "Other")
        _git(other, "config", "user.email", "other@example.com")
        _commit(other, "other.txt", "fix: pushed first by another run")
        _git(other, "push", "-q")
        code, result = _json(monkeypatch, capsys, "patch")
        assert code == 6 and result["error"]["code"] == "push_failed" and result["error"]["retryable"]
        assert _git(remote, "tag", "--list") == ""
        assert _git(work, "tag", "--list") == "v1.0.1"  # still there locally to push later

    def test_falls_back_when_the_remote_cannot_push_atomically(self, monkeypatch):
        calls = []

        class Result:
            def __init__(self, returncode, stderr=""):
                self.returncode, self.stderr = returncode, stderr

        def run(cmd, **kwargs):
            calls.append(cmd)
            if "--atomic" in cmd:
                return Result(128, "fatal: the receiving end does not support --atomic push\n")
            return Result(0)

        monkeypatch.setattr(bump2v_main.subprocess, "run", run)
        assert bump2v_main._push_branch_and_tags()
        assert calls == [["git", "push", "--atomic", "--follow-tags"], ["git", "push"],
                         ["git", "push", "--follow-tags"]]
