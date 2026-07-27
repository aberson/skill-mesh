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

- **Orientation shape** — `/task-handoff --resume`
  ([`../task-handoff/core.md`](../task-handoff/core.md) § `--resume` — in-window
  orient).
- **Verdict + loss report** — `/session-wrap --advise`
  ([`../session-wrap/core.md`](../session-wrap/core.md) § `--advise` — verdict +
  loss report) is the ONE owner of triage: signal collection, route scoring, the
  read-only salvage preview, the 4-verdict banner (KEEP GOING / RECYCLE WINDOW /
  WRAP & CLOSE / SAFE TO CLOSE), and the two-line loss report.
- **State fields** — `current.md` format, field semantics, path resolution, and
  staleness are owned by
  `../../references/task-state-schema.md`
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

Read `<git-root>/.claude/task-state/current.md` (path resolution and field semantics
per the schema doc above) plus quick git state: `git log --oneline -5`,
`git rev-parse --short HEAD`, `git status --porcelain` (dirty/ahead counts per
touched repo). Output the orientation block in task-handoff `--resume`'s shape:

  Resuming [Task field]: [Status]
  Next Action: [Next Action field verbatim]
  git: <repo> <branch> @ <short-sha> — <n> dirty, <m> ahead

One deliberate difference from `--resume`: do NOT auto-proceed yet. `--resume`
proceeds without confirmation; user-wrap defers the proceed/stop decision to the
verdict — a KEEP GOING verdict restores `--resume`'s no-confirmation proceed in
Step 4.

Absent or stale `current.md` (staleness per the schema doc — never restate its
threshold here): say so in the orientation block ("no fresh task state — orientation
from git only") and continue to Step 2; the `--advise` triage handles degraded
signals itself.

Step 1 writes nothing and mutates nothing — no checkpoint, no commit, no
`current.md` touch.

### Step 2 — Delegate the verdict (never compute it)

Invoke `session-wrap --advise` via the Skill tool. That mode owns everything about
the verdict — see session-wrap SKILL.md § `--advise`. user-wrap never computes a
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
| `KEEP GOING` | Execute current.md's Next Action immediately — task-handoff `--resume` semantics: no confirmation ask, no "should I continue?". State the command being run — naming its target directory when it runs in a project repo — then run it. |
| `RECYCLE WINDOW` | Invoke bare `/session-wrap` via the Skill tool — it re-triages and ACTS (durable state, git verb, Pick-up-here block ending in `/clear`). |
| `WRAP & CLOSE` | Invoke `/session-wrap --end` via the Skill tool **automatically — no confirmation gate** (this is the only remaining step; run it, don't ask). `--end`'s own anomaly pre-flight owns concurrent-session/foreign-state safety — invoke it even then, don't pre-empt. When the wrap completes, emit exactly one plain closing line — `RAN SESSION-WRAP & SAFE TO CLOSE` (a plain line, not a second `## ` banner) — then STOP. |
| `SAFE TO CLOSE` | Print ONE line — everything is durable; the window can be closed — then STOP. No skill invocation, no write, no git verb. |

> Next-step / Pick-up-here commands name their target directory, and the proactive project-switch message fires on a cwd≠project mismatch with no pin, per transition-directory-contract.md.

user-wrap itself never writes state or runs a git verb at any point: Steps 1–3 are
read-only, and every Step 4 mutation happens inside the delegated skill (or, on
KEEP GOING, inside the Next Action work itself).

---

## Maintenance

The `evals/` suite targets THIS front-door contract (created 2026-07-13, plan Step 4
/ #305): **10 assertions** across **3 categories** in `evals/evals.json` (passing
threshold **8/10**), **4 scenarios** in `evals/test_scenarios.json` (one per verdict
path), and a golden corpus of 4 goods + 10 single-defect bads under `evals/golden/`
(manifest.json maps each bad to the one assertion it trips). Any edit that changes an
output contract here (orientation block, re-presentation rules, per-verdict actions)
must update the affected assertions and goldens in the same diff, keeping this
footer's numbers equal to `evals.json`'s. The verdict + loss-report CONTENT contract
stays owned by session-wrap's `--advise` section — when that changes, re-check the
re-presentation assertions here instead of duplicating the contract.
