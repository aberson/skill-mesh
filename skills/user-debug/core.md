# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-debug/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# User Debug

> Formerly `/bug-fix`; also supersedes the public mirror's `user-fix`.

Run a bug report end-to-end: investigate, reproduce, design, fix, verify.
Avoid the command-paste loop with the user.
Run diagnostic commands yourself, read logs yourself, and verify CLI
suggestions against argparse before invoking them.
## When to use

Use `/user-debug` when:
- Something is broken and you want a fix, not just a discussion.
- You have a symptom (log line, error, screenshot) but not a confirmed root
  cause.
- You want the LLM to do the triage instead of pasting commands back and
  forth.

Use something else when:
- The fix is a one-character typo you can do faster yourself.
- You want to discuss the design before committing — use a regular
  conversation.
- The work is forward-feature, not a bug — use `/build-step`.

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--symptom` | yes | -- | What's broken. Quote the error, log line, or describe the misbehavior precisely. |
| `--repro` | no | -- | Command or steps to reproduce. If omitted, the skill derives one from the symptom. |
| `--issue` | no | -- | GitHub issue number to link/close. user-debug alone closes it, at Step 6; it is never forwarded to `/build-step` as `--issue`, because build-step closes the issue on its own PASS, before Step 5 verifies the fix. |
| `--triage` | no | `quick` | `quick` (worktree + reviewers) or `investigate-only` (Diagnosis Block then stop). `full` is accepted as a deprecated synonym for `quick` — the prior TDD-driven `full` mode delegated to `/build-step-tdd`, which was archived 2026-05-24 after 0 invocations. |
| `--review` | no | `code` | `code` (build-step's five review-gauntlet code reviewers) or `auto` (gates only). `none` is accepted as a deprecated synonym for `auto`: `/build-step --reviewers` has no reviewer-free or gate-free value, so print `--review none -> --reviewers auto (gates still run)`. Applies to both quick and full. |
| `--max-iter` | no | inherit `/build-step` | Optional positive integer ceiling on developer-reviewer rounds; forward only when explicitly supplied. |
| `--skip-verify` | no | false | Skip Step 5 (verify-against-original-repro). DANGEROUS — only use when the repro is too expensive or impossible from the skill's environment (multi-hour soak, hardware-bound, live opponent required). The skill prints a loud warning and records the skip in the final report. |

## Steps

### Step 0 — Pre-flight & memory citation

1. **Detect platform.** Check `$env:OS` / `uname` / git config to identify Windows vs Linux/Mac.
   State the detected platform in chat output ("Platform: Windows 11" or "Platform: Linux").
   Use PowerShell syntax (no `&&`, no `export`, use `$env:VAR`) for user-facing commands on Windows; bash on Linux/Mac.
   Note that the skill's own Bash tool calls are unaffected — this is for commands the user might run.
2. **Cite relevant memory.** Read MEMORY.md AND all project_*.md files in the same memory directory BEFORE Step 1 begins.
   Do this before any diagnostic commands run.
   Do not defer this scan into Step 1; it is a pre-investigation check.
   Check each entry against five categories:
   (1) **symptom keywords** (the exact error text or its component words),
   (2) **file paths** mentioned in the symptom,
   (3) **module names** (Python/JS imports referenced),
   (4) **command/tool names** (the executable that produced the error), and
   (5) **failure-mode patterns** (e.g., `silent`, `encoding`, `corrupt`, `stale path`, `subprocess`, `hang`, `race`).
   Add **every matching entry** by `feedback_*.md` filename inline — no paraphrase, cite all as the default.
   Apply the runaway-match carve-out when ≥10 entries match across all five categories combined:
   cite the most-recent 8 by file mtime plus a one-line footer ``N additional matches truncated, see `grep -l <pattern> <memory-dir>` for full list``.
   If none apply, say so explicitly.
3. **Detect project context.** Stack, test command, lint, typecheck,
   dependency install. Same detection logic as `/build-step` Step 0.
4. **Stash uncommitted changes** (only if `--triage` is `quick` or `full`):
   ```bash
   git rev-parse --show-toplevel          # the repo this run stashes
   git rev-parse HEAD                     # start commit (Step 6.4, § Stops)
   git symbolic-ref -q --short HEAD       # start branch; empty when detached
   git status --porcelain=v1 --untracked-files=all --ignore-submodules=none
   git submodule foreach --quiet --recursive 'git status --porcelain=v1 --untracked-files=all'
   # If changes exist:
   git rev-parse -q --verify refs/stash   # before; empty when no stash exists
   git stash push -m "user-debug pre-run <start sha7> <UTC yyyymmddThhmmssZ>" --include-untracked
   git rev-parse -q --verify refs/stash   # after
   git stash list --format="%gd %H %gs"   # the entry carrying this run's message
   ```
   Before `stash push`, any non-empty nested-submodule status stops as
   `STASH-FAILED (dirty submodule: <paths>)` with no git mutation: a parent
   stash cannot save that work. Ignored files are outside this proof and must
   be reported as such; they are never evidence that the filesystem is clean.
   Record a stash only when the push exits 0, `refs/stash` changed, and exactly
   one listed entry's subject ends with this run's message; that entry's `%H` is
   the run's stash identity. Exit 0 with `refs/stash` unchanged saved nothing:
   `Stash: none`. Otherwise (a non-zero push, or zero or several entries carrying
   the message) stop before Step 1 with state `STASH-FAILED`: print the push's
   first error line, `git status --porcelain` and each entry carrying the message
   as `kept <sha>`, and run no further git mutation.
   After a successful push, repeat both status checks. Any remaining tracked,
   non-ignored untracked, or submodule dirt stops before Step 1 and retains the
   owned entry; do not claim isolation. `Stash: none` is allowed only when the
   pre-stash parent status and recursive submodule status were both empty.
   State `Stash: <sha> in <toplevel>` in chat, or `Stash: none`. The run owns
   only this entry; § Stops and stash restoration says how every exit restores it.

### Step 1 — Investigation (forced; output is a Diagnosis Block, not a fix)

Do not skip this step. Output structured diagnosis with primary-source citations.

1. **Read the symptom carefully.** Note that a log line, error message, or file path in the symptom is the entry point.
2. **Pull primary sources directly:**
   - Error message → grep for the exact string in source.
   - Log line → grep for the format string that would produce it.
   - Misbehavior → read the code path that should handle it (don't guess
     from name — read it).
   - CLI failure → read the script's argparse and confirm the flag/module
     path exists. **Never invoke a command without verifying its argparse
     first** — covers the rename-trap (e.g., `alpha4gate.runner` →
     `bots.v0.runner`).
3. **Run diagnostic commands yourself with the Bash tool.** Do NOT ask the
   user to paste output for things you can run.
4. **For commands that must run on the user's interactive terminal** (GUI app, SC2 client, anything platform-bound):
   Write the verified PowerShell command.
   Use Write-then-`bash <path>` for WSL multi-line scripts (inline `bash -lc 'multi-line'` is unreliable).
   Always quote `/mnt/c/...` args from Git Bash inside `bash -lc '...'` to prevent MSYS rewrite.
5. **Reproduce the bug.** Run `--repro` if given; else derive one (the failing test, the failing endpoint, the code path) and run that.
   Write the bad output verbatim — Step 5 compares against this exact text.

Use the Diagnosis Block as an **output gate**, not just a template.
Do not mark Step 1 done until all six required fields are filled:
**Symptom**, **Reproduction**, **Primary sources**, **Suspected root
cause**, **Confidence**, and **Memory entries that apply**.

Write after Step 1:

```markdown
## Diagnosis

