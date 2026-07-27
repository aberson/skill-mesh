# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-orient/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# User Re-Orientation

This skill produces a status snapshot for a user returning mid-session. Read-only by default; does not mutate memory, plans, or code. Two modes: **full** (default — Steps 1-2 below) and **`--quick`** (a no-lookups three-section thread summary — see "Quick mode" below; for in-flow check-ins, not post-gap re-orientation).


---

## Steps

### Step 1: Run autonomous asides in parallel (BEFORE composing output)

Run all relevant tool calls in parallel in a single message. Do not output the findings yet — they feed Step 2. Pick the subset that fits the project:

- `git status --short` (working tree state)
- `git log --oneline origin/<main>..HEAD` (unpushed commits)
- `git log --oneline -5` (recent activity context)
- Tail (last 30 lines) of the most recently modified file in `logs/` if the project has one
- Read any current run-state JSON for active long-running processes this project tracks (e.g. `data/evolve_run_state.json` for Alpha4Gate)
- Read `MEMORY.md` from the project's auto-memory directory if not already in context

If a project has its own status conventions (e.g., a build-state file, a test-counts marker, a daemon health endpoint) and you know about them from earlier in the session, query those too.

Apply those findings to compose Step 2.

---

### Step 2: Compose the orientation

Write SIX sections in this fixed order: (1) Verified-working, (2) Not-yet-verified, (3) Manual checks, (4) Autonomous asides surfaced, (5) Near-term sequencing, (6) Most honest recommendation. Do NOT reorder — even when a Step 1 aside is dramatic (dead process, surprise origin commit), it stays in section 4. Leading with an aside breaks the reader's mental model. Skip any section that has nothing to report; do not promote it upward.

Default total target: ~250 words. If the session has > 4 hours of context or the user has been away > 24 hours, expand to ~600 words. If session has < 30 minutes of activity, output a compressed version (no headers, just the recommendation).

### 1. Verified-working

Write 3-7 bullets of concrete confirmations, each with citable evidence (commit SHA, `file:line`, log line, test count).

### 2. Not-yet-verified

Open assumptions the verified work depends on. Each item names the *risk* if the assumption is wrong. 1-4 bullets.

### 3. Manual checks (user can run in < 60s)

1-3 concrete USER commands that would convert "not verified" items to "verified". Skip this section if not-verified is empty or items can't be resolved user-side.

Write each as:
- **What to run:** exact command, copy-paste ready
- **What the answer tells us:** the specific signal we're looking for
- **Why it matters:** what LLM work it unblocks

Rank by impact (highest-leverage first). The criteria for inclusion: low cost (≤ 60s) and high LLM-unblock value.

### 4. Autonomous asides surfaced

If Step 1 turned up anything notable that the user might not know about (a new commit on origin, a process that died, a stale lock file), surface it briefly here. **OMIT this section entirely when Step 1 was unremarkable — do NOT include a placeholder like "nothing notable", "no findings", or "no new commits". Section absence IS the signal.**

### 5. Near-term sequencing

The next 2-5 concrete steps, each with rough effort estimate (e.g., "~30 min", "1-2 hr"). Distinguish user-side vs LLM-side steps when both are present.

### 6. Most honest recommendation

One paragraph. What to do RIGHT NOW. Why this over alternatives. If unsure between two paths, say so and explain the tradeoff.

---

## Constraints

- **READ-ONLY.** Do not write memory, edit files, commit, or push. FLAG stale memory or missing docs and offer a follow-up turn — do not auto-update.
- **Be specific.** "Things are mostly working" is useless. "The 8-hour soak from 23:10 PDT completed, 0 promotions, regression-rollback path exercised cleanly (commit ce8545f)" is useful.
- **Be honest about uncertainty.** Sections 2 and 3 carry the value. Do not minimize them to keep the output tidy.
- **Fresh session edge case.** If there is no prior work to orient on, respond with a brief "fresh session — what would you like to work on?" instead of empty sections.
- **Respect user-stated priorities.** Pull from `MEMORY.md` for project goals; don't propose actions that contradict known user preferences without flagging the conflict.

---

## Quick mode (`--quick`)

A quick working-memory refresh of the current thread: ~150 words, three sections, no autonomous lookups. Skip Step 1 entirely — fire no tool calls; everything comes from the conversation already in context.

Summarize our current working thread in plain text. Be concise. Cover exactly three things:

**1. Problem** — What are we trying to solve? One or two sentences max. Include the ticket/PR number if applicable.

**2. What we tried** — Bullets. Label each with outcome (`worked`, `didn't fix`, `confirmed`). Actions without outcomes don't count.

**3. Still to do** — What's unresolved or next? Bullet list. If nothing is left, say so.

Never start with preamble, the phrase "here's your recap", or closing remarks. Output just the three sections.

### When `--quick` suffices vs full orientation

Default to `--quick` for in-flow check-ins ("remind me where this thread is") when the thread is live and everything needed to answer is already in context. Run the full six-section orientation when returning fresh or after a context gap. Escalation trigger: if drafting the quick summary reveals you cannot reconstruct state from the thread alone — any "What we tried" bullet whose outcome you would need to read git or files to state honestly — quick mode has hit its design boundary; run the full orientation instead. Don't silently widen scope: switch modes cleanly rather than padding a quick summary with unmarked guesses (docs/investigations/user-recap/05-recap-vs-orient-boundary.md).

Depth scales by selective retention, not length: a longer thread does NOT earn a longer quick summary — the ~150-word budget is fixed. Collapse each older resolved sub-problem to one state line ("<sub-problem>: resolved (<outcome>)"); keep full detail only on the active sub-thread. If you cannot name a single active sub-thread the summary is refreshing, the thread is too broad for quick mode — run the full orientation (docs/investigations/user-recap/11-scaling-recap-depth.md).

Compacted-context caveat: when earlier turns have been compacted to a summary, build the quick summary only from the summary + live turns you can actually read. Demote pre-boundary attempts to the fidelity the summary supports — if the summary says "investigated X" with no outcome, do NOT promote it to an invented `worked` / `didn't fix` label — and append a one-line gap flag, e.g. `(earlier context compacted; pre-<X> attempts may be incomplete)`. Do NOT run lookups to backfill the gap — needing to reconstruct lost context is the escalation signal to the full orientation (docs/investigations/user-recap/12-recap-across-compacted-context.md).

---

## Limitations

- Mid-debugging on a single live thread; wants a quick working-memory refresh — use `--quick` (above), not the full six-section orientation.
- Project-axis overview — what a project shipped, has planned, could do next, could cut (plan+git-derived) — use `user-pm`.
- Comprehensive handoff to a fresh context window — use `session-wrap`.
- Verify a document is self-contained — use `plan-wrap`.
