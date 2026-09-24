# Step 153 completion checkpoint

Reviewed candidate: `48c926f392a6a4b06212bd92037ffe637c5f3b2b`, based on
`110d916df9d46916fa7aeee19fefc2847b9f5476`. The preserved implementation was
integrated with current main without changing its behavior. The original dirty
worktree remains untouched. This is an unfinished build, not a release certificate.

## Evidence completed

- Fresh Sol developer verification: existing ancestor-reparse repair is present;
  no implementation change needed. Intervening Phase CD distribution tests retained.
- Manifest generation: exit 0. All three provider builds: exit 0, 17.838 seconds.
- Focused helper suite: **100 passed in 173.08 seconds**, exit 0.
- Normal installer into a disposable Codex home, followed by the emitted helper's
  record/replay/pending/disposition cycle: **PASS in 94.15 seconds**; fixtures removed.
- Diff check: exit 0. No configured lint/typecheck gate; the installed mechanical
  pre-pass records unavailable ruff and unconfigured mypy, without inventing a PASS.
- Six independent fresh Terra lenses: correctness, bugs, test-quality, style and
  plan-conformance PASS. Security has one Block. Deterministic installed aggregation
  returned **NEEDS-WORK**. A malformed initial style response was preserved as
  invalid and replaced by one fresh, valid report; no verdict was rewritten.
- A 1.93-second synthetic Windows-junction reproduction confirmed the security
  finding. Only disposable fixture paths were affected and all were removed.

The full repository-root suite has **not started**. There is no full-suite PASS,
merge, issue closure, live profile activation or Step 154 acceptance.

## Decision needed: local filesystem trust

The guard in `_shared/lesson_observations.py` checks path components and resolved
containment, then publication opens a pathname. A process able to replace the
private inbox directory between those operations can redirect the write outside
the common Git directory. The module's statement that a swap between inspection
and opening still cannot move a record out of the clone is therefore false.

**Proposed first-version boundary, awaiting operator decision:**

> The helper operates in operator-controlled Git metadata. Its symlink/reparse
> and containment checks inspect the filesystem state before access; they are not
> a security boundary against another process replacing directories concurrently.
> Hostile concurrent mutation of Git metadata is outside this version's support.
> Concurrent capture and reading through the helper remain supported. Private
> storage placement, no-overwrite atomic publication, bounded reads and sanitized
> publication rules remain requirements.

If selected, correct the false claim and document this boundary consistently,
then obtain a closing review of the changed assumptions. Preserve this historical
Block and its reproduction; do not relabel it as a passing deep review.

The alternative is race-resistant filesystem access before first delivery. That
requires an explicit implementation decision and revised scope; it is not another
line-level recheck, which would merely move the same race window.

The [bounded execution record](../mistake-capture-step153-completion.md) retains
the cumulative retry ceiling and one-root-gate limit. No expensive test runs are
admitted while this decision is unresolved. Memory admission is checked immediately
before the eventual gate rather than assumed from an earlier observation.
