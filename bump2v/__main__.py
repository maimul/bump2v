#!/usr/bin/env python3

import subprocess
import sys
import os

# Hold up!
holdup = "Hold up!! 👮🚨"
thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"

def tag_exists(tag):
    print("Checking for existing tags 🏷️ ... ")
    tag = 'v' + str(tag)
    """Check if the tag already exists in Git."""
    existing_tags = subprocess.run(["git", "tag"], capture_output=True, text=True).stdout.splitlines()
    return tag in existing_tags

def create_github_config():
    # Create .github directory if it doesn't exist
    if not os.path.exists('.github'):
        print("Creating .github directory...")
        os.makedirs('.github')

    # Create .bumpversion.cfg file if it doesn't exist
    config_file_path = ".github/.bumpversion.cfg"
    if not os.path.exists(config_file_path):
        print("Creating .bumpversion.cfg file...")
        with open(config_file_path, 'w') as config_file:
            config_file.write(
                "[bumpversion]\n"
                "current_version = 1.1.2\n"
                "commit = True\n"
                "tag = True\n"
                "message = Version Updated: {current_version} → {new_version} 🚀\n\n"
                "[bumpversion:file:PATH to your config file in root DIR]\n"
            )
    else:
        print(".bumpversion.cfg already exists. Skipping creation.")

def main():
    # Create .github and .bumpversion.cfg if needed
    create_github_config()

    # Check the latest commit message
    latest_commit_message = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True).stdout.strip()

    # Define the prefix you want to check for
    prefix_to_check = "Version Updated:"
    prefix_to_check2 = "Bump version:"

    # Check for uncommitted changes
    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout:
        print(f"{holdup} Working directory is not clean. Please commit or discard changes before bumping the version. {thankyou}")
        exit(1)

    elif latest_commit_message.startswith(prefix_to_check) or latest_commit_message.startswith(prefix_to_check2):
        print(f"{holdup} Bump version rejected. 😿 There are no changes to the code.")
        exit(1)

    # Extract the next tag from bump2version dry-run
    dry_run_output = subprocess.run(["bump2version", "--dry-run", "--list"] + sys.argv[1:], capture_output=True, text=True).stdout
    for line in dry_run_output.splitlines():
        if line.startswith("new_version="):
            new_version = line.split("=")[-1].strip()
    
    # Check if the tag already exists
    if tag_exists(new_version):
        print(f"{holdup} Tag '{new_version}' already exists. Please check Github and update the version number manually. {thankyou}")
        exit(1)

    # Run bump2version with the correct config file path
    subprocess.run(["bump2version", "--config-file", ".github/.bumpversion.cfg"] + sys.argv[1:])
    print(f"Yay! 😺🎉 Bump version accepted. {okay}")

    # Run git push --follow-tags
    subprocess.run(["git", "push", "--follow-tags"])

if __name__ == "__main__":
    main()
