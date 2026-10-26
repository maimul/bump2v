# TRACKER notes

Detail for items in [TRACKER.md](TRACKER.md), by ID. Not read at session start; open the section for the item being continued.

## T-023

Team pilot, round 2: 12 pipelines moved to the Action (pinned to 1.9.2). In 11 first runs `auto` picked patch, commit and tag went out in one push, the build checked out the version commit, and the deploy recorded the matching image tag.

## T-026

1.9.0 (`auto` classifies a merge commit by its PR title, from a real-history check: up to two-thirds of team PR titles are conventional) and 1.9.2 (outputs written when HEAD is a [skip ci] version commit; tests use explicit UTF-8 and CI fails on default encodings). 1.9.1 was blocked by the pre-publish gate on a Windows-only test bug and never published.
