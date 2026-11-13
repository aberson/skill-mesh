# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- This skill ships no runtime scripts. It requires the packaged shared contract at `<repo>/_shared/shakedown-engine.md`; repository-only eval inputs are not runtime assets.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# User walkthrough

Attended, **operator-driven** UAT. You (the operator) drive; the agent rides along. Each turn
you ask a question or point at a problem; the agent answers from PRIMARY SOURCE (reads the
actual code/artifact, cites `file:line` — never vibes), marks any coverage the exchange earned,
routes issues to fix-now or log-for-later, then **stops and hands the turn back**. Coverage
accrues as a byproduct of poking the build, not as a script you march through.

The ledger it reads and writes is defined once in
`<repo>/_shared/shakedown-engine.md` — this skill
never redefines the row grammar, slug rule, or status vocabulary; it cites the engine.

Before acting, read `<repo>/_shared/shakedown-engine.md` in full, resolving `<repo>` as the
loaded Skill Mesh package root rather than the target project's git root. If it cannot be read,
stop with `required_tool_missing: <repo>/_shared/shakedown-engine.md`, write nothing, and never
reconstruct the grammar from memory. Other workspace policy references cited below are optional
context; if one is unavailable, say so, apply this core's complete local rule, and never
reconstruct the missing document.

With `--shakedown`, the same skill instead runs the engine's autonomous mode, which closes the
ledger to zero open items by itself: see **Shakedown mode (`--shakedown`)**. Everything outside
that section describes the attended mode.

## When to use / not

- **Use:** a tool or feature was just built (post-`/build-phase`, post-`/build-step`, or a
  fresh `/user-debug`) and you want to poke it yourself — ask how it works, try things, surface
  issues — with the agent answering from source, fixing small breakage live, and tracking what
  got covered. You want to be in the driver's seat.
- **Use `--shakedown`:** UAT needs to be *closed out* on a just-built feature and you want the
  agent to do it autonomously — ideally armed under a `/goal` so it re-drives itself every
  turn until the ledger is clean. Good for draining a walkthrough's leftover open rows, or a
  fresh closure pass.
- **Don't use** the attended mode when you want the agent to close out UAT autonomously (that
  is `--shakedown`). Don't use either mode to execute an already-written UAT block for you
  (`/user-uat`) or to refine a fuzzy UAT script (`/review-uat`). If you have no build to poke yet, there is nothing
  to walk through.

## Invocation

```text
/user-walkthrough <tool/feature>     # attended walkthrough of the named build
/user-walkthrough export-button      # slug resolves the ledger per the engine's slug rule
/user-walkthrough --shakedown <tool/feature>     # autonomous closure (Shakedown mode below)
```

Use the argument a later `--shakedown` run will use: the slug keys off the raw argument
(engine §1), so a near-miss starts a second ledger.

Its one flag is `--shakedown` (**Shakedown mode** below). Without it, it runs in this same
attended, offer-only mode, including when invoked bare. With no argument the attended mode
never computes an empty slug and never writes a ledger: if exactly one
`shakedown-*.md` ledger exists under `<git-root>/.claude/task-state/`, offer it by path but load
it only after the operator confirms that it is the intended feature scope (a lone ledger is not
identity proof); otherwise ask once which feature to walk through, and yield.

## Inputs, writes, and re-runs

- **Inputs:** the `<tool/feature>` argument; the existing ledger, else the feature's plan (engine
  §4); the working tree; the operator's questions and reports.
- **Writes the skill makes on its own (only these):** the ledger; live-tree small fixes;
  disposable test, verification and issue-body files (never committed); at wrap, only the
  closers the operator selects (one local commit; GitHub issues). It never pushes or opens a
  pull request on its own, and no closer does. Any outward-facing or hard-to-reverse action,
  including a push or pull request, runs only when the operator explicitly asks for that
  specific action, and any `git add`, commit or push gets the wrong-directory guard first
  (**Running things**). Never write into a plan's `## Manual UAT` block (**Constraints**).
