bump2v
======

A CLI wrapper and native fork of `bump2version <https://github.com/c4urself/bump2version>`_ for automated semantic versioning. Bumps version numbers across files, commits, tags, and pushes -- all in one command.

.. code-block:: zsh

    pip install bump2v        # or: pipx install bump2v

Requires Python 3.11 or newer (older Pythons get 1.6.x). No other dependencies.

-----------

How it works
------------

bump2v reads your current version from a config file, increments it, rewrites it in every file you specify, commits the change, creates a git tag, and pushes -- all in one command. The **source of truth for the version** lives in your project's main file:

- **Node.js / React / JS** -- ``package.json`` -> ``"version": "1.0.0"``
- **Python** -- ``appInfo.py`` -> ``__version__ = "1.0.0"``
- **Any other file** -- configurable via ``.bumpversion.cfg``

The ``.bumpversion.cfg`` file tells bump2v where to find and update that version string. **You only need to run bump2v -- never edit the version manually.**

-----------

Quick Start
-----------

**Once per project:** let bump2v find your version and write ``.bumpversion.cfg``, then review and commit it.

.. code-block:: zsh

    bump2v init

**Step 1:** Make your code change.

**Step 2:** Stage and commit.

.. code-block:: zsh

    git add .
    git commit -m "fix: describe your change here"

**Step 3:** Bump the version and push.

.. code-block:: zsh

    bump2v patch   # 1.0.0 -> 1.0.1  (bug fix)
    bump2v minor   # 1.0.0 -> 1.1.0  (new feature)
    bump2v major   # 1.0.0 -> 2.0.0  (breaking change)
    bump2v auto    # detect level from commit messages automatically

Alternative command aliases: ``bumptydumpty``, ``versionkaboom``

Preview first
~~~~~~~~~~~~~

.. code-block:: zsh

    bump2v plan patch          # new version, files, commit message, tag, push; changes nothing
    bump2v plan auto --json    # the same as JSON, for scripts and AI agents
    bump2v patch --dry-run     # the older form; also changes nothing (--verbose shows each file)

bump2v pushes only what the run itself created. With ``--dry-run``, ``--no-commit`` or ``commit = False`` there is nothing new, so nothing is pushed.

-----------

Commands
--------

- ``bump2v <part>`` -- bump, commit, tag and push. ``<part>`` is ``major``, ``minor``, ``patch`` or a part from your config
- ``bump2v auto`` -- the same, with the part picked from your commit messages (see Auto mode below)
- ``bump2v release <part|auto>`` -- the same as ``bump2v <part>``, named explicitly
- ``bump2v plan <part|auto>`` -- show what a bump would do. Changes nothing
- ``bump2v show [field ...]`` -- print ``current_version``, ``files``, ``tag_name``, ``next.major``, ``next.minor``, ``next.patch``, ...
- ``bump2v check`` -- fail with exit code 4 if a configured file doesn't contain ``current_version``
- ``bump2v init [--agents]`` -- write ``.bumpversion.cfg`` for this project. ``--agents`` also adds release instructions for AI coding agents

Options for every command: ``--json`` (one JSON result on stdout), ``--no-push``, ``--push``. For CI: ``--sync`` (fast-forward to the remote branch tip first; exit 7 if the tip is already a version commit), ``--retry N`` (if another run pushed first, catch up and bump again, up to N times; implies ``--sync``), ``--github-output`` (write ``version``, ``previous_version``, ``tag``, ``sha``, ``bumped``, ``pushed`` to ``$GITHUB_OUTPUT``). ``bump2v <part> --help`` lists every bumpversion option (``--config-file``, ``--allow-dirty``, ``--no-commit``, ``--no-tag``, ``--new-version``, ...).

If your config defines a part named ``release``, ``bump2v release`` on its own still bumps that part; ``bump2v release patch`` is the command.

-----------

Setup by project type
---------------------

Node.js / React
~~~~~~~~~~~~~~~

The version lives in ``package.json``. bump2v finds and updates it there.

``.bumpversion.cfg``:

.. code-block:: ini

    [bumpversion]
    current_version = 1.0.0
    commit = True
    tag = True
    message = Version Updated: {current_version} -> {new_version} [skip ci]

    [bumpversion:file:package.json]
    search = "version": "{current_version}"
    replace = "version": "{new_version}"

