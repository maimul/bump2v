#!/usr/bin/env python3
import io
import logging
import os
import re
import subprocess
import sys

from bump2v.bumpversion.cli import main as _bumpversion_main

holdup = "Hold up!! 👮🚨"
thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"

# Conventional Commits: type(scope)!: or type!: or type(scope): or type:
_CC_HEADER = re.compile(r'^(?P<type>[a-z]+)(?:\([^)]+\))?(?P<breaking>!)?\s*:')
_CC_BREAKING_FOOTER = re.compile(r'^BREAKING[ -]CHANGE\s*:', re.MULTILINE)
_MINOR_TYPES = frozenset({"feat"})


def _classify_commits(messages):
    """
    Pure function. Classify a list of full commit message strings by
    Conventional Commits spec.

    Returns (level, rows, found_conventional) where:
      level             -- 'major' | 'minor' | 'patch'
      rows              -- list of (first_line, detected_level_or_None)
      found_conventional -- True if at least one CC commit was found
    """
    level = "patch"
    rows = []
    found_conventional = False

    for msg in messages:
        msg = msg.strip()
        if not msg:
            continue
        first_line = msg.splitlines()[0].strip()

        # BREAKING CHANGE: in footer takes priority over header analysis
        if _CC_BREAKING_FOOTER.search(msg):
            found_conventional = True
            level = "major"
            rows.append((first_line, "major"))
            continue

        m = _CC_HEADER.match(first_line)
        if not m:
            rows.append((first_line, None))
            continue

        found_conventional = True
        is_breaking = m.group("breaking") == "!"
        commit_type = m.group("type")

        if is_breaking:
            detected = "major"
        elif commit_type in _MINOR_TYPES:
            detected = "minor"
        else:
            detected = "patch"

        rows.append((first_line, detected))

        if detected == "major":
            level = "major"
        elif detected == "minor" and level != "major":
            level = "minor"

    return level, rows, found_conventional


def _detect_bump_level():
    """
    Analyze git commits since the last tag using Conventional Commits and
    return the appropriate bump level: 'major', 'minor', or 'patch'.
    """
    try:
        last_tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except subprocess.CalledProcessError:
        print("No tags found -- defaulting to patch.")
        return "patch"

    try:
        raw = subprocess.check_output(
            ["git", "log", f"{last_tag}..HEAD", "--format=%B%x00"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        print(f"Could not read commits since {last_tag} -- defaulting to patch.")
        return "patch"

    messages = [m.strip() for m in raw.split("\x00") if m.strip()]

    if not messages:
        print(f"No commits since {last_tag}. Nothing to bump.")
        sys.exit(1)

    level, rows, found_conventional = _classify_commits(messages)

    _LEVEL_LABEL = {"major": "MAJOR", "minor": "minor", "patch": "patch", None: "-"}

    print(f"Analyzing commits since {last_tag}...\n")
    for summary, detected in rows:
        short = (summary[:62] + "...") if len(summary) > 65 else summary
        print(f"  {short:<65}  {_LEVEL_LABEL[detected]}")

    if not found_conventional:
        print("\nNo conventional commits found -- defaulting to patch.")

    print(f"\nAuto-detected: {level}")
    return level


def _get_new_version(args):
    """Run a dry-run and capture the new_version from bumpversion's list output."""
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    log = logging.getLogger("bumpversion.list")
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    try:
        _bumpversion_main(["--dry-run", "--list", "--config-file", ".bumpversion.cfg"] + args)
    except (SystemExit, Exception):
        pass
    finally:
        log.removeHandler(handler)
    for line in buf.getvalue().splitlines():
        if line.startswith("new_version="):
            return line.split("=", 1)[1].strip()
    return None


def main():
    args = sys.argv[1:]
    if args and args[0].lower() == "bump":
        args = args[1:]

    if args and args[0].lower() == "auto":
        args[0] = _detect_bump_level()
        print()

    latest_commit_message = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True, check=True
    ).stdout.strip()

    prefix_to_check = "Version Updated:"
    prefix_to_check2 = "Bump version:"

    porcelain = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout
    tracked_dirty = [l for l in porcelain.splitlines() if not l.startswith("??")]
    if tracked_dirty:
        print(f"{holdup} Working directory is not clean. Please commit or discard changes before bumping the version. {thankyou}")
        sys.exit(1)

    if (
        latest_commit_message.startswith(prefix_to_check)
        or latest_commit_message.startswith(prefix_to_check2)
    ) and "[skip ci]" in latest_commit_message:
        print(f"{holdup} Bump version rejected. 😿 There are no changes to the code.")
        sys.exit(1)

    try:
        new_version = _get_new_version(args)
    except Exception:
        print(
            f"{holdup} Failed to run bump2v dry-run. Please check the following:\n"
            "- Ensure that '.bumpversion.cfg' is present and correctly configured. \n"
            "- Verify that the version part (e.g., major, minor, patch) is specified correctly."
        )
        sys.exit(1)

    if new_version:
        print(f"📦 Bumping to version: {new_version}")

    try:
        _bumpversion_main(args)
        print(f"Yay! 😺🎉 Bump version accepted. {okay}")
    except SystemExit as e:
        if e.code == 0:
            print(f"Yay! 😺🎉 Bump version accepted. {okay}")
        else:
            print(
                f"{holdup} Failed to bump the version. Please try the following: {thankyou}\n"
                "- Check your bump2v configuration.\n"
                "- Verify that the versioning arguments are correct (e.g., major, minor, patch).\n"
                "- Ensure your Git repository is in a valid state (no uncommitted changes)."
            )
            sys.exit(1)
    except Exception:
        print(
            f"{holdup} Failed to bump the version. Please try the following: {thankyou}\n"
            "- Check your bump2v configuration.\n"
            "- Verify that the versioning arguments are correct (e.g., major, minor, patch).\n"
            "- Ensure your Git repository is in a valid state (no uncommitted changes)."
        )
        sys.exit(1)

    if os.path.isdir("tests"):
        try:
            subprocess.run(["pytest", "--tb=short", "-q"], check=True)
            print(f"Yay! 😺🎉 Tests passed. {okay}")
        except subprocess.CalledProcessError:
            print(f"{holdup} Tests failed. Fix before pushing. {thankyou}")
            sys.exit(1)

    try:
        subprocess.run(["git", "push", "--follow-tags"], check=True)
        print(f"Yay! 😺🎉 Push successful. {okay}")
    except subprocess.CalledProcessError:
        print(f"{holdup} Failed to push changes to the remote repository. Please push manually. {thankyou}")
        sys.exit(1)


if __name__ == "__main__":
    main()