**Symptom (verbatim from input or observed):**
<exact text>

**Reproduction:**
$ <command>
<observed output, quoted>

**Primary sources:**
- <file:line>: `<code snippet>`
- <log file:line>: `<log line>`
- <argparse line>: `<flag/module>`

**Suspected root cause:**
<paragraph with file:line citations inline>

**Confidence:** high | medium | low

**Ruled out (when applicable):**
- <hypothesis 1> — <why ruled out, with file:line evidence>
- <hypothesis 2> — <why ruled out, with file:line evidence>

**Memory entries that apply:**
- `<feedback_*.md>` — <one-line gloss>
```

Stop on `--triage investigate-only`: hand to user (stop state `INVESTIGATED`).

**Feature-shaped, not a bug?** If Step 1's investigation concludes the symptom is not a
defect — the code works as designed and the ask is really designed, multi-step work —
that is the routing web's bug→plan direction: follow
`skill-pipeline.md § Re-route contract` instead of
forcing a fix. The correct-rail seed is a `/plan-feature` seed built from the Diagnosis
Block; write back to the intake ledger when one exists, per the contract, and stop
(stop state `RE-ROUTED`; see § Stops and stash restoration).

### Step 2 — Independent reproduction (always)

Run one fresh-context, read-only Explore arm using the provider adapter's
diagnostic-diversity model binding (`sonnet` on Claude). It must never inherit
the parent context or an escalated session, mutate source, or receive the
suspected root cause. Record requested, accepted/configured and runtime-reported
model and effort separately. If fresh isolation or the required model binding
cannot be established, stop with `required_tool_missing` before Fix Design.
Give it only the symptom, repro instructions and bounded primary-source scope.
Pass it one job: come to its own conclusion, then we compare:
- Diagnoses match → confidence becomes high, proceed; **but matching
  MEDIUM confidence does NOT upgrade to high**.
  Mark the combined confidence as medium.
- Diverge → do not proceed to Step 3. First classify the divergence shape,
  then present a Diagnosis Comparison block.
  Apply one of the four resolution options below.
  Never synthesize a hybrid third diagnosis.

Write a Diagnosis Comparison block when diagnoses diverge:

```markdown
## Diagnosis Comparison

