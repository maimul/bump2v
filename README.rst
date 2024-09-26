Quick Start | How to Setup/Run
================================

For first-time users, please download the `bump2v <https://pypi.org/project/bump2v/>`_ package as shown below:

.. code-block:: zsh

    pip install bump2v

---------------------------

**Step 1:** Make a Code Change

**Step 2:** Stage and Commit the Changes

You may stage and commit using the GUI method or the command line as shown below:

.. code-block:: zsh

    git add .
    git commit -m "Describe your changes here"

**Step 3:** Assign the Tag 🏷️ and Push to GitHub

**Example:**

.. code-block:: zsh

    bump2v patch

.. code-block:: zsh

    bump2v minor

.. code-block:: zsh

    bump2v major

- **v0.0.1** 👈🏻 **Patch Version:** This is typically reserved for bug fixes or minor improvements that are backward-compatible with the existing features.
- **v0.1.0** 👈🏻 **Minor Version:** Reflects smaller, backward-compatible enhancements and features added to the software.
- **v1.0.0** 👈🏻 **Major Version:** Indicates significant, potentially backward-incompatible changes to the software.

**Note:** _Always use 'v' before the version number._ **vX.X.X** This type of versioning is called Semantic Versioning (SemVer).
To learn more about Semantic Versioning, `click here <https://www.geeksforgeeks.org/introduction-semantic-versioning/>`_.

--------

For a new project, you need the following configuration:

**Step 1:** Create a **.bumpversion.cfg** file and an **appInfo.py** file.

**Step 2:** Populate the **.bumpversion.cfg** file with the data below:

.. code-block:: ini

    [bumpversion]
    current_version = 0.0.1
    commit = False
    tag = True
    TAG_NAME = {new_version}
    TAG_MESSAGE = "Release {new_version}: Changelog: {changelog}"

    [bumpversion:file:app/appInfo.py]  # <- location to your appInfo.py file. Example: app/appInfo.py or appInfo.py

**Step 3:** Populate **appInfo.py** with information about your app as shown below:

.. code-block:: python

    # File: app/appInfo.py
    app_name = "Your App Name"
    __version__ = "v0.0.1"  # Initial version, leave as it is.
    description = "Describe your app here"
    tags_metadata = "tags metadata here"

**Step 4:** Import **appInfo.py** to your **main.py** and use the variables from **appInfo.py** to assign your version, app name, and description as shown below:

.. code-block:: python

    from appInfo import __version__, app_name, description, tags_metadata
    from fastapi import FastAPI

    app = FastAPI(
        title=app_name,
        description=description,
        version=f" 🏭 Prod:{__version__} ",
        openapi_tags=tags_metadata
    )

PS. 👾 **Fun Tip:** 👾 You can use alternative commands like **versionkaboom**, **bismillah**, or **bumptydumpty** instead of bump2v.

**Example:**

.. code-block:: zsh

    versionkaboom patch

.. code-block:: zsh

    bismillah patch

.. code-block:: zsh

    bumptydumpty patch

This release of the `bump2v` package brings a set of enhancements, bug fixes, and new features aimed at improving functionality and user experience. The version is deemed production-ready.

## Readiness for Production

This version has undergone thorough testing and is considered stable for production use.

## Upgrade Instructions

If you are upgrading from a previous version, please follow the upgrade instructions in the `documentation <link-to-docs>`_.

## Contributors

This package is built on top of Bump2version. A sincere thank you to all contributors who participated in making this release possible.
