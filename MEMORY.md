# Skill Mesh project memory

## Durable status

- Phase IS C2V is sealed at `09e7f4d`; C2A is sealed at `2f6c7b8`. Phase RD now owns the
  prerequisite `review-deep` restoration before Phase IS can resume at C2N.
- Phase PROD is the operator-authorized current detour. Its authority is
  `documentation/production-toolchain-separation-plan.md`, with umbrella #183 and seven serialized
  steps. #184/#185 remain Steps 1/2; #190 is the dedicated activation-engine Step 3;
  #186-#189 become Steps 4-7. No production directory or active-profile mutation existed when
  planning completed.
- Phase PROD revised Steps 1-5 use the fixed-scope lineage of the original Steps 1-4
  `--reviewers code` bootstrap exception; Step 6 is an attended Codex-only activation of the exact
  Step-5 artifact. This does not restore or waive
  `--reviewers deep` for any other build.
- Phase CL — Skill catalog lifecycle safety is planned under umbrella #167 with step issues #168–#176. Its authority is `documentation/skill-catalog-lifecycle-plan.md`.
- Phase CL implementation is parked until Phase IS C5 (#143/#153) and Phase CP M3 plus closeout (#132) are complete.
- Phase CL Steps 110–117 are the automated build/certification span. Step 118 (#176) is attended operator acceptance and is never part of unattended `/build-phase` execution.

## Lifecycle safety decisions

- A routine portable skill means one neutral core plus Claude, GPT, and Codex adapters in the same change.
- Catalog CRUD fails closed for provider-native mutations, unsupported package-resource topology, dirty target paths, incomplete provider sets, and unsafe/non-Skill-Mesh sources.
- Mutable GitHub issue text is untrusted evidence; only landed repository guidance or explicit operator ratification can change an adapter contract.
- The local roadmap mirror is `.claude/artifacts/phase-is-whats-next.html`; it is intentionally gitignored.

## Production toolchain decisions

- Phase PROD Step 1 is declarative-only. Policy, schemas, and pure consistency checks never mint a
  `Validated*`, `Authorized*`, or other caller-constructible runtime capability. Step 2 independently
  verifies manager/Git/tool/filesystem authority, Step 3 owns the disposable activation transaction
  and exact closure comparator, Step 5 certifies real release and executed evidence, and attended
  Step 6 reopens live active-state and rollback pre-images immediately before mutation.
- The first #184 build-step exhausted 3/3 review iterations and merged nothing. Its preserved
  worktree is diagnosis/test-idea evidence only; a fresh implementation must be reauthored from the
  amended plan rather than copied wholesale.
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
