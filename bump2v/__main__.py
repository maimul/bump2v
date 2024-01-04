#!/usr/bin python3

import subprocess 
import sys

# Hold up!
holdup = "Hold up!! 👮🚨"
thankyou = "Thank you! 👾"
okay = "Okhay lessgo! 🚀🚀🚀"

def main():
    
    # Check for uncommitted changes
    if subprocess.run(["git", "status", "--porcelain"]).stdout:
        print(f"{holdup} Working directory is not clean. Please commit or discard changes before bumping the version. {thankyou}")
        exit(1)

    # Check the latest commit message
    latest_commit_message = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True).stdout.strip()

    # Define the prefix you want to check for
    prefix_to_check = "Version Updated:"

    # Check if the latest commit message starts with the specified prefix
    if latest_commit_message.startswith(prefix_to_check):
        print(f"{holdup} Bump version rejected. 😿 There are no changes to the code.")
        exit(1)
    else:
        print(f"Yay! 😺🎉 Bump version accepted. {okay}")

    # Run bump2version
    subprocess.run(["bump2version"] + [arg for arg in sys.argv[1:]])

    # Run git push --follow-tags
    subprocess.run(["git", "push", "--follow-tags"])

if __name__ == "__main__":
    main()