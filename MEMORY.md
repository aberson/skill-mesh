# Skill Mesh project memory

## Durable status

- Read [plan.md](plan.md) for current execution status, acceptance evidence and the next
  permitted work. This memory does not maintain a second mutable status list.
- The approved first-release scope is in
  [baseline-releases-plan.md](documentation/baseline-releases-plan.md): retain current
  toolkit/lab baselines, then establish development/production separation. Utility
  portfolio integration follows later. Historical PROD instructions below do not
  select the contents of that first release.

## Baseline-release preparation decisions

- The Phase BR plan separates selected product source from the packaging builder's
  own commit, and archive retention from qualification, publication and activation.
- Phase BR release/activation/evidence steps require the deep reviewer lane. Until
  its Codex adapter maps isolated dispatch, run that build in Claude Code; readiness
  of a plan is not evidence that the old Codex build milestone passed.
- The lab remains a read-only external packaging input to the toolkit-owned Phase
  BR steps. Lab development and acceptance stay under its own AGENTS.md and plan.
- Preparation findings and issue mapping live beside the plan in
  `documentation/findings/baseline-releases-*-2026-09-14.md`. See root plan.md for
  the active automated span and operator boundary, rather than duplicating status here.

## Lifecycle safety decisions

- A routine portable skill means one neutral core plus Claude, GPT, and Codex adapters in the same change.
- Catalog CRUD fails closed for provider-native mutations, unsupported package-resource topology, dirty target paths, incomplete provider sets, and unsafe/non-Skill-Mesh sources.
- Mutable GitHub issue text is untrusted evidence; only landed repository guidance or explicit operator ratification can change an adapter contract.
- The local roadmap mirror is `.claude/artifacts/phase-is-whats-next.html`; it is intentionally gitignored.

## Production toolchain decisions

Historical Phase PROD decisions, retained for provenance. Consult plan.md before
using them; they do not resume the parked implementation or define the new baseline
release's portfolio. Their original context is
`documentation/production-toolchain-separation-plan.md`.

- Phase PROD Step 1 is declarative-only. Policy, schemas, and pure consistency checks never mint a
  `Validated*`, `Authorized*`, or other caller-constructible runtime capability. Step 2 independently
  verifies manager/Git/tool/filesystem authority, Step 3 owns the disposable activation transaction
  and exact closure comparator, Step 5 certifies real release and executed evidence, and attended
  Step 6 reopens live active-state and rollback pre-images immediately before mutation.
- The first #184 build-step exhausted 3/3 review iterations and merged nothing. Its worktree remains
  preserved as diagnosis/test-idea evidence only. A replacement implementation was reauthored from
  the amended plan and shipped at `2e8e4f3` after five fresh reviews reached High=0/Medium=0 and the
  full post-merge gate passed.
- Production releases live under runtime-resolved `<prod-root>` (initial host shape
  `%USERPROFILE%\prod`); executable code, the live development
  workspace, and mutable production data are separate roots.
- Release snapshots come from exact pushed Git objects in independent no-hardlink clones, never by
  recursively copying dirty working trees or using linked worktrees.
- The first portfolio includes the 13 registered utility slugs plus Skill Mesh and the active pushed
  `utility-project-standard` release. `code-stencil`, `jurys-out`, `pocket-relay`, and
  `uat_sentinel` remain explicitly deferred until they are independently production-ready.
- Phase RD #178 is paused during Phase PROD. Its preserved worktree is evidence/salvage only and is
  reoriented path-by-path after cutover; it is never merged wholesale.