**Orchestrator:** <root cause: file:line — mechanism; confidence>
**Independent sub-agent:** <root cause: file:line — mechanism; confidence>
**Divergence type:** <one of the four shapes below>
```

Mark the divergence as one of four shapes before choosing a
resolution:
- **Different file:line** — different root cause at a different code
  location.
- **Same location, different mechanism** — same code site, different
  theory about why it fails.
- **Same root cause, different confidence** — agreement on what,
  disagreement on how sure.
- **One can reproduce, the other cannot** — reproduction divergence is
  itself a real diagnostic.

Apply one resolution:
1. **Re-investigate** — run diagnostic commands targeting the divergence point itself.
   Re-grep the contested file, re-read the contested code, re-run the repro with extra logging.
   Apply when divergence is "different file:line" or "same location, different mechanism" and one extra command might resolve it.
2. **Surface to user** — present both diagnoses side-by-side using the
   Diagnosis Comparison block above and ask the user to disambiguate
   using domain knowledge the LLMs lack. Best when re-investigation has
   not yielded convergence after one extra round, or the divergence
   requires domain-specific intuition.
3. **Proceed with confidence marked low/medium** — only when the
   divergence is minor (same mechanism, different call site; or same
   root cause, different confidence) and the fix design is robust to
   either interpretation. The Diagnosis Block's **Confidence** field
   must be set to low/medium and the Fix Design's **Risk** field must
   explicitly acknowledge the divergence.
4. **Tie-breaker third sub-agent** — only after Option 1 re-investigation
   has been tried and the two diagnoses still diverge. Spawn a FRESH
   sub-agent (same provider binding as Step 2's arm) given
   only the symptom + repro instructions and NEITHER
   prior diagnosis (same constraint as Step 2's original independent
   sub-agent). Its independent verdict breaks the tie or confirms the
   divergence is genuine (in which case escalate to Option 2 — surface
   to user — with all three diagnoses laid out).

### Step 3 — Fix design (no code yet)

Write output:

```markdown
## Fix Design

**Change:** <one paragraph on what changes>
**Files touched:** <list with line ranges>
**Regression test:** <path, what it asserts, how it would fail today>
**Risk:** <what else this could break, why it won't>
**Rollback:** <how to undo>
```

Confirm the design with the user before delegating to Step 4. The
confirmation message names the run's stash (`Stash: <sha>` or `none`). A
declined design stops with state `DESIGN-DECLINED`; an operator who ends the
run at this or the Step 2 Option 2 pause stops with state `OPERATOR-STOPPED`.

**Model and capability gate before delegation.** Apply the current provider
adapter's pre-delegation gate. Record separately the model requested for each
arm, the configured selection the host accepted, and the model/effort actually
reported by host metadata; `not reported` remains unknown and a model's own
prose is never identity evidence. Never infer another provider's binding from
the tier map. When the adapter requires `HANDOFF`, print the full combined
problem (Step 4 template), exact `/build-step` command, and Step 1 repro under
the adapter's execution-context line. With `--issue`, also print
`Issue: #N left open` and the close command to run only after the fix is
verified and committed.

### Step 4 — Implement (delegate)

