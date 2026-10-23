# NOTE: This is the canonical provider-independent contract. Every provider wrapper must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/research-prospect/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# research-prospect

Scan each active project for research gaps and produce a ready-to-run deep-research menu, grouped by project.

## When to use

- You want high-token tasks to distribute across multiple windows.
- You want to understand what research would most improve each project before starting a deep-work session.
- You need a menu of specific, grounded research questions rather than a brainstorm.

## When NOT to use

- You already know the topic — skip straight to `/deep-research-pinned "<topic>"` (never the built-in `/deep-research`; see § Constraints).
- You want a deep investigation of one specific project — ask for that directly instead.
- MEMORY.md "Active projects" is known to be stale — run `/session-wrap --end` first (only the end-window route runs the full memory pass; bare invocation may route `continue` and touch nothing).

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--projects <list>` | no | all active projects from MEMORY.md | Comma-separated project names or directory paths. Example: `--projects Alpha4Gate,toybox` |
| `--session-wrap` | no | off | After rendering the menu, park each rendered topic in this session's task-state file § Parked (Step 4), then invoke bare `/session-wrap` (triage decides the route). |

## Placeholders

- `<workspace>` — the coding-root directory the invoking session was opened in; its child directories are the projects.
- `<workspace-memory>` — the host's project-memory directory for `<workspace>` (on Claude, the auto-memory directory that holds `MEMORY.md`; other hosts use their own project-memory convention). Never invent one: if it or its `MEMORY.md` is absent, the memory is empty.
- `<CURRENT_PLAN>` — the resolved authoritative current plan for one project, or the literal `none`. Resolve an explicit plan pointer in that project's `CLAUDE.md` or `AGENTS.md` first. With no explicit pointer, use the first existing path in the workspace convention: `docs/plans/master_plan.md`, then the supported legacy locations `plan.md`, `master_plan.md`, `plans/master_plan.md`, `docs/master_plan.md`, or `documentation/master_plan.md`. An explicit pointer that does not resolve is `none`, not permission to choose a different plan silently.
- `<PROJECT_MEMORY>` — per project, the host's project-memory directory for a session opened at `<PROJECT_DIR>`, keyed to that directory the same way `<workspace-memory>` is keyed to `<workspace>`. It is the project's own memory, not the workspace's. Never invent one: when none exists on disk, fill the literal `none`.
- Resolve each to an absolute path before Step 2 (`<CURRENT_PLAN>` and `<PROJECT_MEMORY>` may instead be the literal `none`) and substitute them into the agent prompts per project. When `<PROJECT_MEMORY>` is `none`, replace the whole `<PROJECT_MEMORY>/MEMORY.md` path in item 5 with `none`, so the arm is handed no path for it.

## Writes and re-runs

- Steps 1–3 are read-only: the orchestrator and the agents read files and run read-only `git log`. Nothing is written, committed or launched.
- Step 4 (only with `--session-wrap`) is the only write: it appends to this session's task-state file § Parked (refreshing only its Session SHA and Last written lines) and regenerates the derived rollup. This skill never commits, pushes or starts research; any git verb belongs to `/session-wrap`.
- Re-running is safe: Steps 1–3 recompute the menu, and Step 4 skips a Parked line that is already present verbatim.

---

## Steps

### Step 1: Resolve project list

**If `--projects` was provided:** parse it as a comma-separated list. Each item is either a project name (look up under `<workspace>/<name>/`) or an absolute path.

**If `--projects` was not provided:** read `MEMORY.md` from `<workspace-memory>/MEMORY.md`. Locate the "Active projects" section. Extract every project name listed there. For each, derive its directory: check `<workspace>/<name>/` (case-insensitive). Capture the one-line MEMORY.md entry for each project — this feeds the agent as background context. A missing `MEMORY.md` or "Active projects" section yields an empty list.

Warn and skip any project whose directory cannot be resolved; it joins the `Skipped` line with reason `directory not resolved`. Do not halt. For every resolved project, also resolve its `<CURRENT_PLAN>` and `<PROJECT_MEMORY>` (§ Placeholders). Read only enough of `CLAUDE.md` / `AGENTS.md` to identify an explicit plan pointer at this stage; the arm reads the plan's relevant current sections.

Emit one line before Step 2: `Scanning N projects: <names>.` When the list is empty, emit `Scanning 0 projects: none.`, dispatch nothing, and go to Step 3's empty state.

---

### Step 2: Fan out parallel Explore agents

Dispatch **all agents in a single parallel message** — one Explore agent per project, each with explicit `model: sonnet` (fan-out arms never inherit an escalated session — model-tiering.md § Default: Opus 4.8 + Sonnet fan-out). Do not wait for one to finish before dispatching others. Parallel dispatch is the primary throughput gain of this skill; sequential dispatch is a defect.

Each agent receives the following prompt (fill in the bracketed fields):

```
Investigate <PROJECT_NAME> at <PROJECT_DIR> to identify 2-3 specific /deep-research topics that would meaningfully improve the project.

