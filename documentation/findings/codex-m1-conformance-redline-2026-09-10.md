# M1 publication 4: redline publication check

**Result:** rendered and validated; explicit operator approval pending.
**Proposal:** `documentation/codex-m1-conformance-proposal.html`.
**Plan:** `documentation/codex-ordinary-build-milestone-plan.md`.
**Input:** reviewed amendment at `df2f558c089e96b4b0c77c9624bb7f9cfe6613b4`.

The operator requested the formal plan-redline step and an opportunity to give
explicit approval. The installed Codex adapter selected its standalone HTML
publication mechanism. The optional reference-proposal file was absent from the
installed skill and canonical worktree; the preserved publication-3 page supplied
the existing visual style. No missing rendering capability was simulated.

## Publication boundary

This is publication 4 of the continuing M1 proposal history and the first HTML
rendering at the stable P5 amendment locator. The earlier publication-3 file
remains unchanged, as the amendment requires. Future amendment publications
overwrite the new locator and increment the label, retaining decision IDs.

The plan now contains its Proposal locator, explicit publication-approval status
and final preparation order. P1-P5 and D1-D14 keep their identity and ownership.
P5's planning direction was already authorized; no explicit approval of this
rendering is inferred. Every D entry has a what, why and tweak axis, including
the deferred and retained defaults.

## Checks performed

- HTML parsed with balanced tags and unique IDs; all eight required sections are
  in order after the header. All 19 decision IDs match the plan inventory.
- Chromium loaded the local standalone file without page errors or external
  resource requests. All 14 default rows contain nonempty what/why/tweak cells.
- Light/dark screen themes, a 390-pixel mobile viewport and forced-light print
  styling passed checks. Root horizontal overflow was absent. The wide decision
  table scrolls within its labeled region on mobile and expands in print.
- Screenshots and a PDF were produced locally. The light view and print preview
  were visually inspected. Seven relative source links resolve to existing files.
- The plan's build and acceptance sections 5/6 are unchanged from the reviewed
  amendment. No reviewer flag, source-step criterion, fixture requirement or run
  limit was changed to produce this rendering.
- `git diff --check` passed. The original proposal has no diff. Main/live remote
  remain `b8acf82924cc3166a078cc50caa26b08d1135321`; the active native controller
  and its candidate gate were observed before publication and remain untouched.

Local validation artifacts live in `.build-step/redline-publication-4/` in the
amendment worktree. This is a document check, not an implementation root gate or
an independent native review. No new pytest or build-phase was launched.

## After feedback

Record the user's explicit approval or ID-referenced changes. Fold changes into
the plan before republishing. Run final plan-wrap after feedback; material
changes also repeat technical review. Synchronize affected issue bodies after
post-sync plan edits, preserving the current #199/#204 contracts until the
adoption handoff. Reconcile the active controller, terminal evidence, checkpoint
and Git before integration. Approval does not reset an exhausted iteration count,
extend the current deadline or authorize an automatic relaunch.
