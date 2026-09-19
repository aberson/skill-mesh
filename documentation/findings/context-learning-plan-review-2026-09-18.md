Reviewing as: feature plan. Sections 17–21 apply.

# Context and learning draft: technical review

Historical target: publication 1, 2026-09-18. The stable plan/proposal files now contain publication 2. This report is retained as history and superseded by the [September 19 review](context-learning-plan-review-2026-09-19.md). Applied the plan-review checklist in the original session; this was not an independent-agent review or implementation certification. No populated Issue fields; no repo-sync performed.

## Blockers

**B1 — repository-specific execution ownership is not yet encoded.** Step 133 explicitly spans Skill Mesh distribution/skill changes and coding-root hooks/settings. A single build-phase invocation has one target repository. The draft correctly prohibits whole-file dispatch, but it is therefore not an executable build plan. Extract repository-specific plans, preserve cross-repository dependencies and recheck unmerged number reservations before repo-sync. This is planned next-iteration work, not a reason to withhold the requested design proposal.

## Significant gaps

**G1 — wire/CLI contract needs final bounds.** Section 5 defines event semantics and payload fields but defers exact closed schemas, input limits and CLI arguments. Freeze these in the executable slice; a fresh builder should not invent incompatible capture/install/host interfaces.

**G2 — native capability and trial route are unproved.** Installed Codex version was read, and official host documentation was inspected. No live hook/capture or independent trial probe ran. Steps 133/136 own that proof and fail/unavailable paths. Current deep-review capability must also qualify before those implementation gates can run; do not downgrade merely to proceed.

**G3 — scheduling against M1 remains an operator choice.** The draft cites current primary-goal constraints and leaves all work deferred. Selecting that slot is a planning decision; this session's investigation is not an instruction to restart M1 or begin a competing build.

## Missing items

None beyond the explicitly tracked execution-contract gap G1. Proposed runtime files and setup/rollback runbooks are build outputs, not falsely described as existing files.

## Nice-to-haves

Blank Issue fields are expected before repo-sync. Observatory discovery reachability is supplied by the root plan link; inclusion in every forecast surface has not been tested. No ports are added, so a port-collision check is not applicable.

## Corrections made during review

- Reconciled the effort table: 9–17 active days; approximately 4–6 elapsed weeks and first context milestone around working days 9–13. These remain estimates.
- Added stable identifier formats and minimum kind-specific payload summaries rather than leaving `payload` uninterpreted.
- Preserved a concrete marker-capture limitation: Stop's final message does not prove intermediate commentary coverage.
- Recorded Observatory Step 72 as merged, supported by Git `19b1cb4` and closed issue #528, instead of inheriting stale CLAUDE.md status.

## Checklist coverage

Sections 1–16: store/replay/concurrency/failure semantics reviewed; local-only data and privacy boundaries explicit; no cloud authentication or new API server; executable packaging/setup gaps recorded; dedup and separate cursors covered; no new daemon; real-component smoke precedes multi-day observation; scope excludes broad document decomposition.

Sections 17–21: source owners and existing parser/install/harvest/view seams inspected; new paths labeled; M1/AP/CL/PROD/Observatory conflicts mapped; exhaustive downstream inventory retained as execution-readiness work rather than claimed complete.

Sections 22–27: numeric step headings and required fields present; operator steps only observe prepared artifacts; no conditional predicates; deep code-review lanes do not need runtime URL flags; live native acceptance follows code setup; high-stakes persistence/installation/trial changes retain deep review.

Auto-applied 2 design-document corrections. Four items remain for the executable-plan iteration: B1 and G1–G3. Suitable for operator design review; not ready for repo-sync or build-phase.
