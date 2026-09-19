# Investigation: six workflow suggestions

Investigated 2026-09-18 against Skill Mesh `a339620` and coding-root `3e2ee5e`. Recommendations are design judgments, not measured improvements. [Controlling plan, publication 2](../context-learning-plan.md).

**Scope update, 2026-09-19:** the original recommendations below are retained as research, not a build sequence. Publication 2 adopts explicit capture/harvest first, reuses M1 resume work, qualifies one evaluator, separates development packaging, and defers checkpoint journals/section history and Observatory visibility. The disposition under each heading overrides its original implementation timing.

## 1. Pyproject.toml for skill entry points and dependencies

**Current disposition:** Project 4, independent development maintenance. Start with existing scripts/dependencies; a new context runtime package is not required.

**Finding: adopt for executable Python assets, not for every Markdown skill.**

Skill Mesh's [project instructions](../../CLAUDE.md) explicitly say its Python interpreter and dependencies are supplied externally. Root inventory confirmed no pyproject or lockfile. Its canonical inventory is [skill-manifest.json](../../config/skill-manifest.json), and the builder emits host-discoverable Markdown. Replacing that inventory with Python entry points would conflate host skill discovery with executable invocation.

The closest successful local precedent is [Dev Observatory's pyproject](../../../dev-observatory/pyproject.toml): declared dependencies, a build backend, `observatory = dev_observatory.cli:main`, and a committed lock. A pyproject declares requirements and entry points; the lock captures resolution, while Python and non-Python prerequisites need separate treatment. The official [uv configuration documentation](https://docs.astral.sh/uv/concepts/projects/config/) requires a build system for entry-point tables; [locking documentation](https://docs.astral.sh/uv/concepts/projects/sync/) distinguishes a checked lock from an unchecked frozen lock.

Start with the new context helper and real development dependency inventory. A project per prose skill would add locks and environments without an executable boundary. Separate projects only when dependencies, Python versions or release lifecycles actually diverge. Do not create a uv workspace linking unrelated utilities: it would couple their environments and revival of Phase PROD is not authorized.

**Proof needed:** clean environment, preserved pytest collection, locked execution, explicit environment repair, install without the authoring checkout, and unchanged existing full-gate meaning. A dependency lock alone is not proof of reproducible model output or Windows shell tooling.

## 2. Shell script invoking uv in the right environment

**Current disposition:** Project 4's thin PowerShell development launcher. Installed runtime packaging and hook provisioning are deferred until a concrete requirement exists.

**Finding: adopt a thin PowerShell wrapper now; a Bash-only wrapper is a poor fit here.**

The repository targets Windows PowerShell 5.1. Installed skills can execute while the current directory points at another project or worktree. Resolve code from the launcher location and target data from an explicit repository argument. uv's project selection does not establish the correct working directory for every tool; Observatory's pytest instructions document the concrete failure.

Use `--locked` to catch metadata/lock drift. Provision at install or explicit setup, not on a latency-sensitive compaction event. Hooks use an already provisioned offline environment and a bounded timeout. Preserve stdout for the host protocol, send diagnostics to bounded local receipts, and propagate exit codes from user-invoked CLI commands. Hook adapters separately convert collector failure into a nonblocking host response.

Packaging is consequential: [build-distributions.ps1](../../tools/build-distributions.ps1) currently rejects shared asset extensions it cannot stamp; [the lifecycle guide](../skill-catalog-lifecycle.md) requires a resource plan for support-asset topology changes. Copying a pyproject into an installed skill by hand would bypass both ownership and release verification.

**Proof needed:** spaces, wrong cwd, nested checkout, missing uv, missing environment, source checkout removed, lock mismatch, interrupted provisioning and child failure. A virtual environment isolates dependencies; it is not a security sandbox for candidate execution.

## 3. Hooks for append-only context management with tombstones

**Current disposition:** reuse M1 checkpoint work and separately assess residual default-hook identity behavior. A new context journal is deferred; it is not a capture/harvest prerequisite.

**Finding: extend existing continuity, beginning with identity correctness.**

Current [wiring](../../../.claude/settings.json) invokes [pre-compact](../../../.claude/hooks/pre-compact.ps1), [session-resume](../../../.claude/hooks/session-resume.ps1) and Stop advisories. [task-state-derive.ps1](../../../.claude/hooks/lib/task-state-derive.ps1) writes an atomic rollup but its resolver falls back to the freshest other session. [task-handoff](../../skills/task-handoff/core.md) writes current Markdown state with append/overwrite field rules. Existing “append” operations do not constitute an event-sourced checkpoint history.

Use a per-session journal of transactions, including section version retirement. Generate compatibility Markdown and bounded resume text from the active versions. Tombstones preserve the reason a fact stopped being current; they cannot remove bytes already sent to a model, guarantee prompt caching, or recover state the model never checkpointed.

Both hosts now document relevant lifecycle events: [Claude hooks](https://code.claude.com/docs/en/hooks) and [Codex hooks](https://learn.chatgpt.com/docs/hooks). Their wire behavior and installation/trust requirements differ. Local Codex 0.147.0 and uv 0.10.9 were observed; the proposed hooks were not activated. Native behavior remains a live-qualification gate.

**Proof needed:** missing own checkpoint with a valid foreign checkpoint; concurrent callbacks; duplicate event delivery; interrupted append; stale Git anchors; manual checkpoint with unavailable hooks; bounded resume; reversible cutover. Keep observer failure from blocking user work, while making failure visible in health evidence.

## 4. Diff and tombstone Markdown sections individually

**Current disposition:** Project 5a only after correct checkpoint selection still loses a demonstrated correction/history fact. No universal parser/store or migration in the first slice.

**Finding: useful for checkpoint projections; defer general document decomposition.**

Existing context and skills are already Markdown with sections. The missing capability is stable section identity and replay semantics. Heading text is insufficient: headings can repeat, be renamed or move. Line numbers drift. A line beginning with hashes inside a code fence is not a heading.

Assign stable IDs and parse CommonMark. Skill Mesh already adopted `markdown-it-py` for document-contract tests after hand-rolled parsing failures, recorded in [CLAUDE.md](../../CLAUDE.md). Adding it as a runtime dependency is a deliberate new use, not a claim it is already installed everywhere.

Diff per section with conservative newline/BOM normalization. Store old-version tombstone and replacement together. Track document ordering separately from identity; renaming/reordering should not retire unrelated sections. Duplicate or ambiguous IDs require reconciliation. Retain a whole-document source identity so the recorded projection can be traced to the checkpoint that produced it.

Restrict the pilot to task state and explicit decisions. [The product charter](../product-charter.md) excludes full multi-file skill decomposition from recovery. Do not turn this suggestion into a universal Markdown database or rewrite accepted canonical plans into event logs.

**Proof needed:** repeated headings, fenced examples, setext headings, nested sections, deletion, rename, reorder, newline variants and reverting to a previously seen hash. Measure correct active-state rendering; do not promise reduced tokens from fewer disk bytes.

## 5. Mistake markers in model output

**Current disposition:** Project 2 uses explicit recording at recognition time. Prose-only marker discipline remains; transcript parsing/collector automation is deferred, so its larger negative-fixture matrix is not a prerequisite for first delivery.

**Finding: adopt as a source-qualified self-report channel, with a deterministic recording fallback.**

The proposed sentinel belongs only in a dedicated assistant commentary paragraph. Exclude code and deliverables by both instruction and collector validation; wording alone cannot guarantee compliance. Parse message roles/channels and Markdown blocks. A literal marker copied from user text, a file or a tool result is not an admission by the assistant.

The payload should preserve the observation and evidence, without prematurely deciding the root cause. A tool failing because the environment is unavailable differs from the model violating a known instruction. Unknowns remain unknown. Record source identity so repeated hooks do not duplicate the event.

Stop hooks are an incomplete collection point for commentary. Both official host hook references expose a latest assistant message, while detailed transcript availability is host/version dependent. Explicit structured capture at recognition time is the reliable pilot path; transcript collection is enabled only after qualification. Strict JSON/code-only outputs must remain valid; do not append a marker to satisfy the protocol.

No existing dedicated marker protocol was found in the scoped Skill Mesh runtime/tools and learning-skill searches. There are already regression signals in lesson-harvest; supplement those rather than claiming markers replace review, tests, or user feedback.

**Proof needed:** a real admission, quoted marker, marker in fence/inline code/HTML/tool output, omitted marker despite an injected error, duplicate delivery, and unavailable commentary capture. Low marker counts are not evidence of high quality.

## 6. Periodic categorization and skill updates

**Current disposition:** Project 2 extends existing harvest at unchanged HEAD. Project 3 separately qualifies an independent trial route; Codex's current adapter maps no scoring-workflow primitive. No fixed weekly cadence, observation quota or mandatory winning result.

**Finding: reuse harvest and evolution, adding canonical isolated trials before review.**

[Lesson-harvest](../../skills/lesson-harvest/core.md) already scans Git/run logs, deduplicates against five stores and drafts candidates. It currently stops if its Git cursor equals HEAD; mistake events need an independent cursor so an unchanged commit does not suppress new observations. [Afterparty](../../skills/user-afterparty/core.md) invokes a dry-run and its [queued effectiveness plan](../user-afterparty-effectiveness-plan.md) owns carry-forward and attribution.

[Skill-evolve](../../skills/skill-evolve/core.md) already calls for distinct producers and graders, but its target is the legacy installed skill. [Phase CL](../skill-catalog-lifecycle-plan.md) explicitly identifies that unsafe seam. New trials must author canonical sources, use generated distributions and disposable host homes, and respect the lifecycle guide even before the CRUD front door is complete.

Following the operator's preference, automatically try one evidence-backed candidate in isolation at a learning-enabled boundary. Compare with baseline on the originating failure and unrelated holdouts; retain loser/inconclusive evidence. A bounded event-driven cadence suits the existing system better than a new always-on watcher. A weekly manual catch-up can use the same command.

**Proof needed:** no-new-Git/new-marker case, already-codified case, false admission, wrong proposed remedy, unavailable grader, holdout regression and an actual candidate review outcome. No automatic live mutation. A successful small trial supports that candidate on those cases, not a general claim that the skill has improved.

## Investigation limits

Read-only code/doc/Git/GitHub investigation plus official documentation lookup. No dependency installation, native hook activation, simulated savings benchmark, skill mutation, model experiment or full test run was performed. Current issue states were read directly; execution status can still change after this snapshot. Token cost, future error reduction and hook latency remain unmeasured.
