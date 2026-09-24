# Baseline overnight build - 2026-09-24

## 1. What This Is

**Objective:** prepare a real, reversible Codex development/production split for
operator testing by **08:00 America/Los_Angeles, September 24, 2026 (15:00 UTC)**.
The operator requested an unattended overnight build after the recommendation to
use current main. This amendment selects that source as agent default ON-D1; the
operator did not separately approve a specific new commit. The September 13 snapshot stays
preserved as historical evidence. No live-profile activation is authorized tonight.

Proposal: [overnight execution view](baseline-overnight-2026-09-24.html).

This is a bounded execution amendment to
[Phase BR](baseline-releases-plan.md), selecting existing Steps **147/#207 and
149/#209**. Step 148 (lab), 151 (report) and 152 (hygiene) wait. Step 150/#210 is
tomorrow's operator decision after a concrete preview. Do not dispatch the old
unattended 147-149 span or restart any historical controller.

## 2. Starting state and source identity

- Main: `7ae573bd1c610f8ba1d8e39d66f1f7a915973b36`; Step 153 accepted under LH-E1.
- Build branch: `build/br147-resume-20260924`, starting checkpoint
  `8d6757e37827d1a7717a6640dc02c3a87a3013e2`. Its preserved Step 147 code is integrated
  with main and the narrow public-packet repair is recorded in the
  [resumption receipt](findings/baseline-releases-resumption-2026-09-24.md).
- Reuse this worktree. Preserve all older worktrees, raw reviews and failed runs.
- The release source is **one final committed integrated candidate descended from
  this current-main-based branch**, including the bounded Step 149 work. Freeze its
  full Git commit and tree before independent review and qualification. The same
  commit identifies builder and product source for this attempt; record both fields.
  Never label the older `79a985a` snapshot as this release or silently change its bytes.
- Release version: `v0.1.0-baseline.20260924`. Retain under a private release store
  outside source and installed discovery roots. A private launch manifest supplies
  exact local paths, executable paths and log locations; no machine paths go in Git.

## 3. Build and review lane

Use one persistent Claude Code Opus coordinator with native fresh Agent dispatch,
medium effort, and existing authentication. A fresh Codex CLI Sol process is the
implementation arm; a Terra CLI process may handle a bounded correction if Sol
is unavailable before it starts. Record actual model resolution; no silent model
fallback. Native independent Claude reviewers supply the cross-family review.
Check these capabilities before substantive work; a missing route is a recorded
blocker, not permission for self-review or weakened gates.

The launch probe resolved the `opus` alias to `claude-opus-5` and actually dispatched
a fresh Sonnet child through native `Agent`. Record the worker's own resolved model
on launch; an older model name in workspace prose is not runtime evidence.
The standalone Sol probe was rejected by the account before implementation.
The permitted fresh-process fallback `gpt-5.6-terra` then returned the requested
no-tool marker with exit 0; Terra is the selected overnight builder. No model-host
repair campaign is part of this work.

Use installed build-step/review-deep mechanics with this amendment's single
candidate and single-owner validation. Six independent code lenses still apply
to the integrated release/activation change; preserve their raw reports and use
the installed deterministic reducer. An observed representative review of this
exact committed candidate by the other model family can supply the charter's
cross-family proof when its requested/resolved identity, independent conversation,
verdict and source are actually recorded. Do not run another review merely to
manufacture a second receipt. Use a named coordinator attestation of the evidence,
never an invented operator signature or an inferred native result.

There is one implementation pass and at most one concrete correction pass tonight,
within the time bounds below. Existing Step 147 failures remain history; this is a
new explicitly bounded continuation, not a reset of their counters. Nits do not
start a correction/review campaign. Record genuine blockers and stop dependent
work. Routine documentation clarification may close its own finding without
restarting all lenses or the test suite.

## 4. Exact deliverables

**Step 147:** finish only concrete defects that prevent a truthful retained toolkit
release. Keep the existing release CLI, immutable source archive, evidence and
public-packet contracts. Before a costly gate, emit distributions and inspect their
offered files for machine-specific paths with the existing scanner. If generated
examples contain such paths, replace only those examples in canonical source with
portable placeholders; follow the existing catalog UPDATE guide. Never edit an
installed profile, rewrite historical source, or broaden this into a scanner rewrite.

**Step 149:** deliver `tools/activate-codex-release.ps1`,
`tests/release/test_codex_release_activation.py`, and
`documentation/codex-release-adoption.md`. Implement only inspect, preview, apply
and rollback for a selected qualified retained Codex release. Reuse installer
`-DistDir`, ownership ledger and shared transaction APIs. The installer uses
`-NoRollback` and deletes its transient journal, so this wrapper must preserve a
durable private preimage and operation state itself. Do not claim the installer
already provides exact rollback.

The original BR section 6.1 owns operation schemas and command flags. Preserve its
UUID4 operation IDs, release identity, full ledger and selector-last rules. The
wrapper manages only the selected profile's owned paths and its own private state.
No force flags, foreign-file overwrite, credential/settings edits, scheduler,
dashboard, general package manager or lab work. Reject unqualified/corrupt releases
before mutation. Preview binds exact target, prior owned bytes, ledger and desired
release; a changed preview is a refusal, not an automatic refresh/apply.

Preparation of Step 149 may use controlled fixtures/disposable artifacts before
147 is qualified. **Neither step becomes DONE and no live target becomes eligible
until the shared integrated gate and real disposable apply/rollback pass.** This
changes development sequencing only, preserving their acceptance dependency.

