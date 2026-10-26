# bump2v adoption playbook: OSS launch, developer marketing, internal rollout and SEA events (as of 26 Oct 2026)

Reddit and PyPI pages could not be fetched. Dates that could not be confirmed are marked **[unconfirmed]**.

## 1. How CLI dev tools grew from zero

### Takeaway
Each documented breakout came from one concrete, checkable claim against a tool people already used: a benchmark, a compatibility score, or "drop-in for X". It was then amplified by Hacker News or GitHub Trending. A Hacker News front page is worth hundreds of stars, not thousands.

### Cited Findings
- **Ruff.** It launched on 30 Aug 2022 as a blog post, "Python tooling could be much, much faster". The post benchmarked against CPython: about 150x faster than Flake8, 300–500 ms against about 75 s. It was framed as an experiment and "not a drop-in replacement". An editor's note later lists adopters: FastAPI, Bokeh, Zulip and Pydantic. — [crmarsh](https://notes.crmarsh.com/python-tooling-could-be-much-much-faster)
- **uv.** Launched 15 Feb 2024 as "a drop-in replacement for pip and pip-tools workflows". It claimed 8–10x faster than pip cold and 80–115x with a warm cache. Its `uv pip` interface needs zero configuration, and the post promised a migration path from Rye. — [Astral](https://astral.sh/blog/uv)
  - It hit #1 on GitHub Trending on 17 Feb 2024, two days after launch. — [Trendshift](https://trendshift.io/repositories/7901)
  - Downloads: about 1.95B total and about 191M in the last 30 days. — [pepy](https://pepy.tech/projects/uv)
  - Stars: about 80.7k around March 2026, from a third-party snapshot. — [OSS Insight](https://ossinsight.io/analyze/astral-sh/uv)
- **Biome.** Christopher Chedeau, a Prettier creator, put up a bounty on Algora. Biome claimed it on 27 Nov 2023 (v1.4.0), raising Prettier compatibility from about 85% to over 96%. The same post mentions new sponsors and new maintainers. — [Biome](https://biomejs.dev/blog/biome-wins-prettier-challenge/)
  - The prize was $22,500 according to a secondary source only. — [reference.org](https://reference.org/facts/Open-source_bounty/QCySymhq)
- **Lazygit.** Early Reddit posts got "virtually zero" response, and a Hacker News post was the inflection point. The app asks users to star the repo, which the author openly calls self-interested. It passed 1M downloads by February 2025. — [Duffield](https://jesseduffield.com/Lazygit-5-Years-On/) (from search snippets)
  - It reached #1 on GitHub Trending on 25 Mar 2024. — [Trendshift](https://trendshift.io/repositories/1069)
- **Bun.** It had over 82k stars and over 7M monthly downloads when Anthropic acquired it in December 2025. — [Gigazine](https://gigazine.net/gsc_news/en/20251203-anthropic-acquired-bun)
- **The Hacker News effect.** A study of 138 AI-tool launches in 2024–25 found an average of +121 stars in 24 hours, +189 in 48 hours and +289 in a week. Posting time mattered. The "Show HN" label gave no advantage once other factors were controlled. — [arXiv 2511.04453](https://arxiv.org/abs/2511.04453v1)

### Inferences
- bump2v has no speed story. Its equivalent of a "benchmark" is a before/after demo: about 6 manual steps (edit files, commit, tag, push) become 1 command, including when an AI agent runs it.
- A Hacker News launch should be expected to bring roughly 100–300 stars. That is a credibility step, not a growth engine.

### Gaps
- No sourced inflection point found for changesets, git-cliff or zoxide. git-cliff shows only about 3.6k Homebrew installs a year. — [Homebrew](https://formulae.brew.sh/formula/git-cliff)
- No Hacker News metrics found for the Bun 1.0 launch.

## 2. Launch channels and their rules

### Takeaway
Hacker News and curated newsletters fit bump2v. Lobsters needs an invite and 70 days of history first. r/Python requires a fixed showcase format. There is no evidence that Product Hunt converts for open-source CLIs.

### Cited Findings
- **Show HN** — [HN rules](https://news.ycombinator.com/showhn.html)
  - It must be something people can try without signing up.
  - Landing pages, reading material and "routine feature releases and version updates" do not qualify.
  - Explain how and why you built it.
  - Never ask friends to upvote.
- **Lobsters** — [lobste.rs/about](https://lobste.rs/about)
  - Accounts come mainly through invitations.
  - Self-promotion should be under 25% of your stories and comments over the past year.
  - New users can't self-promote, and can't use the "show" tag, for their first 70 days.
- **r/Python** — [mirror](https://redlib.hbubli.cc/r/python+madeinpython/new)
  - Showcase posts use the headings "What My Project Does / Target Audience / Comparison".
  - **[Unconfirmed]:** the official rules page couldn't be fetched.
- **PyCoder's Weekly.** It accepts submissions of your own projects, but not every link is featured. — [pycoders.com/submit](https://pycoders.com/submit)
- **Console.dev.** It features 2–3 tools a week. It asks whether a tool is useful to developers, developer-first, self-serve, and something the reviewer would share. It does not sell sponsored reviews. — [Console](https://console.dev/selection-criteria)
- **Product Hunt.** GitHub CLI was #1 Product of the Day with 408 upvotes, but it had GitHub's brand behind it. — [hunted.space](https://hunted.space/product/github/launches/github-cli)
  - Shell GPT, a smaller open-source CLI, placed #26 with 65 upvotes. — [hunted.space](https://www.hunted.space/dashboard/cli-productivity-tool-powered-gpt-3/launches/shell-gpt)

### Gaps
- Submission rules for Python Weekly, TLDR, dev.to and awesome-lists were not verified.
- No data found on Product Hunt converting to stars or installs for open-source CLIs.

## 3. Repo signals that build trust

### Cited Findings
- A study of 1,950 READMEs found that popular projects tend to be well organised, with lists and images. Contribution guidelines and references were linked with higher popularity. — [arXiv 2206.10772](https://arxiv.org/abs/2206.10772v1)
- Across 14,901 Java repos, READMEs that follow GitHub's guidelines get more stars. — [Liu et al. 2022, catalogue record](https://katalog.hcu-hamburg.de/vufind/Search2Record/ELV007903707)
- Badges appear in 46% of npm packages (294,941 sampled). What the study found about popularity was not retrieved. — [Trockman et al., ICSE 2018](https://par.nsf.gov/servlets/purl/10063054)

### Inferences
- **README order:**
  1. One-line pitch
  2. Demo GIF made with VHS or asciinema
  3. `pipx install bump2v`
  4. 30-second quickstart
  5. Comparison table
  6. "Migrating from bump2version"
  7. "Using with AI agents"
  8. CONTRIBUTING and good-first-issues
- These are unsourced best practice: VHS/asciinema GIFs and OpenSSF Scorecard were not researched.

### Gaps
- No causal evidence found for badges or docs sites, and no Scorecard adoption data.

## 4. Positioning and naming

### Cited Findings
- **bump2version.** Its README says it is "no longer maintained" and points users to bump-my-version. It has 1.1k stars and no archive banner. — [GitHub](https://github.com/c4urself/bump2version)
- **bump-my-version.** A "maintained refactor of the bump2version fork". It adds pyproject.toml config and a click/rich CLI. — [PyPI](https://pypi.org/project/bump-my-version)
- **A Rust `bumpversion` crate** claims full compatibility with existing configs. — [docs.rs](https://docs.rs/crate/bumpversion/0.0.10)
- **Commitizen** already maps Conventional Commits to bumps (feat→MINOR, fix→PATCH) and updates files and changelogs. — [PyPI](https://pypi.org/project/commitizen/3.15.0)
- **bump2v vendors bump2version.** So existing `.bumpversion.cfg` files work unchanged. — this repo's `CLAUDE.md`

### Inferences
- **"Drop-in for bump2version configs" is the honest migration pitch.** The archived tool's own README sends its traffic to bump-my-version, so bump2v competes for the people who never moved.
- **Don't pitch it as "drop-in for bump-my-version".** That would be unverified, and bump2v uses a different config format.
- **What sets it apart is one command: bump, commit, tag, push, with guards.** `auto` mode alone is not unique, because Commitizen already does it.
- **The name helps search (people looking for "bump2version alternative") but hurts trust ("2v of a deprecated tool?").** Keep the name and lead with what it does, not its lineage.
- **Gap:** the PyPI page couldn't be read to check its summary and keywords.

## 5. Internal adoption

### Cited Findings
- **Spotify Golden Paths** began as a Hack Week project and are part of every new hire's onboarding. — [Spotify Eng](https://engineering.atspotify.com/2020/8/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem)
- **Backstage reached 99% voluntary adoption** after about a year of onboarding and promotion. Spotify credited incentives and treating the platform as a product. — [The New Stack](https://thenewstack.io/how-spotify-achieved-a-voluntary-99-internal-platform-adoption-rate/)
- **AGENTS.md is used by over 60k open-source projects.** About two dozen agents read it, including Codex, Cursor, Copilot's coding agent and Gemini CLI. It is stewarded under the Linux Foundation. — [agents.md](https://agents.md/)

### Inferences
- **Make bump2v the default in four places:**
  - the starter template every new repo is created from
  - a config file in each repo, using the stack's manifest (`package.json`, `pyproject.toml`, `appInfo.py`) as the source of truth
  - a "Releasing" section in each repo's CLAUDE.md/AGENTS.md that says to run `bump2v auto` and never hand-edit versions
  - a CI check that rejects version changes not made by bump2v
- **Measure it:**
  - share of repos with a config
  - share of release tags whose commit message matches bump2v's "Version Updated: X → Y" pattern (visible in this repo's own log)
  - releases per month

## 6. Events (Malaysia and SEA first)

| Event | Date / place | CFP status | Source |
|---|---|---|---|
| DevFest KL 2026 (15th year) | Sat 14 Nov 2026, Sunway University, Petaling Jaya | Speaker form mentioned in a search snippet; the page itself shows no CFP; schedule still "Stay Tune!" | [GDG](https://gdg.community.dev/events/details/google-gdg-kuala-lumpur-presents-devfest-kuala-lumpur-2026/) |
| DevFest KL 2025 (for scale) | 6–7 Dec 2025, APU; over 700 attendees | — | [APU](https://www.apu.edu.my/news/apu-alumni-returned-inspire-developers-devfest-gdg-kl-2025) |
| FOSSASIA Summit 2027 | 7–9 Mar 2027, True Digital Park West, Bangkok | **Open; deadline not listed.** Explicitly invites "open source project showcases" | [eventyay](https://eventyay.com/fossasia/summit2027/) |
| FOSSASIA: past deadline pattern | 2025 edition closed 22 Dec 2024, so expect about mid-to-late Dec 2026 **[inferred]** | 2026 formats: 5-min lightning, 15-min, 25-min | [DropTimes](https://www.thedroptimes.com/node/44870), [2026 CFP](https://dev.eventyay.com/ots/fossasia2026/cfp) |
| Docker Kuala Lumpur | Date "to be defined" | Closes 30 Dec 2026 (the page contradicts itself) | [Sessionize](https://sessionize.com/docker-kuala-lumpur/) |
| PyCon MY | Last confirmed: 1–2 Nov 2025, Sunway University | **No 2026/2027 info found** | [pycon.my](https://pycon.my/) |
| PythonAsia (formerly PyCon APAC) | 2026: 21–23 Mar, DLSU Manila | 2027 not found | [pretalx](https://pretalx.com/python-asia-2026/), [PSF Discuss](https://discuss.python.org/t/pycon-apac-2025-a-historic-transition-for-the-asian-python-community/83014) |
| PyCon Thailand 2027 | 18–19 Jun 2027, Bangkok | Not open yet | [Sessionize](https://sessionize.com/pycon-thailand-2027) |
| KCD Kuala Lumpur 2026 | 27 Jun 2026, already held **[date from a LinkedIn recap]** | — | [Humanitix](https://events.humanitix.com/kcd-kuala-lumpur-2026) |
| AWS Cloud & AI Day KL | 4 Nov 2026, KLCC (AWS-run event, not a community CFP) | No Community Day MY 2026 found | [AWS](https://aws.amazon.com/events/cloud-day-kuala-lumpur/) |
| OSS Japan 2026 | 7–9 Dec 2026, Tokyo | Closed 24 Aug | [Sessionize](https://sessionize.com/oss-als-elc-japan-26) |
| OSS India / OSS Korea 2026 | Jun / Aug 2026 | Closed 6 Mar / 26 Apr, so Linux Foundation CFPs close about 3–4 months ahead | [India](https://sessionize.com/open-source-summit-india-2026), [Korea](https://sessionize.com/open-source-summit-korea-2026) |
| Claude events | KL "Claude AI Day", 5 Jul 2026, UOB Plaza 1 **[weak source: a LinkedIn snippet]**; Singapore Claude Meetup, 10 Sep 2026; Luma "Claude Community Events" (Manila, Taipei) | Organiser-run | [LinkedIn](https://my.linkedin.com/in/alwin-siang), [SGInnovate](https://sginnovate.com/event/singapore-claude-meetup), [Luma](https://luma.com/cc-manila-1) |
| Smaller KL meetups | Junior Developers Malaysia (Worq Bangsar); PyLadies KL | Ask organisers | [allai.events](https://allai.events/event/junior-developers-malaysia-meetup), [PyLadies KL](https://kl.pyladies.com/events/), [dev.events KL](https://dev.events/meetups/AS/MY/Kuala_Lumpur) |

**Gaps:** nothing found for JSConf/React KL, DevOpsDays KL, GitHub Universe 2026 or a 2027 Open Source Summit Asia. No sourced guidance found on what gets a CFP accepted.

**Inference on CFPs:** pitch the problem, not the tool. For example:
- "Your AI agent can write the code, but who cuts the release?"
- "Versioning in a multi-stack studio: Python, Vite, Expo"

Use FOSSASIA's project-showcase and 5-minute lightning slots for a live demo: Claude Code runs `bump2v auto` → commit → tag → CI publishes. Record a backup video in case the live demo fails.

## Prioritised playbook

1. **Weeks 1–2: fix positioning and the README.**
   - Lead with "bump, commit, tag, push in one command; reads your existing `.bumpversion.cfg`".
   - Add a demo GIF, a pipx install line, and a comparison table against bump-my-version, Commitizen and the Rust bumpversion crate.
   - Add a "Migrating from bump2version" guide and an "AI agents" section with a ready-to-paste AGENTS.md snippet.
2. **Weeks 2–4: internal adoption across the team's repos.**
   - Add config, CLAUDE.md/AGENTS.md release rules and a CI guard.
   - Put it in the starter template.
   - Run one lunch-and-learn with a live agent release.
   - Track the share of release tags made by bump2v.
3. **Now to December: submit CFPs.**
   - FOSSASIA 2027: showcase plus lightning talk. Likely deadline around December.
   - Docker KL: deadline 30 Dec.
   - Attend DevFest KL on 14 Nov and ask organisers for a lightning slot or a 2027 speaking spot.
   - Offer the agent-release demo to the Malaysian Claude community organisers.
4. **After internal proof: run the launch sequence.**
   - Publish a blog post framing the problem, using internal numbers.
   - Post a Show HN on a weekday morning US time and stay in the comments; never ask for votes.
   - The next day, post to r/Python using the What/Audience/Comparison headings.
   - Submit to PyCoder's Weekly, and to Console.dev if it fits their criteria.
   - Skip Product Hunt.
5. **2027: watch for and pre-write abstracts for the next CFPs.**
   - PyCon MY (check pycon.my), PyCon Thailand, PythonAsia 2027.
   - Linux Foundation Asia events: CFPs close about 3–4 months before the event.
6. **Continuously.**
   - Keep strict semver and a changelog, and label good-first-issues.
   - Ask happy users to star the repo, as lazygit does.
