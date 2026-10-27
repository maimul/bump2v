# TRACKER archive

Finished items moved out of [TRACKER.md](TRACKER.md), verbatim, newest first. Not read at session start.

## Done
- T-026 2026-10-26 1.9.0 (`auto` reads a merge commit's PR title) and 1.9.2 (outputs on a [skip ci] tip; explicit UTF-8). 1.9.1 never published. Detail: [TRACKER-NOTES.md](TRACKER-NOTES.md#t-026) sync: —
- T-025 2026-10-26 1.8.2 on PyPI: `auto` ignores tags when tag = False (it had counted from tags left over from before tagging was turned off and planned a major bump). Tests, Action (3 OSes) and publish green. sync: —
- T-009 2026-10-26 Team pilot: all 13 pin PRs (`bump2v>=1.6.2,<2`) open and mergeable; the round-2 pilot PR (move one pipeline to the Action) is open too. Merging is the team's call. sync: —
- T-018 2026-10-26 Removed the unused PyPI token secret, `PYPI_USERNAME` variable and `PYPI_API_TOKEN` environment; only the `pypi` environment (Trusted Publishing) remains. sync: —
- T-022 2026-10-26 1.8.0/1.8.1 on PyPI: `--sync`, `--retry`, `--github-output`, `show` fails on a missing value, the GitHub Action; 1.8.1 fixes Windows (git output decoded as UTF-8, init paths with /). Action verified on Linux, macOS and Windows; tests now gate publishing on all three OSes. sync: —
- T-019 2026-10-26 1.7.1 on PyPI: branch and tag pushed atomically, so a rejected push leaves no orphan tag (`4572d22`; test fails on the old code). sync: —
- T-008 2026-10-26 Team pipeline audit (dev/stg/prod): failures came from how pipelines call bump2v (push races, non-atomic tag push, missing config, branch rules), not from bump2v; no pipeline parses its output. Report kept outside this public repo. sync: —
- T-012 2026-10-26 1.7.0 on PyPI (wheel + sdist, requires-python >=3.11): plan/release/show/check/init, `--json`, exit codes, `--no-push`, TOML config, safer file edits, `auto` by tag_name or version commit. Installed fresh on 3.15 and run. sync: —
- T-010 2026-10-26 Published 1.7.0 through Trusted Publishing (run 40291785502); PyPI shows a provenance attestation from `pypi-publish.yml`. sync: —
- T-007 2026-10-26 1.6.2 on PyPI: never pushes on `--dry-run`/no commit (`3cea284`), runs on Python 3.15 (`sre_constants` removed, `6e71693`). sync: —
- T-002 2026-10-26 `test.yml` green on 3.10–3.15 × ubuntu/macos/windows (run 40285273117); CLAUDE.md corrected. sync: —
- T-011 2026-10-26 Scratch notebook removed; local builds no longer ship the `bump2version/` clone (`b95315e`). sync: —
- T-001 2026-10-26 Version files synced to 1.6.1 (a251bc9); the core dry-run now previews 1.6.2. sync: —
- T-006 2026-10-26 Research notes in docs/research/, roadmap in docs/ROADMAP.md. sync: —
- T-004 2026-10-26 GitHub repo description, PyPI homepage link and topics set. sync: —
- T-005 2026-06-21 1.6.1 published on PyPI (confirmed via the PyPI API on 2026-10-26). sync: —
