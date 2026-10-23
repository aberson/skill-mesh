# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/repo-sync/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Repo Sync

Bidirectional sync between a plan document and GitHub issues. Creates,
updates, closes, and **enriches** issues so GitHub mirrors the plan's
structure and any fresh-context LLM picking up a step has enough context
in the issue body to start work.

## Operating contract

- **Position:** plan pipeline stage 5 of 7 — after `/plan-review` → `/plan-redline` → `/plan-wrap`, before `/build-phase`; `/repo-init` is the first-time alternative at the same stage (see Prerequisites).
- **Input:** `--plan` is required. A bare invocation, or a `--plan` path that is missing or unreadable, ends `Result: NOT RUN (<reason>)` before any `gh` call. Never guess a plan: a guessed plan would flow into issue mutation.
- **Target repo:** resolved once in Step 0, in the precedence of `.claude/references/transition-directory-contract.md` § The resolved target repo (`/user-project` pin → the plan's project → cwd repo). Every `gh` call after Step 0's resolution passes `-R <owner>/<repo>` for that one repo.
- **Allowed writes:** in the target repo only — `gh issue create`, `gh issue edit` (title and body), and `gh issue close` with its comment; temp body files under the Windows-safe temp directory, deleted after use; and blank `**Issue:**` values in the plan (Step 7b). Nothing else: no reopen, delete, label, milestone or other comment, no other repository, and no git write command (add, commit, push, stash, checkout, reset); read-only `git rev-parse` is allowed for target resolution, the wrong-directory guard and the footer `<git-short-sha>`. `--dry-run` writes nothing.
- **Result:** every run, including a stop, ends with one `Result:` line followed by the `Next:` line (Step 8). Callers should read the `Result:` line (plan-expedite adoption: X3), not the last line, which is `Next:`; success is never inferred from prose.
- **Re-run:** matching is by title prefix and footer, so a re-run after a partial failure or a plan edit converges — existing issues become ENRICH, UPDATE or NO-OP rather than duplicates, and Step 7b never overwrites an existing issue number.

## Principle: optimize for LLM effectiveness, not human-noise reduction

Issue bodies should be substantive. A fresh-context model reading
`gh issue view #N` should understand:
- What to build (not just a name)
- Where in the codebase (specific files)
- How to know it's done (concrete acceptance)
- What it depends on (prior issues, blocked-by relationships)
- Build-phase flags (reviewers, isolation, **`--ui` when frontend is touched**)
- Where the canonical design lives (build doc + section anchor)
- **Whether the step can run in parallel with neighbors** (declared explicitly,
  not left for the operator to infer)

Lean bodies (just "What to build" and a footer) tax every future
session that picks up that issue. Treat enrichment as a first-class
output, not optional polish. Issue count and inbox tidiness are
human-experience costs the operator is fine paying — don't optimize for
them at the expense of the LLM-context-effectiveness above.

## Operator preference (HEAVY) — autonomous + bundled UI + parallel

This skill propagates the operator's strong workflow preference through every
issue it writes. Three dials, applied to every step body:

1. **Autonomous build readiness.** Step bodies must contain enough acceptance
   detail (`Done when`) for `/build-step` to verify PASS without asking the
   operator a follow-up. Bodies that force a human ping mid-build are a
   regression. When enriching, prioritize concrete acceptance over prose.

2. **UI-bundle declaration.** If a step's `Files` touch `frontend/`, change a
   `/api/...` shape consumed by the dashboard, or modify WebSocket payloads,
   the issue body's `Flags (recommended)` line MUST include `--ui` and the
   `Done when` MUST reference UI evidence (Playwright screenshot, dashboard
   smoke, or any project-specific UI/dashboard smoke commands defined in
   the project's `CLAUDE.md`). Code-only acceptance on frontend-touching
   work is the gap repo-sync is here to close — flag any existing issue
   that violates this and propose enrichment.

3. **Parallelism declared explicitly.** If a step has no `Depends on` and
   shares no `Files` with another open step in the same phase, the body MUST
   note `**Parallel-safe with:** #M` (and the reciprocal noted on #M too).
   Sequential is fine, but `none — strictly sequential` MUST carry a one-line
   justification (e.g. "Step N+1 imports this module"); a bare
   "strictly sequential" without a reason is a defect — the parallelism
   choice must be visible in the issue, not hidden in the operator's head.

These dials are applied during CREATE, ENRICH, and UPDATE — not just on first
write. A pre-existing rich body that lacks the UI-bundle declaration on a
frontend-touching step still counts as needing ENRICH.

## When to use

- Plan steps were added, removed, or reworded after issues were created
- Existing issues have lean bodies that need richer context (`--enrich`)
- Cutting issues for a new phase from its build doc
- User says: "sync issues", "update GitHub issues", "enrich step issues",
  "issues are out of date"

## When NOT to use

- Closing a single issue after a step completes — just `gh issue close N`
- Bulk-closing issues from a deleted plan (use `gh issue list ... | xargs gh issue close`)

---

## Prerequisites

Run the plan pipeline in order. `/repo-sync` is step 5 of 7:

  1. `/plan-init` or `/plan-feature` — produce `plan.md`.
  2. `/plan-review` — gap-check before sync.
  3. `/plan-redline` — operator P/D feedback on the corrected plan.
  4. `/plan-wrap` — clean-context check before sync.
  5. `/repo-sync` (or `/repo-init` the first time) — mint or update issues from the plan.
  6. `/build-phase` — execute the steps.
  7. `/repo-update` — commit, update docs, push.

Skipping `/plan-review` or `/plan-wrap` before sync is the
**N+1 rework trap**: one plan edit becomes N+1 edits — the plan
file plus every step issue body that needs the same fix.
`/repo-sync` mints fresh-context-LLM-targeted issue bodies
straight from the plan, so plan-only ambiguities (undefined IDs,
unexplained acronyms, lingering TBDs) bake into every issue.

For an autonomous pre-flight that runs the chain unattended,
use `/plan-expedite --plan <path>` — it runs the pre-sync review
chain, then this skill, then its handoff, in one shot (its core
owns the exact stage list).

Canonical workspace-level statement of the chain lives in
`dev/.claude/references/plan-and-issue-flow.md` § Order (the
`dev/.claude/rules/plan-and-issue-flow.md` stub points there).

---

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--plan` | yes | -- | Path to plan/build-doc (e.g. `documentation/plans/phase-d-build-plan.md`). Absent or unreadable → `Result: NOT RUN`; never guessed |
| `--phase` | no | inferred | Phase identifier (B, D, E, 6, 7, F, G, G.2, 9, etc.) — letters and numbers both supported. Inferred from filename if omitted. |
| `--scope` | no | both | `umbrella`, `steps`, or `both` |
| `--enrich` | no | false | Update existing-issue bodies if richer content is now in the plan |
| `--dry-run` | no | false | Print issue-change preview and exit without applying — for validation before commit |
| `--force` | no | false | Proceed despite missing evidence that the plan-review and plan-wrap prerequisite gates ran. An explicit operator waiver of that one gate only: it never waives the Step 0 repo checks, and the run prints `Prerequisites: waived by --force (<missing gate>)`. |

---

## Phase identifier conventions

Phases can be:
- Numeric: `Phase 0`, `Phase 1`, ..., `Phase 9` — common for substrate/operational tracks
- Letter: `Phase A`, `Phase B`, `Phase D`, ..., `Phase G` — common for capability tracks
- Sub-phase: `Phase G.1`, `Phase G.2`, `Phase G.3` — for multi-step phases that fork

Numbering gaps are allowed and intentional (e.g. project skipped Phase C
during a merge; project may skip Phase 8 to align with pre-existing
issue titles). The skill honors the plan as-written — does NOT try to
fill gaps.

Step numbering within a phase uses dot notation in the build doc
(e.g. `D.1`, `D.2`, `7.1`, `G.2.1`) but issue titles use the friendlier
`Phase X Step N:` form.

Issue title patterns the skill recognizes:
- Umbrella: `Phase X — <name>`  (e.g. `Phase D — Build-order z-statistic`)
- Step: `Phase X Step N: <name>`  (e.g. `Phase D Step 1: Audit reward_rules.json`)
- Sub-phase umbrella: `Phase X.M: <name>`  (e.g. `Phase G.2: Zerg bot`)
- Sub-phase step: `Phase X.M Step N: <name>`

## Step-detection formats supported in plan docs

The skill scans the plan for any of:
- `### Step N: <name>` — heading style
- `### Phase X Step N: <name>` — explicit phase heading
- `#### Step N: <name>` — sub-heading style
- `- **Step N:** <name>` — list style
- `| X.N | <description> |` — table row in a Scope / Build-steps section

For table-row format, the description is the step title; richer body
content must be pulled from explicit per-step subsections OR the doc is
flagged as lean (see "Doc richness check").

---

## Flow

### Step 0 — Pre-flight: resolve and verify target repo

Before proceeding to issue mutation, verify plan-review and plan-wrap have each been run on the target plan. Accept evidence such as a checkpoint entry (for example a `.plan-expedite-state` `completed[]` entry for that gate on this plan), a record in this session that the gate ran on this plan, or `Status: DONE` on the corresponding review steps. Print one line naming the source for each gate, e.g. `Prerequisites: plan-review (.plan-expedite-state), plan-wrap (this session)`. If evidence for either gate is absent, emit a `WARNING` naming the missing prerequisite evidence and halt (`Result: NOT RUN (missing prerequisite evidence: <gate>)`) unless the operator supplied the explicit `--force` flag. Do not silently skip prerequisite gates. Redline evidence is not checked.

`gh` resolves the target repo from cwd by walking up to the nearest
`.git/`. The `dev/` workspace root is itself a git repo with its own
remote (`aberson/coding-root`), so running `gh` from `dev/` silently
lands on `aberson/coding-root` instead of the intended project
subdirectory. `<absolute-project-dir>` below is the resolved target
(Operating contract). When a set `/user-project` pin names a different
repo than the one containing `--plan`, print one
`WARNING target repo '<pin-repo>' != plan repo '<plan-repo>'` line
naming both, then continue with the resolved target (advisory, like the
wrong-directory guard below). Resolve and echo the repo before any
mutating call:

```bash
cd <absolute-project-dir>
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
echo "Target repo: $REPO (default branch: $DEFAULT_BRANCH)"
```

Confirm the printed `Target repo:` matches the intended project. If it
does not, or no repo resolves, stop — the cwd is wrong
(`Result: NOT RUN (target repo: <reason>)`).

`$DEFAULT_BRANCH` is the `<default-branch>` placeholder every body
template below interpolates into its `../blob/<default-branch>/` doc
links. **Resolve it — never assume.** GitHub has defaulted new repos to
`main` since 2020, so a hardcoded `master` 404s every minted build-doc
link, and a hardcoded `main` merely inverts the same defect for a repo
that genuinely still uses `master`. When the build doc lives in a
DIFFERENT repo than the issues (a cross-repo plan), resolve that repo's
branch instead — `gh repo view <owner>/<repo> --json defaultBranchRef -q
.defaultBranchRef.name` — because the link must resolve against the repo
that actually hosts the doc.

> Wrong-directory guard: before this gh issue sync, warn if the resolved target project repo != the repo `gh` resolves from cwd's remote (advisory, never blocks) — per working-directory.md § Wrong-directory guard; reference impl `Test-WrongDirGuard`.

For every subsequent `gh` call in the run, pass `-R <owner>/<repo>`
defensively so cwd-resolution cannot drift mid-run:

```bash
gh -R aberson/Alpha4Gate issue create ...
gh -R aberson/Alpha4Gate issue list ...
```

Equivalent fix: `cd` into the project subdirectory before invoking
`gh` (e.g., `cd Alpha4Gate && gh ...`). The `-R` flag is preferred
because it survives mid-run cwd changes.

### Step 1 — Read the plan and infer phase

Read `--plan`. If `--phase` not specified, infer from filename
(`phase-d-build-plan.md` → `D`; `phase-9-build-plan.md` → `9`;
`improve-bot-evolve-plan.md` → check `# Phase X ...` H1 in content).

Extract:
- **Umbrella metadata:** title (from `# <H1>`), goal, prerequisites,
  effort, kill criterion, validation
- **Step list:** every step matching one of the supported formats

For each step, capture from per-step subsections if present:
- `Problem` / `What to build`
- `Files` / `Files to modify` / `Files touched`
- `Existing context`
- `Done when` / `Acceptance`
- `Flags` (build-step flags like `--reviewers code --isolation worktree`)
- `Depends on`
- `Produces`

If steps are table-only (sparse), flag this and run the richness check
(below).

### Step 2 — Doc richness check (the LLM-effectiveness gate)

For each step, count populated rich-fields out of 6:
{Files, Done when, Flags, Existing context, Produces, Depends on}.

- **Rich step:** ≥ 3 fields populated
- **Lean step:** ≤ 2 fields populated

If >50% of steps are lean:

```text
WARNING: <plan> has N of M lean steps (only title + description).

Issues created from lean steps will be lean too. Every fresh-context
LLM session that opens those issues will need to drill into the build
doc or source code for context the issue body should have.

Per the LLM-effectiveness principle (memory:
feedback_optimize_for_llm_over_human_noise.md), the recommendation is:

  1. Enrich the build doc first with per-step Files / Done when /
     Flags / Existing context sections.
  2. Then re-run this skill (or run with --enrich for an existing
     issue set).

Continuing — issue bodies will reflect the plan's current shape.
Operator can re-run /repo-sync after enriching the plan if higher-
fidelity issues are needed.
```

Surfacing this cost is mandatory; the warning is a printed observability
note that proceeds automatically without prompting. The operator can
re-run `/repo-sync` after enriching the plan when richer issues are
needed — but no halt mid-sync.

### Step 3 — Fetch existing GitHub issues

```bash
# jq requires POSIX classes - no \d / \w / \s / \. (see Common mistakes § Perl-style regex escapes)
# the jq string escape \u2014 (six ASCII characters) decodes to the umbrella em-dash, so no non-ASCII character crosses the shell boundary
gh -R "$REPO" issue list --state all --limit 1000 --json number --jq 'length'
gh -R "$REPO" issue list --state all --limit 1000 --json number,title,body,state \
  --jq '.[] | select(.title | test("^Phase [A-Z0-9]+([.][0-9]+)?( Step [0-9]+)?:|^Phase [A-Z0-9]+([.][0-9]+)? (\u2014|-) "))'
```

This regex matches both umbrella titles (`Phase X <em-dash> ...`) and step
titles (`Phase X Step N: ...`) across numeric, letter, and sub-phase
numbering. Falls through to the legacy `(Phase [0-9]+ )?Step [0-9]+:` if the
new pattern returns nothing (back-compat). The umbrella separator is the
jq string escape `\u2014` (written as six ASCII characters; jq decodes it to the em-dash) or an ASCII `-`, never a literal em-dash,
which is mangled in `gh` flag values on Windows
(`.claude/references/windows-shell.md` § Shell args & grep gates); `.`
is not used because it matches any character.

**Fetch failure fails closed.** If any Step 3 command (including the legacy
fallback) exits non-zero, or the first prints anything other than an integer, the issue state is unknown:
stop before any mutation with `Result: NOT RUN (issue list unavailable)`.
An empty or failed list is never read as "no issues" (that would mint
duplicate CREATEs).

If the first command prints the limit (1000), the list may be truncated
and the absence of an issue is unproven: print one
`WARN: issue list truncated` line, hold every CREATE (preview label
`CREATE … (held: issue list truncated)`) and run the other buckets.
Only when at least one CREATE is actually held does the run end
`Result: PARTIAL (issue list truncated; <n> creates held)`, with `Next:`
naming the fix — create the held steps by hand from the preview, or
transfer stale issues to another repo until the repo-wide count is below
1000, then re-run. Closing issues does not help: `--state all` still
counts closed issues. With zero held creates the warning stays and the
normal Result rules apply, so "create by hand, then re-run" converges.
A repo at or above the limit never gets an automatic CREATE. Under
`--dry-run`, `Result: DRY-RUN` wins and the preview carries the held
labels plus the warning line. The limit is a backstop, not a scope: the list stays repo-wide
(not a `--search` query), because search results are index-backed and
can omit a just-created issue, which would break re-run convergence.

#### 3.1 — Cross-plan collision check

When a repo holds issues from multiple plans, step keys
(`Phase X Step N`) collide and a new plan's step may match a
stale issue belonging to an unrelated, possibly closed prior
plan.

The disambiguator is the body footer `/repo-sync` writes.
There are TWO footer shapes — both encode the source-plan
path and the parser must recognize both. In the rendered
issue body the plan path is a markdown link (square-bracket
label wrapping the path, parenthesis URL `../blob/<default-branch>/`
plus that same path) so the path is clickable from the
GitHub issue — never a code-spanned path followed by a
parenthetical "linked to" phrase.

- Create path (see Body template — step):
  `*Synced from `<plan>` by /repo-sync at <git-short-sha>*`
  (with `<plan>` rendered as the markdown link described above).
- Enrich / update path (see Update / enrich):
  `*Enriched by /repo-sync from <plan> @
  <git-short-sha>*`

Long-lived issues that have been re-synced carry the second
shape; the parser must match both or every previously
enriched issue falls through as "footer missing" — exactly
the issues most likely to be cross-plan-colliding.

Regex shapes the parser must match:
- Create:  `Synced from \[(.*?)\]`
- Enrich:  `Enriched by /repo-sync from (.+?)( @ |$)`

Algorithm: for each fetched issue in this plan's phase (the
Step 3 fetch above, matched to a plan step or not, so CLOSE
can prove ownership), parse the footer's plan path from the
issue body — from EITHER `Synced from [<plan>]` OR
`Enriched by /repo-sync from <plan>`. `<plan>` in both footers
is the `--plan` file's path relative to the doc repo root, with
forward slashes, and both templates render it in that form.
Normalize both the parsed path and the current `--plan` path
before comparing: strip backticks and a leading `./`, convert
`\` to `/`, make an absolute path relative to the doc repo
root, and compare case-insensitively on Windows. If the
normalized footer path differs from the normalized `--plan`
path, classify the match as a CROSS-PLAN COLLISION (the issue
belongs to a different plan; the step key collision is
incidental). An issue this skill enriched from the same plan
therefore never classifies as a collision.

Action: emit a `WARN: cross-plan collision` line in the
Step 5 preview output for each collision. **No halt** —
autonomous default still executes; the operator sees the
warning in the preview but the run proceeds without
prompting. Collided issues are excluded from every mutation
bucket — ENRICH, UPDATE and CLOSE (treat as stale w.r.t. this
plan; this skill never reopens). A plan step whose only title
match is a collided issue is not created either; it stays in
the preview with its WARN line (see Edge cases § Cross-plan
step-key collision).

Example warning line in the preview:

```text
WARN: cross-plan collision — issue #123 "Phase D Step 3: foo"
  plan footer: documentation/old-plan.md
  --plan arg:  docs/archived-plans/repo-sync-improvements-plan.md
  classify as: stale (do not ENRICH, UPDATE or CLOSE)
```

Footer-absent issues (legacy or hand-authored) cannot be
classified by this check; fall through to the existing
title-prefix match behavior. Add `(footer missing)` to the
preview note so the operator knows the check could not run
on that issue.

**Always-surface contract.** The rendered Step 3.1 output
MUST state the two recognized footer shapes explicitly —
even when no existing issues were matched in Step 3. This
makes the parser's footer-aware classification visible and
auditable in every run, not only runs that exercise it.

Required Step 3.1 header line in the rendered output:

```text
Footer shapes recognized:
  Create:  Synced from [<plan>](...)
  Enrich:  Enriched by /repo-sync from <plan> @ <sha>
```

When no issues were matched, follow with `(no existing
issues to classify)`. When issues exist, list each with its
footer plan path or `(footer missing)` per the algorithm
above. Either way, neither footer shape is omitted from the
output, so enriched-path issues are never silently treated
as `footer missing`.

### Step 4 — Match and diff

Match plan entries to existing issues by title prefix:
- Umbrella: `Phase X — <anything>` matches plan's H1 phase
- Step: `Phase X Step N: <anything>` matches plan step `X.N` or `Step N`
  within the phase

Classify into buckets:

| Bucket | Condition | Default action |
|---|---|---|
| **CREATE umbrella** | Plan has phase, no umbrella issue | Create with full body |
| **CREATE step** | Plan step has no matching issue | Create with rich body |
| **ENRICH** | Issue exists, body is lean (≤2 sections), plan now has richer content | Update body (auto if `--enrich` OR if plan has clear new fields) |
| **UPDATE** | Issue exists but title or body changed substantively | Update |
| **CLOSE** | Open issue in this plan's phase whose step was removed from the plan AND whose footer names this plan (Step 3.1) | Close with comment |
| **NO-OP** | Issue exists, body is rich, no plan change | Skip |

CLOSE requires proven ownership. An open issue whose step key is absent
from the plan but whose footer is missing or names another plan is never
closed: list it as `NO-OP` with the note `not closed: footer <missing |
names another plan>`.

### Step 5 — Preview

Print all proposed changes grouped by phase:

```text
repo-sync: documentation/plans/phase-d-build-plan.md (Phase D)

  Build doc richness: 3/8 steps rich, 5/8 lean

  CREATE umbrella  Phase D — Build-order z-statistic (reward refactor)
  CREATE step      Phase D Step 1: Audit reward_rules.json (rich body)
  CREATE step      Phase D Step 2: Define z schema (rich body)
  CREATE step      Phase D Step 3: build_order_reward.py (lean — Files missing)
  ENRICH           Phase D Step 5 (#168) — body lacks Done when + Files
  UPDATE           Phase D Step 7 (#170) — title changed
  CLOSE            (none)
  NO-OP            (none)
```

If `--dry-run` was specified, stop here and print:

```text
Dry-run complete. No changes applied.
```

followed by the `Result: DRY-RUN` and `Next:` lines (Step 8).

Otherwise, proceed directly to Step 6 — print `Applying changes now...`
and execute. **Do not prompt for confirmation.** The preview is the
operator's read-out, not a halt point; autonomous orchestration
(`/build-phase`, `/plan-expedite`) depends on this.

#### --dry-run flag

When `/repo-sync --dry-run` is invoked, the preview above is printed but
no changes are applied. The skill exits cleanly with the message
`Dry-run complete. No changes applied.` Use this to validate plan→issue
mapping before committing to a sync.

### Step 6 — Execute (one tool call per gh action)

Process in this order:
1. Umbrella issues first (so step issues can reference them)
2. Step issue creates
3. Step issue enrichments + updates
4. Closes last

Each `gh issue create/edit/close` is its own Bash tool invocation, OR a
loop in one Bash with explicit per-iteration error handling. Do NOT
batch with `&&` — one failure must not break the chain.

Record each action's exit status and the issue number or URL `gh`
returns. A non-zero exit, or a create that returns no issue URL, is a
failed action: report it, continue with the remaining actions, and never
infer success. A failed step create leaves that step without an issue
(no umbrella line, no Step 7b value); a failed umbrella create leaves
step bodies without the umbrella reference and skips Step 7. Any failed
action makes the result `PARTIAL`; completed actions stand, and a re-run
converges (Operating contract).

#### Body delivery — always use `--body-file`

All `gh issue create/edit` calls in this skill MUST deliver bodies via `--body-file <path>`, never inline `--body "$(cat <<EOF ... EOF)"`. The inline heredoc form silently truncates or parser-tangles bodies that contain nested quote levels (code spans, quoted text, tables) — see `dev/.claude/rules/windows-shell.md` § gh / jq.

Use a Windows-safe temp path:
- Bash: `$LOCALAPPDATA/Temp/` (e.g. `C:/Users/<user>/AppData/Local/Temp/`)
- PowerShell: `$env:TEMP`

POSIX `/tmp/` is invisible to `gh.exe` on Windows (different temp roots).

The Create / Update / Close templates below all assume this delivery method.

**Link notation.** In the templates, `` `<path>` (linked to `<url>`) ``
is notation, not literal output: render it as the markdown link
`[<path>](<url>)` with the resolved `<default-branch>`, as Step 3.1
requires. Never emit the "linked to" parenthetical.

#### Body template — umbrella

```markdown
**Umbrella:** #<master-plan-umbrella-issue-if-exists>
**Blocked by:** Phase <prerequisite-phase-if-any>
**Build doc:** `<build-doc-path>` (linked to `../blob/<default-branch>/<build-doc-path>`)
**Track:** <track-from-plan>

## Goal

<goal paragraph from plan>

## Work (N steps)

- [ ] **#<step-1-issue>** Step 1: <name>
- [ ] **#<step-2-issue>** Step 2: <name>
...

(Step issue numbers populated after step creates — re-edit umbrella in Step 7.)

## Acceptance

<validation / acceptance from plan>

## Effort

<effort estimate from plan>

## Kill criterion

<kill criterion from plan>
```

#### Body template — step

```markdown
## Build step N of M — Phase <X> (umbrella #<umbrella-issue>)

**Build doc:** `<build-doc-path>` (linked to `../blob/<default-branch>/<build-doc-path>`) §<section> Step <X.N>

### What to build
<full description from plan, not abbreviated>

### Existing context
<from plan's "Existing context" section if present, scoped to this step>
<otherwise: omit (will be flagged in summary)>

### Files to modify/create
<file list from plan if present>
<otherwise: omit (flagged in summary)>

### Done when
<acceptance from plan, specific not generic>
<otherwise: "All tests green, mypy strict + ruff clean. See umbrella for phase-level gate.">

### Flags (recommended)
<build-step flags from plan if present, e.g. `--reviewers code --isolation worktree`>
<if step touches frontend/, /api/ shapes, or WebSocket payloads: ALSO include `--ui`>

### Depends on
<previous step issue # if known, or "none">

### Parallel-safe with
<list any open step issue # in the same phase that shares no Files and no
Depends-on with this step. When no such peers exist, write
`none — strictly sequential (<one-line justification>)`. The justification
is REQUIRED — bare "strictly sequential" without a reason hides the
choice from the operator. Acceptable justifications: "Step N+1 imports
this module", "shares <Files entry> with #X", "soak gate after Step N
must finish first". When the plan is lean (no Depends on, no Files
declared), default to listing peers as parallel-safe rather than
collapsing to strictly sequential.>

### Produces
<list from plan if present>

### Operator workflow notes (autonomous + UI-bundle + parallel)
- This step is intended to run end-to-end via `/build-step` without
  mid-iteration check-ins; the `Done when` above is the verification gate.
- If `--ui` is in the Flags line above, UI evidence (Playwright screenshot,
  or any project-specific UI/dashboard smoke commands defined in the
  project's `CLAUDE.md`) is part of acceptance, not a follow-up.
- Parallel-safe pairs above can be dispatched in parallel worktrees by
  `/build-phase`.

---
*Synced from `<plan>` (linked to `../blob/<default-branch>/<plan>`) by /repo-sync at <git-short-sha>*
```

The footer with the source path + SHA helps a future LLM verify whether
the issue body is current vs the build doc.

Sections without source content can be omitted, but **issues missing
>2 of {Existing context, Files, Done when, Flags, Produces} are flagged
in the summary** as candidates for follow-up enrichment.

#### Update / enrich

```bash
# Windows-safe temp path; POSIX /tmp/ is invisible to gh.exe.
BODY_FILE="$LOCALAPPDATA/Temp/repo-sync-issue-$NUMBER.md"
cat > "$BODY_FILE" << 'BODYEOF'
<full new body following template>

---
*Enriched by /repo-sync from <plan> @ <git-short-sha>*
BODYEOF
gh -R "$REPO" issue edit <NUMBER> --title "<title>" --body-file "$BODY_FILE"
rm "$BODY_FILE"
```

The enrich footer replaces the template's `Synced from` footer; a body
carries exactly one footer.

#### Close

```bash
gh -R "$REPO" issue close <NUMBER> --comment "Closed by /repo-sync - step removed from plan."
```

Close only issues in the CLOSE bucket (ownership proven, Step 4).

### Step 7 — Re-edit umbrellas with step references

After step issues are created, edit each phase's OPEN umbrella issue to
include the **Work** checklist with actual issue numbers. A CLOSED
umbrella match is never edited here or in UPDATE/ENRICH (it may be
`/repo-update`'s closed phase-audit issue, `Phase N — …`); report
`NO-OP #<n> not edited: umbrella closed`. When more than one issue
matches a phase's umbrella title, warn and skip all of them (as Edge
cases § Multiple issues match same step key):
`WARN: multiple umbrella matches #<a>, #<b> — not edited`.

```markdown
## Work (N steps)

- [ ] **#164** Step 1: Audit reward_rules.json
- [ ] **#165** Step 2: Define z schema
...
```

This creates bidirectional cross-refs that an LLM can follow either
direction. Without this, the umbrella has stale `<step-1-issue>`
placeholders or a generic `(steps will be cut by /repo-sync)` note,
which forces the LLM to do a separate `gh issue list` to find them.

### Step 7b — Backfill the plan's `**Issue:**` fields

After Step 7, and never under `--dry-run` or a `NOT RUN` result, write
each step's issue number into the plan, so `/build-phase` can post
progress (it posts nothing for a step without an Issue) and plan-review
and plan-redline can see that the plan was synced.

- **Map:** every plan step matched in this run to exactly one
  non-collided issue that is created now, an existing open issue, or an
  existing closed issue whose footer names this plan (Step 3.1). A
  closed match whose footer is missing is never mapped; report
  `Issue not backfilled: Step N #B (closed, footer missing)`, so
  `/build-phase` cannot route progress comments to an unowned closed
  issue. Collided, multiple-match and failed-create steps get no value.
- **Scope:** only the value of the step's own `**Issue:**` line, and only
  when it is blank, `#` or `TBD`. Never add a missing `**Issue:**` line,
  never change any other byte, and never overwrite an existing number;
  when it differs from the matched issue, report
  `Issue mismatch: Step N plan #A, issue #B`.
- **Mechanics:** one in-place pass that preserves the file's encoding and
  line endings, using the snippet below as the reference implementation,
  then the verification command below.
- **Boundary:** the plan edit is left uncommitted; this skill runs no git
  write command (read-only `git rev-parse` only). If the plan cannot be written, print the remaining map with
  the snippet for the operator; the result is `PARTIAL`.

Report line: `Backfilled: <k> Issue fields; missing field: <m>; mismatch: <j>`.

Backfill snippet (Python) — the reference implementation, and the
operator's fallback when Step 7b could not write. `ISSUE_MAP` is this
run's step-to-issue map:

```python
# Backfill blank **Issue:** values after /repo-sync.
# ISSUE_MAP = {step_number: issue_number} from this run's mapping, e.g.:
ISSUE_MAP = {
    1: 164,   # Step 1 -> issue #164
    2: 165,
    # ...
}

import re
# REPLACE <plan-file> with your plan's actual filename,
# e.g. "documentation/phase-rs-plan.md".
PLAN = "documentation/<plan-file>"
with open(PLAN, encoding="utf-8", newline="") as f:  # newline="" keeps line endings
    text = f.read()
for step_n, issue_n in ISSUE_MAP.items():
    # Match Step N heading, then consecutive single-line
    # **Field:** bullets, then the step's own **Issue:** line.
    # No re.DOTALL: `.` does not match newlines, so `.*?\n`
    # stays within a single line and the bullet-eater group
    # matches only consecutive single-line bullets (no
    # cross-step contamination).
    # The `(?:- )?` makes the list-bullet prefix OPTIONAL: plans
    # use BOTH `- **Issue:**` and bare `**Issue:**` styles.
    # Only a blank, `#` or `TBD` value matches; an existing
    # number never matches, so it is never overwritten.
    pattern = (
        rf"(### Step {step_n}:.*?\n(?:(?:- )?\*\*[^*]+\*\*.*?\n)*?"
        rf"(?:- )?\*\*Issue:\*\*)[ \t]*(?:TBD|#)?[ \t]*(?=\r?\n|\Z)"
    )
    text, n = re.subn(pattern, rf"\g<1> #{issue_n}", text, count=1, flags=re.M)
    if n == 0:  # count=0 is NOT success: field missing or already set
        print(f"Step {step_n}: Issue field missing or already set; not changed")
with open(PLAN, "w", encoding="utf-8", newline="") as f:
    f.write(text)
```

Verification — after a fully-populated backfill, the following
returns empty: every `**Issue:**` line holds exactly one `#<number>`
(no `TBD`, blank, bare `#` or malformed value). REPLACE `<plan-file>`
with your plan's actual filename:

```bash
grep -nE "\*\*Issue:\*\*" documentation/<plan-file> | grep -vE "\*\*Issue:\*\* #[0-9]+[[:space:]]*$"
```

This pattern is one instance of the broader bulk-placeholder-fill
discipline (see `feedback_bulk_placeholder_fills.md`). Background
and rationale in investigation
`docs/investigations/skill-deep-dives/repo-sync/03-issue-blank-lines-kill-build-phase.md`.

### Step 8 — Report

The second line of the report, directly under the header, MUST surface
this skill's plan-pipeline position — `step 5 of 7: after /plan-review →
/plan-redline → /plan-wrap, before /build-phase` — so the operator and
any fresh-context downstream LLM see at a glance what runs next. The
breadcrumb is non-optional.

```text
repo-sync complete for Phase D (umbrella #114)
Plan pipeline: /plan-review → /plan-redline → /plan-wrap → /repo-sync (step 5 of 7) → /build-phase

  Created: 1 umbrella, 8 step issues (#164–#171)
  Enriched: 0
  Updated: 0
  Closed:  0
  Failed:  0
  Backfilled: 8 Issue fields; missing field: 0; mismatch: 0

  Body richness: 3/8 issues fully rich; 5/8 missing Files/Existing-context
  Cross-refs: umbrella #114 updated with step issue links

  Recommendation: build-doc step richness was lean (5/8). Consider
  enriching documentation/plans/phase-d-build-plan.md with explicit
  per-step Files / Done when / Existing context sections, then
  re-run with --enrich to bring issues to richer state.

Result: SYNCED
Next: /build-phase --plan documentation/plans/phase-d-build-plan.md — run in <absolute-project-dir>
```

Every run, a stop included, ends with these two lines, `Next:` last:

- `Result: SYNCED` — every planned action succeeded (a run whose rows are all NO-OP included) and every plan step has a usable `**Issue:**` value. `Next: /build-phase --plan <plan> — run in <absolute-project-dir>` (the Step 0 target).
- `Result: PARTIAL (<detail>)` — at least one `gh` action failed, creates were held (Step 3), the Step 7b plan write failed, or a plan step is left without a usable `**Issue:**` value — `PARTIAL (<n> steps without issue: <reasons>)`, reasons from collision-held, multiple-match, failed or held create, closed footer missing, missing field, mismatch; each failure is listed above. Completed actions stand. `Next: /repo-sync --plan <plan> — run in <absolute-project-dir>` after fixing the cause; a re-run converges.
- `Result: DRY-RUN` — after `Dry-run complete. No changes applied.`; `Next:` is the same command without `--dry-run`.
- `Result: NOT RUN (<reason>)` — a stop before any mutation (missing or unreadable `--plan`, no steps found, no or wrong target repo, missing prerequisite evidence, issue list unavailable). `Next:` names the fix; for missing evidence, the missing gate per Prerequisites, then this command.

> Next-step commands name their target directory, and the proactive project-switch message fires on a cwd≠project mismatch with no pin, per transition-directory-contract.md.

---

## Matching rules (extended)

Issue matching is prefix-based on the step key. The skill normalizes:
- Whitespace
- Phase notation: `Phase D` ≡ `Phase D` (no normalization across letter/digit; B != 2; D != 4)
- Sub-phase: `Phase G.2 Step 1` matches plan `G.2.1` or `Step 1` within phase G.2

Manually renamed issue titles still match as long as the step prefix
(`Phase X Step N` or `Phase X.M Step N`) is preserved.

---

## Edge cases

- **Cross-plan step-key collision:** Step keys collide when a
  repo holds issues from multiple plans (`Phase D Step 3`
  exists in plan A and plan B). The Step 3.1 check (see Flow)
  flags these via the body footer's plan path. Workaround for
  new plans that share step keys with closed prior plans:
  bypass `/repo-sync` for the new plan and create issues
  manually with namespaced titles (`<feature> — Phase X Step
  N: <name>`); those manual issues will not be re-matched by
  future runs. See investigation
  `docs/investigations/skill-deep-dives/repo-sync/01-step-key-collision.md`.
- **Closed issue, step still in plan:** Log it as an informational note in the sync report and skip mutation (do not reopen, do not prompt). The operator can reopen manually if needed. Step 7b may still fill a blank `**Issue:**` with its number, but only when the issue's footer names this plan (Step 7b § Map).
- **Multiple issues match same step key:** Warn and skip — user must resolve manually.
- **Plan has no umbrella H1, just steps:** Skip umbrella creation; only step issues.
- **No steps found:** Error: `No steps found in <path>. Expected "### Step N:", "### Phase X Step N:", or "| X.N | ... |" table row.`, then `Result: NOT RUN (no steps found)`.
- **No GitHub repo:** See Step 0 — Pre-flight. The resolve command halts early if no repo is found (`Result: NOT RUN`).
- **Numbering gaps:** If plan jumps from Phase 7 to Phase 9 (intentional), don't try to create Phase 8. Honor the plan as written.
- **Existing umbrella, plan adds new steps:** Create new step issues + re-edit umbrella to add their links.
- **Step issue exists but lean, build doc still lean:** ENRICH would be a no-op. Recommend doc enrichment in summary; do not edit issue.

---

## Common mistakes

**Batching gh calls in one shell command**
- Fix: One `gh issue create/edit/close` per call, separate Bash tool invocations OR a loop in one Bash with explicit per-iteration error handling.

**Halting mid-sync for confirmation**
- Fix: Preview-then-execute is the default; no `(y/n)` prompt. Operators who want preview-only behavior pass `--dry-run`. Autonomous orchestrators (`/build-phase`, `/plan-expedite`) depend on this — a mid-sync halt breaks them.

**Matching by issue number instead of title prefix**
- Fix: Issue numbers change. Always match by the step-key prefix in the title.

**Using Perl-style regex escapes in `--jq` filters**
- Fix: jq's regex engine does NOT accept `\d`, `\w`, `\s`, `\.`
  (and most other Perl-style shorthand). It silently rejects
  the filter or returns empty matches — failing the
  classification, which then surfaces as duplicate-issue
  CREATEs in Step 5 preview. Use POSIX classes or literal
  character sets:

  | Avoid | Use |
  |---|---|
  | `\d` | `[0-9]` |
  | `\w` | `[a-zA-Z0-9_]` |
  | `\s` | `[ \t\n\r]` (POSIX whitespace; or the named class with single-bracket pairs the engine supports) |
  | `\.` | `[.]` |

  Prefer regex-free forms when the prefix is fixed:
  `startswith("Phase D")` beats `test("^Phase D")` and
  sidesteps the escape limit entirely.

  Reference: `feedback_jq_regex_escape_limits.md` and
  investigation `docs/investigations/skill-deep-dives/repo-sync/13-jq-regex-escaping.md`.
  PowerShell-specific quoting issues for `gh -q` are
  documented in `dev/.claude/rules/windows-shell.md` § gh / jq.

**Lean bodies on creation**
- Fix: Run the doc richness check first. If steps are lean, propose enriching the build doc before creating issues. Don't normalize lean issues as the steady state.

**Forgetting umbrella back-references**
- Fix: After creating step issues, edit the umbrella to include the **Work** checklist with issue numbers. Bidirectional links matter.

**Ignoring sub-phase notation**
- Fix: Phase G.2 is its own phase, not "Phase G". Match titles accordingly.

**Skipping the doc-richness warning**
- Fix: A lean issue taxes future LLM sessions every time someone opens it. Surface this cost explicitly; default to enriching the doc first.

**Treating issue creation as one-shot**
- Fix: `--enrich` exists because issues drift behind build docs over time. Re-run the skill after each plan revision.
