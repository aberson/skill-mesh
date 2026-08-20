# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/goblin-sweep/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# goblin-sweep

Present the discovered **obligation atoms** for one workspace project and route the operator to
`/goblin-do <obl-id>`. An obligation atom (`obl-<project>-<slug>`) is discovered *existing work* —
a plan step, an open issue, a TODO marker, or an operator-ask that the project has already
committed to — not a generated suggestion. `/goblin-suggest` invents ranked *new* ideas;
`/goblin-sweep` surfaces obligations the project already owes.

**This skill is a thin wrapper.** It shells the installed Goblin CLI's deterministic `goblin sweep`
subcommand, parses that command's `--json` output, and renders a fixed report. It contains **NO**
obligation-extraction, deduplication, atom-parsing, source-scanning, or generation logic — all of
that lives in the engine (`b2_project_goblin`). If the engine is not installed, this skill fails
loudly rather than fabricating an empty backlog (see **Prerequisites**).

Throughout this contract, `<workspace-root>` means the operator's coding-root workspace directory —
the parent of the project directories, resolved at run time. It is never a literal path in this
file.

## Prerequisites (fail-loud, checked in order)

Run these three checks **in order** before invoking the engine. On the FIRST failure, STOP loudly
and name the engine plan `b2_project_goblin/documentation/goblin-sweep-plan.md` as the remediation
(the engine ships the `goblin sweep` subcommand; this skill only consumes it). Never continue past a
failed check, and never emit an empty or fabricated backlog in place of a real run.

1. **`uv` is on PATH.** The invocation shells `uv`. Check it resolves:

   ```powershell
   Get-Command uv
   ```

   If `uv` is missing → STOP: `goblin-sweep: prerequisite failed — 'uv' is not on PATH. The goblin sweep engine runs via 'uv run'; install uv and run 'uv sync' in the engine project. Remediation: b2_project_goblin/documentation/goblin-sweep-plan.md.`

2. **The engine project directory exists.** The pinned invocation targets it by absolute path,
   resolved from the workspace root:

   ```powershell
   Test-Path (Join-Path $workspaceRoot 'b2_project_goblin')
   ```

   If it does not exist → STOP: `goblin-sweep: prerequisite failed — the engine project b2_project_goblin was not found under the workspace root. The obligation-sweep engine ships there and must be present. Remediation: b2_project_goblin/documentation/goblin-sweep-plan.md.`

3. **The `goblin sweep` subcommand is shipped (help exits 0).** This proves the engine plan's
   subcommand actually landed — not just that the repo exists:

   ```powershell
   uv run --project (Join-Path $workspaceRoot 'b2_project_goblin') goblin sweep --help
   ```

   If this exits non-zero (subcommand absent, deps not synced) → STOP: `goblin-sweep: prerequisite failed — 'goblin sweep --help' did not exit 0, so the engine's sweep subcommand is not available. Run 'uv sync' in the engine project and confirm the plan shipped. Remediation: b2_project_goblin/documentation/goblin-sweep-plan.md.`

All three green → proceed to the invocation.

## How to invoke (the pinned invocation)

Run the engine's deterministic sweep, JSON mode, against the target project. The invocation is
**pinned to the engine project by absolute path** (resolved from `<workspace-root>`), so it works
from any cwd — no `cd` into the engine repo:

```powershell
uv run --project (Join-Path $workspaceRoot 'b2_project_goblin') goblin sweep <project> --json
```

`<project>` is a direct-child project directory name under the workspace root (e.g. `toybox`,
`void_furnace`). The engine's grounding layer validates it; an unknown project fails inside the
engine, which this skill surfaces verbatim. **Parse `--json` ONLY** — the engine's human-readable
default output is presentational and unpinned; this skill never scrapes it.

## What it does