- **Re-runs.** An existing ledger is loaded, never re-seeded. Fixes stay uncommitted until the
  operator selects the commit closer; every row whose fix edited the tree names the edited
  path(s) in its evidence, so a later wrap can find them. A row whose evidence ends with
  `filed #<n>` is never filed again. One gap remains: if GitHub creates an issue but the marker
  is never written (`gh` errors after creation, or the session ends first), the next selection
  files that row again.

## Local git safety rules

These rules are complete even when the optional workspace policy documents are unavailable.
Before any `git add`, commit, or push, resolve the intended target repository in this order: a
verified `/user-project` pin; the repository identified by the explicit invocation argument or
the feature's plan; otherwise the current directory's git root. An unreadable or merely announced
pin is not verified: do not invent its path; report that it was not used and continue down the
precedence list. Resolve the actual commit repository with `git rev-parse --show-toplevel` from
the directory where git would run. Compare normalized full paths (trim trailing separators;
compare case-insensitively on Windows). On mismatch, emit one advisory line naming both
repositories and stating where the git action lands, then proceed; on a match, remain silent.

Before editing a candidate file, inspect its index, worktree, and untracked state. Edit it only
when that path is clean; otherwise leave it untouched and keep the row `open`, or mark it
`logged` when separation is no longer a small fix, naming the mixed-change file. Record the
clean baseline identity and, after a successful applicable test, the exact activity patch.
Before staging, recheck the index and each eligible patch. Any unrelated pre-existing staged
entry, mixed-change path, or patch mismatch makes the commit closer hold without staging or
committing. Preserve every existing index/worktree change and never reset or rewrite another
actor's index. Only verified `fixed` paths whose patches still match are eligible. After scoped
staging, verify that the cached path set and diff equal exactly the recorded patches; on mismatch,
make no commit and report the staged state without resetting it.

## Flow

### 1. Entry — orient, establish the contract

1. **Resolve or derive the ledger** per the engine reference. An empty normalized slug or
   ambiguous near-match is an identity hold: ask for the engine-required slug/scope clarification,
   write nothing, and yield. Otherwise compute the feature-slug, resolve
   the ledger path via `git rev-parse --show-toplevel`, and **load it if it already exists**
   (never re-seed — a prior walkthrough or shakedown may have started it). If absent, derive it
   per the engine's checklist-derivation rules (seed from the plan's `## Manual UAT` /
   `Type: operator` M-steps when present; else a lightweight derived expectation set). Outside a
   git repository there is no ledger path: say so and stop; never write a cwd-relative ledger.
   Run the engine's structural check before changing rows. A missing/unreadable ledger, check
   abort, invalid header/separator/order, read failure, or malformed data row is an integrity
   hold: report it, change no row or live-tree file, and yield. A malformed non-`open` row is
   never treated as ordinary open work or silently repaired.
2. **Check operator-started prerequisites.** When the plan, an M-step, or the project
   instructions name the operator as the one who starts a server, device, or session, never
   start, spawn, or background it. Check it only with a plainly read-only probe (port, HTTP
   status, process list). If it is down, report `<service> is down`, restate its documented
   start command and directory, and yield; carry on once the operator says it is running.
3. **State the operating contract once**, then yield: "I'll answer from source with `file:line`,
   fix small things in-tree and show you, log big ones, and mark coverage as we go. You drive —
   ask or point at anything." Optionally kick off the tool and show its output to seed the first
   turn — a local, disposable run only (see **Running things** below).

### 2. Loop — one operator turn at a time

Per turn the operator asks a question or reports a problem. The agent:

1. **Answers from PRIMARY SOURCE.** Read the actual code/artifact and cite `file:line`. Never
   answer a "does it / how does it" question from memory or inference — open the file. A
   confidently-wrong answer from vibes is worse than "let me check."
2. **Marks coverage earned this turn.** If the exchange exercised a behavior matching a ledger
   row, mark that row `satisfied` with concrete evidence (the command output / observed result /
   `file:line`) per the engine's coverage-marking rule — never a bare status flip. Show each mark
   (row, status, evidence) in the response; an operator correction wins.