## 5. Bounded schedule and test ownership

All times below are UTC on September 24 (Pacific is UTC minus seven hours):

| Deadline | Work |
|---|---|
| 08:15 | Check actual host/model capability, memory and prior state; start implementation |
| 10:30 | Finish bounded implementation/correction, focused checks and generated privacy preflight |
| 11:00 | Freeze integrated candidate, complete independent review and actual cross-family proof |
| 11:00-14:30 | One authoritative release qualification attempt, including all nested tests |
| 14:30-14:50 | Verify retained artifacts and real disposable-home apply/rollback; prepare operator packet |
| 14:50-15:00 | Record outcome, preserve work and clean only owned temporary processes |

If setup runs late, the final deadline does not slide. Do not start a costly gate
unless it fits the remaining window. Require at least **4 GiB free physical memory**
before heavy tests; wait visibly for headroom, never close user applications.

During implementation run only meaningful affected activation/publication cases.
Save exact commands, exit codes, elapsed times and candidate identities. No
lint/typecheck is configured. Do not add a large matrix of prose-mirroring tests.

For the final frozen source, **`tools/baseline_release.py toolkit` owns the only
repo-root `python -m pytest` invocation**, followed by its existing
`release.ps1 -Provider all` staged gate and artifact verification. Its private
proof file uses the existing checks/reviews/environment schema from BR section 6.1
and the runbook. Run it from the clean frozen builder with `--source-root` pointing
to this repository, `--source-commit` equal to the frozen builder commit, the
version above, private `--store`, explicit `--python-exe`, actual `--proofs` and a
named `--attest-reviews` value. Never invent proof contents.

The release's root suite includes the new release and activation tests. Reuse this
one exact-source result for both code steps and for merge/wrap; do not run separate
candidate, post-merge, after-step or final-wrap root suites. Existing staged
package-integrity is part of the same qualification attempt, not another pre-run.
This is a single-owner execution amendment, **not a full-gate waiver**. If source
and builder differ, or tested code/config/package inputs change, reuse is invalid;
preserve incomplete work instead of automatically admitting a second root run.

The supervisor's final deadline is hard. The worker must also enforce the 14:30
qualification cutoff and stop only its owned process tree on failure/timeout.
Report failures promptly instead of allowing release cases to repeat a known
failure for hours. No full-suite retry tonight and no adaptive scope expansion.

## 6. Disposable acceptance and morning packet

Prepare exact PowerShell commands and resolved artifact locators for:

1. Inspect source/builder identity, qualification evidence, public/retained hashes.
2. Preview changes against a disposable Codex home containing owned and foreign files.
3. Apply; verify all owned bytes and full ledger, then selector publication.
4. Repeat as a no-op; verify bytes and ledger remain stable.
5. Refuse foreign collision, changed preview/owned bytes and unqualified/corrupt input.
6. Preserve recoverable state after a controlled interrupted apply/selector failure.
7. Roll back; verify exact prior bytes, absences, full ledger and previous selector;
   refuse post-apply drift, and preserve all foreign files.

Use the normal entry points, real disposable filesystem and actual installer for
the complete apply/rollback observation. Existing focused failure tests cover
the remaining named cases; do not repeat a broad suite for each. No live-home
apply/rollback or daily discovery-root change occurs unattended. A read-only live
preview is allowed once qualified and must be clearly distinguished from apply.

Write `documentation/baseline-morning-test.md` with the result, exact candidate and
artifact identity, completed/missing checks, remaining limitations and commands
for tomorrow. Public prose uses placeholders; a private morning file supplies
resolved local paths. If blocked, give the single concrete next action and a
disposable-only test path where available. Do not claim READY FOR LIVE ADOPTION
unless every prerequisite actually passed.

On success, check upstream, integrate preserving tested inputs, push and update
#207/#209 once. Administrative status changes are listed separately; receipts keep
the actually tested commit. Step 150 remains open. On failure or timeout, push the
candidate checkpoint and keep issues open. In every case leave a durable morning
report, status file and logs; the supervisor exit alone is not a product PASS.

## Appendix

### Preparation evidence

On September 24, fresh read-only plan-review returned READY with no blocking
findings. After publication of the standalone proposal, a separate fresh-context
plan-wrap checked all thirteen sections and returned READY with no blockers, gaps
or minor findings. Neither reviewer ran product tests or edited files. The host
probes in section 3 are capability observations, not release acceptance. Issue sync
follows this preparation; implementation and qualification are still pending.

### Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| ON-P1 | P | Run overnight so the operator can test the dev/prod split next morning | selected 2026-09-24 |
| ON-P2 | P | Operator will free memory and leave the computer awake | confirmed 2026-09-24 |
| ON-D1 | D | Use current-main-based integrated candidate; preserve the September 13 snapshot | selected for overnight request; records prior recommendation |
| ON-D2 | D | Prioritize 147 and 149; defer lab/report/hygiene and leave live adoption attended | selected to reach the usable split |
| ON-D3 | D | One shared exact-source qualification gate, with no full-suite retry | selected to avoid repeated multi-hour checks |
| ON-D4 | D | Hard stop 08:00 Pacific, 4 GiB memory admission, one correction pass | selected execution bounds |
| ON-D5 | D | Opus coordinator, Sol implementation, independent Claude review; fresh-process Terra only if Sol unavailable before starting | selected from available authenticated host route |

Agent defaults can be adjusted by ID; this document is the execution authority,
while the HTML is its operator-facing view. An overnight request authorizes this
bounded setup and build, not an unattended live-profile change.
