# Skill Mesh product charter

**Status:** APPROVED — 2026-08-13

**Approved by:** Abraham Robison

**Decision record:** `documentation/skill-mesh-course-correction-plan.md`

## Product goal

Skill Mesh gives Abraham materially consistent planning, building, review, and handoff workflows in Claude Code and Codex. It makes model choice, fallback, evidence, and important host differences visible.

"Materially consistent" means the same workflow steps, safety rules, output structure, and visible differences. It does not mean identical wording, speed, hidden reasoning, or model behavior.

## Skill Mesh owns

- One main definition of each portable workflow and skill behavior
- Small Claude Code and Codex instruction layers
- Model roles, tested model pairs, and an explicit fallback policy
- Checks that distinguish finding a package from running it correctly
- Representative behavior tests with deliberately planted defects
- Versioned run records that show what was requested, what ran, what evidence was produced, and what was deferred
- Generated compatibility files only where a host needs them

The existing `.github/skills` files and GPT connection are GitHub Copilot-specific. They are not proof of native Codex support. The recovery plan must audit, retarget, or retire those files and connections.

## Host-native systems own when experiments prove them sufficient

- Installation and update
- Discovery and package version selection
- Enable, disable, and uninstall
- Host-specific permissions and session behavior
- Host package manifests and marketplaces

Package lifecycle and cross-family review are separate problems. Native packaging does not prove that a Claude-hosted workflow can run a GPT-family reviewer, or the reverse.

## Dev Observatory owns

- Reading a limited amount of Skill Mesh evidence and converting it to an existing display shape
- Showing evidence age, compatibility, and load errors
- Summary and at-a-glance views backed by saved evidence
- Transparency views that show only mechanical caller and consumer connections

Dev Observatory reads and displays evidence. It does not route live Skill Mesh work. A static at-a-glance page does not prove that a utility is connected or that a run occurred.

## Utility Project Standard owns

- Project profiles and standard-check manifests
- Shared evidence terms and named contract owners
- Publication rules

The standard remains independent. Its unfinished v1 is not a Skill Mesh release prerequisite. A future `utility-project.toml` can name the Skill Mesh receipt owner, version, and locator after the standard stabilizes.

## Anti-goals

1. Skill Mesh will not become a general framework-of-frameworks or replace Claude Code and Codex.
2. Provider count is not a success metric. Claude Code and Codex are the release hosts.
3. Skill Mesh will not silently fall back, relabel a model, or infer model identity from a host or adapter name.
4. The release will not test every skill, model, and host combination. Representative behavior plus repeatable contract checks is sufficient.
5. Skill Mesh will not own host lifecycle when a host-native package passes the lifecycle experiment and Abraham approves that choice.
6. Dev Observatory will not become a runtime requirement for skill invocation.
7. A Skill Mesh run record will not replace a real utility call when a workflow needs that utility's behavior.
8. Utility Project Standard will not become a Dev Observatory subproject or standardize a one-producer schema prematurely.
9. Omnigent, local models, Gemini, and GitHub Copilot are not part of this release.
10. The current Step 4 installer work is neither discarded nor presumed correct. Preserve it before the architecture decision.
11. Full multi-file skill decomposition is not part of product recovery. Correct the contracts first, then redesign and test skill structure as a separate project.
12. Formal ASD-STE100 compliance is not part of this release. Pilot the proposed plain operational English profile for operator-facing communication.

## Release invariants

- Run at least one real representative cross-family review.
- Record requested model identity and resolution status for every release proof.
- Observe actual resolved identity where the host supports it. Any waiver is explicit and named.
- Keep deterministic tests as the primary correctness gate.
- Review the exact committed candidate files. Do not review changing worktree files.
- Do not let Nits cause an automatic correction or review cycle.
- Treat unknown or uncertain verdicts as unable to advance.
- Use focused tests during iteration and one authoritative full result for each exact release-candidate SHA and declared environment/configuration.
- Preserve or recover consumer-owned bytes before any live lifecycle change.

## Communication

The recovery plan offers an optional pilot of `documentation/operator-communication-profile.md`. If Abraham starts the pilot, keep the short rule in always-loaded instructions for the pilot candidate. Load the detailed profile only when writing or reviewing operator-facing material. Abraham may accept, refine, or decline the profile after user acceptance testing.