3. **Routes any issue** by size, per the engine's two paths:
   - **Small + unambiguous → fix it now, in the live tree.** Apply **Local git safety rules**,
     edit only a clean candidate path in place (uncommitted), and run the NARROWEST applicable
     test. Mark the row `fixed` only after that test succeeds, with evidence naming the edited
     path, command, and passing result. Do **not** spin a `/build-step` worktree; the fix must be visible to the
     running tool immediately. **Never block on a (y/n) for your own small fix — just make it
     and report what you did.** No applicable test, a missing test, or a red/erroring test never earns `fixed`: report
     its output verbatim, undo only your own edit (never a whole-file checkout or restore that
     would discard other uncommitted work), and leave the row `open` (a new row is appended
     `open`) with the failing result as evidence — or mark it `logged` with a one-line
     diagnosis when the failure shows the defect is not small. If the operator asks to keep or
     re-apply the edit, re-apply it; the row stays `open` or `logged` (never `fixed`), its
     evidence names the still-edited path and the red result, and the wrap flags and excludes
     the file from its commit closer.
   - **Big → log it, don't rabbit-hole.** Append the row `logged` with a one-line diagnosis and
     move on; it becomes a sibling issue at wrap.
4. **STOP and hand the turn back.** One operator ask → one agent response → stop. Do not keep
   working, do not chain into the next check unprompted, do not march a script. Yielding is the
   whole point of the attended mode.

**Operator reports.** When the operator says something works or looks fine, still run the
agent-side check the row allows (`.claude/references/plan-and-issue-flow.md` § UAT push back).
If it agrees, mark the row with both (`operator: <their words>` plus your evidence); if it
disagrees, report the discrepancy verbatim and ask one disambiguating question instead of
marking. A row only the operator can judge (visual, feel, a real device) is marked only from the
operator's own stated observation, quoted.

**Running things.** On your own initiative, run only local, disposable commands: the tool, the
narrowest test, a read-only probe. The small-fix path's in-place edits and the ledger are the
only non-disposable writes you make unasked. An outward-facing or hard-to-reverse action — a
deploy, an external send, a `git push`, a pull request, a publish, a write or drop on
non-disposable data — runs only when the operator asks for that specific action in a turn;
otherwise answer from source and name the command. Before any `git add`, commit or push —
closer 1, or one the operator asks for, including a pull request that pushes a branch — apply
the complete advisory guard and own-change boundary in **Local git safety rules**.
Prefer the tool's own `--dry-run`/preview. When reversibility or outward-facing-ness is
unclear, treat it as outward-facing.

### 3. Wrap — "did I miss anything?"

When the operator signals they're done (or asks for a wrap), report coverage in three buckets:
`satisfied` (with evidence), still-`open`, and `logged` bigs. Name the ledger path and any files
this walkthrough edited that are still uncommitted, flagging any whose last narrowest test was
red. Then **offer** — do not execute — three closers:

1. **Batch-commit the verified live fixes** as one reviewable diff under **Local git safety
   rules**, using scoped `git add <paths>` only after its checks (never `git add -A`). The offer lists eligible files —
   the edited path(s) this walkthrough's row evidence records (**Re-runs**), never a file a row
   only cites — with their `git diff --stat` and passing applicable tests. It separately lists
   and excludes any mixed-change, retained, red/erroring, or missing-test file. It offers the project's declared full suite first;
   narrowest tests alone are not full-suite gate evidence. When selected: apply the
   local wrong-directory guard and before-staging boundary; never stage the ledger or an
   ineligible file; never include unrelated pre-existing staged work in the ordinary commit;
   never bypass hooks. On a hold or failure, report it verbatim and preserve the worktree and
   index without resetting another actor's state.
