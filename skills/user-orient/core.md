# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- This skill has no runtime scripts or assets. Its evals are support assets and are never loaded at runtime.
- It calls no named skill, spawns no agent or sub-agent, and uses no model tier: the invoking session performs every step.
- A missing host capability never blocks. Run the lookups the host supports, skip the rest, and report any claim that needed a skipped lookup under Not-yet-verified. Never simulate a tool result.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# User Re-Orientation

This skill produces a status snapshot for a user returning mid-session. Read-only by default; does not mutate memory, plans, or code. Two modes: **full** (default — Steps 1-2 below) and **`--quick`** (a no-lookups three-section thread summary — see "Quick mode" below; for in-flow check-ins, not post-gap re-orientation).

**Invocation.** An explicit `/user-orient` runs the full orientation and `/user-orient --quick` runs quick mode; any other text after the command is context for what to orient on and does not change the mode. When the skill is selected from a natural-language request instead (for example "where are we" or "remind me where this thread is"), pick the mode by "When `--quick` suffices vs full orientation" below. Never block or ask before orienting. The output is operator-facing text only: no file, artifact, or downstream skill call. Re-running is safe and reflects the state at that moment.

---

## Steps

### Step 1: Run autonomous asides in parallel (BEFORE composing output)

Run all relevant tool calls in parallel in a single message. Do not output the findings yet — they feed Step 2. Parallelism is an optimization; withholding findings until Step 2 is the contract. Pick the subset that fits the project:

- `git status --short` (working tree state)
- `git log --oneline origin/<main>..HEAD` (commits ahead of the locally known default-branch ref; `<main>` is the repository's default branch; this does not say whether they were pushed to the current branch's upstream)
- `git log --oneline HEAD..origin/<main>` (commits on origin's default branch that HEAD lacks, as of the last fetch)
- `git log --oneline -5` (recent activity context)
- Tail (last 30 lines) of the most recently modified file in `logs/` if the project has one
- Read any current run-state JSON for active long-running processes this project tracks (e.g. `data/evolve_run_state.json` for Alpha4Gate)
- Read `MEMORY.md` if not already in context: the one in the host's auto-memory directory for this project, else the one the loaded project instructions name. Skip this only when neither exists; read no other file in its place.

If a project has its own status conventions (e.g., a build-state file, a test-counts marker, a daemon health endpoint) and you know about them from earlier in the session, query those too.

**Which repository.** Run git in the repository this session's work is in, as the thread shows it (a project pin or the paths it edited; use `git -C <path>`), else the current directory's repository. A workspace can nest project repositories inside a parent repository whose state is not the project's. When the thread edited files in more than one repository, run the git asides in each of those repositories. When a queried repository is not the current directory's, name its path in the first evidence that cites it.

**Lookup limits.** Every aside is a read-only query on this machine: no `git fetch`, pull, or request to a remote host, and no command run to change files, memory, or git refs. A status endpoint from the project conventions above may be queried only on a loopback address (such as `localhost`) and only with a read-only request (such as an HTTP GET). Remote-tracking refs are as of the last fetch; when their currency matters, offer `git fetch` as a Manual check instead of running it, and offer any status check that needs a remote host the same way. Do not open credential or secret files (for example `.env` or token stores), and never quote a secret value that appears in a log line; name the file and line instead.

**When an aside fails or does not apply** (not a git repository, no `origin` or default branch, no `logs/`, an unreadable file, a host that cannot run commands): skip it and do not guess its result. A claim that needed it goes to Not-yet-verified, naming the lookup that failed or was skipped. Surface the failure itself in section 4 only when it meets section 4's rule (for example, no remote exists where the user believes they pushed).

Apply those findings to compose Step 2.

---

### Step 2: Compose the orientation

Write SIX sections in this fixed order: (1) Verified-working, (2) Not-yet-verified, (3) Manual checks, (4) Autonomous asides surfaced, (5) Near-term sequencing, (6) Most honest recommendation. Do NOT reorder — even when a Step 1 aside is dramatic (dead process, surprise origin commit), it stays in section 4. Leading with an aside breaks the reader's mental model. Skip any section that has nothing to report; do not promote it upward.

Default total target: ~250 words. If the session has > 4 hours of context or the user has been away > 24 hours, expand to ~600 words. If session has < 30 minutes of activity, output a compressed version (no headers, just the recommendation).

### 1. Verified-working

Write 3-7 bullets of concrete confirmations, each with citable evidence (commit SHA, `file:line`, log line, test count).

Evidence means current state observed by this invocation's asides or by this session's own tool results. Memory entries, handoff notes, task-state files, and earlier summaries are leads, not verification: a claim resting only on them goes to Not-yet-verified. When a lead conflicts with git or the files, cite both; the observed state wins.

### 2. Not-yet-verified

Open assumptions the verified work depends on. Each item names the *risk* if the assumption is wrong. 1-4 bullets.

### 3. Manual checks (user can run in < 60s)

1-3 concrete USER commands that would convert "not verified" items to "verified". Skip this section if not-verified is empty or items can't be resolved user-side.

Write each as:
- **What to run:** exact command, copy-paste ready for the operator's shell as the project instructions name it
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
- **Respect user-stated priorities.** Pull project goals from `MEMORY.md` (when one exists) and the project instructions; don't propose actions that contradict known user preferences without flagging the conflict.

---

## Quick mode (`--quick`)

Quick mode absorbed the retired `user-recap` skill. The `docs/investigations/user-recap/` files cited below are design rationale in the dev workspace, not runtime inputs.

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
- Sitting back down and deciding whether to keep going, recycle, or close the window — use `user-wrap`.
- Resuming a saved task checkpoint in this window — use `task-handoff --resume`.
