# Coordinator handoff contract review

Date: 2026-09-14. Scope: the approved coordinator/builder changes in the five
canonical pipeline cores and their Claude, GPT and Codex adapters, based on
preparation commit `990e33364efde7b816ac96de03d402c9be1f4743`.

Two independent fresh-context reviewers performed a read-only source review and
forward decision exercises. They did not launch a production pipeline, qualify a
host bridge, run release steps or install a profile. Their bounded follow-ups
reported no remaining source blockers after the corrections below.

## Corrections checked

- Committed builder output uses explicit base/candidate ranges through review,
  runtime evidence and integration; uncommitted-only diff capture cannot hide it.
- Candidate refs and hashed gate/review receipts survive disposable cleanup.
  Audit receipts cannot replace the authenticated verdict channel.
- Explicit safe detachment permits standalone handoff while retaining packet
  history; unresolved launches prevent detachment and replacement.
- Packet resume bypasses the ambient current.md selector, including other
  coordinators working from the same plan.
- Coordinator integration uses a clean checkout and scoped commits. Legacy
  stash/restore and broad staging cannot sweep unrelated work into a checkpoint.
- Codex checkpoint invocation uses real same-session skill execution; the shared
  schema dependency is emitted for both coordinator and standalone paths.

## Forward decision exercises

These are decisions derived from source instructions, not observed host execution.

| Situation | Required decision |
|---|---|
| Preparation only; code 1, operator 2, code 3 | Prepare step 1; record boundary 2 and preparation-only authority; no builder launch |
| Explicit steps 1,3 across unfinished boundary 2, even in dry-run | Read-only BLOCKED; no dispatch or state mutation |
| Unacknowledged launch and uncertain prior owner | INCOMPLETE/reconcile; no takeover or replacement; refusal only in the new host's own checkpoint |
| Step 1 accepted, operator 2 pending | NEEDS_OPERATOR at 2; keep step 3 and umbrella pending |
| Explicit standalone interactive handoff with no packet | Preserve the existing two-block clear/goal/build presentation after successful checkpoint |
| Explicit end with unresolved children | End-window checkpoint remains INCOMPLETE with the exact packet pointer; no fabricated exit or release |
| Required Claude review from Codex without a verified bridge | BLOCKED with required_tool_missing; preserve review requirements and coordinator host |
| Interactive switch after assignments exited | Verify ownership and completed writes, detach safely, retain historical receipts, then present interactive handoff |
| Interactive switch with an unacknowledged launch | INCOMPLETE; retain packet attachment and emit no interactive opener |

## Evidence boundary

The implementation is an instruction contract using existing host/filesystem/Git
capabilities. It adds no scheduler or new signing authority. Packaging checks and
the root test suite verify source/distribution integrity; live end-to-end
coordinator acceptance still requires a real run with the declared host ports and
interruption recovery. Current execution status and test receipts are indexed by
[plan.md](../../plan.md).
