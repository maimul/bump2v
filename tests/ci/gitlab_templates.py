"""Run the GitLab CI/CD templates in templates/ the way a GitLab runner would, in the image.

    python tests/ci/gitlab_templates.py --image bump2v:test

GitLab itself isn't available here, so this does what the runner does for these jobs:
reads the template's spec, fills in the inputs, checks out the pipeline's commit with a
detached HEAD, and runs the job's script in the image with the CI_* variables set. The
remote is a bare repo whose pre-receive hook records the push options. Needs Docker and
PyYAML. Not collected by pytest (no test_ prefix); CI runs it in the Action workflow.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INPUT = re.compile(r"\$\[\[\s*inputs\.([A-Za-z0-9_-]+)\s*\]\]")
DOTENV_LINE = re.compile(r"^[A-Za-z0-9_]+=[^\n]+$")
CONTAINER_PROJECT = "/builds/group/project"
CONTAINER_REMOTE = "/remote.git"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout.strip()


def render(template, inputs):
    """The job definitions of a template, with its inputs filled in as GitLab does."""
    text = (ROOT / "templates" / template).read_text(encoding="utf-8")
    header, body = text.split("\n---\n", 1)
    spec = yaml.safe_load(header)["spec"]["inputs"]
    unknown = set(inputs) - set(spec)
    assert not unknown, f"{template}: no such inputs: {sorted(unknown)}"
    values = {}
    for name, rules in spec.items():
        value = inputs.get(name, rules.get("default"))
        assert value is not None, f"{template}: input {name} is mandatory"
        kind = rules.get("type", "string")
        if kind == "boolean":
            assert isinstance(value, bool), f"{template}: {name} must be a boolean"
            value = "true" if value else "false"
        elif kind == "number":
            assert isinstance(value, (int, float)), f"{template}: {name} must be a number"
        if "regex" in rules:
            assert re.search(rules["regex"], str(value)), f"{template}: {name}={value!r} fails its regex"
        values[name] = str(value)
    used = set(INPUT.findall(body))
    assert used <= set(spec), f"{template}: uses undeclared inputs {sorted(used - set(spec))}"
    return yaml.safe_load(INPUT.sub(lambda m: values[m.group(1)], body))


def run_job(template, job, image, work, remote, inputs=None, env=None):
    """Run one job of a template in the image; returns (exit code, output, dotenv lines)."""
    definition = render(template, inputs or {})[job]
    variables = {
        "CI": "true", "GITLAB_CI": "true",
        "CI_PROJECT_DIR": CONTAINER_PROJECT,
        "CI_COMMIT_SHA": git(work, "rev-parse", "HEAD"),
        "CI_COMMIT_BRANCH": "main", "CI_COMMIT_REF_SLUG": "main",
        "CI_REPOSITORY_URL": CONTAINER_REMOTE,
        **{k: str(v) for k, v in definition.get("variables", {}).items()},
        **(env or {}),
    }
    command = ["docker", "run", "--rm", "-w", CONTAINER_PROJECT,
               "-v", f"{work}:{CONTAINER_PROJECT}", "-v", f"{remote}:{CONTAINER_REMOTE}"]
    for key, value in variables.items():
        command += ["-e", f"{key}={value}"]
    command += [image, "sh", "-c", "\n".join(definition["script"])]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    output = result.stdout + result.stderr
    dotenv = []
    report = definition.get("artifacts", {}).get("reports", {}).get("dotenv")
    if report and (work / report).exists():
        dotenv = (work / report).read_text(encoding="utf-8").splitlines()
        bad = [line for line in dotenv if not DOTENV_LINE.match(line)]
        assert not bad, f"GitLab would reject these dotenv lines: {bad}"
    return result.returncode, output, dict(line.split("=", 1) for line in dotenv)


def pipeline_checkout(remote, base, name):
    """A fresh clone at the remote tip, HEAD detached, origin set to the container path."""
    work = base / name
    git(base, "clone", "-q", str(remote), str(work))
    git(work, "checkout", "-q", "--detach")
    git(work, "remote", "set-url", "origin", CONTAINER_REMOTE)
    return work


def expect(condition, message, output=""):
    if not condition:
        sys.exit(f"FAIL: {message}\n{output}")
    print(f"ok  {message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--image", required=True)
    image = parser.parse_args().image

    base = Path(tempfile.mkdtemp(prefix="bump2v-gitlab-"))
    try:
        os.environ["GIT_CONFIG_GLOBAL"] = str(base / "gitconfig")
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
        for key, value in {"name": "Dev", "email": "dev@example.com"}.items():
            git(base, "config", "--global", f"user.{key}", value)

        remote = base / "remote.git"
        git(base, "init", "-q", "--bare", "-b", "main", str(remote))
        git(remote, "config", "receive.advertisePushOptions", "true")
        hook = remote / "hooks" / "pre-receive"
        hook.write_text('#!/bin/sh\ni=0\nwhile [ "$i" -lt "${GIT_PUSH_OPTION_COUNT:-0}" ]; do\n'
                        '  eval "echo \\$GIT_PUSH_OPTION_$i" >> push-options.log\n  i=$((i + 1))\ndone\n',
                        encoding="utf-8")
        hook.chmod(0o755)

        seed = base / "seed"
        git(base, "clone", "-q", str(remote), str(seed))
        (seed / ".bumpversion.cfg").write_text(
            "[bumpversion]\ncurrent_version = 0.1.0\ncommit = True\ntag = True\n\n"
            "[bumpversion:file:package.json]\n"
            'search = "version": "{current_version}"\nreplace = "version": "{new_version}"\n',
            encoding="utf-8")
        (seed / "package.json").write_text('{\n  "version": "0.1.0"\n}\n', encoding="utf-8")
        git(seed, "add", "-A")
        git(seed, "commit", "-q", "-m", "chore: start")
        git(seed, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
        (seed / "feature.txt").write_text("new\n", encoding="utf-8")
        git(seed, "add", "-A")
        git(seed, "commit", "-q", "-m", "feat: a new feature")
        git(seed, "push", "-q", "--follow-tags", "origin", "main")

        # The pipeline for "feat: a new feature" starts; meanwhile a fix lands on main.
        work = pipeline_checkout(remote, base, "pipeline-1")
        (seed / "fix.txt").write_text("fix\n", encoding="utf-8")
        git(seed, "add", "-A")
        git(seed, "commit", "-q", "-m", "fix: landed while the pipeline was queued")
        git(seed, "push", "-q", "origin", "main")

        code, output, env = run_job("release.yml", "bump2v-release", image, work, remote)
        expect(code == 0, "release: the job succeeds", output)
        expect(git(remote, "log", "-1", "--format=%s", "main") == "Bump version: 0.1.0 → 0.2.0",
               "release: bumps minor (feat) on top of the fix that landed meanwhile", output)
        expect(git(remote, "tag", "--list", "v0.2.0") == "v0.2.0", "release: pushes the tag")
        expect((remote / "push-options.log").read_text(encoding="utf-8").split() == ["ci.skip"],
               "release: pushes with ci.skip")
        expect(env == {"BUMP2V_VERSION": "0.2.0", "BUMP2V_PREVIOUS_VERSION": "0.1.0",
                       "BUMP2V_TAG": "v0.2.0", "BUMP2V_SHA": git(remote, "rev-parse", "main"),
                       "BUMP2V_BUMPED": "true", "BUMP2V_PUSHED": "true"},
               "release: dotenv carries the version, tag and the commit to build", str(env))

        # A second pipeline for the same commit, queued behind the first one.
        again = pipeline_checkout(remote, base, "pipeline-2")
        git(again, "checkout", "-q", "--detach", "HEAD~2")
        code, output, env = run_job("release.yml", "bump2v-release", image, again, remote)
        expect(code == 0 and "Nothing to release" in output,
               "release: a pipeline behind an earlier release succeeds without bumping", output)
        expect(env.get("BUMP2V_BUMPED") == "false" and env.get("BUMP2V_VERSION") == "0.2.0"
               and "BUMP2V_TAG" not in env, "release: its dotenv says bumped=false, version 0.2.0", str(env))
        expect(git(remote, "tag", "--list", "v0.2.*") == "v0.2.0", "release: no second tag")

        check = pipeline_checkout(remote, base, "check")
        code, output, _ = run_job("check.yml", "bump2v-check", image, check, remote)
        expect(code == 0 and "ok       package.json" in output, "check: passes when versions match", output)
        package = check / "package.json"
        package.write_text(package.read_text(encoding="utf-8").replace("0.2.0", "0.2.1"), encoding="utf-8")
        code, output, _ = run_job("check.yml", "bump2v-check", image, check, remote)
        expect(code == 4 and "MISSING  package.json" in output, "check: fails (exit 4) on drift", output)

        for template, inputs in {"release.yml": {"part": "patch; rm -rf /"}}.items():
            try:
                render(template, inputs)
            except AssertionError:
                print(f"ok  {template}: refuses a part that isn't a plain name")
            else:
                sys.exit(f"FAIL: {template} accepted part={inputs['part']!r}")
    finally:
        # The jobs ran as root in the container; on Linux, hand their files back first.
        if hasattr(os, "getuid"):
            subprocess.run(["docker", "run", "--rm", "-v", f"{base}:/work", image,
                            "chown", "-R", f"{os.getuid()}:{os.getgid()}", "/work"],
                           capture_output=True)
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
