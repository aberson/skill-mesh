Reviewing as: feature plan. Sections 17–21 apply.

# Baseline release plan review - 2026-09-14

Plan: `documentation/baseline-releases-plan.md`. Reviewed in-session through the
installed Codex plan-review contract, with autofix enabled. No independent review
is claimed or required for this planning skill. Base preparation: `23ce98b`.

## Blockers

None remaining. The mixed toolkit/lab writer ambiguity was resolved: all new code
belongs to toolkit packaging/reporting; the lab remains read-only external input.
Step 150 contains an operator decision and actual target acceptance, no code build.

## Significant gaps

None remaining. Steps 147/149/151 now use deep review; Step 148 declares deep review
for the shared release writer. The current Codex deep adapter explicitly lacks the
required dispatch, so the build host is Claude Code with isolated reviewer preflight.
This does not claim that the old M1 route passed. Routing follows the trigger owner
`skills/review-deep/core.md:32`; existing Codex limitation is
`skills/review-deep/providers/codex.md:9` (DS-D3).

## Missing items

None remaining. New files, record shapes, input ownership, command contracts,
exit behavior, interrupted-operation recovery and checks are explicit.

## Nice-to-haves

Issue fields are intentionally blank until repo-sync. No additional runtime,
portfolio connector, hosted dashboard or scheduler is required.

## Checklist and source evidence

| Check | Result / evidence |
|---|---|
| 1 Data persistence | PASS - immutable release/observation directories; atomic private metadata; retained attempts, no automatic deletion (plan 6.1) |
| 2 Dependencies | PASS - existing PS/Python/Git toolchain; external dependency inventory retained; no utility portfolio prerequisite |
| 3 Authentication and secrets | PASS - no credential capture; private evidence/public packet split; no auth change |
| 4 Concurrency | PASS - target lock plus existing compare-before-write guards, per-operation UUID and per-observation output |
| 5 Errors | PASS - bad-input/execution exit semantics, truthful qualification, partial receipt retained |
| 6 Toolchain | PASS - actual PS 5.1 release/install parameters verified; root pytest required; no lint/typecheck/server invented (CLAUDE.md:24,32,114,208) |
| 7 Decisions | PASS - approved baseline scope retained; version and implementation defaults named; live adoption is Step 150 |
| 8 Setup | PASS - plan 6.2 names current prerequisites and separates existing commands from new interfaces |
| 9 Idempotency | PASS - release collision refusal, operation preconditions, explicit interruption handling and no-op test |
| 10 Seams | PASS - index/commit binding, raw versus normalized hashes, selector last, saved evidence versus native support |
| 11 Scope | PASS - three small entries reuse existing code; no service or replacement orchestration |
| 12 Security | PASS - explicit roots, path/reparse checks, no force flags, preserve consumer bytes; raw records private |
| 13 Tests | PASS - meaningful archive/activation/drift checks plus applicable exact-source gates |
| 14 Operations | PASS - retained attempt diagnostics, reopen and observed rollback; no implicit restart or promotion |
| 15 End-to-end | PASS - Step 147 complete packaging slice; Step 149 disposable real install; Step 150 live target observation |
| 15.5 Pipeline smoke | PASS - Step 151 real 60-second smoke, exact two repositories and receipts, drift, elapsed time and locators |
| 16 Fresh context | PASS - source IDs, paths, schemas, capability limitations and run guide inline |
| 17 Existing code | PASS - release.ps1:98,192,230,261,285; install-skill-mesh.ps1:129,497,998,1129; lab tools/records.py:45,99,149 read in actual lab root |
| 18 Impact | PASS - canonical afterparty files included; old installer/telemetry/lab schemas read only |
| 19 Conflicts | PASS - historical M1/PROD not restarted; lab source/candidate/oracle identities separate; MEMORY status correction reflected |
| 20 Context | PASS - baseline report and evidence linked; existing entry points and changed ownership explained |
| 21 Slice | PASS - initial toolkit package is usable without report/hygiene; lab remains an experimental archive |
| 22 Operator/code | PASS - five code steps, one operator adoption step; prepared mechanics belong to 149 |
| 23 Conditional predicate | N/A - no conditional steps |
| 24 Reviewer runtime flags | PASS - deep/code only; neither full nor runtime reviewer lane, no artificial URL |
| 25 Walker format | PASS - six headings 147-152, required fields, exactly six autofix markers; mechanically checked |
| 26 Substrate smoke | PASS - Step 150 is the operator live Codex target smoke with real discovery evidence; 149 is disposable preflight |
| 27 Review stakes | PASS after routing fixes; 152 remains ordinary code review for scope prose; advisory model guidance only |

Additional primary evidence: toolkit `runtime/telemetry/telemetry-writer.ps1:47`
sets stub usage; `skills/user-afterparty/core.md:141` selects nearest CLAUDE scope;
the lab's own AGENTS.md and its tools/records.py line 45 -- external lab source, outside
this repository -- own its independent checks and run schema.
No existing public API signature is changed by this plan. The implementation steps
must search all callers again before any proposed shared-interface change.

## Auto-applied 12 fixes

1. Populated exact Files and Existing context for Steps 147-152.
2. Added PENDING status and explicit sequential execution disposition to all six steps.
3. Routed Step 147 from code to deep review, preserving isolation.
4. Routed Step 149 from code to deep review, preserving isolation.
5. Routed Step 151 from code to deep review, preserving isolation.
6. Added missing review flags to Step 148 and operator N/A flags to Step 150.
7. Resolved Step 148's shared-writer dependency and read-only lab boundary.
8. Defined release/store/proof shapes, immutable publication and failed-attempt behavior.
9. Defined activation preview/preimage/selector/recovery and concurrency contracts.
10. Defined compact report inputs, projections, null/stub handling and explicit hygiene scope.
11. Added run/setup guide and distinguished disposable smoke from live Step 150 smoke.
12. Corrected stale context and recorded the actual deep-review host prerequisite.

Exactly one autofix marker precedes each touched step. Full re-check found no
remaining defects; the final verification pass made no further fixes.

0 items need your input.
Auto-applied 0 fixes. Plan is ready for `/plan-wrap` and `/repo-sync`.

READY
