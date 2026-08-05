# Step 47 decomposition decision

**Date:** 2026-08-05
**Status:** Adopted — landed in the same commit as the plan revision in
`host-native-discovery-cutover-plan.md` (Step 47 re-scoped; Step 47b added).
**Context:** issue #60; branch `build-step-1785890195` @ `bde8a5f` (unmerged);
five `/review-deep` rounds, 2026-08-04 → 2026-08-05. Audit trail: the #60
comment thread (rounds 1–4 posted; round 5's outcome pending) plus the
`.review-deep/` sidecars preserved with the build worktree (session-local,
gitignored). This document was itself adversarially reviewed before landing
(four independent verification agents; their corrections are folded in).

## Problem

Step 47 ("reversible legacy-install migration") went through five review
rounds without converging. The actual history, with aggregate Block counts:

| Round | Reviewed | Blocks | What happened |
|---|---|---|---|
| 1 | iteration 1 | 4 | Consumer-home mutations missing a containment or content-identity check that a sibling branch already performs. |
| 2 | iteration 2 | 5 | Same shape at new sites — **two minted by iteration 2's own fixes**. Stop-and-audit fired. |
| 3 | iteration 3 (structural refactor) | 4 | One runtime choke point (`Resolve-HomeTarget`), one shared content-identity rule (`Assert-OurBytesAtTarget`), and a new committed structural gate (`tests/distributions/test_path_choke_point.py`). All six lenses rejected it; the choke point's contract violation was real. |
| — | targeted fixes → `5ef1045` | — | Choke-point contract fixed; gate rule made exact + transitive; sweep of the tree clean (56 mutating sites, 8 files, 0 violations, non-vacuous). |
| 4 | `5ef1045` | **1** | Near-convergence. The single Block: on `-Resume` after a crash, a drifted **preserved** file lands a plain `rolled_back` — the reviewer demanded escalation. Gate items were Nits. |
| 5 | `5ef1045..bde8a5f` | 6 | `bde8a5f` answered round 4's Block with an **unconditional** preserve-drift escalation — which round 5 condemned as a regression of the same path (details below). The gate hardening riding in the same commit (71 of the 93 delta lines) added three holes of one shape, two later downgraded to FYI/Nit by skeptics, plus two critic-found idioms, a proven strict weakening on multi-command lines, and zero test coverage on the production fix itself. |

**The decisive observation is the round 4 → round 5 oscillation.** Round 4's
*only* Block demanded that preserve-drift escalate; round 5's headline Block
condemned exactly that escalation: a consumer editing their own preserved file
during downtime now lands `failed_incomplete` (exit 3) with a false *"the
consumer home is MIXED … recover from it manually"* message — on a home where
every byte the tool mutated was restored. (The state is recoverable via the
documented remedy — delete the transaction directory — so "wedged" is
temporary; the false MIXED claim is the dangerous half, because it invites
restoring a backup over the consumer's own newer edit.) Two consecutive
independent review rounds Block'd **opposite policies on the same hunk**. That
is not a bug list; it is proof that the underlying policy — *which drift is
this tool's business, and what does each terminal status claim?* — was never
decided, and that no amount of patch-and-review can converge an undecided
policy. The code agrees: the same function encodes both answers
(`$verifyUndo` bounded to the verification-failure set at
`migrate-legacy-install.ps1:1470`; the round-5 `$undo` unconditional at
`:1405`).

The recurring sibling-asymmetry defect shape has now been introduced *by a
fix round* three times (iteration 2 twice, `bde8a5f` once).

**The diagnosis:** Step 47 is one step doing two unrelated jobs, and they
fail for different reasons.

1. **The transaction rollback semantics** (`tools/migrate-legacy-install.ps1`
   + `tools/skill-mesh-transaction.ps1`) — a *state-machine policy* question.
   Undecided policy, two encodings, review oscillation.
2. **The containment gate** (`tests/distributions/test_path_choke_point.py`)
   — a *static-analysis tooling* question: a regex over PowerShell source
   text keeps losing to expression shapes, while its docstring promises "a
   sixth [unguarded site] cannot appear" — a claim its mechanism cannot
   support.

The gate is in **no step's Done-when** — it entered as the stop-and-audit
remedy after round 2, was built in round 3, and has consumed every round
since as a plan-orphaned artifact with no acceptance criteria for the
plan-conformance lens to bound changes against.

## Decisions

### D1 — Split the step; Step 47 merges alone

Step 47 keeps its original Done-when — the migrator and the shared
transaction engine — plus the D2 policy obligations, and **merges without
waiting for any gate work**. A new **Step 47b** owns the gate's improvement
with its own Done-when, **off the Step 48→50 critical path** (Step 48's
dependencies are unchanged: 42, 47). A gate-completeness finding raised
during Step 47's confirming review is routed to 47b, not treated as a merge
blocker.

What the split irreplaceably provides is a **plan home for the gate**: its
own Done-when for the plan-conformance lens to bound against, its own
recorded acceptance, and an explicit dependency edge. The convergence levers
themselves are D2 (one decided policy, so there is one answer to encode) and
D3 (an honest claim, so gate completeness stops being a merge-blocking
criterion); the findings-routing rule enforces the boundary during review.

### D2 — Transaction drift policy (Step 47)

**What `rolled_back` claims.** Exactly this: *every byte this tool mutated
has been restored from backup, and every file this tool created has been
removed.* It does **not** claim the home is byte-identical to its
pre-migration state on paths the tool never touched: `preserve` actions carry
no backup payload — a deliberate disclosure-minimization choice — so the
broader claim is structurally unprovable and must not be enforced.

**The three drift cases, decided:**

1. **Mutated-path content identity** → escalate (`failed_incomplete`,
   exit 3). `Assert-OurBytesAtTarget` — already called by every undo branch
   that destroys or overwrites — refuses to clobber bytes the transaction did
   not write. Unchanged, correct.
2. **Preserved-path verification failure after a fully-applied transaction**
   → escalate (`failed_incomplete`, exit 3), bounded to the failure set
   (`$verifyUndo`'s `$badSet`). This is the deliberate boundary: the tool's
   own post-install acceptance failed on that path while committing, and
   there is no payload to restore. Kept — but its operator-facing message
   must be corrected: by the time `$verifyUndo` throws, rollback's strict
   reverse order guarantees every mutating action was already undone, so the
   message must say "every path this tool mutated was restored; preserved
   path X changed during the transaction and has no backup payload by
   design" — not the current "the consumer home is MIXED … recover from it
   manually", which invites restoring a backup over the consumer's own edit.
   Calibration note: this branch is reachable in practice only via the
   post-apply tamper seam or a live same-process edit race, which is why no
   ordinary run hits it. A future revision may demote this case to advisory
   as well; that question is explicitly not relitigated here.
3. **Preserved-path drift during a pre-completion apply/resume abort** →
   **do not escalate**: land `rolled_back` (exit 1 on the failure-triggered
   shared path) plus an **advisory diagnostic** naming the path and its
   expected/observed hashes. This is the round-5 scenario, and — a mechanism
   this decision's first draft got wrong — the drift here typically *is* the
   triggering failure: the engine's post-mutation hash check
   (`skill-mesh-transaction.ps1:479-483`) runs for **every** non-skipped
   action with no kind filter, a `preserve` action carries
   `post_hash = pre_hash`, and its mutate is a pure no-op, so an edited
   preserved file re-run under `-Resume` throws mid-apply. The case still
   lands `rolled_back` because the narrow claim is *true* — every mutated
   path is restored behind case 1's guard, the preserve undo never touches
   the consumer's file — and the correct operator move is a fresh `-Apply`,
   which re-plans against the edited file's new hash and converges. The
   boundary with case 2 is structural, not trigger-site-based: escalation is
   reserved for a **fully-applied** transaction whose acceptance failed;
   a pre-completion abort never escalates on preserve drift.

This adjudicates the round-4/round-5 oscillation: round 4's Block was correct
only under the broad reading of `rolled_back`, which the no-payload design
makes unsupportable; the honest fix is the narrow status claim plus the
advisory, not escalation.

**Obligations folded into Step 47's acceptance:**

- Revert the shared `$undo` (`migrate-legacy-install.ps1:1405-1415`) to its
  `5ef1045` form — the plain `Invoke-ActionUndo` wrapper.
- Add the case-3 advisory diagnostic; correct case 2's escalation message per
  above.
- Reword the shared path's success line ("the consumer home was restored to
  its pre-migration state", `:1434`) to the narrow claim; audit
  `Invoke-Rollback`'s outcome line (`:1654`) for the same overclaim.
- Correct the four stale/false comment blocks: `:1008-1011` and `:1441-1445`
  (both claim the engine post-hash-checks "mutating actions only" — false,
  the check is kind-blind), `:1399-1404` (argues for the unconditional
  escalation, and falsely claims the explicit `-Rollback` path escalates —
  it uses the plain wrapper at `:1646`), and the `$verifyUndo` block to
  state the case-2 boundary.
- Exit codes stay: failure-triggered shared rollback → `rolled_back`/exit 1;
  explicit `-Rollback` → `rolled_back`/exit 0; escalations → exit 3.
- **Coverage for the shared rollback path** (today: zero — reverting the
  round-5 hunk fails no test): a test that crashes the apply at seq 0 via
  the existing `SKILL_MESH_TX_CRASH_AT=0` seam (defaults to `after-begin`;
  no new production seam is needed), edits a preserved file out-of-process,
  then `-Resume`s — asserting `rolled_back`, exit 1, the advisory naming the
  path, and a follow-up bare `-Apply` succeeding.

**Considered and rejected:** adding `Test-Preconditions` to `Invoke-Resume`.
After a partial apply, applied actions hold post-state, so a resume-time full
precondition pass would flag every already-applied action and block every
legitimate resume. The resume-time controls are the per-action
`Test-ActionAlreadyApplied` skip checks plus the engine's per-action
post-mutation hash verification (and post-install verification once fully
applied); the round-5 wedge came from the escalation policy, not a missing
precondition pass.

### D3 — The containment gate: honest claim now, in Step 47

Step 47 **reverts the gate to its `5ef1045` state** — discarding the
`bde8a5f` alias/mixed-operand delta, which round 5's A/B proved *strictly
weaker* on multi-command lines (a newly-recognised alias consumes the single
match slot and shadows a real ungated cmdlet later on the line) and whose
new tests blessed the very idioms they missed — and lands the small
**docstring-honesty edit**: the "a sixth cannot appear" completeness claim is
removed, and the gate is documented as a best-effort tripwire enforcing the
`$safe*`-from-resolver convention *on the expression shapes it can parse*.

**What it actually catches — corrected by empirical reconstruction** (the
first draft of this document claimed all five historical instances; that was
read off the gate's own anchor test, which substitutes containment lookalikes
for two of them):

- It catches the **containment half** of the historical defect class: the
  three containment instances from rounds 1–2 (the retire delete, the
  ungated undo restores, and the `:1186` lexical pre-image read — the last
  only in its current `Join-HomePathLexical` spelling; in its historical
  `Join-HomePath` spelling it was flagged only via the then-ungated
  destination).
- The two **content-identity** instances (`:972-980`, `:982-989` — precisely
  the two introduced by iteration 2's own fixes) are outside any static
  path-gate's reach: their targets were correctly `$safe*`-gated and the
  defect was a missing byte-identity check. **The content-identity half of
  the invariant has no mechanical enforcement today** — it is guarded by
  per-site convention (`Assert-OurBytesAtTarget` calls) and by review. Step
  47b adds the missing mechanical check (D5); until then, Step 47's
  confirming review explicitly asks the content-identity question, since the
  D2 delta edits exactly those undo branches.

**Documented blind-spot classes** (recorded in the module as accepted
limitations, not closed): inline resolver splice; mutating-primitive argument
expressions; `$null = <cmd>` capture position; string-literal suffixes;
second primitive on a line; aliased copy/move source; **helper-call
laundering** (a raw path passed to a mutating helper whose internal primitive
is site-exempt on an unverified "every caller passes `$safe*`" reason); and
**the hand-maintained `LEXICAL_HOME` joiner-name list** (a renamed or new
lexical joiner is invisible until added — the workspace's own doctrine says
hand-maintained gate lists are false greens). All are latent: zero instances
across the tracked `.ps1` files, and the runtime choke point
(`Resolve-HomeTarget`), not this gate, is what protects a consumer machine.

**Calibration constraint for any future gate work** (recorded so no round
re-attempts it): extending the mixed-operand check to resolver calls was
tried by a round-5 skeptic and produced **36 violations against correct
shipped code** — resolver *arguments* are inputs, not path prefixes. The
short-circuit that looks like the bug is structurally required; closing that
hole needs resolver-call stripping, which is AST-shaped work (D5).

### D4 — Branch disposition

`build-step-1785890195` is salvage, not a merge candidate. The revised Step
47 build resumes **from the branch**: restore both changed files to their
`5ef1045` state (round 4 proved that tree one decided-policy Block away from
convergence), then implement the D2 obligations. Keepable and already in
place at `5ef1045`: the runtime choke-point contract fix,
`Assert-OurBytesAtTarget`, `tools/skill-mesh-discovery.ps1` (one owner for
the provider→discovery-root map; closes #89), `New-BackupManifest`'s null
guard, `Get-CreatedDirs`'s resolver fix, and ~100 new tests including
previously-never-executed branches.

### D5 — Step 47b's scope, and the deferred AST check

**Step 47b** (off the critical path; may land in parallel with or after
Steps 48–50):

- Re-add the alias and mixed-operand hardening **without the weakening**:
  acceptance includes a committed differential corpus containing the round-5
  counterexamples — at minimum one multi-command line where a recognised
  alias precedes an ungated long-name cmdlet — which the `5ef1045` gate
  flags and the `bde8a5f` gate accepts. **The `bde8a5f` gate failing this
  corpus is the test of the criterion**: a plain no-weakening check over the
  real tree and the existing anchors is vacuous (both gates flag zero
  there).
- Add the **content-identity tripwire**: enumerate `Invoke-ActionUndo`'s
  branches (enumerated, never hand-listed) and fail if any branch that
  destroys or overwrites lacks an `Assert-OurBytesAtTarget` call — the
  mechanical guard for the defect class fix rounds actually introduced.
- Re-document the gate's five-sites anchor test to what it actually proves
  (the containment instances in their historical spellings), naming the two
  content-identity instances it deliberately cannot represent.
- Re-word or verify `SITE_EXEMPT` reasons that assert caller behavior; keep
  the red-on-garbage anchors and the non-vacuity check.

**The AST-based real check stays deferred.** A sound gate exists in
principle — parse with `[System.Management.Automation.Language.Parser]` and
walk the AST, making command position, argument shape, aliases, multi-command
lines, and resolver-call stripping exact — but it is a new mini-tool with its
own review burden (the exact dynamic that consumed rounds 3–5) while every
known hole is latent and Step 50 gates Phase 8 plus two downstream
workstreams. **Un-defer trigger, covering both halves of the invariant:** a
live false negative — a shipped containment defect the stated convention
should have caught, or a mutating undo branch shipping without its
content-identity check — discovered by any later review round, incident, or
ad-hoc sweep. (An AST sweep can be run as a one-off diagnostic at any time
without committing a tool; note the AST rewrite remedies only the containment
half — a content-identity miss re-escalates as the 47b tripwire's problem,
not the parser's.)

## Alternatives considered

- **A sixth patch-and-review round.** Rejected. Round 4 shows patching *can*
  converge the tree — but only once the policy exists: the rounds after the
  refactor oscillated on the undecided drift policy (round 4 Block'd the
  absence of escalation; round 5 Block'd its presence), and the recurring
  defect shape was introduced by fix rounds three times.
- **Delete the static gate entirely.** Rejected: at `5ef1045` its sweep
  proved the tree clean non-vacuously, and synthetic reconstruction shows it
  catches the containment shapes of the historical defect class — cheap
  regression insurance. (It does not and cannot catch the content-identity
  half; that argues for 47b's tripwire, not for deletion.)
- **Rewrite the gate on the AST now.** Rejected for scheduling, not
  soundness — see D5.
- **Keep one step; bound review scope by instruction only.** The routing
  rule does do the review-scoping work — but only a step of its own gives
  the plan-orphaned gate a Done-when anchor, and a plan-orphaned artifact
  with no acceptance criteria is exactly how the gate consumed three rounds
  unbounded.
- **Merge 47 and 47b as one unit** (this document's own first draft).
  Rejected: it contradicts "a gate finding is not a merge blocker" — the
  migrator would physically land only when the gate rework resolved — and it
  puts `scan_source` rework, the exact code class that consumed rounds 4–5,
  on the Step 48→50 critical path that gates Phase 8.

## Consequences

- Step 47 becomes finishable: revert to a tree round 4 already found one
  Block from clean, implement one decided policy, add the missing coverage.
  Its confirming review is one bounded question — does the migrator
  implement D2 (including the content-identity spot-check on the edited undo
  branches)?
- Step 47b is scheduled, scoped, and off the critical path; Step 48's
  dependencies are unchanged.
- Round 5's operator-facing regression is reverted: a consumer's own edit to
  their own preserved file can no longer produce the false "MIXED" claim or
  the blocked-tool state.
- Accepted risks: the reverted gate misses alias-spelled and multi-command
  shapes until 47b lands (all latent today; runtime choke point unaffected);
  the content-identity half stays convention-guarded until 47b's tripwire
  (mitigated by the explicit review question in Step 47); a future ungated
  site in any documented blind-spot shape ships uncaught until D5's trigger
  fires.
