#!/usr/bin/env python3
"""bump2v command line.

The vendored bumpversion core (bump2v/bumpversion/) works out and applies a bump.
This module adds the subcommands (plan, release, show, check), Conventional-Commits
`auto`, the guards, the push, and the --json / exit-code contract (bump2v/output.py).
"""
import configparser
import os
import re
import subprocess
import sys

from bump2v.bumpversion import cli as core
from bump2v.bumpversion.exceptions import (
    VersionNotFoundException,
    WorkingDirectoryIsDirtyException,
)
from bump2v.bumpversion.vcs import Git
from bump2v.output import (
    EXIT_DIRTY,
    EXIT_ERROR,
    EXIT_NOTHING_TO_RELEASE,
    EXIT_PUSH_FAILED,
    EXIT_TAG_EXISTS,
    EXIT_USAGE,
    EXIT_VERSION_NOT_FOUND,
    Failure,
    Output,
)

thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"

USAGE = """\
usage: bump2v <part|auto> [options]          bump, commit, tag and push
       bump2v plan <part|auto> [options]     show what a bump would do; changes nothing
       bump2v release <part|auto> [options]  same as `bump2v <part>`, named explicitly
       bump2v show [field ...]               print the current version and settings
       bump2v check                          check every configured file has the current version

<part> is major, minor or patch (or a part from your config). `auto` picks it from
the Conventional Commits since the last release.

options:
  --json        print one JSON result on stdout (messages stay on stderr)
  --no-push     commit and tag, but don't push (also: push = False in the config)
  --push        push even if the config says push = False
  --dry-run     change nothing; same as `plan`
  bump2v <part> --help lists every bumpversion option (--config-file,
  --allow-dirty, --no-commit, --no-tag, --new-version, ...)

exit codes: 0 ok, 1 error, 2 usage, 3 dirty tree, 4 version not found in a file,
            5 tag exists, 6 push failed, 7 nothing to release
"""

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



def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _detect_bump_level():
    """
    Analyze git commits since the last tag using Conventional Commits.

    Returns a dict: level ('major' | 'minor' | 'patch'), since (the tag, or None),
    commits (list of {subject, level}) and conventional (whether any commit
    followed the spec). Raises Failure when there is nothing new to release.
    """
    describe = _git("describe", "--tags", "--abbrev=0")
    if describe.returncode != 0:
        return {"level": "patch", "since": None, "commits": [], "conventional": False}
    last_tag = describe.stdout.strip()

    log = _git("log", f"{last_tag}..HEAD", "--format=%B%x00")
    if log.returncode != 0:
        return {"level": "patch", "since": last_tag, "commits": [], "conventional": False}

    messages = [m.strip() for m in log.stdout.split("\x00") if m.strip()]
    if not messages:
        raise Failure(
            EXIT_NOTHING_TO_RELEASE, "nothing_to_release",
            f"No commits since {last_tag}. Nothing to bump.",
        )

    level, rows, found_conventional = _classify_commits(messages)
    return {
        "level": level,
        "since": last_tag,
        "commits": [{"subject": subject, "level": detected} for subject, detected in rows],
        "conventional": found_conventional,
    }


def _report_auto(out, auto):
    labels = {"major": "MAJOR", "minor": "minor", "patch": "patch", None: "-"}
    if auto["since"] is None:
        out.say("No tags found -- defaulting to patch.")
        return
    out.say(f"Analyzing commits since {auto['since']}...\n")
    for commit in auto["commits"]:
        summary = commit["subject"]
        short = (summary[:62] + "...") if len(summary) > 65 else summary
        out.say(f"  {short:<65}  {labels[commit['level']]}")
    if not auto["conventional"]:
        out.say("\nNo conventional commits found -- defaulting to patch.")
    out.say(f"\nAuto-detected: {auto['level']}\n")


def _git_state():
    """HEAD sha and the set of tags, to tell whether the bump created anything to push."""
    head = _git("rev-parse", "HEAD").stdout.strip()
    tags = set(_git("tag", "--list").stdout.split())
    return head, tags


