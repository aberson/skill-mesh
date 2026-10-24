# goblin's "second brain" (and why goblin-suggest / goblin-do need an external runtime)

`/goblin-suggest` and `/goblin-do` publish their full behavior contracts here, but their
Goblin runtime and atom store are **not** part of this repo. A run therefore depends on:

1. **A per-project "second brain" — an atom store.** goblin persists its ranked improvement
   ideas, UAT tasks, and obligations as markdown+YAML files under `brain/suggestions/`. That
   store holds the operator's real, project-specific notes, so it is **omitted for privacy**.
   `goblin-suggest` is the producer, although its current `--small`, `--big`, and `--uat`
   write paths are held by its safety contract. `goblin-do` reads an existing atom and
   renders what the operator may run next; it never acts on the atom itself.
2. **The `goblin` CLI.** The pipeline itself (grounding, candidate generation, the parallel
   LLM-judge rubric, ranking, persistence seams, and deterministic atom renderer) lives in a
   separate project that exposes a `goblin` console script (`goblin suggest`, `goblin do`)
   plus Workflow bridges. That project is **not published here**. The Skill Mesh cores state
   the current integration contract, including the held suggestion paths and the renderer's
   read-only boundary.

Everything below is what you need to **build your own second brain** so the two skills'
design is reproducible in your own workspace.

## What an "atom" is

One idea = one file. Dateless `id` (the filename stem) so a re-run **updates in place**
instead of creating dated duplicates. Two kinds share the `brain/suggestions/` directory and
never collide, because their filename prefixes differ (`sugg-` vs `uat-`).

### Suggestion atom — `brain/suggestions/sugg-<project>-<slug>.md`

Contracted output of `/goblin-suggest --small` (additive quick wins) or `--big` (larger
ideas). Those write paths are currently held; existing atoms retain this shape.

```yaml
---
id: sugg-<project>-<slug>
type: suggestion
mode: small          # small | big
status: proposed     # proposed | accepted | declined; goblin-do does not change it
project: <project>
title: <short title>
anchor: <a REAL artifact>     # tracked file path | issue #N — other shapes are refused by goblin-do
scores:                        # 4-axis rubric, each 1-5, the median over N judge runs
  feasibility: 4
  fit: 4
  leverage: 3
  reversibility: 5
composite: 4.0                 # mean of the four axis-medians (drives the ranking)
provenance: []                 # source provenance; goblin-do does not append to it
---
<the suggestion body: what to change and why, grounded in `anchor`>
```

### UAT atom — `brain/suggestions/uat-<project>-<slug>.md`

Contracted output of `/goblin-suggest --uat` (triage of operator-asks for AI takeover).
That path is currently held. A UAT atom carries **no `scores`** — the triage fields *are*
the score.

```yaml
---
id: uat-<project>-<slug>
type: uat
mode: uat
status: proposed
project: <project>
description: <the operator-ask this task covers>
anchor: <where the ask came from: a plan M-step, a `Type: operator` step, a handoff cue>
ai_doable: true                # can an AI do this end-to-end, no human?
clarifying_question: none      # none | one | many (the consensus ordinal) — or the single Q to start
human_residual_steps: []       # what a human must still do; empty => fully AI-doable
---
<task detail>
```

## Minimal DIY setup

1. Make the store: a git-tracked `brain/suggestions/` directory (a `brain/SCHEMA.md`
   documenting the frontmatter above is optional but recommended — goblin keeps its schema
   there as the one source of truth).
2. Write the pipeline the skill cores describe: **ground** (read the target project's
   CLAUDE.md + plan + open issues, enveloped as untrusted data), **generate** anchored
   candidates via one model call, **grade** each with N parallel judge calls (drop any with
   fewer than N valid verdicts — the partial-verdict guard), **rank** by `composite`, and
   **persist** one atom per survivor (atomic write, update-not-duplicate). Keep persistence
   held until both the engine write boundary and the Workflow relay boundaries satisfy the
   repairs and independent reviews required by the `goblin-suggest` core.
3. Implement `goblin do` as a read-only renderer: resolve one persisted atom, recheck its
   anchor, then print either its copy-pasteable `/goal` block or the seed for its kind. Do not
   execute work, dispatch `/build-step`, create branches, merge, push, or edit atom state.

The two skill cores spell out the held producer modes, renderer rule, refusals, and output
formats in full.