The ``current_version`` in ``.bumpversion.cfg`` must always match the ``"version"`` field in ``package.json``. bump2v keeps them in sync automatically -- never edit either one by hand.

Python
~~~~~~

The version lives in ``appInfo.py`` (or wherever you store your app metadata).

``app/appInfo.py``:

.. code-block:: python

    app_name = "Your App Name"
    __version__ = "1.0.0"
    description = "Describe your app here"

``main.py``:

.. code-block:: python

    from appInfo import __version__, app_name, description

    app = FastAPI(
        title=app_name,
        description=description,
        version=__version__,
    )

``.bumpversion.cfg``:

.. code-block:: ini

    [bumpversion]
    current_version = 1.0.0
    commit = True
    tag = True
    message = Version Updated: {current_version} -> {new_version} [skip ci]

    [bumpversion:file:app/appInfo.py]
    search = __version__ = "{current_version}"
    replace = __version__ = "{new_version}"

Multiple files
~~~~~~~~~~~~~~

You can target as many files as needed:

.. code-block:: ini

    [bumpversion]
    current_version = 1.0.0
    commit = True
    tag = True

    [bumpversion:file:package.json]
    search = "version": "{current_version}"
    replace = "version": "{new_version}"

    [bumpversion:file:app/appInfo.py]
    search = __version__ = "{current_version}"
    replace = __version__ = "{new_version}"

-----------

Semantic Versioning
-------------------

- ``bump2v patch`` -- ``1.0.0 -> 1.0.1`` -- Bug fixes, minor improvements
- ``bump2v minor`` -- ``1.0.0 -> 1.1.0`` -- New backward-compatible features
- ``bump2v major`` -- ``1.0.0 -> 2.0.0`` -- Breaking changes
- ``bump2v auto``  -- Detect level automatically from commit messages

-----------

Auto mode (Conventional Commits)
---------------------------------

``bump2v auto`` analyzes every commit since the last release using the
`Conventional Commits <https://www.conventionalcommits.org>`_ spec and
selects the bump level automatically. The last release is the newest tag your
``tag_name`` could have made (``baseline-v{new_version}`` -> tags matching
``baseline-v*``), or, with ``tag = False``, the last commit whose subject
matches your ``message``. No more guessing whether this week's
work is a patch or a minor.

**Rules:**

- ``feat!:`` or ``BREAKING CHANGE:`` in commit footer -> major
- ``feat:`` -> minor
- ``fix:``, ``perf:``, ``refactor:``, ``chore:``, ``docs:``, etc. -> patch
- Scopes are supported: ``feat(auth):`` counts as ``feat``
- The **highest** level found across all commits wins

**Example output:**

.. code-block:: zsh

    $ bump2v auto
    Analyzing commits since v1.5.3...

      feat: add websocket endpoint                        minor
      fix: handle null pointer in auth module             patch
      chore: update dependencies                          patch
      feat!: redesign configuration API                   MAJOR

    Auto-detected: major
    Bumping to version: 2.0.0

If no conventional commits are found, bumps patch as a safe fallback.
With no earlier release it bumps patch. With nothing new since the last
release it stops with exit code 7. In CI, check out the full history
(``fetch-depth: 0`` in GitHub Actions); a shallow clone that hides the last
release fails with exit code 1 instead of guessing. Preview with
``bump2v plan auto``.

-----------

GitHub Action
-------------

.. code-block:: yaml

    on:
      push:
        branches: [development]

    concurrency:                       # one release at a time per branch
      group: release-${{ github.ref }}
      cancel-in-progress: false

    jobs:
      release:
        runs-on: ubuntu-latest
        permissions:
          contents: write
        outputs:
          version: ${{ steps.bump.outputs.version }}
          sha: ${{ steps.bump.outputs.sha }}
        steps:
          - uses: actions/checkout@v6
            with:
              fetch-depth: 0           # auto reads the commits since the last release
          - id: bump
            uses: maimul/bump2v@v1.8.0 # or pin the full commit SHA
            with:
              part: auto               # major, minor, patch or auto (the default)

      build:
        needs: release
        steps:
          - uses: actions/checkout@v6
            with:
              ref: ${{ needs.release.outputs.sha }}   # build the version commit itself

What the action does for you:

- **Bumps from the branch tip.** CI checks out the commit that triggered the run; if another run pushed since, the action fast-forwards first instead of bumping a stale commit.
- **Retries a lost race.** If another run still pushes first, it drops its own version commit and tag, catches up and bumps again (``retry``, default 3).
- **Skips a released tip.** If the branch tip is already a version commit, it succeeds with ``bumped=false`` and the current version, so later steps still have a version to use.
- **Pushes atomically.** The branch and tag land together or not at all, so no orphan tags.
- **Outputs** ``version``, ``previous-version``, ``tag``, ``sha`` (the commit to build), ``bumped``, ``pushed``.
- **Runs from its own commit.** No ``pip install``, nothing downloaded; pin it by SHA and that exact code runs. Needs Python 3.11+ on the runner (GitHub-hosted runners have it).

Inputs: ``part`` (``auto``), ``push`` (``true``), ``retry`` (``3``), ``working-directory`` (``.``), ``args`` (extra bump2v options).

-----------

In CI pipelines
---------------

.. code-block:: yaml

          - uses: actions/checkout@v6
            with:
              fetch-depth: 0   # auto reads the commits since the last tag
          - name: Bump, tag and push
            id: bump
            run: |
              pip install "bump2v>=1.8,<2"
              bump2v release auto --sync --retry 3
              echo "version=$(bump2v show current_version)" >> "$GITHUB_OUTPUT"

- Pin a version range (``bump2v>=1.8,<2``) so a new major release can't change your pipeline.
- When git has no user set and ``CI`` is set, bump2v commits as ``github-actions[bot]`` on GitHub Actions (or ``bump2v`` elsewhere), so no ``git config`` step is needed.
- ``bump2v show current_version`` prints just the version; no need to grep the config.
- ``bump2v release auto --json`` returns the old and new version, files, commit SHA, tag and push result in one object.
- ``--no-push`` commits and tags without pushing, for jobs that push later or not at all.
- Pushes made with ``GITHUB_TOKEN`` don't start new workflow runs, so the version commit won't trigger the pipeline again. Use a ``concurrency`` group so two releases never race.
- bump2v stops before writing anything if the new tag already exists (exit 5), and keeps the commit and tag local if HEAD is detached (exit 6).
- The branch and the tag are pushed together (``git push --atomic``): if the push is rejected because another run pushed first, no tag is left behind on the remote to block the next bump.

-----------

Using with AI coding agents
---------------------------

.. code-block:: zsh

    bump2v init --agents

adds a **Releasing** section to ``CLAUDE.md`` (or ``AGENTS.md``) that tells Claude Code, Codex, Cursor and other agents to preview with ``bump2v plan auto --json``, release with ``bump2v release auto``, check with ``bump2v check``, and never edit versions by hand.

To let an agent preview freely but ask before it releases, in Claude Code's ``.claude/settings.json``:

.. code-block:: json

    {
      "permissions": {
        "allow": ["Bash(bump2v plan *)", "Bash(bump2v show *)", "Bash(bump2v check *)"],
        "ask": ["Bash(bump2v release *)"]
      }
    }

Output is plain text (no emoji) when it isn't going to a terminal, or when ``NO_COLOR``, ``CI`` or ``CLAUDECODE`` is set.

-----------

Exit codes and JSON output
--------------------------

- ``0`` -- done
- ``1`` -- other error
- ``2`` -- bad arguments or config
- ``3`` -- working tree has uncommitted changes
- ``4`` -- a configured file doesn't contain the current version
- ``5`` -- the new tag already exists
- ``6`` -- push failed (or HEAD is detached); the commit and tag are local
- ``7`` -- nothing to release

With ``--json``, stdout carries one object (abbreviated here) and messages stay on stderr:

.. code-block:: json

    {
      "format_version": "1.1",
      "command": "plan",
      "ok": true,
      "current_version": "1.2.3",
      "new_version": "1.3.0",
      "part": "minor",
      "files": [{"path": "package.json", "changed": true, "matches": 1}],
      "commit": {"enabled": true, "message": "Version Updated: 1.2.3 -> 1.3.0", "sha": null},
      "tag": {"enabled": true, "name": "v1.3.0", "created": false},
      "push": {"enabled": true, "pushed": false}
    }

On failure: ``"ok": false``, ``"exit_code"``, and ``"error": {"code", "message", "hint", "retryable"}``. ``format_version`` changes minor for added fields and major for removed or renamed ones.

-----------

Advanced Flags
--------------

