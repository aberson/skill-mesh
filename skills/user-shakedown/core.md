# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- This skill ships no runtime scripts. It requires the packaged shared contract at `<repo>/_shared/shakedown-engine.md`; repository-only eval inputs are not runtime assets.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# User shakedown

Autonomous **ledger closure**. Where `/user-walkthrough` yields to the operator each turn, this
skill drives itself: it works down the ledger's open items — verifying, quick-fixing, or logging
each — until the ledger has zero open items. It is **pipeline-autonomous**: no confirmation
prompts, and at wrap it EXECUTES the closers rather than offering them. It STOPS (by logging,
never guessing) on anything that genuinely needs operator judgment.

The ledger it reads and writes is defined once in
`<repo>/_shared/shakedown-engine.md` — this skill
never redefines the row grammar, slug rule, or status vocabulary; it cites the engine. Because
it uses the same slug rule, it resolves the **same** ledger file a `/user-walkthrough` may have
started, and picks up mid-stream (load-before-derive per the engine — never re-seed).

Before acting, read `<repo>/_shared/shakedown-engine.md` in full, resolving `<repo>` as the
loaded Skill Mesh package root rather than the target project's git root. If it cannot be read,
stop with `required_tool_missing: <repo>/_shared/shakedown-engine.md`, write nothing, and never
reconstruct the grammar from memory.

## When to use / not

- **Use:** UAT needs to be *closed out* on a just-built feature and you want the agent to do it
  autonomously — ideally armed under a `/goal` so it re-drives itself every turn until the
  ledger is clean. Good for draining a walkthrough's leftover open rows, or a fresh closure pass.
- **Don't use** when you want to drive the exploration yourself (that is `/user-walkthrough`),
  when you have an already-clear script to just execute (`/user-uat`), or to refine a fuzzy UAT
  (`/review-uat`).

## Invocation

```text
/user-shakedown <tool/feature>     # autonomous closure of the named build's ledger
```

Invoke with the same argument a prior `/user-walkthrough` used; the slug keys off the raw
argument (engine §1).

## Inputs, writes, and re-runs

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

## Local git safety rules

These rules are complete even when the optional workspace policy documents are unavailable.

**Wrong-directory guard.** Before any `git add`, commit, or push, resolve the intended target
repository in this order: a verified `/user-project` pin; the repository identified by the
explicit invocation argument or the feature's plan; otherwise the current directory's git root.
An unreadable or merely announced pin is not verified: do not invent its path; report that it was
not used and continue down the precedence list. Resolve the actual commit repository with
`git rev-parse --show-toplevel` from the directory where git would run. Compare normalized full
paths (trim trailing separators; compare case-insensitively on Windows). If they differ, emit one
line naming both repositories and stating that the git action here lands in the actual commit
repository, then proceed because the guard is advisory. If they match, remain silent.

**Own-change boundary.** Before editing a candidate file, inspect both the index and worktree,
including untracked state. Edit it only when that path is clean; otherwise leave it untouched and
keep the row `open`, or mark it `logged` when separation is no longer a small fix, naming the
mixed-change file. Record the clean file's baseline identity and, after a successful applicable
test, the exact activity patch. Before staging, recheck the index and each eligible path. If any
unrelated entry is already staged, or an eligible path's current patch differs from the recorded
activity patch, do not stage or commit; report a commit hold and preserve every existing index and
worktree change. Never reset or rewrite another actor's index. Only verified `fixed` paths whose
patches still match are eligible. After scoped staging, verify that the cached path set and cached
diff equal exactly those recorded patches before an ordinary commit; on any mismatch, make no
commit and report the staged state without resetting it.

## Flow

### 1. Entry — resolve or derive the ledger; check operator prerequisites

Compute the feature-slug and resolve the ledger path via `git rev-parse --show-toplevel` per the
engine reference. Before resolving or writing a ledger, honor the engine's identity rules. An
empty normalized slug or ambiguous near-match is an **identity hold**: request the specific slug
or scope clarification the engine requires, write nothing, skip wrap, and stop this run. **Load
the ledger if it exists** (never re-seed); else derive it per the engine's checklist-derivation
rules. Because the slug rule is shared, this is the exact file a `/user-walkthrough <same
feature>` would have written.

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

### 2. Closure loop — one open item at a time

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

### 3. STOP-not-guess rule (the escape hatch)

Anything that needs operator judgment — an ambiguous expectation, a design call, a
visual/credentialed/real-device check the agent cannot drive, an outward-facing action the
verify step must not run — is **parked as `logged` with the judgment question recorded in the
evidence cell**, never auto-resolved with a fabricated verdict.
Logging IS the no-guess escape hatch: it keeps zero-open reachable without the agent inventing a
pass it can't stand behind. A guessed verdict is a contract violation; a logged question is
correct behavior.

### 4. Wrap — EXECUTE the closers (autonomous)

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
   `user-shakedown <feature-slug> <row id>: <first clause of the diagnosis or question>`.
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

## Designed for /goal

This skill is built to run **armed under a `/goal`**. The canonical arm command (copy-paste,
from the engine) is:

```text
/goal "shakedown ledger for <feature-slug> has zero open items"
```

The condition is checkable **every turn** by running the engine's zero-open check block and
asserting `UNSATISFIED == 0`. The Stop hook re-drives this skill each turn until the ledger is
clean — the termination condition IS the goal condition, which is exactly why the autonomous
mode is the one designed to be armed (the inverse of `/user-walkthrough`, which must never arm a
`/goal` mid-loop).

Arm it only once every operator-started prerequisite the open rows need is running: a finish line
that waits on the operator cannot be driven to true by the agent. On a prerequisite hold under an
armed goal, each re-driven turn re-probes once, repeats the one-line hold report, and recommends
`/goal clear`; it never polls.

## Constraints

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

| Skill | What it does |
|---|---|
| `/user-uat` | EXECUTES an already-clear UAT script FOR the operator under its own evidence and confirmation gates. |
| `/review-uat` | REFINES a fuzzy UAT script until every step is unambiguous. |
| `/user-walkthrough` | The operator DRIVES exploration; the agent answers, fixes small, logs big. |
| `/user-shakedown` | **This skill.** The agent AUTONOMOUSLY CLOSES the ledger to zero open items. |

`/user-walkthrough` and `/user-shakedown` share one ledger file (same slug rule → same path), so
this skill can pick up a walkthrough's half-filled ledger and drive it to zero.
