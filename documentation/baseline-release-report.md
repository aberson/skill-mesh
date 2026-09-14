# Skill Mesh baseline report

Observed 2026-09-14 03:28 UTC (September 13 local). This is a dated inventory.
Current execution status stays in each repository's plan.md; acceptance is scoped to
its cited source and environment. See the [release plan](baseline-releases-plan.md).

## At a glance

| Area | Observed baseline | Attention / next action |
|---|---|---|
| Toolkit source | Clean main at `79a985a`; remote main matches; 57 catalog skills | Qualify and package this exact baseline; GitHub release list is empty |
| Codex daily profile | 125/125 ledger files present; all match both ledger hashes and freshly emitted `79a985a` bytes exactly | Retained owned-file snapshot; installed ledger carries no source/version field |
| Claude daily profile | Discovery root is a junction into the development workspace | Record and preserve its mixed content before a later independent installation |
| Copilot profile | Home discovery root absent; current source builds 54 adapter packages | Build availability only; no daily-profile or workflow-support claim |
| Lab current source | Clean `editor-project-input-20260914` at `700a71e`; main remains `032da7d` | Preserve current work as experimental; Step 144 acceptance is INCOMPLETE |
| Lab delivery | No remote and no tags; four responsibilities, two observed host bindings | A source snapshot and restorable Git bundle now retain the baseline locally |

The installed home also contains consumer-only skills. The inspector's
`owned_count` describes generated-header shape, not ledger ownership or
unchanged bytes. Only the explicit 125-file Codex comparison above establishes
byte agreement. The Claude inventory includes seven catalog-name skills without
generated headers; this is a preservation concern, not permission to replace them.

## Capability evidence

| Product / host | Established evidence | Limit |
|---|---|---|
| Toolkit / Codex | Historical `25b54a5` root gate: 1636 passed, 1 skipped; current installed bytes equal a fresh `79a985a` distribution | Native ordinary-build M1 remains unfinished in the controlling plan; byte equality is not new workflow acceptance |
| Toolkit / Claude | Current source emits 57 skill packages | No fresh native acceptance performed in this inventory; daily discovery remains development-linked |
| Toolkit / Copilot | Current source emits 54 skill packages | Build-only scope; home profile absent |
| Lab / Codex and Antigravity (Gemini route) | Prepared editor tasks at `0a56c672`: 15/15 fixed cases each, separate native review; source gate 218 passed in 813.45s | Historical prepared-task proof; user acceptance pending; it does not certify the later `700a71e` source |
| Lab / Claude and open-model routes | Desired future product scope | No supporting native evidence in the inspected capability record |

Toolkit generated profiles contain 128 Claude files, 125 Copilot files, and 125
Codex files. The lab defines build/review/handoff in its three-entry catalog and
adds the editor workflow entry separately; counting only SKILL.md source files
would incorrectly report one responsibility.

## Checks and retained material

- Fresh build from the exact toolkit source archive: all three profiles emitted.
- Staged toolkit package-integrity check: **417 passed, 3 skipped in 85.10s**, exit 0.
  This focused staged-tree result is not the repository-root DONE gate or a release certificate.
- Source archives checked against every Git blob and the complete file set:
  toolkit **579 files**, lab **93 files**, all exact.
- Codex snapshot: 125 owned files plus ledger; ZIP contents read back and hashes
  verified; source files and ledger stayed unchanged across capture.
- Lab Git bundle verified and restored into an independent bare repository;
  current-branch and main commits recovered exactly.

Raw records and retained archives live under the private evidence locator
`%LOCALAPPDATA%/SkillMesh/Evidence/baseline-release-20260914T032353Z/`.
The [portable observation summary](evidence/baseline-release-20260914.json) carries
the identities and artifact hashes. These are local copies; off-machine backup
and restoration of ignored lab run evidence have not been established.

## Dependencies, hygiene, and minimal telemetry

| Area | Finding | Disposition |
|---|---|---|
| Environment | PowerShell 5.1.26100.9444; Python 3.14.3; pytest 9.1.1; PyYAML 6.0.3; markdown-it-py 4.2.0; jsonschema 4.26.0 | Observed tooling, not a newly declared supported-version range |
| External utilities | Some workflow instructions call workspace utilities; build-step's observatory hook is one verified example | List exact integrations in release notes; portfolio-wide release management is later |
| Current-status duplication | Toolkit MEMORY.md still names the parked PROD track active | Reconcile memory to the authoritative plan in this planning change |
| Worktrees | 24 pre-existing toolkit worktrees plus this planning worktree; 15 lab worktrees | Registered count only; no orphan or deletion verdict inferred |
| Afterparty scope | Current scope discovery uses CLAUDE.md; lab uses AGENTS.md and .local records | Add explicit targeting before using a combined sweep |
| Run telemetry | Lab records already provide identities, timestamps, states, checks and review | Project them into the compact report; keep acceptance with the original coordinator |
| Usage telemetry | Toolkit writer can emit zero usage with a stub verdict | Exclude stub values from measured usage; unknown cost/tokens remain unknown |

Next: review the release plan, qualify the retained baseline artifacts, and retain
their first release identities. Keep later source work and any live-profile
activation separately attributable.