2. **File the logged bigs** as GitHub sibling issues (via `gh` with `--body-file`) that feed
   `/plan-feature` or `/build-step`. The offer names the target — the `owner/name` of the git
   root's `origin` GitHub remote (none → say so; nothing can be filed) — and each unfiled row
   with the exact title it would get.
   When selected, for each `logged` row whose evidence does not end with `filed #<n>`: write the
   body — the row id, the repo-relative ledger path and the one-line diagnosis, nothing else
   from the evidence cell — to a disposable temp file that `gh` can read, outside the repository
   tree (never staged); run `gh issue create --repo <owner/name> --title <title> --body-file <file>`,
   where `<title>` is `user-walkthrough <feature-slug> <row id>: <first clause of the diagnosis>`
   with backticks and quote characters removed, passed as one literal argument (never inside
   shell double quotes); then append `filed #<n>` as the evidence cell's last token (status
   unchanged). On failure, leave the row unmarked, report `not filed: <reason>` with the error
   verbatim, and never invent an issue number; after a `gh` error, say the issue may already
   exist on `<owner/name>` and should be checked before re-selecting. These target, title,
   body, marker and failure rules apply to any filing transport, including a host GitHub tool
   used instead of `gh`.
3. **Emit the canonical `/goal` string** from the engine to hand autonomous closure to
   this skill's `--shakedown` mode (`/user-walkthrough --shakedown <same argument>`):
   `/goal "shakedown ledger for <feature-slug> has zero open items"`

The operator picks which closers to run — this is the attended mode; the operator decides.
Report what each selected closer did: the commit hash (or why there is none), the target
repository, and for each row the issue filed (number or URL), skipped, or not filed (with the
reason).

## Constraints

- **MUST NOT arm a `/goal` DURING the attended loop.** A `/goal` arms a Stop hook that re-prompts the
  *agent* every turn until its condition holds — which makes the session agent-paced and
  destroys the operator-driven dynamic (the agent would keep working instead of yielding to
  you). The `/goal` string is **emitted at wrap only**, opt-in, for the operator to paste. This
  is the single hardest rule in this skill's attended mode; `--shakedown` is the mode designed
  to be armed (**Designed for /goal**).
- **Never block on a (y/n) for the skill's own small fixes.** Make the fix, run the narrowest
  test, report it. The operator is already in the loop every turn; a confirmation gate is noise.
