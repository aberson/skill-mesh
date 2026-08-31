# Phase RD plan review

Reviewing as: feature plan. Sections 17–21 apply.

Plan reviewed: `documentation/phase-rd-review-deep-restoration-plan.md`
Mode: `--no-autofix`
Date: 2026-08-31

## Blockers

None.

- The plan is heading-parseable and all three steps have `Problem`, `Type`, `Issue`, `Files`,
  `Existing context`, `Produces`, `Done when`, `Flags`, and `Depends on` fields
  (`phase-rd-review-deep-restoration-plan.md:103-200`).
- The pinned coding-root commit resolves and `git ls-tree -r` returns exactly 39 tracked review-deep
  eval/script inputs. The plan distinguishes the one lint security derivative from the 38 byte-identical
  imports (`:40-54`), resolving the prior provenance contradiction.
- There are no conditional or operator/code hybrid steps. The only blank issue values are the
  expected pre-repo-sync `**Issue:** #` form.
- The accepted Phase IS plan, frozen UAT, C2V/C2A artifacts, real profiles, provider resources, and
  workstation security state are explicit exclusions (`:10-13`, `:119-123`, `:239-246`).

## Significant gaps

One documented bootstrap exception, accepted for this plan:

- Steps 1-2 touch a high-stakes installer/distribution seam but declare `--reviewers code`
  (`:134-139`, `:166-169`). The usual stakes-aware route is `--reviewers deep`, per
  `skills/review-deep/core.md:25-34`. That route cannot run before Step 1 because the mandatory
  calibration invocation at `skills/review-deep/core.md:762-775` currently lacks its package.
  Issue #177 also requires five fresh isolated code-review lenses. The plan therefore locks a
  bootstrap-only exception: all five fresh code lenses plus parent-only deterministic aggregation,
  zero High/Medium findings, and full-root gates. Step 3 restores the normal deep lane immediately.
  This is a bounded review-route disposition, not an unresolved operator choice.

The deployment-seam smoke check is satisfied by the already-authoritative Phase IS C3/C4 disposable
host acceptance rather than by this bridge plan. The bridge explicitly forbids a real-host install and
does not claim deployment acceptance (`:91-94`, `:239-246`).

## Missing items

None.

- Current source establishes the stated gap: `skills/review-deep/providers/codex.md:9` still contains
  the provider-wide rejection, while `skills/review-deep/core.md:10-19` requires independent lens
  contexts and parent-owned deterministic aggregation.
- Current generator input owns `support_assets` but no `package_assets` contract
  (`tools/gen_manifest.py:290-426`), so Steps 1-2 name the generator, manifest, builder, installer,
  package-integrity, distribution, calibration, and documentation consumers together.
- Existing profile counts are 128/125/125 in the frozen UAT; adding 39 raw leaves plus one index to
  each yields the candidate 168/165/165 closure without rewriting the frozen measurement.

## Nice-to-haves

None required before execution. The two preserved worktrees remain useful diagnostic references, but
the plan correctly excludes their uncommitted bytes and reports from acceptance evidence.

## Toolchain and risk disposition

- Install: no workstation-wide install; fresh worktrees only.
- Dev server/UI: N/A.
- Build: `tools/build-distributions.ps1 -Provider all`.
- Test: focused suites plus repository-root `python -m pytest` on every step and at phase end.
- Lint/typecheck: no separate project-wide commands; PowerShell parsing, `bash -n`, generator
  no-unexpected-diff, and `git diff --check` are explicit.
- Concurrency: all steps are serialized; Step 2 consumes Step 1 and Step 3 consumes calibrated Step 2.
- Recovery: fresh worktrees, authenticated fail-closed verdicts, read-only donors, and no partial
  package/builder/installer landing.

Auto-applied 0 fixes. Plan is ready for `/plan-wrap` and `/repo-sync` with the recorded bootstrap
review-route exception.