Build a combined problem statement from the Diagnosis Block + Fix Design
Block.
Write the full combined text inline in your chat output before invoking
the delegated skill.
Do NOT collapse the blocks to a placeholder like `<combined problem>` or
`<Diagnosis Block from Step 1>`.
Ensure the actual prose of the Diagnosis and Fix Design blocks appears in
the message so the user sees the prompt the developer agent will receive.
Template:

```markdown
PROBLEM (bug fix):

<Diagnosis Block from Step 1>

<Fix Design Block from Step 3>

REQUIREMENTS:
- Add the regression test described in the Fix Design Block. The test must
  fail against the current code (before the fix is applied).
- Implement the fix described in the Fix Design Block.
- Touch only the files listed under "Files touched"; if you need to touch
  another file, stop and report why.
- Make surgical edits, not whole-file rewrites: in a multi-step phase,
  whole-file rewrites overwrite shared files modified by prior steps and
  cause worktree merge conflicts (see `feedback_buildphase_worktree_merge.md`;
  reference home: `.claude/references/worktree-hygiene.md § 6 "Shared-file merges across steps"`).
- Context only: GitHub issue #<N> (when `--issue` was given). Do not close
  or comment on it; user-debug closes it after verifying the fix.
```

Delegate to `/build-step` (both `quick` and the deprecated `full` synonym
route here):

```bash
/build-step --problem "<combined problem>" --reviewers <code|auto> [--max-iter <explicit value>]
```

Map `--review code` to `--reviewers code`, and `auto` or `none` to
`--reviewers auto`. Never forward `--issue`. When `--max-iter` is omitted,
omit it from the delegation so `/build-step` owns the default. Preserve an
explicit operator value unchanged.

Invoke build-step through its current provider adapter. user-debug never
creates, reads or forwards a build-step verdict key or sidecar path; those are
private to build-step's owning orchestrator. Accept only build-step's terminal
contract result, and never reconstruct PASS from prose or partial artifacts.

When `/build-step` returns, run Restore step 1 (Find it, § Stops and stash
restoration) once. Current build-step records and restores only its own
path-scoped stash by object id; it never restores this caller-owned entry. If
the caller-owned entry is nevertheless gone, print its `missing` line and treat
that as an integrity fact rather than silently adopting another stash.

Stop on `/build-step` BLOCKED: do not proceed to Step 5.
Pass build-step's BLOCKED report to the user unchanged, including its reason,
run/recovery evidence, and diagnosis path when present. Stop state:
`BUILD-BLOCKED`. If any fix path is in the current path set, say only what the
tree proves: build-step landed that path uncommitted before its later halt.

### Step 5 — Verify the fix (against the ORIGINAL repro)

Run the **original reproduction from Step 1** again against the fixed code.

```text
**Before (Step 1):**
$ <repro command>
<bad output>

**After (Step 5):**
$ <same repro command>
<output now>
```

Check the two outputs verbatim.
Mark BLOCKED if the after-output still shows the symptom (stop state
`VERIFY-BLOCKED`). The fix is already in the project working tree: build-step
landed it there at its PASS, without committing. Do not commit it, continue
to Step 6, or close or comment on the issue.
Pass the gap to the user with options: re-investigate, accept partial
improvement, or revert, and print the fix path set (§ Stops). The skill takes
none of these actions on its own: accepting needs only the operator's own
path-scoped commit, and Step 6 would record an unverified fix as fixed.

On `SYMPTOM GONE`, record a **verified fix snapshot** immediately: the current
HEAD, the exact repro command/output, and for every path in the fix path set
either `deleted` or the Git blob id from `git hash-object --path=<path> <path>`.
The regression-test path is part of this map. This snapshot describes bytes,
not a commit or authority. Any later change to one mapped state invalidates it;
return to Step 5 and re-run the original repro before claiming verification.

#### `--skip-verify` (dangerous)

Skip this step but print the following warning when `--skip-verify` was passed:

```text
!!! VERIFY-AGAINST-REPRO SKIPPED (--skip-verify) !!!
The fix passed gates and reviewers, but the original symptom was NOT
re-checked against the fixed code. The bug may persist in a way the
test suite does not capture.
Reason for skip: <user-supplied or "not provided">
```

Document the skip in the final report. A skipped repro creates no verified fix
snapshot, never closes or comments on an issue, and never records the bug as
fixed. Print a deferred handoff containing the original repro plus the exact
verify-and-close conditions from Step 6.
Apply only when the repro is genuinely expensive (multi-hour soak,
hardware-bound, requires live opponent) or impossible from the skill's
environment.

