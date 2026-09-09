Completion gate: no consistent completion markers found -- running full check (fail-safe default).

# M1 fresh-context plan check

Target: `documentation/codex-ordinary-build-milestone-plan.md`, publication 3,
after technical review and stable proposal publication on 2026-09-09.
All four units are PLANNED; this is the full forward check. It was performed in
the current session as the installed Codex plan-wrap adapter specifies; it is
not an isolated-agent test or native-host compatibility observation.

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

None requiring a planning decision. Native qualification is explicitly unproved;
issue synchronization and the new Step 127 issue remain required before dispatch.
Plan READY does not satisfy those execution prerequisites.

## Minor

None. The historical plan is visibly superseded for M1, the entry plan points to
the current contract, and the proposal's P/D IDs remain stable.

## Evidence

- Sections 3/4 define ordinary reviewer coverage, private authority, candidate
  identity, support values, native IDs, checkpoint ownership and persisted fields.
  Opaque native IDs come from the host rather than a role alias or fabricated ID.
- Section 6 defines concrete HTTP request/response behavior, fake actors, fixture
  asset/build paths, generated loopback port and full-review plan flags. The app
  and its runnable procedure are explicitly Step 128 outputs; a fresh reader does
  not need to invent them before implementation.
- Sections 5/7 define contiguous Steps 126-129, dependencies, the source-review
  bootstrap, its expiry, qualification-first behavior, concrete build-phase
  command, ordinary mechanical checks and the unchanged full-root DONE gate.
- Read-only structure validation found exactly three code units and one wait,
  all PLANNED with every required field. Step 127's blank issue is explicitly
  backfilled by repo-sync, not treated as permission to dispatch without one.
- Twenty-three explicitly enumerated existing source/test/contract/tool paths
  resolved across the technical review and wrap checks. The five future outputs
  (capture, checkpoint helper, workflow tests, operator procedure, fixture) are
  absent as expected and assigned to implementation steps. Glob-like impact
  descriptions are not claimed as individual existing files.
- `git cat-file -e` verified the pinned coding-root checkpoint producer. The
  current repaired-main certificate exists; publication-2's failed/unfinished
  repair snapshots are explicitly historical. The native failure is distinct.
- The proposal HTML is a stable standalone view of the plan. It distinguishes
  approved P4 from agent-selected D11/D12 and surfaces the source-review tradeoff.
- Main remained clean at `380d38b82ee8f07c876e76bf789f7b235ebe0b55`. The protected
  Step 111 worktree still carries its seven staged files; the protected Claude
  handoff worktree is clean. No build, pytest, live install or acceptance ran.
- All 18 frozen files in the expired windows-stdin-v2 run retained their before/
  after SHA256 values. HTML IDs/internal links, ordered plan-step fields and
  `git diff --check` passed. Source/tool/test trees match repaired main; changes
  in this revision are planning documents only.

The scope correction, source-file ownership fix and explicit regression paths
were completed during technical review before proposal publication. No further
behavioral plan change was needed by this check. References to these reports and
the explicit untrusted-input boundary document existing obligations.

READY
