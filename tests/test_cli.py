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
        f.write_text("no version here")
        cf = ConfiguredFile(str(f), semver_config)
        version = semver_config.parse("1.0.0")

        with pytest.raises(VersionNotFoundException):
            _check_files_contain_version([cf], version, context)

    def test_ignore_missing_does_not_raise(self, tmp_path, semver_config, context):
        f = tmp_path / "test.txt"
        f.write_text("no version here")
        cf = ConfiguredFile(str(f), semver_config)
        version = semver_config.parse("1.0.0")

        # Must not raise with ignore_missing=True
        _check_files_contain_version([cf], version, context, ignore_missing=True)

    def test_passes_when_version_present(self, tmp_path, semver_config, context):
        f = tmp_path / "test.txt"
        f.write_text("current version is 1.0.0 here")
        cf = ConfiguredFile(str(f), semver_config)
        version = semver_config.parse("1.0.0")

        # Must not raise
        _check_files_contain_version([cf], version, context)

    def test_ignore_missing_still_passes_found_files(self, tmp_path, semver_config, context):
        found = tmp_path / "found.txt"
        found.write_text("version is 1.0.0")
        missing = tmp_path / "missing.txt"
        missing.write_text("no version here")

        cf_found = ConfiguredFile(str(found), semver_config)
        cf_missing = ConfiguredFile(str(missing), semver_config)
        version = semver_config.parse("1.0.0")

        # Mixed: one found, one missing — should not raise with ignore_missing=True
        _check_files_contain_version([cf_found, cf_missing], version, context, ignore_missing=True)

    def test_empty_file_list_is_noop(self, semver_config, context):
        version = semver_config.parse("1.0.0")
        _check_files_contain_version([], version, context)
