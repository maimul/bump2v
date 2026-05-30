#!/usr/bin python3
import subprocess 
import sys

# Hold up!
holdup = "Hold up!! 👮🚨"
thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"

def main():
    new_version = None  # Initialize new_version to avoid UnboundLocalError

    # Strip optional "bump" subcommand so both "bump2v patch" and "bump2v bump patch" work
    args = sys.argv[1:]
    if args and args[0].lower() == 'bump':
        args = args[1:]

    # Check the latest commit message
    latest_commit_message = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True, check=True).stdout.strip()

    # Define the prefix you want to check for
    prefix_to_check = "Version Updated:"
    prefix_to_check2 = "Bump version:"

    # Check for uncommitted changes
    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout:
        print(f"{holdup} Working directory is not clean. Please commit or discard changes before bumping the version. {thankyou}")
        exit(1)

    # Only reject if the commit is a CI-generated version bump (has [skip ci]) to avoid
    # false rejections when a version commit is fast-forward merged from another branch
    elif (latest_commit_message.startswith(prefix_to_check) or latest_commit_message.startswith(prefix_to_check2)) and "[skip ci]" in latest_commit_message:
        print(f"{holdup} Bump version rejected. 😿 There are no changes to the code.")
        exit(1)

    # Extract the next tag from bump2version dry-run
    try:
        dry_run_output = subprocess.run(["bump2version", "--dry-run", "--list", "--config-file", ".bumpversion.cfg"] + args, capture_output=True, text=True, check=True).stdout
        for line in dry_run_output.splitlines():
            if line.startswith("new_version="):
                new_version = line.split("=")[-1].strip()
    except subprocess.CalledProcessError:
        print(f"{holdup} Failed to run bump2v dry-run. Please check the following:\n"
              "- Ensure that '.bumpversion.cfg' is present and correctly configured. \n"
              "- Verify that the version part (e.g., major, minor, patch) is specified correctly.")
        exit(1)

    # Run bump2version
    try:
        subprocess.run(["bump2version"] + args, check=True)
        print(f"Yay! 😺🎉 Bump version accepted. {okay}")
    except subprocess.CalledProcessError:
        print(f"{holdup} Failed to bump the version. Please try the following: {thankyou}\n"
              "- Check your bump2v configuration.\n"
              "- Verify that the versioning arguments are correct (e.g., major, minor, patch).\n"
              "- Ensure your Git repository is in a valid state (no uncommitted changes).")
        exit(1)

    # Run git push --follow-tags
    try:
        subprocess.run(["git", "push", "--follow-tags"], check=True)
        print(f"Yay! 😺🎉 Push successful. {okay}")
    except subprocess.CalledProcessError:
        print(f"{holdup} Failed to push changes to the remote repository. Please push manually. {thankyou}")
        exit(1)
        
if __name__ == "__main__":
    main()
