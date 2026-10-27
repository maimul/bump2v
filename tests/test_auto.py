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

    # --- merge commits: the PR title in the body decides ---

    def test_merge_commit_uses_the_pr_title(self):
        msg = "Merge pull request #12 from org/add-exports\n\nfeat: add CSV exports"
        level, rows, found = _classify_commits([msg])
        assert level == "minor" and rows == [("feat: add CSV exports", "minor")] and found

    def test_merge_commit_with_breaking_pr_title(self):
        msg = "Merge pull request #13 from org/v2-api\n\nfeat(api)!: drop v1 endpoints"
        level, _, _ = _classify_commits([msg])
        assert level == "major"

    def test_merge_branch_without_body_stays_unclassified(self):
        level, rows, found = _classify_commits(["Merge branch 'staging' into development"])
        assert level == "patch" and rows == [("Merge branch 'staging' into development", None)]
        assert not found

    def test_prose_in_a_pr_title_is_not_a_level(self):
        msg = "Merge pull request #24 from org/lockfile\n\nUpdate the lockfile so the major CI runs"
        level, _, found = _classify_commits([msg])
        assert level == "patch" and not found

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
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
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
    (work / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (work / ".bumpversion.cfg").write_text(
        "[bumpversion]\ncurrent_version = 1.0.0\ncommit = True\ntag = True\n\n"
        "[bumpversion:file:VERSION]\n",
        encoding="utf-8",
    )
    _git(work, "add", ".")
    _git(work, "commit", "-q", "-m", "initial")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-q", "-u", "origin", "main")
    (work / "notes.txt").write_text("local work\n", encoding="utf-8")
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
        assert (work / "VERSION").read_text(encoding="utf-8") == "1.0.0\n"

    def test_no_commit_pushes_nothing(self, repo, monkeypatch):
        work, remote = repo
        remote_head = _git(remote, "rev-parse", "main")
        _run(monkeypatch, "patch", "--no-commit", "--no-tag")
        assert _git(remote, "rev-parse", "main") == remote_head
        assert (work / "VERSION").read_text(encoding="utf-8") == "1.0.1\n"

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
        assert result["ok"] and result["command"] == "plan" and result["format_version"] == "1.1"
        assert (result["current_version"], result["new_version"]) == ("1.0.0", "1.1.0")
        assert result["files"] == [{"path": "VERSION", "changed": True, "matches": 1}]
        assert result["tag"]["name"] == "v1.1.0"
        assert _git(work, "status", "--porcelain") == ""
        assert (work / "VERSION").read_text(encoding="utf-8") == "1.0.0\n"

    def test_plan_on_dirty_tree_fails_like_release_would(self, repo, monkeypatch, capsys):
        work, _ = repo
        (work / "VERSION").write_text("1.0.0\nedited\n", encoding="utf-8")
        code, result = _json(monkeypatch, capsys, "plan", "patch")
        assert code == 3
        assert not result["ok"] and result["error"]["code"] == "dirty_tree"

    def test_plan_auto_reports_the_commits(self, repo, monkeypatch, capsys):
        work, _ = repo
        _git(work, "tag", "v1.0.0", "HEAD~1")
        (work / "feature.txt").write_text("x\n", encoding="utf-8")
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
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("tag = True\n", "tag = True\npush = False\n"), encoding="utf-8")
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
        (work / "VERSION").write_text("1.0.0-dev\n", encoding="utf-8")
        (work / ".bumpversion.cfg").write_text(
            "[bumpversion]\ncurrent_version = 1.0.0-dev\n"
            "parse = (?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(-(?P<release>\\w+))?\n"
            "serialize =\n\t{major}.{minor}.{patch}-{release}\n\t{major}.{minor}.{patch}\n\n"
            "[bumpversion:part:release]\noptional_value = final\nvalues =\n\tdev\n\tfinal\n\n"
            "[bumpversion:file:VERSION]\n",
            encoding="utf-8",
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
        (work / "VERSION").write_text("1.0.9\n", encoding="utf-8")
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
    (work / name).write_text(message + "\n", encoding="utf-8")
    _git(work, "add", name)
    _git(work, "commit", "-q", "-m", message)


class TestAutoBoundary:
    def test_only_tags_that_tag_name_makes_count(self, repo, monkeypatch, capsys):
        work, _ = repo
        cfg = work / ".bumpversion.cfg"
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("tag = True\n", "tag = True\ntag_name = baseline-v{new_version}\n"), encoding="utf-8")
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
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("tag = True\n", "tag = False\n"), encoding="utf-8")
        _git(work, "commit", "-q", "-am", "Bump version: 0.9.0 → 1.0.0")
        boundary = _git(work, "rev-parse", "HEAD")
        _commit(work, "a.txt", "feat: a feature")
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 0
        assert result["auto"]["since"] == boundary and result["auto"]["level"] == "minor"
        assert [c["subject"] for c in result["auto"]["commits"]] == ["feat: a feature"]

    def test_with_tagging_off_old_matching_tags_are_ignored(self, repo, monkeypatch, capsys):
        work, _ = repo
        _git(work, "tag", "v0.1.0", "HEAD~1")   # from before tagging was turned off
        cfg = work / ".bumpversion.cfg"
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("tag = True\n", "tag = False\n"), encoding="utf-8")
        _git(work, "commit", "-q", "-am", "chore: stop tagging releases")
        _commit(work, "old.txt", "feat!: an old breaking change, long released")
        _git(work, "commit", "-q", "--allow-empty", "-m", "Bump version: 0.9.0 → 1.0.0")
        boundary = _git(work, "rev-parse", "HEAD")
        _commit(work, "new.txt", "fix: the only new change")
        code, result = _json(monkeypatch, capsys, "plan", "auto")
        assert code == 0
        assert result["auto"]["since"] == boundary
        assert result["auto"]["level"] == "patch" and result["new_version"] == "1.0.1"

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
        assert code == 6 and result["error"]["code"] == "push_rejected" and result["error"]["retryable"]
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
        assert bump2v_main._push_branch_and_tags() == (True, False)
        assert calls == [["git", "push", "--atomic", "--follow-tags"], ["git", "push"],
                         ["git", "push", "--follow-tags"]]