``--no-push`` / ``push = False`` -- Commit and tag without pushing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: zsh

    bump2v patch --no-push

Or set ``push = False`` in ``[bumpversion]``; ``--push`` overrides it for one run.

``replace_all`` -- Bump only the first match
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default every match of ``search`` in a file is replaced. If the same version string appears elsewhere (a dependency pinned to the same version), bump only the first match:

.. code-block:: ini

    [bumpversion:file:pyproject.toml]
    search = version = "{current_version}"
    replace = version = "{new_version}"
    replace_all = False

``bump2v plan`` warns when a search matches more than once. ``bump2v init`` sets ``replace_all = False`` for ``pyproject.toml`` and ``Cargo.toml``.

``--tag-only`` -- Tag without bumping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tags the current HEAD using ``current_version`` from config, without bumping or committing. Useful when you need to commit a build artifact between the version bump commit and the release tag.

.. code-block:: zsh

    bump2v patch --no-tag       # bump + commit, skip the tag
    # ... build artifact, git add, git commit ...
    bumpversion --tag-only      # tag HEAD now

Fixes `#256 <https://github.com/c4urself/bump2version/issues/256>`_.

``--ignore-missing-version`` -- Skip files without a version string
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using glob patterns, some files may not contain the version string. Instead of crashing, bump2v logs a warning and skips those files.

.. code-block:: zsh

    bump2v patch --ignore-missing-version

Or set it permanently in config:

.. code-block:: ini

    [bumpversion]
    ignore_missing_version = True

Fixes `#267 <https://github.com/c4urself/bump2version/issues/267>`_.

``--extra-files`` -- Include generated files in the bump commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stage additional files alongside the version bump commit, even if not modified by bumpversion. Files can be dirty or untracked.

.. code-block:: zsh

    bump2v patch --extra-files docs/changelog.md dist/summary.txt

Or set them in config:

.. code-block:: ini

    [bumpversion]
    extra_files = docs/changelog.md dist/summary.txt

Fixes `#259 <https://github.com/c4urself/bump2version/issues/259>`_.

``sign_tags`` config fix
~~~~~~~~~~~~~~~~~~~~~~~~

Setting ``sign_tags = False`` in ``.bumpversion.cfg`` now works correctly. Previously it was silently ignored, causing GPG signing attempts to fail.

.. code-block:: ini

    [bumpversion]
    sign_tags = False

Fixes `#269 <https://github.com/c4urself/bump2version/issues/269>`_.

-----------

Full Config Reference
---------------------

.. code-block:: ini

    [bumpversion]
    current_version = 1.0.0
    commit = True
    tag = True
    sign_tags = False
    message = Version Updated: {current_version} -> {new_version} [skip ci]
    tag_name = v{new_version}
    tag_message = Release {new_version}
    commit_args =
    ignore_missing_version = False
    extra_files =
    push = True                   # False: commit and tag, but don't push
    replace_all = True            # False: bump only the first match in each file
    allow_dirty = False

    [bumpversion:file:package.json]
    search = "version": "{current_version}"
    replace = "version": "{new_version}"

bump2v looks for its config in this order and uses the first it finds: ``--config-file``, ``$BUMP2V_CONFIG``, ``.bumpversion.cfg``, ``.bumpversion.toml``, ``pyproject.toml`` with a ``[tool.bumpversion]`` table, ``setup.cfg``.

TOML config
~~~~~~~~~~~

``.bumpversion.toml`` and ``pyproject.toml`` use the ``[tool.bumpversion]`` table (the same format as bump-my-version):

.. code-block:: toml

    [tool.bumpversion]
    current_version = "1.0.0"
    commit = true
    tag = true

    [[tool.bumpversion.files]]
    filename = "pyproject.toml"
    search = 'version = "{current_version}"'
    replace = 'version = "{new_version}"'
    replace_all = false

bump2v updates ``current_version`` by editing that one line, so comments and formatting stay. Options it doesn't support (hooks, ``regex``, ...) are reported and ignored.

-----------

Tips
----

Remove all local tags if you need to reset:

.. code-block:: zsh

    git tag -l | xargs -n 1 git tag -d

-----------

Contributors
------------

Maintained and extended by `@maimul <https://github.com/maimul>`_.

Built on top of `bump2version <https://github.com/c4urself/bump2version>`_ by Christian Verkerk.