### Step 6 — Land & report

Continue if verify passed (or was skipped):

1. Confirm changes are in the project tree (the delegated build skill
   already landed its reviewed payload; standalone build-step leaves it
   uncommitted).
2. Run every gate the project declares in the main project, including the FULL
   test suite (every declared test root). Detect typecheck and lint from project
   configuration: an absent gate is `not configured`, never `OK`. A configured
   gate that is unavailable or not run blocks completion; a deliberately absent
   typecheck/lint does not. Name the suites that ran; an unnamed subset count is
   not gate evidence.
   Always emit the actual command + tail of output in the chat.
   Do NOT only state the result line in the final report — the user must
   see proof the gates ran. Format:
   ```bash
   $ <typecheck command> | not configured
   <last 1-3 lines of output, when run>
   $ <lint command> | not configured
   <last 1-3 lines of output, when run>
   $ <test command>
   <last 1-3 lines of output>
   ```
   A failing gate stops with state `GATE-FAILED`: show the failing output,
   leave the fix uncommitted and print the fix path set (§ Stops), and do
   not touch the issue.
3. Restore the run's stash (§ Stops and stash restoration).
4. If `--issue` was given, closure is forbidden when Step 5 was skipped. Leave
   the issue open, post nothing, and print the deferred verify-and-close handoff.
   For a verified run, prove all of the following immediately before closing:
   - the verified fix snapshot is still valid and
     `git status --porcelain -- <fix path set>` is empty;
   - `git merge-base --is-ancestor <start> HEAD` succeeds, and the current HEAD
     tree maps every fix path to exactly the snapshot blob id or deletion;
   - walking `git rev-list --reverse <start>..HEAD -- <fix path set>` finds a
     first commit whose complete fix-path tree equals that snapshot. That exact
     commit is the fix commit; a commit that merely touched one path is not;
   - after stash restoration, run the original repro again against the current
     HEAD and observe `SYMPTOM GONE`, then recheck the complete path map and HEAD
     before the outbound call. Any difference invalidates verification and
     leaves the issue open until Step 5 is repeated.
   user-debug never creates the commit.
   - **Exact commit and fresh repro proved:** close the issue. Use `gh -R <owner>/<repo>` from inside
     the project directory (the workspace `dev/` root resolves to a different
     repo per `.claude/references/windows-shell.md § gh / jq`).
     Add a comment containing the fix commit hash + a one-line
     fresh "symptom-gone" confirmation and the verified fix-path blob/deletion
     map so a future LLM viewing the
     closed issue can verify the fix actually shipped.
     Use `--body-file` for multi-line comments.
   - **Proof missing or stale:** leave the issue open and post nothing. Print
     which proof failed plus the repro and exact comparison/close commands to
     run after the verified bytes are committed.
5. Report. When the fix is uncommitted, follow the block with the fix path
   set and its path-scoped commit command (§ Stops).

```text
user-debug complete
  Triage: quick | investigate-only
  Diagnosis confidence: high | medium | low (independently confirmed: yes | no | diverged)
  Files changed: N
  Regression test: <test path>
  Gates: typecheck <OK | failed | not configured | not run>, lint <OK | failed | not configured | not run>, test <OK | failed | not run> (suites: <names>)
  Delegated to: /build-step
  Delegated verdict: PASS (iteration N/M)
  Review: PASS | NEEDS WORK | skipped     (if --review code)
  Repro before/after: SYMPTOM GONE | SKIPPED (--skip-verify)
  Fix commit: <sha with verified path map> | uncommitted | unproved
  Stash: restored <sha> (entry retained) | restored <sha> (no reflog entry; object applied by id) | kept <sha> (<reason>) | missing <sha> (<detail>) | none
  Issue: #N closed | #N left open (verification skipped | fix uncommitted | proof stale/unproved) | not supplied
```

## Stops and stash restoration

Every exit other than the Step 6 report prints:

```text
user-debug stopped: <state> — <reason>
  Stash: restored <sha> (entry retained | no reflog entry) | kept <sha> (<reason>) | missing <sha> (<detail>) | none
```

States: `STASH-FAILED` (Step 0.4; restores nothing), `INVESTIGATED`
(`--triage investigate-only`; no stash exists), `RE-ROUTED`,
`OPERATOR-STOPPED`, `DESIGN-DECLINED`, `HANDOFF`, `BUILD-BLOCKED`,
`VERIFY-BLOCKED`, `GATE-FAILED`, `RESTORE-FAILED`, and any adapter stop such as
`required_tool_missing`. A pause for operator input (Step 2 Option 2, Step 3)
is not an exit; its message names the stash.

