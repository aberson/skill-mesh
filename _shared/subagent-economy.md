# Subagent economy — keep the orchestrator window slim

> **Vendored into skill-mesh.** This is a copy of the workspace reference document of the
> same name, vendored into the shared payload (`_shared`) so that the skill cores citing it
> resolve inside a host discovery root rather than against a workspace directory no
> consumer home has.
> Two adaptations apply throughout: citations to workspace documents that are **not** part
> of this payload are rendered as plain names rather than links (their targets do not ship
> here), and operator-specific identifiers, private issue/cron references and
> harness-configuration paths have been removed. The per-file sign-off and the full list of
> link dispositions are recorded in this repository's Step 66 decision record.

The dominant token cost in this workspace is **resident orchestrator context**, not subagent fan-out. A heavy `/build-phase` window rides one session for hundreds to thousands of turns and pins near its context ceiling; **the large majority of a long window's token cost is incurred at high context**. Two leaks dominate such a window: `tool_result` is the largest single share of it, split about evenly between **`Agent` returns (sub-agents returning whole reports instead of a verdict)** and **`Read` (orchestrators reading files inline a sub-agent should read)**. Both are resident *forever* once they land. Two disciplines fix it, at zero independence/correctness cost.

## Rule 1 — Subagent returns are a terse verdict; detail goes to a file

When an orchestrator/review skill spawns a sub-agent (Agent tool, Workflow `agent()`, or a `/build-step` dev/reviewer), the sub-agent's prompt MUST instruct it to:

- **Return only the load-bearing verdict** — a PASS/BLOCKED/verdict line, counts, and at most the single most important finding. Target a handful of lines, not paragraphs.
- **Write any longer detail to a file** (e.g. `<worktree>/.build-step/<role>-report.md`, a findings `.json`, an investigation doc) and return only its path. The orchestrator reads that file **only when the verdict requires it** (e.g. on BLOCKED/NEEDS-WORK, to feed findings back to the developer) — not eagerly.

The harness already states "the agent's final message IS the tool result — relay what matters"; this rule is the skills honoring it. A whole-report return that the orchestrator skims once and then carries resident for the rest of a long session is the exact anti-pattern.

Structured-output sub-agents (Workflow `schema:`) are exempt from the prose-trim but should still keep array payloads bounded — return findings as `{severity, title, file:line, fix}` rows, not full re-quoted file bodies.

## Rule 2 — Orchestrators delegate reads; they hold conclusions, not file dumps

An orchestrator should not `Read` a file inline to answer a question a sub-agent is already positioned to answer. Push the read into the sub-agent (which returns the conclusion per Rule 1) and keep only the conclusion resident. Reserve orchestrator-side `Read` for small, decision-critical files it must act on directly (the plan step it's executing, `current.md`, a config it's about to edit) — not for surveying source, scanning diffs a reviewer will scan, or re-reading what a sub-agent reported.

## Scope

Applies to every skill that spawns sub-agents and rides a long window: `build-phase`, `build-step`, `build-queue`, `skill-iterate`, `skill-evolve`, `review-deep`, `review-gauntlet`, `deep-research`, and the `user-*` fan-out skills. Highest leverage is `build-phase`/`build-step` (the heaviest sessions). Point-of-action enforcement lives in each skill's spawn templates; this file is the single source of the discipline.

## Not in scope (do not over-correct)

- Do NOT trim a return so far that the orchestrator must re-spawn to recover a needed fact — the verdict must carry everything the next decision needs.
- Do NOT collapse independent reviewer findings into one summary before the gate — independence is bought with context isolation (see `code-quality.md` and judge-core); file-backing preserves the full findings, it does not merge them.

## Source

Two workspace token-usage investigations (2026-06-22), which measured the
high-context cost share and identified the two leaks. Neither is vendored here.
