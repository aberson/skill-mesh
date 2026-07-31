# skill-mesh

**Agent skills for planning, building, reviewing, and shipping software — run as a gated pipeline
where every build step clears independent, calibrated reviewers, and the same skills run on Claude
Code and GitHub Copilot from one behavior contract.**

- **Gated pipeline** — plans are reviewed before they become issues; builds run autonomously but every
  step is gated; acceptance is evidence-based.
- **Independent, calibrated review** — verdicts come from fresh-context reviewers that must cite
  `file:line`, aggregated deterministically; the judges themselves are calibrated against gold
  fixtures, not trusted on faith.
- **Real & provider-neutral** — ~50 skills actually used day to day, extracted from a personal
  workspace; one behavior contract runs on Claude Code and GitHub Copilot (47 portable; 3 Claude-native).

Swap the placeholders (`<workspace>`, `<project>`, `<your-org>`) before use — see
[Adapt before use](#adapt-before-use).

## Workflows

How these skills **chain together** in practice — every sequence below is a workflow run in
production, with copy-pasteable commands. Detailed write-ups are collapsed; click a heading to expand.

- `/goal`, `/loop`, `/schedule`, and `/deep-research` are Claude Code built-in commands (not skills in
  this repo) that several skills emit or arm — substitute your host's equivalent or skip on Copilot.
- Pipeline skills are autonomous by default (no mid-run "(y/n)?" prompts); conversational skills
  (`plan-init`, `plan-feature`, `plan-merge`, `plan-trim`, the `user-*` ideation skills) stop and ask
  by design.

### The core pipeline

Plan → sync → build → ship. Everything else supports this spine.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/core-pipeline-dark.svg">
  <img alt="The core pipeline: PLAN (plan-init or plan-feature → plan-review → plan-wrap), then SYNC to GitHub (repo-sync; first run repo-init), then BUILD (build-phase → build-step × N → review gates), then SHIP (acceptance UAT → repo-update)." src="_shared/core-pipeline-light.svg">
</picture>

`plan-expedite` collapses the middle — `plan-review → plan-redline → plan-wrap → repo-sync →
handoff` — into one autonomous command, ending by printing the `/goal` + `/build-phase` pair to
paste next.

Order is load-bearing twice. **plan-review before repo-sync**: a gap caught after issues are minted
means editing the plan plus N issue bodies (the "N+1 edit" trap). **repo-sync before build-phase**:
build-phase posts live progress to those issues, so blank `Issue:` lines kill the audit trail.

### The routing web

Every operator fragment — a bug report, a half-formed feature idea, a "does this even work?" — lands
on one of **8 rails**, and `/user-gateway` is the intake front door that sorts a whole brain-dump
across them, one ledger row per fragment (full table and all 9 re-route edges:
[_shared/skill-pipeline.md](_shared/skill-pipeline.md)).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/routing-web-dark.svg">
  <img alt="The routing web: operator vent through /user-gateway to eight rails — bug, do, plan, investigate, verify, trim, decide, draft — with the plan rail forking to /plan-feature (existing project) and /plan-init (brand-new project)." src="_shared/routing-web-light.svg">
</picture>

The graphic shows where each rail *goes*; the table shows what a fragment *sounds like* to land there:

| Rail | Sounds like | Routes to |
|------|-------------|-----------|
| **bug** | "X is broken / erroring" | `/user-debug` |
| **do** | "just do X" — small, resolved | `/goblin-do` |
| **plan** | "add / build capability X" | `/plan-feature` (existing) · `/plan-init` (new) → build |
| **investigate** | "what's true / why does X happen?" | `/deep-research` · Explore sweep |
| **verify** | "does X actually work?" | `/review-uat` · `/user-uat` · `/user-shakedown` · `/user-walkthrough` |
| **trim** | "plan feels bloated / what to cut" | `/plan-trim` |
| **decide** | "should we do A or B?" | surfaced, then parked |
| **draft** | "here are rough thoughts" | `/user-draft` → `/goal` |

## What's inside

<details>
<summary><strong>50 skills across planning, building, review, shipping, and skill/workspace maintenance</strong></summary>

**Core pipeline** — plan → build → review → ship:

| Stage | Skills |
|------|--------|
| **Planning** | [plan-init](skills/plan-init/core.md) · [plan-feature](skills/plan-feature/core.md) · [plan-review](skills/plan-review/core.md) · [plan-redline](skills/plan-redline/core.md) · [plan-wrap](skills/plan-wrap/core.md) · [plan-merge](skills/plan-merge/core.md) · [plan-trim](skills/plan-trim/core.md) · [plan-expedite](skills/plan-expedite/core.md) |
| **Building** | [build-step](skills/build-step/core.md) · [build-phase](skills/build-phase/core.md) · [build-queue](skills/build-queue/core.md) |
| **Review** | [review-deep](skills/review-deep/core.md) · [review-gauntlet](skills/review-gauntlet/core.md) · [review-proof](skills/review-proof/core.md) · [review-uat](skills/review-uat/core.md) · [judge-ui](skills/judge-ui/core.md) · [judge-motion](skills/judge-motion/providers/claude.md) |
| **Repo & docs** | [repo-init](skills/repo-init/core.md) · [repo-sync](skills/repo-sync/core.md) · [repo-update](skills/repo-update/core.md) |

**Supporting**:

| Area | Skills |
|------|--------|
| **User & session** | [user-brainstorm](skills/user-brainstorm/core.md) · [user-debug](skills/user-debug/core.md) · [user-draft](skills/user-draft/core.md) · [user-gateway](skills/user-gateway/core.md) · [user-learn](skills/user-learn/core.md) · [user-orient](skills/user-orient/core.md) · [user-pm](skills/user-pm/core.md) · [user-project](skills/user-project/core.md) · [user-shakedown](skills/user-shakedown/core.md) · [user-uat](skills/user-uat/core.md) · [user-walkthrough](skills/user-walkthrough/core.md) · [user-wrap](skills/user-wrap/core.md) · [user-lavishify](skills/user-lavishify/core.md) · [session-wrap](skills/session-wrap/core.md) · [task-handoff](skills/task-handoff/core.md) · [research-prospect](skills/research-prospect/core.md) |
| **Skill tooling** | [skill-eval-setup](skills/skill-eval-setup/core.md) · [skill-evolve](skills/skill-evolve/core.md) · [skill-iterate](skills/skill-iterate/core.md) · [tier-offload](skills/tier-offload/core.md) · [tier-escalate](skills/tier-escalate/core.md) |
| **Maintenance & hygiene** | [test-prune](skills/test-prune/core.md) · [lesson-harvest](skills/lesson-harvest/core.md) · [memory-distill](skills/memory-distill/core.md) · [context-slim](skills/context-slim/providers/claude.md) · [user-afterparty](skills/user-afterparty/core.md) · [observatory-doctor](skills/observatory-doctor/core.md) |
| **Project improvement** | [goblin-suggest](skills/goblin-suggest/core.md) · [goblin-do](skills/goblin-do/core.md) — *reference only; needs a private second-brain store + the `goblin` CLI, see [_shared/goblin-second-brain.md](_shared/goblin-second-brain.md)* |
| **Reference** | [claude-oauth-auth](skills/claude-oauth-auth/providers/claude.md) |

`_shared/` holds resources referenced by several skills — the judging doctrine
([judge-core.md](_shared/judge-core.md)), the skill routing web
([skill-pipeline.md](_shared/skill-pipeline.md)), the intake-ledger contract
([intake-engine.md](_shared/intake-engine.md)), the skill-role taxonomy the `tier-*` skills
share ([skill-role-taxonomy.md](_shared/skill-role-taxonomy.md)), a guide to rebuilding the
`goblin-*` second brain ([goblin-second-brain.md](_shared/goblin-second-brain.md)), and the
skill-scoring harness.

Links point to each skill's `core.md` behavior contract; the 3 Claude-native skills link to their
`providers/claude.md`. Full capability and exclusion matrix:
[documentation/providers/](documentation/providers/README.md).

</details>

## Pick your entry point

| Start with | What it's for |
|---|---|
| [`/plan-init`](#entry-1) | Brand-new project — gated to greenfield; any existing commit redirects to `plan-feature`. |
| [`/plan-feature`](#entry-2) | Add a feature to existing code — `plan-review` finds gaps, `plan-wrap` proves self-containment. |
| [`/build-step`](#entry-3) | One well-scoped change, no plan — three orthogonal knobs (isolation, reviewers, UI). |
| [`/user-debug`](#entry-4) | Stuck circling a bug — forces an independent repro before any code change. |
| [`/review-gauntlet`](#entry-5) | Review a diff or PR — lean profile over `review-deep`'s engine, terser verdict. |
| [`/review-uat`](#entry-6) | A build needs human acceptance — agent runs the mechanical tier, escalates judgment calls with evidence. |
| [`/build-queue`](#entry-7) | Run several phases overnight — every halt parks as a GitHub issue; nothing retries at 3am. |
| [`/user-wrap`](#entry-8) | Sitting back down / "where were we?" — one skill makes the wrap/continue/clear call. |
| [`/user-gateway`](#entry-8) | A head full of half-formed observations — sorts the brain-dump across 8 rails, one row each. |
| [`/user-pm`](#entry-9) | Survey or challenge the plan — prescribes but never executes; `plan-trim` writes. |
| [`/skill-evolve`](#entry-10) | Improve the skills themselves — A/B variants; prints the PR, never opens it. |
| [`/user-brainstorm`](#entry-11) | Explore an idea or learn a topic — deliberately conversational. |

<a id="entry-1"></a>
<details>
<summary><strong>1. New project → shipped v1</strong></summary>

```
/plan-init                          # structured conversation → plan.md
/repo-init                          # first time only: git init, GitHub repo, README, plan → issues
/plan-expedite --plan plan.md       # autonomous: plan-review → plan-redline → plan-wrap → repo-sync → handoff
```

`plan-expedite` finishes by printing a ready-to-paste pair — arm the goal, then build:

```
/goal "<completion condition it emitted>"
/build-phase --plan plan.md
```

Then wrap the phase:

```
/repo-update                        # README, plan doc, memory, commit, posterity issue, push
```

- `plan-init` is gated to greenfield: if the project has *any* commit it stops and redirects to
  `plan-feature`.
- `build-phase` reads `### Step N:` blocks from the plan, spawns one `build-step` per code step,
  posts progress to the GitHub issues, and only halts for five legitimate reasons (quality-gate
  hard fail, wait-type step, merge conflict, bad conditional predicate, stop-and-audit).

</details>

<a id="entry-2"></a>
<details>
<summary><strong>2. Feature on an existing project</strong></summary>

Same spine, different front door:

```
/plan-feature <one-liner>                                   # reads the codebase, asks about the delta
/plan-expedite --plan documentation/<feature>-plan.md
/goal "<emitted condition>"
/build-phase --plan documentation/<feature>-plan.md
/repo-update
```

Prefer the à-la-carte version when you want to inspect between stages:

```
/plan-review documentation/<feature>-plan.md    # technical gaps, risks (autofix on by default)
/plan-redline --plan documentation/<feature>-plan.md   # operator-facing proposal + P/D feedback fold-in
/plan-wrap documentation/<feature>-plan.md      # self-containment for a fresh-context model
/repo-sync --plan documentation/<feature>-plan.md
/build-phase --plan documentation/<feature>-plan.md
```

- `plan-review` and `plan-wrap` check different things: review finds *technical* gaps; wrap checks
  the doc is *self-contained* for a model with zero conversation history (issue bodies and
  autonomous builds depend on that). `plan-redline` sits between them, turning the corrected plan
  into an operator-facing proposal and folding P/D feedback back in.

</details>

<a id="entry-3"></a>
<details>
<summary><strong>3. One-off change, no plan</strong></summary>

```
/build-step --problem "<what to build or fix>" [--issue N]
```

One skill, three independent knobs:

- `--isolation worktree|docker` — where the developer agent works (worktree default).
- `--reviewers auto|code|runtime|full` — `auto` = quality gates only; `code` = 4 parallel
  review-gauntlet agents; `runtime` = 3 evidence-based reviewers; `full` = all seven.
- `--ui --start-cmd "<cmd>" --url <url>` — Playwright evidence capture for frontend steps.

</details>

<a id="entry-4"></a>
<details>
<summary><strong>4. Getting unstuck on a bug (user-debug)</strong></summary>

```
/user-debug --symptom '<exact error / log line / misbehavior>'
```

- Reach for it when a bug keeps **circling between you and the agent** — command-paste back-and-forth
  that isn't converging. It forces primary-source investigation and an **independent reproduction
  before any code change**, then delegates the fix to `build-step` and re-runs the original repro to
  prove the symptom is gone.
- It's operator-invoked when *you're* stuck, not a plan-driven step — which is why it lives with the
  `user-*` skills rather than the `build-*` pipeline. (It still writes real code via `build-step`.)
- `--triage investigate-only` stops after the diagnosis block — root cause without the fix.
- If investigation concludes the "bug" is really designed, multi-step work, it re-routes to a
  `/plan-feature` seed instead of forcing a fix (the routing web's bug→plan edge — see
  [_shared/skill-pipeline.md](_shared/skill-pipeline.md)).

</details>

<a id="entry-5"></a>
<details>
<summary><strong>5. Reviewing a diff on its own</strong></summary>

Both review skills also run standalone, outside `build-step`:

```
/review-gauntlet <prompt> <diff>     # routine diffs: lean profile over review-deep's engine (5 code lenses, terse verdict)
/review-deep --prompt '<intent>' --diff <PR# | git diff | paste>    # high-stakes: 6 lenses + JSON audit trail
```

- `review-gauntlet` is a **thin profile over review-deep's engine** — the same code lenses
  (correctness, bugs, security, test quality, style) and deterministic aggregation, but
  positional args, a terse PASS / NEEDS-WORK verdict, and no JSON sidecar. Reach for
  `review-deep` on substrate/schema/key-shape changes and producer→consumer chains;
  `--plan-step <plan>:<step>` adds a plan-conformance lens.
- Inside the pipeline, `build-step --reviewers deep` dispatches review-deep directly for
  high-stakes steps, and `plan-review` (§27) routes those steps at plan time by rewriting the
  step's Flags line from `--reviewers code` to `--reviewers deep`.
- `review-proof` is the cross-cutting discipline both lean on: findings must cite `file:line` or
  be dropped. Invoke it directly for "are you sure?" moments — audits, debugging, architecture
  claims.

</details>

<a id="entry-6"></a>
<details>
<summary><strong>6. Acceptance testing (UAT)</strong></summary>

After a build, human-facing verification splits by whether a test script exists.

**A script exists** (a plan M-step, a commands+expectations table):

```
/review-uat plan.md#step-M          # refine: explicit prereqs, observable pass criteria, agent/human split
/user-uat plan.md#step-M            # execute: agent runs the mechanical tier, auto-judges with evidence
```

**No script — explore the built thing directly:**

```
/user-walkthrough <feature>         # attended: you drive, agent answers from source, fixes small things live
/user-shakedown <feature>           # autonomous: closes every open ledger item (verify / quick-fix / log)
```

- Walkthrough and shakedown share one ledger, so you can explore attended and then hand the
  remainder to shakedown, armed under a mechanically checkable goal:
  `/goal "shakedown ledger for <slug> has zero open items"`.
- Anything needing human judgment is escalated with evidence, never guessed.
- `review-uat --exec` is refine-then-delegate: it hands the refined script to `/user-uat` for
  execution rather than running anything itself.
- Finish with `/repo-update` to commit the fixes and file the logged issues.

</details>

<a id="entry-7"></a>
<details>
<summary><strong>7. Unattended overnight runs</strong></summary>

```
/build-queue --queue <path>         # one line per phase plan
```

- For each queue item it runs `plan-expedite` then `build-phase`, each phase in its own worktree,
  strictly sequential.
- Any halt is **parked** — a GitHub issue with halt context — and the queue moves on; nothing
  retries at 3am. A kill-switch file (`.build-queue-killswitch`) is the only mid-run control.
- You get a morning summary; run `/repo-update` per shipped phase over coffee.

</details>

<a id="entry-8"></a>
<details>
<summary><strong>8. Session &amp; context management</strong></summary>

*These session skills assume Claude Code's context harness — auto-compaction, a SessionStart hook that
re-injects `current.md`, and `/clear` / `/compact`. On hosts without it, they degrade to plain
checkpoint/handoff files.*

One skill (`session-wrap`) makes the wrap/continue/clear decision; everything else is a library it
calls or a mode it delegates to.

```
/session-wrap                       # the front door: triages (context, task boundary, git, armed /goal), announces ONE route, acts
/session-wrap --advise              # read-only verdict: KEEP GOING / RECYCLE WINDOW / WRAP & CLOSE / SAFE TO CLOSE + loss report
/user-wrap                          # the return moment ("sitting back down — keep going or close?"): orient, delegate to --advise, act
/task-handoff --loop                # checkpoint library: durable current.md write mid-task (~5s)
/task-handoff --next-task <label>   # durable task-boundary save, keep working
/task-handoff                       # bare = --resume: orientation block from the last checkpoint
/user-project <name>                # pin the session's active project so pipeline skills target the right repo
/user-orient                        # session-axis re-orientation: verified vs not, asides, recommendation (read-only)
/user-orient --quick                # ~150-word thread refresh: problem / tried / still to do (no lookups)
/user-gateway <topic> <vent>        # pre-work intake: convert a brain-dump into routed, ledger-backed work
/user-draft <rough thoughts>        # polish a rough idea into a reusable prompt or a /goal condition
/context-slim [--apply]             # audit auto-loaded context files; prune per-turn token cost
```

- **`session-wrap` makes the call.** Invoked bare at any transition moment, it scores
  mechanical signals (context utilization, task-boundary state from `current.md`, git state,
  armed `/goal`), announces one route, then acts: `continue` (checkpoint + one line),
  `clear-next` (durable state → rendered handoff prompt → git verb → emit `/clear`), or
  `end-window` (full wrap: memory/docs passes + a Pick-up-here block). `--advise` is the
  read-only variant — a verdict banner + two-line loss report, never acts.
- **`user-wrap` serves the return moment** — sitting back down after lunch or overnight.
  Despite the name, the most common verdict is KEEP GOING. It owns zero triage logic of its
  own: it orients from `current.md` + git, delegates the verdict to `session-wrap --advise`,
  re-presents the banner + loss report front and center, then acts per verdict.
- **`task-handoff` is the checkpoint library** orchestrators call (`build-phase`, `build-step`,
  `plan-expedite`, `user-draft`); operators usually want `/session-wrap`.
- **`user-gateway` converts a brain-dump into routed work**: one ledger row per voiced fragment,
  routed by consulting the routing web, each with a ready-to-paste seed — it converts what you said
  and never proposes work of its own.

See the [**routing web** map](#the-routing-web) near the top for how `/user-gateway` sorts a vent
across all 8 rails.

- The underlying doctrine is *native context management first*: auto-compaction and
  goal-arming handle most sessions, so the default is to keep working in one window and reach
  for the front door only at genuine transition moments.
- `user-draft` is the authoring helper — it turns rough thoughts into a clean prompt or a
  checkable `/goal` string and checkpoints via `task-handoff --loop` so a window pivot loses nothing.

</details>

<a id="entry-9"></a>
<details>
<summary><strong>9. Plan &amp; portfolio maintenance</strong></summary>

```
/user-pm [--cut|--goal|--overnight|...]   # read-only PM snapshot: shipped / outstanding / next / cuttable
/plan-trim                                # the write path: propose 3-8 cuts, execute on confirm
/plan-merge <plan-1> <plan-2>             # reconcile overlapping plans into one spine
/research-prospect                        # survey all active projects → menu of /deep-research topics to farm out
```

- `user-pm` prescribes, never executes — its Build/Overnight moves print the ready
  `/plan-*` or `/build-phase` command with prerequisites. `plan-trim` is its writing companion.
- `research-prospect` is the cross-project sibling of `user-pm`: read-only, it surveys every active
  project and emits a prioritized menu of research topics to farm out to other windows.
- After a merge, re-run `/plan-review` + `/plan-wrap` on the merged plan and `/repo-sync` to
  re-cut issues. Originals are archived, never deleted.

</details>

<a id="entry-10"></a>
<details>
<summary><strong>10. Improving the skills (and the workspace's memory)</strong></summary>

Two independent tracks operate on the skills themselves and on the workspace's feedback memory.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/improve-skills-dark.svg">
  <img alt="Two independent tracks. Improve a skill: user-brainstorm → skill-eval-setup → skill-evolve → skill-iterate. Codify a lesson: lesson-harvest → memory-distill." src="_shared/improve-skills-light.svg">
</picture>

```
# improve a skill
/user-brainstorm <skill or problem>              # candidate strategies / framings to try
/skill-eval-setup <skill>                        # bootstrap evals.json + scenarios + golden corpus
/skill-evolve --skill <name> --variants <file>   # A/B N variants in parallel; pushes winner, prints gh pr create
/skill-iterate                                   # overnight serial hill-climb (1h or 12 iters per skill)

# codify a lesson
/lesson-harvest --dry-run                        # scan git history + run logs for un-codified regressions → draft PR
/memory-distill                                  # human gate: distill drafts into durable principles (the only memory writer)
```

- The improve track is explore-then-exploit: brainstorm framings, A/B them with `skill-evolve`, then
  hill-climb the winner with `skill-iterate`. (In steady state the two loop — `skill-iterate` runs
  nightly and hands plateaued skills back to `skill-evolve`; see each skill's `core.md`.)
- `skill-evolve` and `skill-iterate` both require the evals folder `skill-eval-setup` creates.
- Nothing self-approves: `skill-evolve` prints the PR command instead of opening it, `lesson-harvest`
  only drafts, and `memory-distill` keeps a human at the write gate.

</details>

<a id="entry-11"></a>
<details>
<summary><strong>11. Ideation &amp; learning</strong></summary>

```
/user-brainstorm <topic>            # 10 seed topics + gap-fill rounds → tiered doc set under docs/investigations/
/user-learn <topic>                 # hands-on learning ramp: runnable notebooks, exercises, tracker
```

These are deliberately conversational — they keep you in the loop instead of running the pipeline.

</details>

## Quick start

<details>
<summary><strong>Install &amp; prerequisites</strong></summary>

Install for your host — the installer and runtime are PowerShell Core (`pwsh`), which runs on Windows,
macOS, and Linux:

```powershell
pwsh -File tools/install-skill-mesh.ps1 -Provider claude -Home <install-home>   # Claude Code
pwsh -File tools/install-skill-mesh.ps1 -Provider gpt    -Home <install-home>   # GitHub Copilot
```

Then run a skill to try one — in Claude Code that's a slash command (`/plan-init`); on GitHub Copilot
the same skill is discovered from its installed folder. Skills ship with placeholders — swap
`<workspace>` / `<project>` / `<your-org>` before running (see [Adapt before use](#adapt-before-use)).

**Prerequisites:** PowerShell 7+ (`pwsh`, cross-platform) to install; an authenticated `gh` CLI for the
`repo-*` and `build-*` skills (they create repos and post to issues); Playwright for the `--ui` and
`judge-*` skills.

</details>

## Providers & installation

Each skill has one provider-neutral behavior contract (`skills/<name>/core.md`) plus a thin per-host
adapter; installing binds one adapter into that host's discovery layout. 47 of 50 skills run on both
hosts; 3 are Claude-native (`claude-oauth-auth`, `context-slim`, `judge-motion`).

| Provider | Host | Discovery location |
|---|---|---|
| Claude | Claude Code | `<install-home>/.claude/skills/<skill>/` |
| GPT | GitHub Copilot CLI | `<install-home>/.copilot/skills/<skill>/` |

- **Install** — see [Quick start](#quick-start). Flags: `-Uninstall`, `-Force`, `-Home`/`-Destination`, `-Provider`/`-Profile`.
- **Auth** (a separate axis from selection) — Claude uses the host's own model (no key); GPT via GitHub Copilot sign-in (`gh auth login`), **no `OPENAI_API_KEY`** needed.
- **Deep dive** — router auto-detection, the full auth/capability/exclusion matrices, and the selection/transport contract: [documentation/providers/](documentation/providers/README.md), [architecture.md](documentation/architecture.md) §5.

## Status & adapting

<details>
<summary><strong>Current status</strong></summary>

- ~50 skills; 47 portable across Claude Code + GitHub Copilot behind one behavior contract; 3 Claude-native.
- Shipped: the canonical `skills/<name>/{core.md,providers/}` source tree, the provider-neutral router,
  and the distribution builder, installer, and release tooling (reproducible SHA-256 checksums over a
  `git ls-files` stage); ~250 tests across seven suites (router, calibration, package-integrity,
  distributions, release, telemetry, smoke).
- The original 46 top-level `<skill>/SKILL.md` packages remain as a compatibility surface during a
  deprecation window — not the canonical source, and not updated by this migration; see
  [documentation/migration.md](documentation/migration.md).
- Full contract: [documentation/architecture.md](documentation/architecture.md).

</details>

<a id="adapt-before-use"></a>
<details>
<summary><strong>Adapt before use</strong></summary>

- Replace placeholders (`<workspace>`, `<project>`, `<your-org>`) with your own values.
- Skills that reference a "control plane" or a memory index assume conventions from the source
  workspace — read the skill's `core.md` and adjust, or skip those skills.
- **Some skills need adapting to your setup.** A few carry assumptions from the source workspace:
  the `goblin-*` pair ships as **reference only** — it needs a private "second-brain" atom store and
  a separate `goblin` CLI, both omitted, so rebuild your own from
  [_shared/goblin-second-brain.md](_shared/goblin-second-brain.md); `tier-offload` emits a config
  for a local-model router and `tier-escalate` a model-tiering escalation map (adapt to your own
  models, or skip if you run neither); `judge-ui` needs a per-project browser adapter (server
  bring-up, auth, test IDs); `observatory-doctor` assumes a "dev-observatory" control-plane
  convention from the source workspace; and `user-lavishify` drives an annotatable-HTML rendering
  step. A handful of workspace reference files stay unpublished (`shakedown-engine.md`,
  `task-state-schema.md`, the `docs/investigations/` corpus); published skills may point at them —
  treat those as adaptation points, not missing files.
- No secrets or credentials are included.

</details>

## Contributing

Issues and suggestions welcome: [github.com/aberson/skill-mesh/issues](https://github.com/aberson/skill-mesh/issues).
Shared as an extracted personal toolkit — read [Adapt before use](#adapt-before-use) before filing.

## License

MIT — see [LICENSE](LICENSE). Built by Abraham Robison ([github.com/aberson](https://github.com/aberson)).
