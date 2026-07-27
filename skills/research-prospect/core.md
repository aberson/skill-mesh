# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/research-prospect/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# research-prospect

Scan each active project for research gaps and produce a ready-to-run `/deep-research` menu, grouped by project.

## When to use

- You want high-token tasks to distribute across multiple windows.
- You want to understand what research would most improve each project before starting a deep-work session.
- You need a menu of specific, grounded research questions rather than a brainstorm.

## When NOT to use

- You already know the topic — skip straight to `/deep-research "<topic>"`.
- You want a deep investigation of one specific project — ask for that directly instead.
- MEMORY.md "Active projects" is known to be stale — run `/session-wrap --end` first (only the end-window route runs the full memory pass; bare invocation may route `continue` and touch nothing).

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--projects <list>` | no | all active projects from MEMORY.md | Comma-separated project names or directory paths. Example: `--projects Alpha4Gate,toybox` |
| `--session-wrap` | no | off | After rendering the menu, park the topic list in `current.md § Parked`, then invoke bare `/session-wrap` (triage decides the route). |

---

## Steps

### Step 1: Resolve project list

**If `--projects` was provided:** parse it as a comma-separated list. Each item is either a project name (look up under `<workspace>/<name>/`) or an absolute path.

**If `--projects` was not provided:** read `MEMORY.md` from `<workspace-memory>/MEMORY.md`. Locate the "Active projects" section. Extract every project name listed there. For each, derive its directory: check `<workspace>/<name>/` (case-insensitive). Capture the one-line MEMORY.md entry for each project — this feeds the agent as background context.

Warn and skip any project whose directory cannot be resolved. Do not halt.

Emit one line before Step 2: `Scanning N projects: <names>.`

---

### Step 2: Fan out parallel Explore agents

Dispatch **all agents in a single parallel message** — one Explore agent per project, each with explicit `model: sonnet` (fan-out arms never inherit an escalated session — tier policy, CLAUDE.md model paragraph). Do not wait for one to finish before dispatching others. Parallel dispatch is the primary throughput gain of this skill; sequential dispatch is a defect.

Each agent receives the following prompt (fill in the bracketed fields):

```
Investigate <PROJECT_NAME> at <PROJECT_DIR> to identify 2-3 specific /deep-research topics that would meaningfully improve the project.

Background from workspace memory: <MEMORY_LINE — the one-line MEMORY.md entry, or "not in memory" if absent>

Read in this order (stop when you have enough context — EXCEPT item 5, which is never skippable):
1. <PROJECT_DIR>/CLAUDE.md — stack, commands, known gotchas
2. <PROJECT_DIR>/documentation/master_plan.md or plan.md — current phase/step status
3. git -C "<PROJECT_DIR>" log --oneline -15 — recent work
4. Any open investigation docs under <PROJECT_DIR>/documentation/investigations/
5. <workspace-memory>/MEMORY.md (if it exists), plus any topic files it links that touch your candidate topics — this is the project's internal empirical evidence. A topic that ignores it risks re-purchasing research the project already paid for in production data. This feeds the "already_known" field below; do not skip it.

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
      "already_known": "<what internal evidence (memory topic files, investigations, retros) already covers part of this topic — or 'none found'>",
      "depth": "high|medium"
    }
  ]
}

Rules:
- 2 topics minimum, 3 maximum.
- Titles must work as /deep-research arguments: specific, concrete, not generic phrases like "improve performance" or "better algorithms."
- "why" must cite something observed in the code, plan doc, or git log — not general best-practices reasoning.
- Narrow every title to the OPEN sub-questions: if memory/investigations already answer part of the topic empirically, the title must target only what remains unknown, and "already_known" must state what is already covered. A title that re-asks a question the project answered in production is a defect.
- "informs" must name a real pending decision. Reject topics whose target decision is pre-registered or frozen (research cannot change those by design) and topics that inform no decision at all.
- "depth" is a scope recommendation: "high" = warrants the full /deep-research harness (5 angles, ~100 agents); "medium" = a narrow 1-3 agent in-session skim is the right spend.
- If the directory does not exist or has no readable files, return: {"project": "<name>", "error": "directory not found or empty"}.
```

Collect all results. Projects that return `"error"` are logged under a `Skipped` line in the output but do not halt rendering.

---

### Step 3: Render the menu

For each project with valid results, render a group. The command form is chosen by the topic's `depth` field — `high` gets the full harness, `medium` gets a narrow in-session skim (do NOT render every topic as a full `/deep-research`; the depth field is the scope recommendation):

```
## <PROJECT_NAME> — <current_state>

  X1: /deep-research "<title>"                                  [full harness — ~100 agents, multi-M subagent tokens]
      Why: <why>
      Informs: <informs>
      Already known: <already_known>

  X2: Research narrowly (1-3 agents max, no deep-research harness): <title>    [narrow — ~1/5 the cost]
      Why: <why>
      Informs: <informs>
      Already known: <already_known>
