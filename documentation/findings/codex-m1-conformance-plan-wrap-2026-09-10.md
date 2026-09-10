Completion gate: no consistent completion markers found -- running full check (fail-safe default).

# M1 conformance amendment: fresh-context plan check

Target: `documentation/codex-ordinary-build-milestone-plan.md` after the P5
technical review, with its amendment record and root status index. All four units
remain unfinished. Checked in this session using the installed Codex plan-wrap
contract; no isolated-agent or native acceptance result is claimed.

§1 Schemas and data structures — pass
§2 Identifiers — pass
§3 Acronyms and tool names — pass
§4 Stack decisions with rationale — pass
§5 Unresolved decisions — pass
§6 API contracts — pass
§7 Development process — pass
§8 Quickstart / how to run — pass
§9 Referenced external files — pass
§10 Scope and constraints — pass
§11 Operator/code step-shape integrity (Blocker if violated) — pass
§12 Conditional steps must declare a Condition: predicate (Blocker) — N/A: no conditional steps
§13 Substrate-smoke step present when the plan touches deployment seams (Significant Gap) — pass

## Blocker

None.

## Gap

None requiring a planning decision. The live gate is still running; pending
integration and actual implementation/acceptance are execution prerequisites,
not a claim that this planning check completed M1.

## Minor

None.

## Evidence

- Section 1 now defines workflow conformance, functional correctness, exact
  mechanical identity and review-quality observations separately. It allows
  valid model variation without excusing skipped obligations or invalid receipts.
- Section 4 summarizes support variables, full Git IDs, host-generated IDs,
  hashes, gates, reviews and checkpoint records. The added quality field links
  actual observations to raw receipts without requiring a prescribed finding.
- Section 6 provides exact shipping-boundary and actor-response requirements,
  actual invalid/corrected candidate handling and mechanical-before-review order.
  The first invalid candidate consumes an iteration; C3/C5 still require all
  independent real reviewers on the corrected candidate and normal verdict rules.
- Step 128 owns the app, fixture plan and concrete provisioning/start/resume
  commands. Those are planned outputs, not required existing files. Step 129
  observes them on the native installed host; preparation cannot mark a live row.
- Section 7 and the amendment record explicitly distinguish the pending plan
  branch from the active frozen run, preserve its candidate/deadline/iteration
  history and require safe integration plus a new recorded handoff before dispatch.
- The root index carries the dated actual run snapshot and evidence locators.
  The deferred-plan banner marks old detection thresholds superseded while
  preserving their historical text and the original approval artifact.
- Ordered heading-format Steps 126-129 retain their type, issue mapping,
  dependencies and completion criteria. Existing support/source/test paths and
  all new report links were checked; templated/generated paths are not mistaken
  for currently existing artifacts.

READY