# --- argument handling -------------------------------------------------------

_OWN_FLAGS = {"--json": ("json", True), "--push": ("push", True), "--no-push": ("push", False)}


def _own_flags(argv):
    """Take bump2v's own flags out of argv; the rest goes to the bumpversion core."""
    opts = {"json": False, "push": None}
    rest = []
    for arg in argv:
        if arg in _OWN_FLAGS:
            key, value = _OWN_FLAGS[arg]
            opts[key] = value
        else:
            rest.append(arg)
    if opts["json"]:
        rest = [arg for arg in rest if arg != "--list"]  # --list would print on stdout
    return opts, rest


def _positional_indexes(args):
    """Indexes of the positional arguments, skipping the values of options that take one."""
    indexes = []
    for i, arg in enumerate(args):
        previous = args[i - 1] if i > 0 else None
        if not arg.startswith("-") and previous not in core.OPTIONAL_ARGUMENTS_THAT_TAKE_VALUES:
            indexes.append(i)
    return indexes


def _part_names(args):
    """The version part names the config's `parse` regex defines (major, minor, patch, ...)."""
    config_file = ".bumpversion.cfg"
    if "--config-file" in args and args.index("--config-file") + 1 < len(args):
        config_file = args[args.index("--config-file") + 1]
    elif not os.path.exists(config_file) and os.path.exists("setup.cfg"):
        config_file = "setup.cfg"
    parse = r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    try:
        config = configparser.RawConfigParser()
        config.read(config_file, encoding="utf-8-sig")
        parse = config.get("bumpversion", "parse", fallback=parse)
        return set(re.compile(parse, re.VERBOSE).groupindex)
    except (configparser.Error, re.error, OSError):
        return {"major", "minor", "patch"}


def _select_command(args):
    """Split off the subcommand. `release` is a subcommand only when a part or `auto`
    follows it; on its own it is still the bump2version part named `release`."""
    if args and args[0] == "bump":
        return "bump", args[1:]
    if args and args[0] in ("plan", "show", "check"):
        return args[0], args[1:]
    if args and args[0] == "release":
        rest = args[1:]
        positionals = [rest[i] for i in _positional_indexes(rest)]
        if positionals and (positionals[0] == "auto" or positionals[0] in _part_names(rest)):
            return "release", rest
    return "bump", args


# --- shared steps ------------------------------------------------------------

def _resolve_auto(args, out):
    """Replace a positional `auto` with the level Conventional Commits point to."""
    for i in _positional_indexes(args):
        if args[i] == "auto":
            auto = _detect_bump_level()
            _report_auto(out, auto)
            return args[:i] + [auto["level"]] + args[i + 1:], auto
        break
    return args, None


def _core_call(function, *args):
    """Call into the bumpversion core, turning its exceptions into Failures."""
    try:
        return function(*args)
    except WorkingDirectoryIsDirtyException as e:
        raise Failure(
            EXIT_DIRTY, "dirty_tree",
            "Working directory is not clean. Please commit or discard changes before bumping the version.",
            hint="Commit or stash the changes listed above, or pass --allow-dirty.",
        ) from e
    except VersionNotFoundException as e:
        raise Failure(
            EXIT_VERSION_NOT_FOUND, "version_not_found", str(e),
            hint="Run `bump2v check` to see which files don't match current_version.",
        ) from e
    except subprocess.CalledProcessError as e:
        raise Failure(
            EXIT_ERROR, "git_failed",
            "{} failed with exit code {}".format(" ".join(map(str, e.cmd)), e.returncode),
        ) from e
    except SystemExit as e:
        if e.code in (0, None):
            raise
        raise Failure(
            EXIT_USAGE if e.code == 2 else EXIT_ERROR, "usage" if e.code == 2 else "error",
            "Invalid arguments or config; see the message above.",
            hint="Run `bump2v --help`, or `bump2v <part> --help` for every option.",
        ) from e


def _first_positional(args):
    indexes = _positional_indexes(args)
    return args[indexes[0]] if indexes else None


