# Context and learning draft: fresh-context readiness

Historical target: publication 1, after its technical review and proposal publication. Stable plan/proposal files now contain publication 2. This report is retained as history and superseded by the [September 19 wrap](context-learning-plan-wrap-2026-09-19.md). Applied the plan-wrap checklist in the original session, not an independent-agent evaluation.

Completion gate: no consistent completion markers found -- running full check (fail-safe default).

All seven proposed implementation units are DEFERRED; none has shipped. The report distinguishes a useful design proposal from an executable build handoff.

§1 Schemas and data structures — findings: 1

§2 Identifiers — pass

§3 Acronyms and tool names — pass

§4 Stack decisions with rationale — pass

§5 Unresolved decisions — findings: 1

§6 API contracts — N/A: local CLI and hook adapters, no new HTTP API

§7 Development process — findings: 2

§8 Quickstart / how to run — findings: 1

§9 Referenced external files — pass; existing owners are linked, proposed outputs are labeled, local links mechanically checked separately

§10 Scope and constraints — pass

§11 Operator/code step-shape integrity (Blocker if violated) — pass

§12 Conditional steps must declare a Condition: predicate (Blocker) — N/A: no conditional steps

§13 Substrate-smoke step present when the plan touches deployment seams (Significant Gap) — pass

## Blocker

**B1 — §7: cross-repository execution needs separate plans.**
Found at: “Do not give the whole file to build-phase” and Step 133's “separately scoped coding-root hook/schema/config changes.”
Fix: prepare repository-scoped executable slices, reconcile unmerged step numbers and preserve their dependencies before issue synchronization. A new model must not infer one commit/build repository for both.

## Gap

**G1 — §§1/8: closed wire and CLI definitions remain a design follow-up.**
Found at: “The executable plan must freeze the closed JSON schemas, string/array size limits and exact CLI arguments.”
Fix: specify command parameters, complete bounded schemas and concrete install/first-run invocations in the executable slice. Proposed tables and quickstart explain the design but are not yet an implementation-ready interface contract. This is one gap appearing in two checklist lines.

**G2 — §5: implementation queue is unselected.**
Found at: “choose when this track should start relative to M1.”
Fix: select that order in the next operator design iteration. P2/P3 establish desired outcome and trial mode; they do not specify resuming/replacing an existing bounded run.

**G3 — §7: independent evaluation/native execution capability is unqualified.**
Found at: “actual host evaluation capability” in Step 136 and “has not been live-probed” in Design Decision 4.
Fix: bind the executable plan to a qualified evaluation route and concrete native hook acceptance. If unavailable, retain the context/capture milestone and report the trial phase unavailable; never substitute self-grading or quietly weaken deep review. The draft already specifies honest fallback behavior.

## Minor

None. Blank issue fields are expected in this unsynchronized draft, not an implementation authorization.

## Needs your input

The next design iteration should focus on D1 (pilot scope), D4 (bounded trial budget) and D8 (queue placement). B1/G1 can then be resolved mechanically for the selected slice; G3 requires actual qualification rather than another prose claim.

## Document validation

Passed a Python validation using Markdown-it and HTMLParser over seven new Markdown documents and the standalone HTML proposal: 54 local links resolve; HTML tags and anchors balance; all 11 P/D decision IDs are present; offline-asset and print-style requirements are present; all seven step blocks have required fields and DEFERRED status; no absolute user-home paths or trailing whitespace were found in the Markdown documents. HTML appearance was not browser-rendered in this pass.

`git diff --check -- plan.md` passed. Read-only investigation commands included `rg`, `Get-Content`, `git log/status/rev-parse/show/worktree list`, `gh issue view`, and runtime version queries. No implementation suite was run because this change only adds planning documents and their canonical entry link.

NEEDS WORK: 1 blockers, 3 gaps
