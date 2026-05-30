import subprocess
import pytest
from bump2v.bumpversion.vcs import Git
from bump2v.bumpversion.exceptions import WorkingDirectoryIsDirtyException


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with one commit."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


class TestAssertNondirty:
    def test_clean_repo_does_not_raise(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        Git.assert_nondirty()

    def test_modified_file_raises(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        (git_repo / "README.md").write_text("changed")
        with pytest.raises(WorkingDirectoryIsDirtyException):
            Git.assert_nondirty()

    def test_staged_file_raises(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        (git_repo / "new.txt").write_text("new file")
        subprocess.run(["git", "add", "new.txt"], cwd=git_repo, check=True, capture_output=True)
        with pytest.raises(WorkingDirectoryIsDirtyException):
            Git.assert_nondirty()

    def test_untracked_file_does_not_raise(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        (git_repo / "untracked.txt").write_text("untracked")
        # Untracked files are always ignored by assert_nondirty
        Git.assert_nondirty()

    def test_allowed_path_exempts_modified_file(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        (git_repo / "README.md").write_text("changed")
        # README.md is dirty but allowed — should not raise
        Git.assert_nondirty(allowed_paths=["README.md"])

    def test_allowed_path_still_raises_for_other_dirty_files(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        (git_repo / "README.md").write_text("changed")
        (git_repo / "other.txt").write_text("other")
        subprocess.run(["git", "add", "other.txt"], cwd=git_repo, check=True, capture_output=True)
        # README.md is allowed but other.txt (staged) is not
        with pytest.raises(WorkingDirectoryIsDirtyException):
            Git.assert_nondirty(allowed_paths=["README.md"])

    def test_multiple_allowed_paths(self, git_repo, monkeypatch):
        monkeypatch.chdir(git_repo)
        (git_repo / "README.md").write_text("changed")
        (git_repo / "CHANGELOG.md").write_text("new changelog")
        subprocess.run(["git", "add", "CHANGELOG.md"], cwd=git_repo, check=True, capture_output=True)
        # Both dirty files are allowed
        Git.assert_nondirty(allowed_paths=["README.md", "CHANGELOG.md"])
