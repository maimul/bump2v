# Making a CLI agent-friendly: design requirements, distribution channels and agent behaviour (researched October 2026)

Notes on evidence: most items come from pages that were fetched. Items marked *(snippet)* come from search-result summaries only; the page was not opened. Two Codex docs URLs on developers.openai.com permanently redirect to learn.chatgpt.com; the URL that actually served the content is cited.

## 1. CLI design guidance for agent consumers

### Takeaway
clig.dev already covers the basics: `--json`, stdout for data and stderr for messages, prompting only on a TTY, `--no-input`, `NO_COLOR`, `--dry-run`, and `--force`/`--confirm`. It never mentions AI agents. Writing from 2026 adds:
- typed errors,
- a separate exit code for each failure type,
- treating output as a stable contract,
- a flag that turns off prompts, plus offline documentation built into the CLI.

### Cited Findings
- clig.dev rules ([clig.dev](https://clig.dev/)):
  - "Send output to stdout", "Send messaging to stderr".
  - "Return zero exit code on success, non-zero on failure", and map non-zero codes to the most important failure modes.
  - "Only use prompts… if stdin is an interactive terminal"; "Never *require* a prompt"; under `--no-input`, fail and name the flag to pass.
  - Turn colour off when the stream is not a TTY, when `NO_COLOR` is set, when `TERM=dumb`, or when `--no-color` is passed.
  - `-n/--dry-run` should "describe the changes that would occur".
  - Dangerous actions: interactive y/yes, otherwise `-f/--force`; for severe actions, `--confirm="name"`.
  - "Lead with examples" in help; errors should be rewritten for humans and suggest a next step.
  - Operations should be idempotent and recoverable.
  - No mention of agents or LLMs. It does not say to drop emoji outside a TTY.
- Speakeasy, 5 Feb 2026 ([Speakeasy](https://www.speakeasy.com/blog/engineering-agent-friendly-cli)):
  - Agents can't answer interactive prompts. Speakeasy added `--skip-interactive`/`--non-interactive`, which use defaults or fail fast.
  - Also added `--output json` and `--quiet`.
  - Non-interactive mode prints INFO/WARN lines and a summary count.
- Enyioha ([dev.to](https://dev.to/uenyioha/writing-cli-tools-that-ai-agents-actually-want-to-use-39no); the page shows "Feb 27" with no year). Practitioner advice, not a standard:
  - "Stdout is your API contract."
  - Keep JSON flat with consistent types; use JSON Lines for streams.
  - Suggested exit codes: 0 ok, 1 general, 2 usage, 3 not found, 4 permission, 5 conflict.
  - Errors carry a machine-readable code, echo the input, suggest a next step, and say whether a retry may work.
  - `--dry-run` returns structured output.
  - Provide `--yes`/`--no-confirm`/`--force`; if stdin is not a TTY, either skip the prompt or fail with a message naming the bypass flag.
  - Prefer declarative `ensure`/`apply`/`sync` verbs; return a separate code when a command can't be idempotent.
- Plivo CLI is "built for AI coding agents": stable JSON in and out, one error shape, exit codes to branch on, `--dry-run`, and a hard `--yes` gate on anything that spends money ([Plivo docs](https://docs.plivo.com/docs/cli/agents)) *(snippet)*.
- Zaparoo `--agent` implies compact JSON, caps arrays at 50 items, and defaults to a `read-only` policy ([Zaparoo CLI output contract](https://cdn.jsdelivr.net/npm/@zaparoo/cli@2.0.0/docs/cli-output.md)) *(snippet)*.
- Precedent for versioning output: Terraform JSON carries `format_version`. A minor bump means a backward-compatible addition, and consumers ignore unknown properties. A major bump is breaking, and consumers reject an unsupported major ([HashiCorp](https://developer.hashicorp.com/terraform/internals/json-format)).
- Detecting an agent:
  - Claude Code sets `CLAUDECODE=1` in Bash/PowerShell tool subprocesses, hooks and stdio MCP servers. IDE terminals set it too.
  - `CLAUDE_CODE_CHILD_SESSION=1` is set only by Claude Code itself ([Claude Code env vars](https://code.claude.com/docs/en/env-vars)).
  - Community detectors also check `AGENT`/`AI_AGENT` ([is-ai-agent](https://docs.rs/crate/is-ai-agent/0.4.0)) *(snippet)*.
  - agenthint recommends no spinners, pagers or prompts, and says detection is "advisory, not for auth/policy" ([agenthint](https://pypi.org/project/agenthint)) *(snippet)*.

### Inferences
- bump2v breaks almost every rule above: emoji prose on stdout, always pushing, and no JSON output.
- Whether output is plain or decorated should depend on TTY, `NO_COLOR` and `CLAUDECODE`, not on a hand-set flag alone. Emoji cost tokens and add parsing noise for an agent.

### Gaps
- No formal standard for agent-facing CLIs was found. The "Agent-Friendly CLI Spec v0.1" and the skill rubrics found are community-written.

## 2. Discovery channels

### Takeaway
- **Widest reach:** AGENTS.md. It is supported by about 24 tools and read natively by Claude Code when the repo has no CLAUDE.md.
- **For a task-triggered verb like "cut a release":** an Agent Skill (SKILL.md), which Claude Code, Codex and Copilot all read.
- **Gated:** Claude Code's two mechanisms that push a plugin at users. One needs an org admin allowlist; the other needs a listing in Anthropic's official marketplace.
- **Little direct effect:** MCP registry entries and llms.txt.

### Cited Findings
- AGENTS.md ([agents.md](https://agents.md/)):
  - Supported by Codex, Jules, Factory, Aider, goose, opencode, Zed, Warp, VS Code, Devin, Junie, Amp, Cursor, RooCode, Gemini CLI, Kilo Code, the Copilot coding agent, Windsurf, Augment and others.
  - Stewarded by the Agentic AI Foundation under the Linux Foundation; "used by over 60k open-source projects".
  - The nearest file wins.
- Claude Code reads `AGENTS.md` only when there is no CLAUDE.md/CLAUDE.local.md; otherwise CLAUDE.md files only, unless CLAUDE.md imports AGENTS.md. CLAUDE.md is "context, not enforced configuration" ([Claude memory docs](https://code.claude.com/docs/en/memory)).
- Copilot reads `.github/copilot-instructions.md`, path-scoped `*.instructions.md`, nested AGENTS.md, or a root CLAUDE.md/GEMINI.md. It also reads agent skills from the head branch for PR review ([GitHub Docs](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)).
- Claude Code skills ([Claude skills](https://code.claude.com/docs/en/skills)):
  - Follow the [Agent Skills](https://agentskills.io) standard.
  - Claude picks a skill from `description` plus `when_to_use`, truncated at 1,536 characters, so "put the key use case first".
  - `allowed-tools` pre-approves tools such as `Bash(git commit *)`.
  - Outside Claude Code only the spec fields are allowed: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
- Codex skills ([Codex skills](https://learn.chatgpt.com/docs/build-skills)):
  - Loaded from `.agents/skills` (repo and parents) and `$HOME/.agents/skills`.
  - Implicit invocation depends on `description`.
  - Installed with `$skill-installer`; plugins are recommended for distribution.
- Vercel evals on Next.js API knowledge (27 Jan 2026), [Vercel](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals):

  | Setup | Pass rate |
  |---|---|
  | Baseline (no docs) | 53% |
  | Skill, default | 53% (never invoked in 56% of cases) |
  | Skill with explicit instruction | 79% |
  | AGENTS.md docs index | 100% |

  The authors still say skills suit "specific, user-triggered tasks". They advise maintainers to ship an AGENTS.md snippet users can paste.
- Speakeasy moved from a Claude-specific plugin to tool-agnostic skills installed with `npx skills add`, and ships offline documentation through a `speakeasy agent` subcommand ([Speakeasy](https://www.speakeasy.com/blog/engineering-agent-friendly-cli)).
- Vercel's docs recommend its plugin for Claude Code and Cursor, and `npx skills add vercel-labs/agent-skills` for other agents ([Vercel docs](https://vercel.com/docs/get-started)) *(snippet; launch date and star counts in secondary sources disagree)*.
- Claude Code plugins ([marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)):
  - Any git repo with `.claude-plugin/marketplace.json` works; users run `/plugin marketplace add owner/repo`.
  - `claude plugin validate` checks it.
  - Anthropic runs an official directory for submissions.
- Relevance signals ([relevance](https://code.claude.com/docs/en/plugins/relevance)):
  - Signals are `cwd`, `cli`, `filesRead` and `manifestDeps`.
  - Suggestions appear only after an admin adds the marketplace to `pluginSuggestionMarketplaces` in managed settings.
  - The `cli` signal records only the first command, so `cd x && bump2v` records `cd`.
- The `<claude-code-hint v="1" type="plugin" value="name@claude-plugins-official" />` line on stderr, gated on `CLAUDECODE` ([cli-hints](https://code.claude.com/docs/en/plugins/cli-hints)):
  - Works only for official-marketplace plugins.
  - Only in interactive local sessions with analytics on.
  - One prompt ever per plugin.
- MCP registry ([registry docs](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/package-types.mdx)):
  - `server.json` with `registryType: "pypi"` and stdio transport.
  - A PyPI package is verified by `<!-- mcp-name: io.github.user/server -->` in the README.
  - The registry is a metadata catalogue that aggregators pull from; it isn't meant for AI apps to query directly ([StackOne](https://www.stackone.com/blog/mcp-registry-how-to-get-listed)) *(snippet)*.
- llms.txt (Jeremy Howard, v2 as of Aug 2026) needs only an H1, plus a blockquote, H2 link lists and an "Optional" section. It proposes `.md` versions of pages but never mentions `llms-full.txt`, and does not say any provider consumes it ([llmstxt.org](https://llmstxt.org/)).

### Inferences
- For "release", "bump the version" or "cut a release", the strongest open channels are:
  1. A short AGENTS.md/CLAUDE.md snippet that `bump2v init` writes into the repo's existing file.
  2. A SKILL.md using only the spec fields, published in a GitHub repo so it installs through `npx skills add`, `.claude/skills` and `.agents/skills`.
  3. A self-hosted Claude marketplace.
- Release requests are user-triggered, which is where Vercel says skills work, so ship both.

### Gaps
- No data found showing which channel actually drives installs of a CLI.
- Cursor's and Gemini CLI's own rule formats beyond their AGENTS.md support were not researched.

## 3. Safety for agents

### Takeaway
Agent hosts block force-push and history rewrites but allow ordinary pushes, and their shell permission rules can't see a push that happens inside another program. bump2v must gate push, tag and publish itself.

### Cited Findings
- Claude Code auto mode ([permission-modes](https://code.claude.com/docs/en/permission-modes)):
  - Blocks force push, `git reset --hard`, `git commit --amend` on a commit from before the session, and "irreversibly destroying files".
  - Allows "Pushing to any branch… including the default branch".
  - Tags are not mentioned.
- Claude Code permissions ([permissions](https://code.claude.com/docs/en/permissions)):
  - Order is deny, then ask, then allow.
  - `Bash(git push *)` doesn't match `git -C . push`; a rule "isn't a security boundary around the program".
  - "Put the `*` after the subcommand"; the docs warn about allow rules with a wildcard before it.
  - Deny and ask rules apply to every part of a compound command.
- Hard blocks belong in a PreToolUse hook, not in CLAUDE.md ([memory docs](https://code.claude.com/docs/en/memory)).
- Codex workspace-write leaves the network off by default and asks before networked commands ([Codex approvals](https://developers.openai.com/codex/agent-approvals-security)) *(snippet; the sandboxing page fetched didn't confirm this)*. Codex "Rules let you allow, prompt, or forbid command prefixes" ([Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing.md)).

### Inferences
- A user who denies `git push` but allows `Bash(bump2v *)` gets pushes they meant to block. Make push opt-in.
- Pre-approval rules match command prefixes, so put each risk level on its own subcommand: `bump2v plan` (read-only), `bump2v bump` (local commit and tag), `bump2v release --push --yes`. Users can then allow `Bash(bump2v plan *)` and set `bump2v release` to ask.
- In Codex the push will likely fail or prompt. Separate exit codes let the agent report "committed and tagged locally; push needs approval".
- Never force-push, never move or overwrite an existing tag, and never amend.

### Gaps
- How Codex treats `git tag` and `.git` writes is unconfirmed.
- Permission models for Cursor, Aider, Devin and Gemini CLI were not researched.

## 4. How agents bump versions without a dedicated tool

### Takeaway
The documented failures are drift between files. No direct primary evidence was found of what agents run when told to bump a version.

### Cited Findings
All five reports below are search snippets *(not opened)*:
- `marketplace.json` was not bumped alongside `package.json`, so Claude Code never saw the new release ([switchbot #68](https://github.com/OpenWonderLabs/switchbot-openapi-cli/issues/68)).
- Nothing checks that `plugin.json` and `package.json` agree, so drift is silent ([loupe #46](https://github.com/dabowman/loupe/issues/46)).
- Lockfiles stayed at 0.1.8 through every release ([dialoguebranch PR #314](https://github.com/dialoguebranch/platform/pull/314)).
- `.claude-plugin` metadata drifted from `package.json` ([cortex-agent #50](https://github.com/Kucell/cortex-agent/issues/50)).
- `npm ci` fails when package.json and the lockfile mismatch ([infrahub-docs #195](https://github.com/opsmill/infrahub-docs/issues/195)).
- uv added pre-release bump kinds to `uv version --bump` (alpha, beta, rc, post, dev) in July 2025 ([uv commit](https://app.semanticdiff.com/gh/astral-sh/uv/commit/042df4a7de85a4732c40e4583c357f83f27d1ba7)) *(snippet)*. Agents in Python repos have a built-in alternative, but it covers only pyproject.toml.

### Inferences
- Agents most likely hand-edit one manifest and miss the lockfile, the second manifest or the plugin metadata.
- A `check` command that reads every configured file and fails with a drift exit code is bump2v's most distinctive offer.

### Gaps
- No transcripts or studies found of what Claude Code or Codex do with "bump the version", and no data on agents using `npm version`.

## 5. Dev tools marketed as agent-first

### Cited Findings
- Speakeasy: non-interactive flags, `speakeasy agent` offline docs, skills ([Speakeasy](https://www.speakeasy.com/blog/engineering-agent-friendly-cli)).
- Plivo: an agent-first CLI ([Plivo](https://docs.plivo.com/docs/cli/agents)) *(snippet)*.
- Playwright: the CLI README says the CLI with skills suits coding agents better than MCP ([playwright-cli README](https://glama.ai/mcp/servers/@microsoft/playwright-mcp/blob/cd9819d0e885bbfed879b7316a088ab369a2a21f/packages/playwright-cli/README.md)) *(snippet)*. Checkly disputes the token-cost gap ([Checkly](https://www.checklyhq.com/blog/mcp-vs-cli-token-efficiency/)) *(snippet)*.
- Stripe: "Stripe Projects" lets agents provision services from the CLI ([Supabase blog](https://supabase.com/blog/supabase-joins-the-stripe-projects-developer-preview)) *(snippet)*.
- Vercel: a Claude Code/Cursor plugin plus skills.sh ([Vercel docs](https://vercel.com/docs/get-started)) *(snippet)*.
- Release-automation skills exist (semantic-release, release-please, changesets) but have 5 to 192 installs ([Skillselion](https://skillselion.com/category/releases)) *(snippet, third-party counts)*.

### Gaps
- No confirmed CLI with a built-in `tool mcp` subcommand was found. gh, Stripe CLI, uv and Biome are unverified.

## 6. Machine-readable introspection

### Cited Findings
- Help that leads with examples, plus suggested corrections for typos ([clig.dev](https://clig.dev/)).
- Offline, step-by-step docs inside the CLI ([Speakeasy](https://www.speakeasy.com/blog/engineering-agent-friendly-cli)).
- A versioned schema contract ([Terraform](https://developer.hashicorp.com/terraform/internals/json-format)).

### Inferences
- `bump2v show --json` (config, files, current version), `bump2v schema` (JSON Schema of the output), `bump2v check`/`doctor`, and `bump2v init` that detects package.json or pyproject.toml are reasonable additions.

### Gaps
- No direct sources found for `doctor`, `init`, `schema` or shell completions as agent features.

## Prioritised requirements checklist

**P0: safety and machine contract**
1. Nothing goes over the network by default: push only with `--push`, and require `--yes` when stdin isn't a TTY. Never `--force`, never move an existing tag, never amend.
2. Separate the risk levels into subcommands (`plan`, `bump`, `release`) so prefix allow and deny rules work in Claude Code and Codex.
3. Add `--json` (and JSON Lines for progress), with a `format_version` field following Terraform's minor/major rules. Return old/new version, files changed, commit SHA, tag, and pushed true/false.
4. Document exit codes, for example: 0 ok, 2 usage, 3 dirty tree, 4 file drift or version not found, 5 tag already exists, 6 push failed or needs network.
5. Make `--dry-run`/`plan` print the full diff as JSON and write nothing.
6. When stdout isn't a TTY, or `NO_COLOR`/`CLAUDECODE` is set, print plain text with no emoji, colour or spinners. Data goes to stdout, messages to stderr.
7. Never prompt when stdin isn't a TTY: fail fast and name the flag. Errors carry `code`, `message`, `hint` and `retryable`.

**P1: discovery and correctness**
8. Add `bump2v check`, which fails on version drift across configured files, lockfiles and plugin manifests.
9. Add `bump2v init`, which detects the stack, writes the config, and adds a 3–5 line release snippet to the repo's existing AGENTS.md or CLAUDE.md.
10. Ship a SKILL.md using only the spec fields. The description should open with "release / bump version / cut a release", and the skill should run `plan` before `release`. Publish it in a public GitHub repo so it installs through `npx skills add`, `.claude/skills` and `.agents/skills`.
11. Make `--help` lead with examples, document the exit codes and JSON fields, and add `show --json` and `schema`.

**P2: reach**
12. Host a Claude plugin marketplace repo and submit to Anthropic's directory. If accepted, emit `<claude-code-hint>` only when `CLAUDECODE` is set.
13. Publish a PyPI MCP server entry (README `mcp-name` line plus `server.json`) and a Codex plugin.
14. Add llms.txt to the docs site (low evidence it helps).