def _push_enabled(plan, opts):
    if opts["push"] is not None:
        return opts["push"]
    return bool(plan.defaults.get("push", True))


def _check_tag_is_free(plan):
    if plan.vcs is Git and plan.args.tag:
        name = plan.tag_name()
        if _git("rev-parse", "-q", "--verify", "refs/tags/" + name).returncode == 0:
            raise Failure(
                EXIT_TAG_EXISTS, "tag_exists", f"Tag {name} already exists.",
                hint="current_version in the config may be behind the latest release: "
                     "compare it with `git tag --list`, or delete the tag if it was made by mistake.",
            )


def _payload(plan, part, auto, push_enabled, before=None, after=None, pushed=False):
    args = plan.args
    commit_enabled = bool(plan.vcs) and bool(args.commit)
    tag_enabled = bool(plan.vcs) and bool(args.tag)
    tag_name = plan.tag_name() if tag_enabled else None
    committed = before is not None and after is not None and after[0] != before[0]
    return {
        "dry_run": bool(args.dry_run),
        "current_version": args.current_version,
        "new_version": args.new_version,
        "part": part,
        "auto": auto,
        "files": [
            {"path": c.path, "changed": c.changed, "matches": c.matches}
            for c in plan.changes
        ],
        "config_file": plan.config_file if plan.config_file_exists else None,
        "commit": {
            "enabled": commit_enabled,
            "message": plan.commit_message() if commit_enabled else None,
            "sha": after[0] if committed else None,
        },
        "tag": {
            "enabled": tag_enabled,
            "name": tag_name,
            "created": bool(after and before and tag_name in after[1] - before[1]),
        },
        "push": {"enabled": push_enabled, "pushed": pushed},
    }


def _warn_multiple_matches(plan, out):
    for change in plan.changes:
        if change.matches > 1:
            out.say(
                f"warning: {change.path}: the search matches {change.matches} places and "
                "all of them are replaced. Set replace_all = False in its section to "
                "bump only the first."
            )


# --- commands ----------------------------------------------------------------

def _guard_version_commit():
    latest = _git("log", "-1", "--pretty=%B").stdout.strip()
    if (
        latest.startswith("Version Updated:") or latest.startswith("Bump version:")
    ) and "[skip ci]" in latest:
        raise Failure(
            EXIT_NOTHING_TO_RELEASE, "nothing_to_release",
            "Bump version rejected. 😿 There are no changes to the code.",
            hint="HEAD is already a version commit; make a change first.",
        )


def cmd_plan(args, opts, out):
    args, auto = _resolve_auto(args, out)
    plan = _core_call(core.compute_plan, args)
    _check_tag_is_free(plan)
    push = _push_enabled(plan, opts)
    payload = _payload(plan, _first_positional(args), auto, push)
    payload["dry_run"] = True

    out.data(f"{payload['current_version']} → {payload['new_version']}  ({payload['part']})")
    for f in payload["files"]:
        note = f"{f['matches']} match" + ("es" if f["matches"] != 1 else "")
        out.data(f"  {f['path']:<40} {note}")
    if payload["config_file"]:
        out.data(f"  {payload['config_file']:<40} current_version")
    commit, tag = payload["commit"], payload["tag"]
    out.data(f"commit: {commit['message'] if commit['enabled'] else 'no'}")
    out.data(f"tag:    {tag['name'] if tag['enabled'] else 'no'}")
    out.data(f"push:   {'yes' if push and commit['enabled'] else 'no'}")
    _warn_multiple_matches(plan, out)
    return payload


