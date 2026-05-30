import pytest
from bump2v.bumpversion.version_part import VersionConfig, VersionPart, Version


@pytest.fixture
def semver_config():
    return VersionConfig(
        parse=r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        serialize=["{major}.{minor}.{patch}"],
        search="{current_version}",
        replace="{new_version}",
    )


class TestVersionConfig:
    def test_parse_standard_semver(self, semver_config):
        v = semver_config.parse("1.2.3")
        assert v["major"].value == "1"
        assert v["minor"].value == "2"
        assert v["patch"].value == "3"

    def test_parse_returns_none_for_no_match(self, semver_config):
        assert semver_config.parse("not-a-version") is None

    def test_serialize(self, semver_config):
        v = semver_config.parse("1.2.3")
        assert semver_config.serialize(v, {}) == "1.2.3"


class TestVersionBump:
    def test_bump_patch(self, semver_config):
        v = semver_config.parse("1.2.3")
        bumped = v.bump("patch", semver_config.order())
        assert semver_config.serialize(bumped, {}) == "1.2.4"

    def test_bump_minor_resets_patch(self, semver_config):
        v = semver_config.parse("1.2.3")
        bumped = v.bump("minor", semver_config.order())
        assert semver_config.serialize(bumped, {}) == "1.3.0"

    def test_bump_major_resets_minor_and_patch(self, semver_config):
        v = semver_config.parse("1.2.3")
        bumped = v.bump("major", semver_config.order())
        assert semver_config.serialize(bumped, {}) == "2.0.0"

    def test_bump_patch_from_zero(self, semver_config):
        v = semver_config.parse("0.0.0")
        bumped = v.bump("patch", semver_config.order())
        assert semver_config.serialize(bumped, {}) == "0.0.1"

    def test_bump_major_large_version(self, semver_config):
        v = semver_config.parse("9.9.9")
        bumped = v.bump("major", semver_config.order())
        assert semver_config.serialize(bumped, {}) == "10.0.0"


class TestVersionPart:
    def test_value(self):
        vp = VersionPart("3")
        assert vp.value == "3"

    def test_bump(self):
        vp = VersionPart("3")
        assert vp.bump().value == "4"

    def test_null_resets_to_first_value(self):
        vp = VersionPart("5")
        assert vp.null().value == "0"

    def test_equality(self):
        assert VersionPart("1") == VersionPart("1")
        assert VersionPart("1") != VersionPart("2")
