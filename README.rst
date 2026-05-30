bump2v
======

A CLI wrapper and native fork of `bump2version <https://github.com/c4urself/bump2version>`_ for automated semantic versioning. Bumps version numbers across files, commits, tags, and pushes — all in one command.

.. code-block:: zsh

    pip install bump2v

-----------

How it works
------------

bump2v reads your current version from a config file, increments it, rewrites it in every file you specify, commits the change, creates a git tag, and pushes — all in one command. The **source of truth for the version** lives in your project's main file:

+------------------------------+-------------------------------------------------+
| Stack                        | Source of truth                                 |
+==============================+=================================================+
| Node.js / React / JS         | ``package.json`` → ``"version": "1.0.0"``       |
+------------------------------+-------------------------------------------------+
| Python                       | ``appInfo.py`` → ``__version__ = "1.0.0"``      |
+------------------------------+-------------------------------------------------+
| Any other file               | Configurable via ``.bumpversion.cfg``           |
+------------------------------+-------------------------------------------------+

The ``.bumpversion.cfg`` file tells bump2v where to find and update that version string. **You only need to run bump2v — never edit the version manually.**

-----------

Quick Start
-----------

**Step 1:** Make your code change.

**Step 2:** Stage and commit.

.. code-block:: zsh

    git add .
    git commit -m "fix: describe your change here"

**Step 3:** Bump the version and push.

.. code-block:: zsh

    bump2v patch   # 1.0.0 → 1.0.1  (bug fix)
    bump2v minor   # 1.0.0 → 1.1.0  (new feature)
    bump2v major   # 1.0.0 → 2.0.0  (breaking change)

Alternative command aliases: ``bumptydumpty``, ``versionkaboom``

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
    message = Version Updated: {current_version} → {new_version} 🚀 [skip ci]

    [bumpversion:file:package.json]
    search = "version": "{current_version}"
    replace = "version": "{new_version}"

The ``current_version`` in ``.bumpversion.cfg`` must always match the ``"version"`` field in ``package.json``. bump2v keeps them in sync automatically — never edit either one by hand.

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
        version=f"🏭 Prod:{__version__}",
    )

``.bumpversion.cfg``:

.. code-block:: ini

    [bumpversion]
    current_version = 1.0.0
    commit = True
    tag = True
    message = Version Updated: {current_version} → {new_version} 🚀 [skip ci]

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

+----------------+------------------+----------------------------------+
| Command        | Example          | When to use                      |
+================+==================+==================================+
| bump2v patch   | 1.0.0 → 1.0.1   | Bug fixes, minor improvements    |
+----------------+------------------+----------------------------------+
| bump2v minor   | 1.0.0 → 1.1.0   | New backward-compatible features |
+----------------+------------------+----------------------------------+
| bump2v major   | 1.0.0 → 2.0.0   | Breaking changes                 |
+----------------+------------------+----------------------------------+

-----------

Advanced Flags
--------------

``--tag-only`` — Tag without bumping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tags the current HEAD using ``current_version`` from config, without bumping or committing. Useful when you need to commit a build artifact between the version bump commit and the release tag.

.. code-block:: zsh

    bump2v patch --no-tag       # bump + commit, skip the tag
    # ... build artifact, git add, git commit ...
    bumpversion --tag-only      # tag HEAD now

Fixes `#256 <https://github.com/c4urself/bump2version/issues/256>`_.

``--ignore-missing-version`` — Skip files without a version string
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using glob patterns, some files may not contain the version string. Instead of crashing, bump2v logs a warning and skips those files.

.. code-block:: zsh

    bump2v patch --ignore-missing-version

Or set it permanently in config:

.. code-block:: ini

    [bumpversion]
    ignore_missing_version = True

Fixes `#267 <https://github.com/c4urself/bump2version/issues/267>`_.

``--extra-files`` — Include generated files in the bump commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    current_version = 1.0.0       # must match the version in your source of truth file
    commit = True
    tag = True
    sign_tags = False
    message = Version Updated: {current_version} → {new_version} 🚀 [skip ci]
    tag_name = v{new_version}
    tag_message = Release {new_version}
    commit_args =
    ignore_missing_version = False
    extra_files =

    [bumpversion:file:package.json]
    search = "version": "{current_version}"
    replace = "version": "{new_version}"

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