def cmd_bump(args, opts, out):
    _guard_version_commit()

    if "--tag-only" in args:
        before = _git_state()
        _core_call(core.main, args)
        after = _git_state()
        pushed = _push_if_needed(out, opts["push"] is not False, False, before, after)
        return {"tag": {"created": sorted(after[1] - before[1])}, "push": {"pushed": pushed}}

    args, auto = _resolve_auto(args, out)
    plan = _core_call(core.compute_plan, args)
    _check_tag_is_free(plan)
    push = _push_enabled(plan, opts)

    out.say(f"Bumping to version: {plan.args.new_version}",
            f"📦 Bumping to version: {plan.args.new_version}")
    before = _git_state()
    _core_call(core.apply_plan, plan)
    after = _git_state()
    if plan.args.dry_run:
        out.say(f"Would bump {plan.args.current_version} → {plan.args.new_version}.")
    else:
        out.say(f"Bumped {plan.args.current_version} → {plan.args.new_version}.",
                f"Yay! 😺🎉 Bump version accepted. {okay}")

    pushed = _push_if_needed(out, push, plan.args.dry_run, before, after)
    return _payload(plan, _first_positional(args), auto, push, before, after, pushed)


def _push_if_needed(out, push, dry_run, before, after):
    # Push only what this run created: a dry run, `commit = False` or `--no-commit`
    # leaves HEAD and the tags unchanged, and pushing then would publish unrelated
    # local commits.
    if dry_run:
        out.say("Dry run: nothing committed, nothing pushed.")
        return False
    if after == before:
        out.say("Nothing was committed or tagged, so nothing to push.")
        return False
    if not push:
        out.say("Not pushing (push is off). Push later with: git push --follow-tags")
        return False
    if _git("symbolic-ref", "-q", "HEAD").returncode != 0:
        raise Failure(
            EXIT_PUSH_FAILED, "detached_head",
            "Committed and tagged, but HEAD is detached, so there is no branch to push.",
            hint="Check out a branch before bumping (in GitHub Actions, pull_request "
                 "events check out a detached merge commit), or pass --no-push.",
        )
    if subprocess.run(["git", "push", "--follow-tags"]).returncode != 0:
        raise Failure(
            EXIT_PUSH_FAILED, "push_failed",
            "Failed to push changes to the remote repository. The version commit and "
            "tag are local; push them manually.",
            hint="If the remote moved on, run `git pull --rebase` and then "
                 "`git push --follow-tags`.",
            retryable=True,
        )
    out.say("Pushed.", f"Yay! 😺🎉 Push successful. {okay}")
    return True


def _settings(args):
    return _core_call(core.load_settings, args)


def _base_context():
    return dict(
        list(core.time_context.items())
        + list(core.prefixed_environ().items())
        + list(core.special_char_context.items())
    )


def _render_tag(settings, version_string, version):
    template = settings.defaults.get("tag_name", "v{new_version}")
    context = _base_context()
    context.update({"current_version": version_string, "new_version": version_string})
    if version is not None:
        context.update({"current_" + p: version[p].value for p in version})
        context.update({"new_" + p: version[p].value for p in version})
    try:
        return template.format(**context)
    except (KeyError, IndexError, ValueError):
        return None


def cmd_show(args, opts, out):
    positions = _positional_indexes(args)
    fields = [args[i] for i in positions]
    flags = [a for i, a in enumerate(args) if i not in positions]
    settings = _settings(flags)
    version = settings.current_version
    defaults = settings.defaults

    nxt = {}
    if version is not None:
        order = list(settings.version_config.order())
        for part in order:
            try:
                nxt[part] = settings.version_config.serialize(
                    version.bump(part, order), _base_context()
                )
            except Exception:  # a values-part at its last value, an incomplete format...
                continue

    info = {
        "current_version": settings.known_args.current_version,
        "config_file": settings.config_file if settings.config_file_exists else None,
        "files": [f.path for f in settings.files],
        "commit": bool(defaults.get("commit", False)),
        "tag": bool(defaults.get("tag", False)),
        "tag_name": _render_tag(settings, settings.known_args.current_version, version),
        "push": bool(defaults.get("push", True)),
        "next": nxt,
    }

    if fields:
        for field in fields:
            value = info
            for key in field.split("."):
                if not isinstance(value, dict) or key not in value:
                    raise Failure(
                        EXIT_USAGE, "unknown_field", f"Unknown field: {field}",
                        hint="Fields: " + ", ".join(
                            sorted(list(info) + [f"next.{p}" for p in nxt])
                        ),
                    )
                value = value[key]
            out.data(" ".join(value) if isinstance(value, list) else str(value))
    else:
        for key, value in info.items():
            if key == "next":
                for part, v in value.items():
                    out.data(f"next.{part}: {v}")
            else:
                out.data(f"{key}: {' '.join(value) if isinstance(value, list) else value}")
    return info