1. Run the three fail-loud prerequisite checks above, in order. Any failure stops the skill.
2. Shell the pinned invocation and capture its stdout.
3. Parse the stdout as the `--json` record (below). If the output is not valid JSON of the expected
   shape, STOP loudly (`goblin-sweep: engine returned malformed --json output`) and name the engine
   plan as remediation — do **not** invent obligations to fill the gap.
4. Render the report — exactly the seven locked fields per obligation (below).
5. End with the single next action: `/goblin-do <obl-id>`. This skill never executes, mutates, or
   plans the target work; it only presents obligations and hands off.

There is no extraction, dedup, atom-parsing, or scanning step here — those are the engine's, not the
wrapper's.

## The `--json` record this skill parses

Consumed contract (the sole seam between this skill and the engine; pinned in the engine plan's §6
"CLI output contract" — mirrored here read-only, edits happen in the engine plan). A JSON array,
ONE FLAT record per obligation, keys in this order:

| field | type | note |
|---|---|---|
| `id` | string | atom id `obl-<project>-<slug>`; persisted at `brain/suggestions/obl-<project>-<slug>.md`, prefix-isolated from `sugg-`/`uat-` kinds |
| `status` | string | `proposed \| accepted \| declined` — reuses the existing suggestion lifecycle |
| `obligation` | string | normalized obligation text (the persisted `description`) |
| `source_kind` | string | `plan_step \| issue \| todo_marker \| operator_ask` |
| `locator` | string | exact source locator, e.g. `plan.md § Step 12` / `issue#41` / `README.md:57` |
| `source_date` | string | ISO date of the source |
| `age_days` | integer | derived at report time from `source_date` |
| `goal_able` | boolean | whether the atom renders a `/goal` block |
| `goal_condition` | string or null | `null` when unset; drives `/goblin-do`'s `/goal` render |
| `provenance` | array of strings | merged source anchors — reruns merge without duplication |

## How to read the output (the seven locked fields)

Provider parity locks **exactly seven** presented fields per obligation. Every provider wrapper loads
this core, so all hosts render the identical set — never add, drop, or reorder them:

1. **Atom id** — `id` (`obl-<project>-<slug>`).
2. **Status** — `status` (`proposed | accepted | declined`).
3. **Obligation text** — `obligation`.
4. **Source locator + source age** — `locator`, plus the source age from `source_date` / `age_days`
   (e.g. `plan.md § Step 12 (dated 2026-06-01, 58 days old)`).
5. **Provenance** — the merged `provenance` anchors.
6. **Goal condition** — `goal_condition`, rendered **only when it is non-null**. When
   `goal_condition` is `null`, omit this field entirely for that obligation (do not print an empty
   or placeholder goal line).
7. **Next-rail line** — the closing `/goblin-do <obl-id>` handoff for the chosen obligation.

Suggested per-obligation layout (order-preserving; the engine emits records in its own order — do not
re-rank):

```text
obl-toybox-wire-judge-sample   [proposed]
  Obligation: Wire schedule_judge_sample into _do_propose so judge calls actually fire.
  Source: plan.md § Step 15 (dated 2026-06-01, 58 days old)
  Provenance: plan.md § Step 15; issue#372
  Goal: judge_calls_per_propose > 0 in a smoke run
  → /goblin-do obl-toybox-wire-judge-sample
```

(Here the `Goal:` line appears because `goal_condition` was non-null; on a `null` obligation that
line is simply absent.)

When the array is empty (no obligations discovered), say so plainly — `goblin-sweep: no open
obligations found for <project>.` — and stop. An empty result is a valid engine answer, distinct from
a prerequisite/engine failure (which stops loudly per **Prerequisites**).

## Next step

To act on one obligation, hand it to the single execution front door:

```text
/goblin-do <obl-id>
```

`/goblin-do` resolves the atom and either EXECUTES it via `/build-step` or HANDS IT OFF with a
`/plan-feature` seed, per its own mode-dispatch. `/goblin-sweep` never executes or mutates the target
project itself — it lists obligations and stops at this handoff (one next action, always).
