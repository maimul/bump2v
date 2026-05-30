#!/usr/bin/env python3
import io
import logging
import os
import subprocess
import sys

from bump2v.bumpversion.cli import main as _bumpversion_main

holdup = "Hold up!! 👮🚨"
thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"


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

    latest_commit_message = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True, check=True
    ).stdout.strip()

    prefix_to_check = "Version Updated:"
    prefix_to_check2 = "Bump version:"

    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout:
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