def cmd_check(args, opts, out):
    settings = _settings(args)
    version = settings.current_version
    if version is None:
        raise Failure(
            EXIT_VERSION_NOT_FOUND, "no_current_version",
            "No current_version: set it in the config or pass --current-version.",
        )
    ignore_missing = bool(settings.defaults.get("ignore_missing_version", False))

    files = []
    for f in settings.files:
        entry = {"path": f.path, "found": False, "matches": 0}
        if not os.path.exists(f.path):
            entry["error"] = "file not found"
        else:
            context = _base_context()
            context["current_version"] = f._versionconfig.serialize(version, context)
            search = f._versionconfig.search.format(**context)
            entry["matches"] = f.count_matches(search)
            entry["found"] = entry["matches"] > 0 or (
                f._versionconfig.search == "{current_version}" and f.contains(version.original)
            )
        entry["ignored"] = not entry["found"] and ignore_missing and "error" not in entry
        files.append(entry)

    tag = None
    if settings.defaults.get("tag") and Git.is_usable():
        name = _render_tag(settings, settings.known_args.current_version, version)
        if name:
            exists = _git("rev-parse", "-q", "--verify", "refs/tags/" + name).returncode == 0
            tag = {"name": name, "exists": exists}

    for entry in files:
        if entry["found"]:
            out.data(f"ok       {entry['path']}  ({entry['matches']} match"
                     f"{'es' if entry['matches'] != 1 else ''})")
        elif entry["ignored"]:
            out.data(f"skipped  {entry['path']}  (no {settings.known_args.current_version}; "
                     "ignore_missing_version)")
        else:
            out.data(f"MISSING  {entry['path']}  ({entry.get('error', 'no ' + str(settings.known_args.current_version))})")
    if tag and not tag["exists"]:
        out.say(f"warning: tag {tag['name']} for the current version does not exist.")

    result = {
        "current_version": settings.known_args.current_version,
        "config_file": settings.config_file if settings.config_file_exists else None,
        "files": files,
        "tag": tag,
    }
    missing = [e["path"] for e in files if not e["found"] and not e["ignored"]]
    if missing:
        raise Failure(
            EXIT_VERSION_NOT_FOUND, "version_drift",
            "{} doesn't contain {}: {}".format(
                "One file" if len(missing) == 1 else f"{len(missing)} files",
                settings.known_args.current_version, ", ".join(missing),
            ),
            hint="Someone edited a version by hand, or current_version is out of date. "
                 "Put the files back in line with current_version (or fix it), then bump.",
            details=result,
        )
    return result


COMMANDS = {
    "bump": cmd_bump,
    "release": cmd_bump,
    "plan": cmd_plan,
    "show": cmd_show,
    "check": cmd_check,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    opts, args = _own_flags(argv)
    out = Output(json_mode=opts["json"])

    if not args or args[0] in ("-h", "--help", "help"):
        print(USAGE, file=sys.stdout if args else sys.stderr)
        sys.exit(0 if args else EXIT_USAGE)

    command, args = _select_command(args)
    try:
        payload = COMMANDS[command](args, opts, out)
    except Failure as failure:
        out.failure(command, failure)
        sys.exit(failure.exit_code)
    except Exception as e:  # unexpected: report it in the same shape
        failure = Failure(
            EXIT_ERROR, "error", f"{type(e).__name__}: {e}",
            hint="Re-run with --verbose for details.",
        )
        out.failure(command, failure)
        if not opts["json"]:
            out.say("Failed to bump the version. Please check your bump2v configuration. "
                    f"{thankyou}")
        sys.exit(EXIT_ERROR)
    out.result(command, payload)


if __name__ == "__main__":
    main()
