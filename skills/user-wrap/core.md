# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-wrap/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-wrap

A THIN front door for the sit-back-down moment. The operator has been away — lunch,
overnight, a context switch — and wants one answer before touching anything: keep
going, recycle the window, wrap it, or just close it? This skill composes three
existing contracts and owns ZERO triage logic of its own:

- **Orientation** — `/task-handoff --resume`
  ([`../task-handoff/core.md`](../task-handoff/core.md) § `--resume` — in-window
  orient) owns both the state source (this session's own file, with the schema
  doc's fallback) and the block shape.
- **Verdict + loss report** — `/session-wrap --advise`
  ([`../session-wrap/core.md`](../session-wrap/core.md) § `--advise` — verdict +
  loss report) is the ONE owner of triage: signal collection, route scoring, the
  read-only salvage preview, the 4-verdict banner (KEEP GOING / RECYCLE WINDOW /
  WRAP & CLOSE / SAFE TO CLOSE), and the two-line loss report.
- **State fields** — `current.md` and `sessions/<session-id>.md` format, field
  semantics, session identity, path resolution, and staleness are owned by
  `<repo>/_shared/task-state-schema.md`
  (cite it, never restate it).

**Defect clause.** Any triage constant appearing in this file or in
user-wrap-authored output prose — a token threshold, a context ceiling, a staleness
window, a route-scoring rule — is a DEFECT. Those numbers live in session-wrap's
threshold table and the task-state schema doc; they reach user-wrap's output only
inside the verbatim re-presented `--advise` report, never as this skill's own
reasoning.

---

## When to use / when NOT to use

**Use** at the return moment — the operator is sitting back down at an open window
and wants a verdict before acting: "sitting back down", "should I keep going or wrap
up", "am I safe to close this window". The name says wrap, but the skill serves the
whole return moment — KEEP GOING is the most common verdict.

**Do NOT use:**

- **Mid-task transition moments** (a boundary just hit, context feels heavy, end of
  day) → bare `/session-wrap` — it triages AND acts in one step; user-wrap would only
  add a detour.
- **Checkpoint-only writes** mid-loop → `/task-handoff --loop`.

---

## Steps

### Step 1 — Orient-lite (read-only)

Read this session's task state exactly as task-handoff `--resume` resolves it: this
session's own `<git-root>/.claude/task-state/sessions/<session-id>.md`, else the
schema doc's fallback (the derived `current.md` rollup, then the freshest session
file). Session identity, path resolution, field semantics, and staleness are the
schema doc's (above). Never fabricate or guess a session ID: a host with no stable
session identity reads the fallback. Add quick git state per touched repo:
`git log --oneline -5`, `git rev-parse --short HEAD`, `git status --porcelain --branch`
(dirty count from the file lines, ahead count from the `##` branch line). Output the
orientation block in task-handoff `--resume`'s shape:

  Resuming [Task field]: [Status]
  Next Action: [Next Action field verbatim]
  git: <repo> <branch> @ <short-sha> — <n> dirty, <m> ahead

