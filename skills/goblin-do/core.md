# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- This skill has no supporting assets or scripts of its own. It shells the installed goblin CLI from the `b2_project_goblin` project directory and relays what the CLI prints.
- A named skill call means the host's skill-dispatch primitive. This skill spawns no Agent, Explore agent, workflow, or sub-agent; every step runs in the invoking session.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# goblin-do

Take ONE persisted goblin atom and print what to run next. `goblin do` is a **read-only
renderer**: it resolves the atom, rechecks that its anchor is still live, and prints either a
copy-pasteable `/goal` block (a goal-able atom) or a planning/handoff seed. It does not execute
the work, lease `/build-step`, create or delete branches, merge, push, or write to `brain/` or
to the target project. The operator runs what it prints.

Atom kinds, all persisted under `b2_project_goblin/brain/suggestions/`:

| Prefix | Producer | Kind |
|---|---|---|
| `sugg-<project>-<slug>` | `/goblin-suggest <project>` (`--small` / `--big`) | Suggestion |
| `uat-<project>-<slug>` | `/goblin-suggest <project> --uat` | UAT task |
| `obl-<project>-<slug>` | `/goblin-sweep <project>` | Obligation |

## Prerequisites

- The atom exists. Run `/goblin-suggest <project>` or `/goblin-sweep <project>` first and pick an id.
- The `b2_project_goblin` runtime is already prepared: its virtual environment and lock file
  exist and contain the `goblin` console script. This skill never synchronizes, installs, or
  updates that runtime. If the prepared runtime cannot run, fail visibly; do not run `uv sync`
  or another install command as recovery.
- `gh` is authenticated **only** when the atom's anchor is an issue reference (`#N` or
  `<word>#N`): the CLI asks `gh` whether the issue is still OPEN and refuses if it cannot tell.
- Nothing else. No OAuth token, clean target tree, or branch state is required, because nothing
  is executed.

## How to invoke

```text
/goblin-do <id-or-text> [--dry-run] [--brain-dir <path>] [--dev-root <path>]
```

From the `b2_project_goblin` directory, the skill runs:

```powershell
uv run --no-sync --frozen goblin do <id-or-text> [--dry-run] [--brain-dir <path>] [--dev-root <path>]
```

- `<id-or-text>`: an atom id (the filename stem, e.g. `sugg-toybox-add-a-smoke-test`,
  `uat-toybox-run-the-emulator-smoke`, `obl-toybox-wire-judge-sample`) or free text that
  fuzzy-matches exactly one atom across all three kinds.
- `--dry-run`: prints the SAME artifact under the line
  ``# DRY RUN (preview) -- the artifact below is exactly what `goblin do` emits:``.
  A preview and a real run print the same artifact. If that artifact requires a re-route, the
  preview also prints the re-route line and next step, but it never writes back to an intake
  ledger. This dry-run exception applies only to the ledger write; it does not suppress the
  operator-facing artifact or re-route.
