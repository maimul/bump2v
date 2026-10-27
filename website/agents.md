# AI coding agents

An agent that edits version numbers by hand forgets one: the lockfile, the plugin manifest,
the `__version__` in a second package. bump2v gives it one command for the whole release and
a way to look before it acts.

## Tell the agent

```sh
bump2v init --agents
```

adds a **Releasing** section to `CLAUDE.md`, or to `AGENTS.md` when there's no `CLAUDE.md`
(Codex, Cursor, Copilot and others read `AGENTS.md`):

```markdown
## Releasing

Versions are managed by bump2v (.bumpversion.cfg). Never edit version numbers by hand.

- Preview: `bump2v plan auto` (add `--json` for a machine-readable plan). Changes nothing.
- Release: `bump2v release auto` bumps every configured file, commits, tags and pushes.
  Add `--no-push` to keep it local. Commit your work first: a dirty tree is refused.
- Check: `bump2v check` fails with exit 4 when a file has drifted from the current version.
- Exit codes: 0 ok, 3 dirty tree, 4 version not found, 5 tag exists, 6 push failed,
  7 nothing to release.
```

## Let it look, ask before it pushes

The commands are split by risk, so permission rules can tell them apart. In Claude Code's
`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(bump2v plan *)", "Bash(bump2v show *)", "Bash(bump2v check *)"],
    "ask": ["Bash(bump2v release *)"]
  }
}
```

| Command | Changes |
|---|---|
| `bump2v plan`, `show`, `check` | Nothing |
| `bump2v release <part> --no-push` | Files, a commit and a tag, locally |
| `bump2v release <part>` | The same, then pushes |

## What the agent reads back

- `--json` puts one object on stdout (`current_version`, `new_version`, the files and match
  counts, the commit, the tag, whether it pushed), and messages go to stderr. Failures carry
  `error.code`, `error.message`, `error.hint` and `error.retryable`.
- Exit codes say what went wrong without parsing text: 3 dirty tree, 4 version not found or a
  file drifted, 5 tag exists, 6 push failed, 7 nothing to release.
- Output is plain text, without emoji, when it isn't going to a terminal or when `NO_COLOR`,
  `CI` or `CLAUDECODE` is set. bump2v never prompts.

The JSON shape and every field are in the
[README](https://github.com/maimul/bump2v#exit-codes-and-json-output).

## Catch hand edits anyway

The [pre-commit hook](https://github.com/maimul/bump2v#pre-commit-hook) runs `bump2v check` on
every commit, so a version edited by hand in one file is refused before it reaches the branch,
whoever made the commit.