- **Never write into any plan's `## Manual UAT` block.** That block is append-only and owned by
  `/build-phase`. The ledger is a SEPARATE task-state artifact (per the engine's path formula) —
  status lives there, never in plan.md.
- **Answer from primary source, always.** Every substantive claim cites `file:line`. No vibes.
- **Small fixes stay in the live tree, uncommitted until wrap.** No worktree; scoped commit at
  wrap only.
- **No prerequisite starts, no unasked outward actions, no invented operator verdicts** (Entry
  step 2, **Running things**, **Operator reports**). A ledger with zero open items can still
  hold `logged` defects; never report it as the operator's acceptance.
- **No secrets in the ledger or in issue titles and bodies.** Record metadata or a redacted
  excerpt, never a credential or secret file's contents. Issues leave the machine: repo-relative
  paths only — no home-directory paths, bare local usernames as path segments, private harness
  metadata paths or slugs, or paths that leave the target repository (`../…`).

## Shakedown mode (`--shakedown`)

Autonomous **ledger closure**. Where the attended mode yields to the operator each turn,
`--shakedown` drives itself: it works down the ledger's open items — verifying,
quick-fixing, or logging each — until the ledger has zero open items. It is
**pipeline-autonomous**: no confirmation prompts, and at wrap it EXECUTES the closers rather
than offering them. It STOPS (by logging, never guessing) on anything that genuinely needs
operator judgment. It uses the same engine, slug rule and ledger file as the attended mode,
so it resolves the **same** ledger an attended walkthrough may have started and picks up
mid-stream (load-before-derive per the engine — never re-seed). The engine requirement and
the **Local git safety rules** above apply to this mode in full. Everything outside this
section describes the attended mode.

```text
/user-walkthrough --shakedown <tool/feature>     # autonomous closure of the named build's ledger
```

Invoke it with the same argument a prior attended walkthrough used; the slug keys off the raw
argument (engine §1).

### Shakedown inputs, writes, and re-runs

- **Inputs:** the `<tool/feature>` argument; the existing ledger, else the feature's plan per the
  engine's checklist-derivation rules; the working tree the rows exercise.
- **Writes (only these):** the ledger file; live-tree small-fix edits (including an accurately
  reported retained edit whose verification failed and which is never eligible for commit); disposable
  verification and test state (never committed); at wrap, one local commit of this run's fix
  files and, only in an operator-owned target repository, one GitHub issue per unfiled `logged`
  row. Never push, never open a pull request, never write into a plan.
- **Re-runs.** An existing ledger is loaded, never re-seeded. A closed ledger probes nothing and
  goes straight to wrap, where a run that edited nothing makes no commit and a row whose evidence
  ends with a `filed #<n>` marker is never filed again. One gap remains: if GitHub creates an
  issue but the marker is never written (`gh` errors after creation, or the session ends first),
  the next wrap files that row again.

### S1. Entry — resolve or derive the ledger; check operator prerequisites

Compute the feature-slug and resolve the ledger path via `git rev-parse --show-toplevel` per the
engine reference. Before resolving or writing a ledger, honor the engine's identity rules. An
empty normalized slug or ambiguous near-match is an **identity hold**: request the specific slug
or scope clarification the engine requires, write nothing, skip wrap, and stop this run. **Load
the ledger if it exists** (never re-seed); else derive it per the engine's checklist-derivation
rules. Because the slug rule is shared, this is the exact file an attended `/user-walkthrough
<same feature>` would have written.

Run the engine's structural and zero-open check before the closure loop. A missing or unreadable
ledger, check abort, invalid header/separator/order, read failure, or any malformed data row is an
**integrity hold**: report the exact failure or malformed row, change no ledger row or live-tree
file, skip wrap, and stop this run. A malformed non-`open` row is not an ordinary loop candidate;
never re-drive an empty loop around it or invent its intended status. The operator may correct the
ledger or clarify its source, then re-run. `UNSATISFIED == 0` is completion only when the check
exits successfully.

**Operator-started prerequisites.** When the plan, an M-step, or the project instructions name
the operator as the actor who starts a server, device, or session ("run X from a fresh
PowerShell window"), treat it as a precondition of the `open` rows that need it. Probe only the
prerequisites at least one `open` row needs; a closed ledger probes nothing. Check each only with
a plainly read-only probe (port, HTTP status, process list); never start, spawn, or background
it, not even to probe. If the probe shows it down, this is a **prerequisite hold**: report the
service, its documented start command, and the target directory; leave every row unchanged; skip
the wrap; stop. If no read-only probe can check it, say so in the report and continue; a row that
then cannot be verified without it is parked per the STOP-not-guess rule with the prerequisite
named, and is filed at wrap like any other `logged` row.

### S2. Closure loop — one open item at a time

For each row still `open`, choose exactly one disposition and record evidence:

- **Verify → `satisfied`.** Exercise the behavior, capture the result, mark the row `satisfied`
  with concrete evidence (command output / observed result / `file:line`). Never a bare flip.
  Verification runs against the local working tree and disposable state. Never run an
  outward-facing or hard-to-reverse action to verify — a deploy, an external send, a `git push`,
  a publish, a write or drop on non-disposable data, or a tool run that writes into a sibling
  repository. Prefer the step's
  own `--dry-run`/preview; otherwise park the row per the STOP-not-guess rule with the action
  named. When reversibility or outward-facing-ness is unclear, treat it as outward-facing.
- **Quick-fix in-tree → `fixed`.** If the item is a small, unambiguous defect and its candidate
  file passes the own-change boundary: edit the live tree (uncommitted) and run the NARROWEST
  applicable test. Mark the row `fixed` only when that test succeeds, with the edited path,
  command, and passing result as evidence. No applicable test, a missing/erroring test, or a red
  result never earns `fixed`. Record the failure truthfully and undo only this activity's exact
  patch when it can be reversed without altering concurrent work. If it cannot, retain and
  report the edit but exclude it from the commit set. Keep the row `open` only for another
  bounded small attempt; otherwise mark it `logged` with the unresolved diagnosis. A prerequisite
  or environment failure that prevents the test is a hold, not proof of a product defect. No
  worktree (per the engine's small-fix path).
- **Log → `logged`.** If it is too big to fix inline, OR it needs operator judgment (see the
  STOP-not-guess rule), append a one-line diagnosis and mark the row `logged`. Do not
  rabbit-hole.

Repeat until the engine's zero-open check reports `UNSATISFIED == 0` — that is the **only**
completion condition. Re-run the check each pass; when it returns 0, the ledger is closed.

Identity, integrity, prerequisite, and required-capability holds do not complete anything. They
are finite fail-closed outcomes, not zero-open success; follow the applicable no-write or
action-specific failure rule above and in the provider adapter.

### S3. STOP-not-guess rule (the escape hatch)

Anything that needs operator judgment — an ambiguous expectation, a design call, a
visual/credentialed/real-device check the agent cannot drive, an outward-facing action the
verify step must not run — is **parked as `logged` with the judgment question recorded in the
evidence cell**, never auto-resolved with a fabricated verdict.
Logging IS the no-guess escape hatch: it keeps zero-open reachable without the agent inventing a
pass it can't stand behind. A guessed verdict is a contract violation; a logged question is
correct behavior.

### S4. Wrap — EXECUTE the closers (autonomous)

Runs only after the zero-open check returns 0. Because this mode is pipeline-autonomous and the
operator's standing default is to file sibling issues without asking, at wrap it EXECUTES rather
than offers:

1. **Batch-commit the verified live fixes** as one reviewable diff under **Local git safety
   rules**, using scoped `git add <paths>` only after the before-staging checks (never
   `git add -A`). No eligible files → no commit. A red, erroring, missing-test, retained,
   mixed-change, or patch-mismatch file is ineligible. Never stage the ledger or sweep changes
   this run did not make (for example a prior walkthrough's live fixes), and never include
   unrelated pre-existing staged work in an ordinary commit; list every exclusion or commit
   hold in the report. Never bypass hooks; if staging verification or commit fails, report the
   error verbatim and leave the live tree and index intact.
2. **File each unfiled `logged` row as a GitHub sibling issue** via `gh issue create` with
   `--repo <owner/name>`, `--title`, and `--body-file` (the body carries the one-line diagnosis /
   judgment question), feeding `/plan-feature` or `/build-step`. Title shape:
   `user-walkthrough --shakedown <feature-slug> <row id>: <first clause of the diagnosis or question>`.
   - **Target.** Resolve it once, before filing: the `owner/name` of the `origin` GitHub remote
     of the ledger's git root. No such remote → each row is `not filed: no GitHub remote`.
   - **Ownership gate (fail closed).** File only into an operator-owned target: every entry of
     the workspace registry (`.claude/observatory/registry.toml`, when readable; `owned` per
     `.claude/references/descriptor-contract.md` §2) whose `repo_url` names the target or whose
     `path` is this git root says `owned = true`; or, when no entry matches, the target owner
     equals the authenticated `gh` login. Otherwise, or when the check cannot complete, file
     nothing: each row is `not filed: target repo not operator-owned (<owner/name>)`.
   - **Marker.** A row is already filed when its evidence cell ends with `filed #<n>` (the
     trailing token, as in the engine's fixture); skip it. A `filed #<n>` elsewhere in the
     diagnosis does not count. After each successful filing, append `filed #<n>` as the evidence
     cell's last token; the status does not change.
   - **Failure.** If filing fails (no GitHub remote, a target not operator-owned, `gh` missing or
     unauthenticated, an API error), leave the row unmarked, report it as `not filed: <reason>`,
     and continue. Never invent an issue number.

Then report the final ledger state and confirm `UNSATISFIED == 0`, with the commit hash (or why
there is none), the target repository, the issues filed (number or URL), skipped, or not filed
(with the reason), and any uncommitted changes left for the operator.

### Designed for /goal

This mode is built to run **armed under a `/goal`**. The canonical arm command (copy-paste,
from the engine) is:

```text
/goal "shakedown ledger for <feature-slug> has zero open items"
```

The condition is checkable **every turn** by running the engine's zero-open check block and
asserting `UNSATISFIED == 0`. The Stop hook re-drives this mode each turn until the ledger is
clean — the termination condition IS the goal condition, which is exactly why the autonomous
mode is the one designed to be armed (the inverse of the attended mode, which must never arm a
`/goal` mid-loop).

Arm it only once every operator-started prerequisite the open rows need is running: a finish line
that waits on the operator cannot be driven to true by the agent. On a prerequisite hold under an
armed goal, each re-driven turn re-probes once, repeats the one-line hold report, and recommends
`/goal clear`; it never polls.

### Shakedown constraints

- **No routine confirmation prompts.** A `(y/n)` gate during valid autonomous row closure is a defect here (per
  `plan-and-issue-flow.md` § autonomous-by-default).
  The skill decides and acts; it does not check in mid-run. Engine-required slug/scope
  clarification is permitted before closure because no safe ledger identity exists. Integrity,
  prerequisite, and capability holds report and stop rather than guessing.
- **Never guess a verdict.** Judgment items are `logged` with the question, not auto-passed.
- **Evidence on every status change.** A flip with no evidence cell content is a contract
  violation (the engine's coverage-marking rule).
- **Never write into any plan's `## Manual UAT` block.** Append-only, owned by `/build-phase`;
  the ledger is a separate task-state artifact.
- **Small fixes in the live tree, no worktree; scoped commit at wrap.** Never `git add -A`.
- **Never start an operator-started prerequisite or run an outward-facing action to verify.**
  Report and stop (Entry), or park the row (Verify).
- **Never file into a repository the operator does not own.** The wrap's ownership gate fails
  closed and reports `not filed`.
- **No secrets in the ledger or in issue titles and bodies.** Record metadata or a redacted
  excerpt, never a credential or secret file's contents. Issues leave the machine: use
  repo-relative paths, never home-directory paths or private harness metadata paths and slugs.

## Limitations — four-mode disambiguation

Four sibling UAT modes; pick by who drives and what shape the input is:

| Skill | What it does |
|---|---|
| `/user-uat` | EXECUTES an already-clear UAT script FOR you under its own evidence and confirmation gates. |
| `/review-uat` | REFINES a fuzzy UAT script until every step is unambiguous. |
| `/user-walkthrough` | **This skill** (attended mode). The operator DRIVES exploration; the agent answers, fixes small, logs big. |
| `/user-walkthrough --shakedown` | **This skill** (autonomous mode). The agent AUTONOMOUSLY CLOSES the ledger to zero open items (same engine). |

The two modes share one ledger file (same slug rule → same path), so `--shakedown` can pick up
a walkthrough's half-filled ledger and drive it to zero.

## Canonical example — one loop turn

> **Operator:** "Does the CSV export respect the active date filter?"
>
> **Agent:** Reads `src/export/csv.py:41-58` — the query is built from `request.filters` and the
> date range is applied at line 47. Cites it: "Yes — `csv.py:47` folds `filters.date_range`
> into the WHERE clause before serialization." Marks ledger row `M1` **satisfied** with
> evidence `csv.py:47 applies date_range`. **Stops, hands the turn back.**
>
> **Operator:** "The export button label says 'Exprot'."
>
> **Agent:** Small + unambiguous → fixes it in the live tree (`templates/export.html:12`), runs
> the narrowest test (`pytest tests/test_export_template.py -k label` → 1 passed), marks the row
> **fixed** with that evidence. No (y/n). **Stops.**
>
> **Operator:** "Export of a 2M-row table times out."
>
> **Agent:** Big → does NOT rabbit-hole. Appends a **logged** row with the one-line diagnosis
> "streaming/pagination needed for large exports; synchronous path blocks." **Stops.**
>
> At wrap: reports `M1` satisfied, the label fixed, the timeout logged; offers to batch-commit
> the label fix, file the timeout as a sibling issue, and emit the `/goal` string for `--shakedown`.