Background from workspace memory: <MEMORY_LINE — the one-line MEMORY.md entry, or "not in memory" if absent>

Read in this order (stop when you have enough context — EXCEPT items 2 and 5, which are never skippable for a returned topic):
1. <PROJECT_DIR>/CLAUDE.md or AGENTS.md — stack, commands, known gotchas
2. <CURRENT_PLAN> — authoritative current plan resolved by the parent. If it is `none`, you may inspect other sources but must return no research topic because pending decision status cannot be established. Otherwise read the opening current-status area and heading inventory, then only the sections relevant to candidate decisions. Do not read unrelated historical journals. A topic may be returned only when this plan shows its target decision is currently pending and not frozen, completed, withdrawn, superseded, or pre-registered against change.
3. git -C "<PROJECT_DIR>" log --oneline -15 — recent work
4. Any open investigation docs under <PROJECT_DIR>/documentation/investigations/
5. <PROJECT_MEMORY>/MEMORY.md (if it exists; a bare `none` in place of this path means this project has no memory, so there is nothing to read), plus any topic files it links that touch your candidate topics — this is the project's internal empirical evidence. A topic that ignores it risks re-purchasing research the project already paid for in production data. This feeds the "already_known" field below; do not skip it.

Focus on: algorithmic gaps, known plateaus, open architectural questions, techniques the plan defers to "future phases", quality or accuracy limitations surfaced in UAT, or infrastructure decisions where research would inform a go/no-go gate.

Return ONLY a JSON object (no prose before or after it):

{
  "project": "<PROJECT_NAME>",
  "current_state": "<one sentence: what is built and where it is stuck>",
  "research_topics": [
    {
      "title": "<research question phrased as a /deep-research argument — 12-25 words, specific and searchable>",
      "why": "<1-2 sentences citing a specific gap in the codebase, plan, or recent git history>",
      "informs": "<the pending decision this research would change, and when that decision fires (e.g. 'critic model pick — v6 bake-off, after re-soak')>",
      "decision_evidence": "<CURRENT_PLAN> plus a heading or line locator proving the decision is currently pending",
      "already_known": "<what internal evidence already covers part of this topic, with a file/heading locator — or 'none found after the required project-memory check'>",
      "depth": "high|medium"
    }
  ]
}