```

Where `X` is a single-letter prefix: first letter of the first word of the project name, uppercased. If two projects share the same letter, use a two-letter prefix for the second (e.g., `VO` for void_furnace if `VF` was already used).

After all groups, emit a flat "QUICK COPY" block, preserving each topic's depth-appropriate command form:

```
--- QUICK COPY (one per window) ---
/deep-research "<A1 title>"                                        (depth: high)
Research narrowly (1-3 agents max, no deep-research harness): <A2 title>   (depth: medium)
...
```

The quick-copy block is **mandatory** regardless of topic count — it lets the user grab a single line per window without stripping the "Why" annotations.

---

### Step 4 (only if `--session-wrap` flag passed)

After Step 3 output, FIRST write the topic list into `current.md § Parked` (read-merge-write per `.claude/references/task-state-schema.md`) — one pointer-style entry per topic (`/deep-research "<title>"`, grouped by project), or one entry pointing at the menu file if it was saved to disk. THEN invoke bare `/session-wrap` — it triages and routes; everything it writes or renders derives from `current.md`, so an unparked topic list would be silently dropped. Use `/session-wrap --end` only when the flow explicitly means end-of-day. One-sentence transition max before the skill call — do not emit verdict prose summarizing what was found.

---

## Output format

- Target: 30–90 lines for the full menu (each topic carries Why / Informs / Already known).
- Do not truncate topics to hit a word count. Accuracy over brevity.
- The QUICK COPY block always appears at the end, even if only one project was scanned.

---

## Constraints

- **Parallel dispatch required.** All Explore agents in one message. Sequential dispatch is a defect.
- **JSON only from agents.** Agents returning prose instead of JSON are treated as parse failures. Log the project as skipped with a note; do not try to extract topics from prose.
- **"why" must be grounded.** If an agent's "why" reads as generic best-practice advice with no codebase anchor, mark it `(unverified — no specific gap cited)` rather than presenting it as a confirmed finding.
- **"informs" must name a pending decision.** A topic with no decision to change, or one aimed at a pre-registered/frozen gate, is dropped at render time — do not present it even if the agent returned it.
- **Honor the depth field.** `depth` drives the command form (full harness vs narrow skim). Rendering every topic as a full `/deep-research` re-creates the over-spend this field exists to prevent.
- **Title phrasing discipline.** Reject titles that are generic. A usable title names the technique, the constraint, and the domain: "SPRT early-stopping thresholds for small-n win-rate gates in game-playing bot evolution" not "statistical testing for bot evaluation."
- **No invented projects.** Only scan projects listed in MEMORY.md or explicitly named via `--projects`.

---

## Limitations

- **MEMORY.md must be current.** Projects not listed under "Active projects" are invisible to this skill unless named via `--projects`. If MEMORY.md is stale, run `/session-wrap --end` first (bare invocation may route `continue` without a memory pass).
- **Explore agents read excerpts, not whole files.** On large plan.md files (>2000 lines), agents see early sections first. Open investigations buried deep in the plan may be missed. Use `--projects <name>` with a more focused prompt if a specific project needs deeper coverage.
- **Directory name must match MEMORY.md entry exactly.** If a project is listed as `b2_project_goblin` but the directory is `goblin/`, resolution will fail. Fix MEMORY.md or use `--projects <workspace>/goblin`.
- **Agent JSON format is best-effort.** Explore agents are not constrained-output models. If an agent returns valid JSON with the right keys, use it. If it returns close-enough JSON (minor key differences), parse it gracefully. Only escalate to "skipped" if the output is unparseable.
