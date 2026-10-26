from argparse import _AppendAction
from difflib import unified_diff
import io
import logging
import os
import re

from .exceptions import VersionNotFoundException

logger = logging.getLogger(__name__)


class DiscardDefaultIfSpecifiedAppendAction(_AppendAction):

    """
    Fixes bug http://bugs.python.org/issue16399 for 'append' action
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(self, "_discarded_default", None) is None:
            setattr(namespace, self.dest, [])
            self._discarded_default = True  # pylint: disable=attribute-defined-outside-init

        super().__call__(
            parser, namespace, values, option_string=None
        )


def keyvaluestring(d):
    return ", ".join("{}={}".format(k, v) for k, v in sorted(d.items()))


def prefixed_environ():
    return {"${}".format(key): value for key, value in os.environ.items()}


UTF8_BOM = b"\xef\xbb\xbf"
_NEWLINE = re.compile(r"\r\n|\r|\n")


def read_text_raw(path):
    """Read a UTF-8 file without newline translation.

    Returns (text, had_bom). Line endings are kept exactly as they are on disk, so
    a replacement can be spliced in without touching any other line.
    """
    with open(path, "rb") as f:
        data = f.read()
    had_bom = data.startswith(UTF8_BOM)
    if had_bom:
        data = data[len(UTF8_BOM):]
    return data.decode("utf-8"), had_bom


def write_text_raw(path, text, had_bom=False):
    """Write text exactly as given (no newline translation), restoring a BOM if there was one."""
    with open(path, "wb") as f:
        f.write((UTF8_BOM if had_bom else b"") + text.encode("utf-8"))


def _search_regex(search):
    """Match `search` literally, letting each newline in it match \\n, \\r\\n or \\r."""
    return re.compile(r"(?:\r\n|\r|\n)".join(re.escape(part) for part in search.split("\n")))


class FileChange:
    """The new content for one file, computed before anything is written."""

    def __init__(self, path, before, after, had_bom=False, matches=0):
        self.path = path
        self.before = before
        self.after = after
        self.had_bom = had_bom
        self.matches = matches

    @property
    def changed(self):
        return self.before != self.after

    def log(self, dry_run):
        if self.changed:
            logger.info("%s file %s:", "Would change" if dry_run else "Changing", self.path)
            logger.info(
                "\n".join(
                    unified_diff(
                        self.before.splitlines(),
                        self.after.splitlines(),
                        lineterm="",
                        fromfile="a/" + self.path,
                        tofile="b/" + self.path,
                    )
                )
            )
        else:
            logger.info("%s file %s", "Would not change" if dry_run else "Not changing", self.path)

    def write(self):
        write_text_raw(self.path, self.after, self.had_bom)

    def restore(self):
        write_text_raw(self.path, self.before, self.had_bom)


def write_changes(changes, dry_run):
    """Log every change, then write them all unless this is a dry run."""
    for change in changes:
        change.log(dry_run)
    if not dry_run:
        write_all(changes)


def write_all(changes):
    """Write every changed file. If a write fails, put back what was already written."""
    written = []
    try:
        for change in changes:
            if change.changed:
                change.write()
                written.append(change)
    except Exception:
        for change in written:
            try:
                change.restore()
            except OSError:
                logger.error("Could not restore %s after a failed write", change.path)
        raise


class ConfiguredFile:

    def __init__(self, path, versionconfig, replace_all=True):
        self.path = path
        self._versionconfig = versionconfig
        # bump2version replaces every match of `search`. Kept as the 1.x default;
        # replace_all = False bumps only the first match.
        self.replace_all = replace_all

    def should_contain_version(self, version, context):
        """
        Raise VersionNotFound if the version number isn't present in this file.

        Return normally if the version number is in fact present.
        """
        context["current_version"] = self._versionconfig.serialize(version, context)
        search_expression = self._versionconfig.search.format(**context)

        if self.contains(search_expression):
            return

        # the `search` pattern did not match, but the original supplied
        # version number (representing the same version part values) might
        # match instead.

        # check whether `search` isn't customized, i.e. should match only
        # very specific parts of the file
        search_pattern_is_default = self._versionconfig.search == "{current_version}"

        if search_pattern_is_default and self.contains(version.original):
            # original version is present and we're not looking for something
            # more specific -> this is accepted as a match
            return

        # version not found
        raise VersionNotFoundException(
            "Did not find '{}' in file: '{}'".format(
                search_expression, self.path
            )
        )

    def contains(self, search):
        if not search:
            return False

        text, _ = read_text_raw(self.path)
        search_lines = search.splitlines()
        lookbehind = []

        for lineno, line in enumerate(_NEWLINE.sub("\n", text).splitlines()):
            lookbehind.append(line)

            if len(lookbehind) > len(search_lines):
                lookbehind = lookbehind[1:]

            if (
                search_lines[0] in lookbehind[0]
                and search_lines[-1] in lookbehind[-1]
                and search_lines[1:-1] == lookbehind[1:-1]
            ):
                logger.info(
                    "Found '%s' in %s at line %s: %s",
                    search,
                    self.path,
                    lineno - (len(lookbehind) - 1),
                    line.rstrip(),
                )
                return True
        return False

    def compute_replacement(self, current_version, new_version, context, previous=None):
        """Work out this file's new content. Writes nothing; returns a FileChange.

        `previous` is an earlier FileChange for the same file (the file is listed
        twice with different searches); this edit then builds on its result.
        """
        if previous is not None:
            before, had_bom = previous.after, previous.had_bom
        else:
            before, had_bom = read_text_raw(self.path)

        context["current_version"] = self._versionconfig.serialize(
            current_version, context
        )
        context["new_version"] = self._versionconfig.serialize(new_version, context)

        search_for = self._versionconfig.search.format(**context)
        replace_with = self._versionconfig.replace.format(**context)

        after, matches = self._substitute(before, search_for, replace_with)

        # Fall back to the version exactly as written (e.g. "1.0" when it serializes
        # as "1.0.0"), but only when `search` is the bare default. A custom search
        # that doesn't match must never turn into "replace this number anywhere".
        if matches == 0 and self._versionconfig.search == "{current_version}":
            after, matches = self._substitute(before, current_version.original, replace_with)

        return FileChange(self.path, before, after, had_bom, matches)

    def _substitute(self, text, search_for, replace_with):
        if not search_for:
            return text, 0

        def replacement(match):
            newline = _NEWLINE.search(match.group(0))
            return replace_with.replace("\n", newline.group(0)) if newline else replace_with

        return _search_regex(search_for).subn(
            replacement, text, count=0 if self.replace_all else 1
        )

    def count_matches(self, search):
        """How many times `search` occurs in the file (line endings ignored)."""
        text, _ = read_text_raw(self.path)
        return len(_search_regex(search).findall(text)) if search else 0

    def replace(self, current_version, new_version, context, dry_run):
        change = self.compute_replacement(current_version, new_version, context)
        write_changes([change], dry_run)

    def __str__(self):
        return self.path

    def __repr__(self):
        return "<bumpversion.ConfiguredFile:{}>".format(self.path)
