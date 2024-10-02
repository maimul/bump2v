# Quick Start | How to setup/run

For first time user, please download [bump2v](https://pypi.org/project/bump2v/) package as shown below 👇🏻
```zsh
pip install bump2v
```

## For new project you need these following configuration

**Step 1:** Create a **.bumpversion.cfg** file and **appInfo.py** file

**Step 2:** Populate the file **.bumpversion.cfg** with these data below 👇🏻
```
[bumpversion]
current_version = 0.0.1
commit = False
tag = True
TAG_NAME = {new_version}
TAG_MESSAGE = "Release {new_version}: Changelog: {changelog}"

[bumpversion:file:app/appInfo.py]  # <- location to your appInfo.py file. Example: app/appInfo.py or appInfo.py
```
**Step 3:** Populate **appInfo.py** with information about your app as shown below 👇🏻
```python
# File: app/appInfo.py 
app_name = "Your App name"
__version__ = "v0.0.1" # Initial version then leave as it is. 
description = "Describe your app here"
tags_metadata = "tags metadata here"
```
**Step 4:** Import **appInfo.py** to your **main.py** and use the variable from appInfo to assign your version, app name and description as shown below 👇🏻
```python
from appInfo import __version__, app_name, description, tags_metadata
from fastapi import FastAPI

app = FastAPI(
    title=app_name,
    description=description,
    version=f" 🏭 Prod:{__version__} ",
    openapi_tags=tags_metadata
)
```

---------------------------

**Step 1:** Make a Code Change

**Step 2:** Stage and Commit the Changes

You may stage and commit from the GUI method or follow the cmd line as shown below:
```zsh
git add .
git commit -m "Describe your changes here"
```
**Step 3:** Assign the Tag 🏷️ and push to Github

**Example:**
```zsh
bump2v patch
```
```zsh
bump2v minor
```
```zsh
bump2v major
```
- v0.0.**1͎** 👈🏻 **Patch Version:** The patch version is typically reserved for bug fixes or minor improvements that are backward-compatible with the existing features.
- v0.**0͎**.0 👈🏻 **Minor Version:** The minor version reflects smaller, backward-compatible enhancements and features added to the software.
- v**0͎**.0.0 👈🏻 **Major Version:** The major version indicates significant, potentially backward-incompatible changes to the software.

**Note📝:** _Always has v before the version number._ **vX.X.X** This type of versioning is called Semantic Versioning (also known as SemVer).
To learn more about Semantic Versioning, [click here](https://www.geeksforgeeks.org/introduction-semantic-versioning/).

--------


**PS. 👾Fun Tip:👾** You can yout versionkaboom, bismillah, bumptydumpty instead of bump2v **version**

_Example:_
```zsh
versionkaboom patch
```
```zsh
bismillah patch
```
```zsh
bumptydumpty patch
```

If there is issue with existing tag use this command to remove the tags and bump the version again
```zsh
git tag -l | xargs -n 1 git tag -d
```


This release of the `bump2v` package brings a set of enhancements, bug fixes, and new features aimed at enhancing functionality and improving the user experience. The version is deemed production-ready.

## Readiness for Production

This version has undergone thorough testing and is considered stable for production use.

## Upgrade Instructions

If you are upgrading from a previous version, please follow the upgrade instructions in the [documentation](link-to-docs).

## Contributors

This package is built on top of Bump2version. A sincere thank you to all contributors who participated in making this release possible.