- `--brain-dir <path>`: override the atom store (default: the goblin repo's `brain/`).
- `--dev-root <path>`: override the workspace root the atom's project resolves under for the
  anchor recheck (default: the real dev root). Read-only.

**Bare `/goblin-do` (no argument):** do not call the CLI. Print the usage line above and the
two ways to get an id (`/goblin-suggest <project>`, `/goblin-sweep <project>`), then stop.

There is no session Workflow path and no execute, land, or apply-result mode. The CLI's
argument parser rejects `--land`, `--apply-result`, and `--output-file` (exit 2); do not
substitute a manual build, merge, or atom edit for them.

## What it does

1. **Resolve** `<id-or-text>` to ONE atom (exact id, else fuzzy text across `sugg-`/`uat-`/`obl-`).
   No match or an ambiguous match refuses with a ranked shortlist of candidate ids.
2. **Resolve the project**: the atom's `project` must be an existing direct child of the dev root.
3. **Recheck anchor liveness** (read-only). An issue-reference anchor (the whole anchor is `#N` or
   `<word>#N`) must be OPEN per `gh issue view`. Any other anchor is treated as a file path: a
   trailing `:<line>[:<col>]` is stripped and the path must be tracked per
   `git -C <target> ls-files --error-unmatch`. Otherwise the CLI refuses.
4. **Render.** A goal-able atom (`goal_able: true` AND a non-empty `goal_condition`) renders a
   `/goal` block. Otherwise the CLI renders the seed for its kind: Suggestion → `/plan-feature`
   seed; UAT task → UAT handoff block; Obligation → obligation `/plan-feature`-style seed. The
   atom's `mode` and the old safe-UAT subset are not consulted.
5. **Reachability note (goal-able atoms only; advisory).** Before presenting the `/goal` block,
   make one brief read-only check and print one line:
   `Reachability: deps <met|blocked|unknown>; decision <made|open|unknown>; verifiable-here <yes|no|unknown>`.
   Checks: (a) is any upstream issue or prerequisite artifact named by the atom still open or
   missing; (b) does the work hinge on an unmade operator decision or a deliberately parked
   finding; (c) can `goal_condition` be checked on this machine, and is it a real proxy for the
   fix. This note never blocks, never edits the artifact, and never replaces the operator's choice.
6. **Relay** the CLI stdout verbatim, then print the next step (below). On a CLI failure, relay
   stderr verbatim with the exit code and stop. If `uv`, the prepared environment, its frozen
   lock, or the `goblin` console script cannot run, that is a CLI failure too: report it and
   stop (the host adapter names the reason code). Never synchronize or install as recovery.
   Never hand-render an artifact the CLI did not print, for example by reading the atom file
   and composing a `/goal` block or seed yourself.

## How to read the output

- **`/goal` block** (goal-able):
  ```text
  # Goal for `<project>`: <description>
  # Anchored to: <anchor>
  # Run both lines in order in a fresh window. The /task-handoff --resume line re-orients the new window from .claude/task-state/current.md; it is harmless to skip for same-window use.
  /task-handoff --resume
  /goal "<goal_condition>"
  ```
  `goal_condition` is used verbatim. If it contains a double quote, say that the `/goal` line
  may need re-quoting before use. The CLI does not consult the atom's `status`, so an
  `accepted` or `declined` goal-able atom still renders a runnable `/goal` block, and the block
  does not show the status (the seeds below show it in their provenance footer).
- **`/plan-feature` seed** (Suggestion): heading, Project, What, Why, Anchor, the rubric scores
  as context, and a provenance footer naming the atom id and status.
- **UAT handoff block** (UAT task): heading, Project, What, Anchor ("read it first"), AI-doable
  verdict, the clarifying question if any, human residual steps if any, provenance footer.
- **Obligation seed** (Obligation): heading, Project, What, Anchor, Source (source kind and date),
  provenance footer.
- **Failure**: `goblin do failed: <reason>` on stderr, exit 1, for a bad, ambiguous, or unknown
  id, an invalid project, or a stale or unverifiable anchor (closed issue, untracked file,
  `gh` missing or failing).

**Known structural refusals.** The current CLI refuses any anchor that is neither an issue
reference nor a tracked path, even when the work is still open: plan-step locators
(`<plan> § Step <id>`) and operator-ask tags (`memory: <name>`) on goblin-sweep obligations, and
prose anchors on older goblin-suggest atoms. Report the refusal and name the anchor shape as
unsupported. Do not edit the atom, `brain/`, or the target to get past it.

**Next step printed after the artifact:**

- `/goal` block: the operator runs both lines (a fresh window) or only the `/goal` line (the same
  window) in the session that will do the work. `/goal` is a Claude Code window command: relay
  the block verbatim as operator text and never claim a goal is armed or started. A host without
  `/goal` still relays the block for a window that supports it; pursuing the `goal_condition` in
  a session on such a host is ordinary implementation work, not an armed goal. On any host, that
  session does implementation work: select it under the host's implementation-worker model
  policy rather than assuming the coordinator session qualifies. goblin-do does not start the
  goal or choose its model.
- Seed or UAT handoff block: this is the do→plan handoff (see **Relationship to other skills**).
  Paste the seed into `/plan-feature`, then follow the build rail in `skill-pipeline.md`. UAT
  residual steps that are human-only remain operator work.

## Write and side-effect boundary

- **Reads:** the atom file, the project directory, `git ls-files` in the target, and `gh issue
  view` for issue anchors.
- **Writes by goblin:** none. No branch, commit, merge, push, atom status flip, provenance append,
  or target edit.
- **Writes by this skill:** on an ordinary invocation, only the intake-ledger write-back that the
  re-route contract requires when a ledger exists (below). A `--dry-run` never performs that
  write-back. Nothing else.
- goblin-do does not review or gate the work a `/goal` drives, and gives it no scratch branch,
  default-branch protection, or `/build-step` review. The session that pursues it owns its own
  branch or worktree isolation and follows the target project's own rules and gates.
- Re-running is idempotent: the same atom and anchor state render the same artifact.
- No confirmation prompt is needed or asked. The CLI render and every `--dry-run` are read-only;
  an ordinary invocation may perform only the already-defined intake-ledger write-back.

## Cost / latency note

Cheap. The CLI reads one atom and renders text; an issue anchor adds one bounded `gh` call. The
reachability note is a short read-only check in the invoking session. No build, sub-agent, or
model fan-out runs.

## Relationship to other skills

- **Producers:** `/goblin-suggest` (`sugg-`, `uat-` atoms) and `/goblin-sweep` (`obl-` atoms).
  The anchor is the contract field: an issue reference or a repo-relative tracked path (a
  `:<line>` suffix is allowed).
- **Consumers:** the operator's `/goal` session for goal-able atoms; `/plan-feature` for seeds.
- `goblin handoff` survives as a deprecated CLI alias that prints the suggestion seed with a
  deprecation note on stderr. Prefer `goblin do <id>`.

A seed handoff (an atom that is not goal-able) is the codified template the routing web's
re-route contract was generalized from: the do→plan edge (the atom needs real planning), and
likewise do→bug when the thing being improved turns out to be broken (the correct-rail seed is
then a `/user-debug --symptom` line rather than a `/plan-feature` seed). The full contract (the
standard emit-line format and the write-back to the intake ledger when one exists) is owned by
`skill-pipeline.md § Re-route contract`; cite it there, never restate it.
For `--dry-run`, print the same re-route and next step but apply the preview exception above: do not
write to the intake ledger.