When the state read is a fallback (no file of this session's own), add exactly one
line under the block naming its source:

  state: <current.md rollup | freshest session file> — not this session's own; orientation only

Absent or stale state (staleness per the schema doc — never restate its
threshold here): say so in the orientation block ("no fresh task state — orientation
from git only") and continue to Step 2; the `--advise` triage handles degraded
signals itself.

One deliberate difference from `--resume`: do NOT auto-proceed yet. user-wrap defers the
proceed/stop decision to the verdict. A KEEP GOING verdict restores `--resume`'s
no-confirmation behavior only for a fresh plain Next Action from this session's own file.
Fallback state stays orientation-only in both skills, and a locked
`task-handoff-next-action-v1` bundle stays held rather than executed.

Step 1 writes nothing and mutates nothing — no checkpoint, no commit, no
`current.md` or session-file touch.

### Step 2 — Delegate the verdict (never compute it)

Invoke `session-wrap --advise` via the Skill tool. That mode owns everything about
the verdict — see session-wrap core § `--advise`. user-wrap never computes a
triage signal, salvage preview, or verdict itself, never re-scores the route, and
never restates a threshold. If the delegated run fails, report the failure and stop
— do not fall back to a self-computed verdict.

### Step 3 — Present the verdict SUPER-clearly

Re-present `--advise`'s report as the centerpiece of the output, verbatim and
unmangled:

1. The advise triage line, as `--advise` printed it.
2. The `## <VERDICT>` banner — the first heading after the triage line, visually
   unmissable.
3. `Already durable:` then `Dies with this window:` immediately under the banner, in
   that order, with every SHA, count, timestamp, and path preserved.

Nothing may be inserted between the banner and the loss report, and nothing may
paraphrase or summarize it — the operator's real question is "do I lose anything if
I close this?", and the loss report exactly as `--advise` wrote it is the answer.

### Step 4 — Act per verdict

Exactly one of four actions, keyed to the banner:

| Verdict | Action |
|---|---|
| `KEEP GOING` | When Step 1 read a fresh plain Next Action from this session's own file: execute it immediately — task-handoff `--resume` semantics: no confirmation ask, no "should I continue?". State the command being run — naming its target directory when it runs in a project repo — then run it. When that own-file Next Action is a locked `task-handoff-next-action-v1` bundle, execute nothing: print it verbatim, then `Locked bundle held (not executed by user-wrap).`, and STOP. Otherwise (fallback, stale, or absent state) execute nothing: print ONE line — `Next Action not run: <state is the current.md rollup | state is the freshest session file | no fresh task state for this session>; orientation only.` — then STOP. No prompt, no write, no git verb. |
| `RECYCLE WINDOW` | Invoke bare `/session-wrap` via the Skill tool — it re-triages and ACTS (durable state, git verb, Pick-up-here block ending in `/clear`, or in the ask response when a git-verb segment reads `ask-first pending`, or in its in-window re-run step when it flags `checkpoint not written`). user-wrap appends nothing after session-wrap's output. |
| `WRAP & CLOSE` | Invoke `/session-wrap --end` via the Skill tool **automatically — no confirmation gate** (this is the only remaining step; run it, don't ask). `--end`'s own anomaly pre-flight owns concurrent-session/foreign-state safety — invoke it even then, don't pre-empt. The wrap completes only on positive evidence: its Pick-up-here block is on screen, no `checkpoint not written` flag and no commit, push or `/repo-update` failure is reported, and every git-verb segment of its Step D report ends in a completed outcome — `repo-update completed + pushed @ <short-sha>`, `committed <N> files + pushed <M> commit(s) @ <short-sha>`, `nothing to commit`, or `pushed <N> pending @ <short-sha>`. Only then emit exactly one plain closing line — `RAN SESSION-WRAP & SAFE TO CLOSE` (a plain line, not a second `## ` banner) — then STOP. Otherwise emit no closing line. When a segment reads `ask-first pending` or the `checkpoint not written` flag appears, session-wrap's own last step (the ask response, or the in-window re-run) stays the last thing on screen; append nothing. Otherwise — any other segment outcome, a reported failure, or no Pick-up-here block — report it in ONE line quoting session-wrap's segment or error verbatim. Then STOP. Never answer the ask, retry a push, re-invoke, or fall back to a self-run wrap. |
| `SAFE TO CLOSE` | Print ONE line — everything is durable; the window can be closed — then STOP. No skill invocation, no write, no git verb. |

> Next-step / Pick-up-here commands name their target directory, and the proactive project-switch message fires on a cwd≠project mismatch with no pin, per transition-directory-contract.md.

user-wrap itself never writes state or runs a git verb at any point: Steps 1–3 are
read-only, and every Step 4 mutation happens inside the delegated skill (or, on
KEEP GOING, inside the Next Action work itself).

---

## Maintenance

The `evals/` suite targets THIS front-door contract (created 2026-07-13, plan Step 4
/ #305): **10 assertions** across **3 categories** in `evals/evals.json` (passing
threshold **8/10**), **8 scenarios** in the repository-only
`skills/user-wrap/evals/test_scenarios.json` (one per verdict path, plus a WRAP & CLOSE
whose wrap stops at `ask-first pending`, a WRAP & CLOSE whose push is rejected, a
WRAP & CLOSE whose checkpoint is not written, and a KEEP GOING on fallback state;
the own-state KEEP GOING scenario also carries its locked-bundle conditional variant),
and a golden corpus of 8 goods + 15 single-defect bads under
`skills/user-wrap/evals/golden/` (manifest.json maps each bad to the one assertion it
trips). These source assets are not emitted or installed. A repository caller runs
them only by passing this explicit evals directory and the built version's
`versions[].skill_md_path`; an installed user-wrap therefore remains unavailable to
`skill-evolve`, whose existing missing-assets halt still governs. The scorer evaluates
caller-supplied rendered output; it does not execute user-wrap itself. Any edit that changes an output contract here
(orientation block, re-presentation rules, per-verdict actions) must update the
affected assertions and goldens in the same diff, keeping this footer's numbers
equal to `evals.json`'s. The verdict + loss-report CONTENT contract stays owned by
session-wrap's `--advise` section — when that changes, re-check the
re-presentation assertions here instead of duplicating the contract. Likewise,
when session-wrap's git-verb outcomes or its `ask-first pending` / `checkpoint not
written` markers change, update the WRAP & CLOSE row and assertion 8 in the same
change.