# --- CI: --sync, --retry, --github-output ---

def _push_from_other_clone(tmp_path, remote, message, name="other"):
    other = tmp_path / name
    if not other.exists():
        _git(tmp_path, "clone", "-q", str(remote), str(other))
        _git(other, "config", "user.name", "Other")
        _git(other, "config", "user.email", "other@example.com")
    else:
        _git(other, "pull", "-q")
    count = len(list(other.glob("other-*.txt")))
    _commit(other, f"other-{count}.txt", message)
    _git(other, "push", "-q")
    return other


@pytest.fixture
def ci_repo(repo, monkeypatch):
    """The repo fixture as CI sees it: nothing unpushed, checked out at the pushed commit."""
    work, remote = repo
    _git(work, "push", "-q")
    return work, remote


class TestSync:
    def test_sync_bumps_from_the_remote_tip(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, remote = ci_repo
        _push_from_other_clone(tmp_path, remote, "fix: landed while this run was queued")
        code, result = _json(monkeypatch, capsys, "release", "patch", "--sync")
        assert code == 0 and result["push"]["pushed"]
        assert _git(remote, "log", "-1", "--format=%s", "main").startswith("Bump version: 1.0.0")
        assert "fix: landed while this run was queued" in _git(remote, "log", "--format=%s", "main")

    def test_sync_stops_when_the_tip_is_already_a_version_commit(self, ci_repo, monkeypatch, capsys):
        work, remote = ci_repo
        code, _ = _json(monkeypatch, capsys, "release", "patch", "--sync")
        assert code == 0
        _git(work, "reset", "-q", "--hard", "HEAD~1")   # a stale checkout of the same branch
        _git(work, "tag", "-d", "v1.0.1")
        code, result = _json(monkeypatch, capsys, "release", "patch", "--sync")
        assert code == 7 and result["error"]["code"] == "already_released"
        assert _git(remote, "tag", "--list") == "v1.0.1"

    def test_sync_works_before_the_upstream_was_fetched(self, ci_repo, tmp_path, monkeypatch, capsys):
        # A CI checkout can have branch.main.remote/merge set but no refs/remotes/origin/main yet.
        work, remote = ci_repo
        _push_from_other_clone(tmp_path, remote, "fix: landed while this run was queued")
        _git(work, "update-ref", "-d", "refs/remotes/origin/main")
        code, result = _json(monkeypatch, capsys, "release", "patch", "--sync")
        assert code == 0 and result["push"]["pushed"]
        assert "fix: landed while this run was queued" in _git(remote, "log", "--format=%s", "main")

    def test_sync_refuses_a_diverged_branch(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, remote = ci_repo
        _push_from_other_clone(tmp_path, remote, "fix: remote work")
        _commit(work, "local.txt", "fix: local work")
        code, result = _json(monkeypatch, capsys, "release", "patch", "--sync")
        assert code == 1 and result["error"]["code"] == "diverged"
        assert _git(work, "log", "-1", "--format=%s") == "fix: local work"


class TestRetry:
    def test_lost_race_is_retried_from_the_new_tip(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, remote = ci_repo
        real_push = bump2v_main._push_branch_and_tags
        calls = []

        def push_after_someone_else():
            calls.append(1)
            if len(calls) == 1:   # another run lands between our bump and our push
                _push_from_other_clone(tmp_path, remote, "fix: the other run")
            return real_push()

        monkeypatch.setattr(bump2v_main, "_push_branch_and_tags", push_after_someone_else)
        monkeypatch.setattr(bump2v_main.time, "sleep", lambda seconds: None)
        code, result = _json(monkeypatch, capsys, "release", "patch", "--retry", "2")
        assert code == 0 and result["attempts"] == 2 and result["push"]["pushed"]
        log = _git(remote, "log", "--format=%s", "main").splitlines()
        assert log[0].startswith("Bump version: 1.0.0") and log[1] == "fix: the other run"
        assert _git(remote, "tag", "--list") == "v1.0.1"

    def test_retry_gives_up_after_n_attempts(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, remote = ci_repo
        real_push = bump2v_main._push_branch_and_tags

        def always_beaten():
            _push_from_other_clone(tmp_path, remote, "fix: yet another run")
            return real_push()

        monkeypatch.setattr(bump2v_main, "_push_branch_and_tags", always_beaten)
        monkeypatch.setattr(bump2v_main.time, "sleep", lambda seconds: None)
        code, result = _json(monkeypatch, capsys, "release", "patch", "--retry=1")
        assert code == 6 and result["error"]["code"] == "push_rejected"
        assert _git(remote, "tag", "--list") == ""

    def test_retry_needs_a_number(self, ci_repo, monkeypatch, capsys):
        code, result = _json(monkeypatch, capsys, "release", "patch", "--retry", "lots")
        assert code == 2 and result["error"]["code"] == "usage"


class TestGithubOutput:
    def test_outputs_after_a_release(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, _ = ci_repo
        out_file = tmp_path / "github_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
        code, _ = _json(monkeypatch, capsys, "release", "patch", "--github-output")
        assert code == 0
        outputs = dict(line.split("=", 1) for line in out_file.read_text(encoding="utf-8").splitlines())
        assert outputs == {"version": "1.0.1", "previous_version": "1.0.0", "tag": "v1.0.1",
                           "sha": _git(work, "rev-parse", "HEAD"), "bumped": "true", "pushed": "true"}

    def test_outputs_when_there_is_nothing_to_release(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, _ = ci_repo
        _json(monkeypatch, capsys, "release", "patch")
        out_file = tmp_path / "github_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
        code, _ = _json(monkeypatch, capsys, "release", "patch", "--sync", "--github-output")
        assert code == 7
        outputs = dict(line.split("=", 1) for line in out_file.read_text(encoding="utf-8").splitlines())
        assert outputs["version"] == "1.0.1" and outputs["bumped"] == "false"


class TestSkipCiGuardOutputs:
    def test_outputs_are_written_when_head_is_a_skip_ci_version_commit(self, ci_repo, tmp_path, monkeypatch, capsys):
        work, _ = ci_repo
        cfg = work / ".bumpversion.cfg"
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("tag = True\n", "tag = True\nmessage = Version Updated: {current_version} → {new_version} [skip ci]\n"), encoding="utf-8")
        _git(work, "commit", "-q", "-am", "chore: skip ci in version commits")
        _json(monkeypatch, capsys, "release", "patch")
        out_file = tmp_path / "github_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
        code, result = _json(monkeypatch, capsys, "release", "patch", "--github-output")
        assert code == 7 and result["error"]["code"] == "nothing_to_release"
        outputs = dict(line.split("=", 1) for line in out_file.read_text(encoding="utf-8").splitlines())
        assert outputs["version"] == "1.0.1" and outputs["bumped"] == "false"


def test_show_fails_loudly_without_a_version(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUMP2V_CONFIG", raising=False)
    code, _, err = _cli(monkeypatch, capsys, "show", "current_version")
    assert code == 4 and "current_version is not set" in err