**Path sets.** Compare unquoted paths (`-z` output). Two paths match when they
are equal or one is a directory prefix of the other.
- *Fix path set:* paths only (strip every line range) from the Fix Design's
  Files touched plus its regression test.
- *Stashed path set:* `git diff --name-only --no-renames -z <sha>^1 <sha>`, plus
  `git ls-tree -r --name-only -z <sha>^3` when `git rev-parse -q --verify <sha>^3`
  succeeds (the stashed untracked files).
- *Current path set:* `git diff --name-only --no-renames -z HEAD`,
  `git diff --name-only --no-renames -z --cached` and
  `git ls-files --others --exclude-standard -z`.

**Fix in the working tree.** When an exit leaves the fix landed and uncommitted
(`BUILD-BLOCKED` after build-step's land, `VERIFY-BLOCKED`, `GATE-FAILED`), and
in the Step 6 report without a fix commit, print the fix path set and say:
commit only these paths (`git add -- <paths>`, then commit); revert only these
paths; never a whole-tree reset, `git add -A` or `git stash`, which would also
sweep the restored pre-run work.

**Restore.** On every exit, and at Step 6.3, restore the immutable stash object
Step 0.4 recorded (`Stash: none`: nothing to do). Never convert its identity to
a mutable stash index. Never pop, drop or clear any entry.
1. **Find it.** Use `git cat-file -e <sha>^{commit}` to require the recorded
   object. Separately record whether `git stash list --format="%H"` still lists
   it; that affects only the remaining-state report, never which object is
   applied. A missing object reports
   `missing <sha> (object unavailable; stashed paths in tree: yes|no|unknown)`
   and stops restoration without touching another entry.
2. **Check.** Keep the entry when:
   - HEAD or the branch differs from the Step 0.4 values: `kept <sha> (HEAD moved)`;
   - a stashed path matches a current path: `kept <sha> (overlaps: <paths>)`.
   For an overlap, first print the path-scoped fix commit commands from **Fix in
   the working tree**; only after those paths are committed print
   `git stash apply --index <sha>` and explain that it may three-way merge. For
   HEAD movement, print the same identity-bound command without implying it is
   safe before the operator checks the new HEAD.
3. **Apply by object.** Derive the expected per-path state before mutation:
   index entries from `<sha>^2`, worktree entries/deletions from `<sha>`, and
   untracked entries from `<sha>^3` when that parent exists. Run exactly
   `git stash apply --index <sha>`. Never use `git stash pop` or an index.
   After exit 0, compare every stashed path's index mode/blob, worktree blob or
   deletion, and untracked blob with those recorded trees. An exact match is
   `restored <sha> (entry retained)` when the reflog still lists it, otherwise
   `restored <sha> (no reflog entry; object applied by id)`. A nonzero apply or
   any state mismatch is `kept <sha> (restore failed: <first error>; staged and
   worktree mismatch: <paths>; conflicts: <paths or none>)`; stop as an
   integrity failure, report the actual remaining state, and perform no further
   stash mutation. A foreign entry pushed at any time is never addressed.

When the reflog still lists the owned entry, it is deliberate recovery
material. Print its SHA and say the operator may drop that exact listed entry
only after checking the restored index/worktree. When no reflog entry exists,
report object-only recovery and do not advise stash-entry removal. user-debug
never performs destructive removal.

**Interruption and re-runs.** user-debug has no resume mode. An interrupted
run's entry stays listed under its Step 0.4 message; recover it with
`git stash apply --index <sha>` and drop it yourself after checking the tree. A re-run
records its own stash and never adopts, pops or drops an earlier run's entry.

## Write-as-you-go

Bug investigation is the highest-risk scenario for context loss. Hypotheses formed and
ruled out, repro conditions confirmed, root cause narrowed — all of this lives in context,
none of it reaches disk until the fix ships (or at all if compaction fires mid-investigation).

user-debug MUST write to this session's task-state file at 8 trigger points (0–7) during execution.
Write at the moment of discovery — NOT at fix completion. The dead ends list IS the
investigation state.

**Write target:** `sessions/<session-id>.md`, where `<session-id>` is the stable
session ID this host's adapter binds (task-state-schema § Session identity).
Use only that adapter binding; never read another host's session variable or
borrow an inherited parent/child identity. Never write
`current.md`: it is a derived rollup that only its owner regenerates. If the host
supplies no stable session ID, print once
`task-state: no stable session id; write-as-you-go skipped` and continue; never
guess or fabricate an ID.

**Path resolution (MUST use git root — never worktree-relative):**
```powershell
$gitRoot = (git rev-parse --show-toplevel).Trim()
$statePath = "$gitRoot/.claude/task-state/sessions/<session-id>.md"
```

### Trigger points

| # | Trigger | What to write to the session file |
|---|---------|------------------------------------|
| 0 | Step 0.4 done (`quick`) | MUST append to `Critical Gotchas`: start commit, branch, `Stash: <sha> in <toplevel>` or `none` |
| 1 | Repro confirmed | MUST overwrite `WIP.Approach`: `"Repro confirmed: [conditions]"` |
| 2 | Any hypothesis formed | MUST append to `WIP`: hypothesis + evidence for it (one line) |
| 3 | Any hypothesis ruled out | MUST append to `Dead Ends`: hypothesis + why ruled out (with evidence) |
| 4 | Root cause identified | MUST overwrite `WIP`: `"Root cause: [description]"` |
| 5 | Fix design agreed | MUST append to `Critical Gotchas`: key constraint the fix must satisfy |
| 6 | Step 5 outcome | `SYMPTOM GONE`: append to `Completed` with the verified snapshot identity. `SKIPPED`: append an explicitly unverified candidate entry with the deferred repro; never say fixed |
| 7 | Every exit and Step 6.3 stash outcome | MUST append to `Critical Gotchas`: `user-debug run <start sha7>: Stash restored | kept | missing | none` |

**Trigger 3 is the most critical.** Dead-end writes MUST happen at dismissal time —
immediately when the hypothesis is ruled out — not at the end of investigation.
If compaction fires mid-investigation, the next context reads the dead ends list and
continues from where investigation left off without repeating ruled-out paths.

### Write formats

**Dead Ends** (trigger 3 — MUST append immediately at dismissal):
```
- [hypothesis in 5-10 words]: [why ruled out — specific evidence, file:line if applicable]
```

**WIP.Approach** (triggers 1, 4 — overwrite):
```
**Approach:** Repro confirmed: [exact conditions]
```
or
```
**Approach:** Root cause: [description with file:line]
```

**Completed** (trigger 6 — append one truthful form):
```
- [<sha> | uncommitted@<HEAD short SHA>] user-debug [bug description]: [root cause summary] — verified candidate (repro: SYMPTOM GONE; snapshot: <path=blob|deleted,...>)
- [unverified@<HEAD short SHA>] user-debug [bug description]: verification skipped; issue left open; deferred repro: <command>
```

**Critical Gotchas** (trigger 5 — append):
```
- [fix constraint]: [why violating it would break the fix or cause regression]
```

**Critical Gotchas** (trigger 0 — append):
```
- user-debug run: start <sha> on <branch | detached>; Stash: <sha> in <toplevel> | none: restore only this entry, by SHA (§ Stops and stash restoration)
```

**Critical Gotchas** (trigger 7 — append):
```
- user-debug run <start sha7>: Stash restored <sha> (entry retained | no reflog entry) | kept <sha> (<reason>) | missing <sha> (<detail>) | none
```

### Schema reference

Full field definitions, overwrite/append rules, session identity, rollup ownership and lifecycle:
`.claude/references/task-state-schema.md`

---

## Constraints

Do not soften rules under pressure.
Note that if the skill's structure feels too verbose mid-task, that's the
bias firing — not a signal to skip steps.
Keep the verbosity; it is the mechanism.

## Stop-and-audit rule

Stop fixing one-at-a-time when you encounter a 3rd instance of the same
bug shape (producer/consumer drift, silent exception fallthrough in a
loop, hardcoded constant mismatch, schema-without-migration).
Grep for siblings.
Land one comprehensive fix.
See the `/build-step` core's § Stop-and-audit rule for the full rationale and examples.

## Limitations

- Worktree isolation only (no Docker option — use `/build-step --isolation
  docker` directly if you need clean-room).
- Step 5 (verify-against-repro) requires a deterministic repro. For flaky
  bugs, may need multiple runs to establish baseline rate before/after.
- Delegates to `/build-step`, so inherits its limitations.
