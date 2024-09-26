#!/usr/bin python3

import subprocess 
import sys

# Hold up!
holdup = "Hold up!! 👮🚨"
thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"

def tag_exists(tag):
    """Check if the tag already exists in Git."""
    existing_tags = subprocess.run(["git", "tag"], capture_output=True, text=True).stdout.splitlines()
    return tag in existing_tags

def main():
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
        print(f"{holdup} Tag '{new_version}' already exists. Please update the version number manually. {thankyou}")
        exit(1)

    # If no tag exists, run bump2version
    print(f"{okay} Tag '{new_version}' does not exist. Proceeding with bump2version.")
    subprocess.run(["bump2version"] + [arg for arg in sys.argv[1:]])
    print(f"Yay! 😺🎉 Bump version accepted. {okay}")

    # Run git push --follow-tags
    subprocess.run(["git", "push", "--follow-tags"])
    
if __name__ == "__main__":
    main()