Rules:
- Return 2 topics minimum and 3 maximum only when that many qualify. When no candidate has authoritative pending-decision evidence, return an empty `research_topics` array and a one-line `reason`; never pad the array.
- Titles must work as /deep-research arguments: specific, concrete, not generic phrases like "improve performance" or "better algorithms."
- "why" must cite something observed in the code, plan doc, or git log — not general best-practices reasoning.
- Narrow every title to the OPEN sub-questions: if memory/investigations already answer part of the topic empirically, the title must target only what remains unknown, and "already_known" must state what is already covered. A title that re-asks a question the project answered in production is a defect.
- "informs" must name a real pending decision. `decision_evidence` must point into `<CURRENT_PLAN>` at the current status or decision text that proves it. Reject topics whose status cannot be established from the authoritative current plan, whose target decision is pre-registered or frozen (research cannot change those by design), and topics that inform no decision at all.
- "depth" is a scope recommendation: "high" = warrants the full /deep-research harness (5 angles, ~100 agents); "medium" = a narrow 1-3 agent in-session skim is the right spend.
- If the directory does not exist or has no readable files, return: {"project": "<name>", "error": "directory not found or empty"}.
- Stay read-only: never create, edit or delete a file, and run no state-changing command (item 3's git log is your only git command).
```

Collect all results. Projects that return `"error"` are logged under a `Skipped` line in the output but do not halt rendering. Before accepting a topic, the parent reads the bounded plan excerpt named by `decision_evidence` and confirms that it belongs to the resolved `<CURRENT_PLAN>` and still describes the named decision as pending and changeable. A missing, stale, mismatched, or inaccessible locator drops the topic. This check is read-only and bounded to the cited heading/lines; do not rescan the whole plan.

---

### Step 3: Render the menu

Apply the render-time rules in § Constraints first. For each project with at least one surviving topic, render a group. The command form is chosen by the topic's `depth` field — `high` gets the full harness, `medium` gets a narrow in-session skim (do NOT render every topic as a full-harness command; the depth field is the scope recommendation):

```
## <PROJECT_NAME> — <current_state>
Resolved path: <PROJECT_DIR>

  X1: /deep-research-pinned "Project: <PROJECT_NAME>. Resolved path: <PROJECT_DIR>. Open question: <title>. Pending decision: <informs>. Decision evidence: <decision_evidence>. Read existing evidence first: <already_known>."                           [full harness — ~100 agents, multi-M subagent tokens]
      Why: <why>
      Informs: <informs>
      Decision evidence: <decision_evidence>
      Already known: <already_known>

  X2: Research narrowly (1-3 agents max, no deep-research harness): Project: <PROJECT_NAME>. Resolved path: <PROJECT_DIR>. Open question: <title>. Pending decision: <informs>. Decision evidence: <decision_evidence>. Read existing evidence first: <already_known>.    [narrow — ~1/5 the cost]
      Why: <why>
      Informs: <informs>
      Decision evidence: <decision_evidence>
      Already known: <already_known>
```

Where `X` is a single-letter prefix: first letter of the first word of the project name, uppercased. If two projects share the same letter, use a two-letter prefix for the second (e.g., `VO` for void_furnace if `VF` was already used).

A project whose topics were all dropped joins the `Skipped` line with reason `all topics dropped`. A project with one surviving topic renders that topic; never pad or invent topics to reach the agent minimum.

After all groups, emit `Skipped: <name> (<reason>), ...` when any project was skipped. Then emit one execution-context line and the flat "QUICK COPY" block, preserving each topic's depth-appropriate command form:

```
Run in: fresh window @ <workspace> · Model: Fable 5 for (depth: high) lines — cited-synthesis escalation; Opus (default) for (depth: medium) lines
--- QUICK COPY (one per window) ---
<the exact enriched A1 command line from its project group>                                 (depth: high)
<the exact enriched A2 narrow-research line from its project group>                         (depth: medium)
...
```

Each execution line is a standalone handoff: it keeps the project name, resolved absolute path, open question, pending decision, current-plan evidence locator, and existing-evidence read instruction together. Before embedding JSON field values in a double-quoted high-depth argument, replace any internal double quote with a single quote; do not change the meaning. Step 4 parks this exact QUICK COPY line, so the durable form retains the same scope.

The context line names `<workspace>` because `deep-research-pinned` resolves only from the cwd project's `.claude/workflows/` (model-tiering.md § `/deep-research` dispatch). Its Model clause follows the tier owner, model-tiering.md § Escalate a session to Fable 5: `/deep-research` cited-report synthesis via `deep-research-pinned` is a named session-escalation point, and the pinned workflow keeps its arms on Sonnet, so only scope and synthesis inherit Fable. Narrow lines stay on the Opus default. Name only the depths present: with no high-depth line render `Model: Opus (default)`; with no medium line render only the Fable 5 clause. The escalation stays the operator's per-window choice; this skill only annotates it.

The quick-copy block is **mandatory** regardless of topic count — it lets the user grab a single line per window without stripping the "Why" annotations. **Empty state:** when no topic survives (no project resolved, every project skipped, or every topic dropped), print `No research topics: <reason>.`, omit the context line, and print the block header followed by the single line `(none)`.

---

### Step 4 (only if `--session-wrap` flag passed)

After Step 3 output, in this order:

1. **Guard.** If no topic was rendered, print `Session wrap not invoked: no topics to park.` and stop. If the host supplies no stable session id (`<repo>/_shared/task-state-schema.md` § Session identity), or the park write in item 2 fails, print `Session wrap not invoked: topics not parked (<reason>) - they remain only in the menu above.` and stop. Never write a session file under a guessed id, and never invoke `/session-wrap` with the list unparked: everything it writes or renders derives from the session state file, so an unparked list would be silently dropped.
2. **Park.** Read-merge-write this session's own file, `<git-root>/.claude/task-state/sessions/<session-id>.md` (git root via `git rev-parse --show-toplevel`), under the schema doc's per-session model and field rules. Append one § Parked entry per rendered topic, grouped by project: `- research-prospect <PROJECT_NAME> <ID>: <its QUICK COPY line>`, skipping any entry already present verbatim. Change only § Parked plus the Session SHA and Last written lines; preserve Task, Status, Next Action, Active project and every other section verbatim. If the file is absent, create it per the schema doc's File format and Lifecycle with only `**Task:** research-prospect | parked research menu`, `**Status:** IN_PROGRESS`, Session SHA, Last written and § Parked. Leave Next Action for `/session-wrap`'s own route write, and never write `/session-wrap` itself as Next Action. The shared `current.md` is a derived rollup: never hand-write it.
3. **Regenerate the rollup** with the schema's helper, exactly as `task-handoff --loop` does (task-handoff core § `--loop`). If the helper is unavailable, print one line saying so and continue; the session file already holds the entries.
4. **Invoke bare `/session-wrap`** — it triages and routes. Use `/session-wrap --end` only when the flow explicitly means end-of-day. One-sentence transition max before the skill call — do not emit verdict prose summarizing what was found. `/session-wrap` owns any git verb after its own anomaly pre-flight (its router may commit and push, or delegate to `/repo-update`); this skill commits nothing.

---

## Output format

- Target: 30–90 lines for the full menu (each topic carries Why / Informs / Already known).
- Do not truncate topics to hit a word count. Accuracy over brevity.
- The QUICK COPY block always appears at the end of the menu, even if only one project was scanned, and as `(none)` in the empty state.

---

## Constraints

- **Parallel dispatch required.** All Explore agents in one message. Sequential dispatch is a defect.
- **JSON only from agents.** Agents returning prose instead of JSON are treated as parse failures. Log the project as skipped with a note; do not try to extract topics from prose.
- **"why" must be grounded.** If an agent's "why" reads as generic best-practice advice with no codebase anchor, mark it `(unverified — no specific gap cited)` rather than presenting it as a confirmed finding.
- **"informs" must name a pending decision.** A topic with no decision to change, or one aimed at a pre-registered/frozen gate, is dropped at render time — do not present it even if the agent returned it.
- **Honor the depth field.** `depth` drives the command form (full harness vs narrow skim). Rendering every topic as a full-harness command re-creates the over-spend this field exists to prevent.
- **Pinned harness only.** The full-harness command is `/deep-research-pinned`, never the built-in `/deep-research`, whose arms run on the session model (model-tiering.md § `/deep-research` dispatch). This skill renders the command; it never launches it.
- **Title phrasing discipline.** Reject titles that are generic. A usable title names the technique, the constraint, and the domain: "SPRT early-stopping thresholds for small-n win-rate gates in game-playing bot evolution" not "statistical testing for bot evaluation."
- **No invented projects.** Only scan projects listed in MEMORY.md or explicitly named via `--projects`.

---

## Limitations

- **MEMORY.md must be current.** Projects not listed under "Active projects" are invisible to this skill unless named via `--projects`. If MEMORY.md is stale, run `/session-wrap --end` first (bare invocation may route `continue` without a memory pass).
- **Explore agents read excerpts, not whole files.** On large plan.md files (>2000 lines), agents see early sections first. Open investigations buried deep in the plan may be missed. Use `--projects <name>` with a more focused prompt if a specific project needs deeper coverage.
- **Directory name must match MEMORY.md entry exactly.** If a project is listed as `b2_project_goblin` but the directory is `goblin/`, resolution will fail. Fix MEMORY.md or use `--projects <workspace>/goblin`.
- **Agent JSON format is best-effort.** Explore agents are not constrained-output models. If an agent returns valid JSON with the right keys, use it. If it returns close-enough JSON (minor key differences), parse it gracefully. Only escalate to "skipped" if the output is unparseable.
