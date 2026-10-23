# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- This skill has no scripts or runtime assets. `evals.seed/` is inactive seed material that stays with the compatibility launcher at `.claude/skills/user-draft/`.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Before Step 1 or Step 4, read task-handoff's core and `<repo>/_shared/task-state-schema.md` in full. Task-handoff's scoped departures govern where it narrows the shared schema. If either dependency is unavailable, skip the checkpoint and emit the bare artifact with the existing `checkpoint not written` line; never infer session ownership from fallback state.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-draft

Turn a rough idea into a finished artifact you can use immediately:

- **prompt** — a precise prompt/instruction for a model or agent
- **goal** — a copy-pasteable `/goal "<condition>"` that keeps a session working until a checkable condition is met

One NL front door for both. `user-draft` figures out which you want, refines it through the same
discipline, and emits an artifact that self-orients the window you paste it into.

## Contract

- **Input:** the free text after the command — rough thoughts, or a `/user-pm --goal` seed that
  carries a draft condition and one open point. **Bare `/user-draft`:** use the operator's latest
  rough thoughts in this conversation, quoted on one line before the Step 0 notice; if there are
  none, ask one question — what to draft — as Step 0's one question, and do nothing else until
  answered. Step 0 then classifies the answer by best call; its notice is the correction path.
- **Output:** one artifact in chat (Step 3a or 3b, with Step 4's preamble only when earned) plus
  the Step 0 notice and the per-step lines defined below: the bare-input quote, `## Changes` (3a),
  the check note and any `Outside the goal:` line (3b), and Step 4's inline note or
  `checkpoint not written` line. user-draft never runs the artifact, never arms `/goal`, and
  writes no file itself.
- **Writes:** only Step 1's `task-handoff --loop` — this session's gitignored session file and the
  derived rollup; no commit, no push. Never hand-write `current.md` or any session file.
- **Re-runs:** stateless. A re-run drafts again from its new input and checkpoints again when
  Step 1's gate holds.

---

## Step 0 — detect intent (goal vs prompt)

Read the user's free-text thoughts and classify:

| Signal | → branch |
|---|---|
| "write/make a goal", "set a goal", "keep working until", "don't stop until", "objective", "until X is done", "/goal" | **GOAL** |
| "write/refine a prompt", "improve this", "make this clearer", "task for an agent", "ask the model to", "instruction" | **PROMPT** |

If no explicit keyword: classify by **what the thought describes**.
- Describes *what "done" looks like* (a stopping/completion state) → **GOAL**
- Describes *what to do* (an instruction/task) → **PROMPT**

If still genuinely ambiguous, ask exactly one disambiguating question — never guess silently,
never ask more than one. Then proceed.

Emit a one-line notice: `user-draft: detected GOAL` / `user-draft: detected PROMPT` so the user can correct.

---

## Step 1 — checkpoint current state (cheap, gated)

The artifact you're about to produce may be pasted into a fresh window. Checkpoint **this
session's** state first, but only when there is real state to preserve. The checkpoint's verified
Git root and session identity are carried into Step 4 so the receiving window can orient from that exact file;
the derived rollup and every foreign session remain orientation-only and never authorize a Next
Action. Session identity and paths follow `<repo>/_shared/task-state-schema.md` (§ Session identity,
§ Per-session model), as narrowed by task-handoff's core:

- **If** this session has a stable session identity and in-flight work — its own
  `<git-root>/.claude/task-state/sessions/<session-id>.md` has Status `IN_PROGRESS` or `BLOCKED`,
  or this window did work that no checkpoint records yet — work means changes toward a task (file
  edits, commits, test or build runs); reading, discussion and drafting this artifact do not
  count. Unrecorded work counts even after a `COMPLETE` checkpoint.
  → invoke `task-handoff --loop` (named skill call). ~5s; gitignored state only — no commit, no push.
  Run it even when nothing changed since the last checkpoint so the artifact names a current
  checkpoint owned by this session.
- **Else** (no stable session identity, or no in-flight work as defined above — for example only
  reading or discussion, or its own file is `COMPLETE` with no work since) → skip silently. Do not
  write a checkpoint for a clean slate, and never fabricate a session identity. The shared
  `current.md` can show another window's work; it never decides this gate.

Step 1 has checkpointed only when `task-handoff` returns `Checkpoint written.`. Any other result
(an error, a missing tool, or a `Checkpoint not written` / `Checkpoint incomplete` line) means no
checkpoint: continue, and Step 4 emits the bare artifact.

This is the "do proper task-handoff activities before starting work" step. It is the only
thing that earns Step 4's identity-bound orientation preamble.

---

## Step 2 — refine (shared flow)

Both branches run the same pass:

1. **Find the gaps.** Ambiguities, missing constraints (format, scope, audience, edge cases),
   assumed context, contradictions, weak verbs ("handle", "process", "deal with").
2. **Sweep for proportionality (PROMPT branch).** When the input is an existing prompt or describes
   a multi-step workflow, identify the stated outcome or named failure mode protected by every
   specified skill, artifact, test family, review pass, and gate. Remove items with no such tie,
   duplicated ceremony, speculative hardening, and exhaustive cross-products when a smaller
   representative check proves the same thing. Preserve user-owned scope, safety and authorization
   boundaries, direct regressions for known failures, and acceptance gates. Do not invent extra
   process merely to perform this sweep.
3. **Ask targeted questions.** 3–5 focused questions, only the ones that meaningfully change the
   output. Skip entirely if the input is already clear. Do not ask obvious questions.
4. **Polish** per the branch below, after the user answers (or directly if no questions needed).

Preserve the user's voice and intent — refine, don't rewrite into a template.

---

## Step 3a — PROMPT branch

Produce the improved prompt with:

- **Concrete verbs** replacing vague ones ("return" not "handle", "reject" not "deal with")
- **Explicit constraints** filled in from the answers (format, scope, audience)
- **Scope boundary** — what's in and out, stated explicitly
- **One literal example pair** — an actual input → actual output, not a description of one
- **Negative examples** where they prevent a known failure mode ("do NOT …")

Return the prompt in a fenced code block (see Step 4 for the preamble). Follow it with a 2–4 line
`## Changes` summary of what you tightened and why. If the proportionality sweep removed material
requirements, name the cuts and why the remaining proof is sufficient.

## Step 3b — GOAL branch

Produce a `/goal "<condition>"` where the **condition is a good stop criterion**:

- **Binary and checkable every turn** by a fast model with tool access.
- **Names concrete artifacts/criteria** — "tests green", "PR #N merged", "file X exists",
  "count == N", "`<cmd>` exits 0". Not "the bot is better" or "code is clean" (unmeasurable →
  the goal never resolves).
- **Agent-completable** — this session can make every clause true with its own tools (code, tests,
  files, commits, analysis); "PR #N merged" qualifies only when this session may merge it. An
  operator step, a clock or soak, or a third party on the critical path is a handoff, not a goal
  (the hook re-fires with no path to release): scope the condition to the agent-completable slice
  and name the rest on one `Outside the goal:` line after the block. If no slice is
  agent-completable, say goal mode does not fit and offer the PROMPT branch instead.
- **Carries guardrails** if the work needs them ("…without touching the public API").

Reject your own first draft if the condition isn't externally verifiable or agent-completable —
rewrite until it is. Return it in a copy block (see Step 4), then a one-line note on *how the
harness will check it*.

---

## Step 4 — bake a self-orienting preamble (gated)

Make the artifact orient whatever window it lands in — **only if** Step 1 returned
`Checkpoint written.`. For a clean-slate draft, emit the bare artifact with no preamble (never tell
a fresh window to read a checkpoint that doesn't apply). When Step 1 ran but did not return
`Checkpoint written.`, emit the bare artifact plus one line:
`user-draft: checkpoint not written; no preamble added`.

**PROMPT branch** — prepend one line inside the block, substituting the verified identity whose
Step 1 checkpoint returned `Checkpoint written.`:

```text
Orient only: read <checkpoint-git-root>/.claude/task-state/sessions/<checkpoint-session-id>.md; if it is absent, continue without checkpoint context. Do not use current.md or another session as a substitute, and do not execute its Next Action. Then:

<the refined prompt>
```

**GOAL branch** — emit the same identity-bound orientation instruction above the goal:

```text
Orient only: read <checkpoint-git-root>/.claude/task-state/sessions/<checkpoint-session-id>.md; if it is absent, continue without checkpoint context. Do not use current.md or another session as a substitute, and do not execute its Next Action. Then:
/goal "<condition>"
```

For same-window use the orientation line is harmless to skip — note that inline. In either
branch it grants read-only context from the explicitly named checkpoint; the refined prompt or
goal is the task. A missing or mismatched file does not fall back to `current.md` or another
session and never authorizes execution; continue with the artifact without checkpoint context.

---

## Principles

- **Shorter is better.** Every line of the artifact earns its place.
- **Specificity over generality.** "return a JSON array" beats "return structured results";
  "tests green and PR #196 merged" beats "the feature is done".
- **Show, don't tell.** A literal example beats a description of one.
- **One artifact, one job.** If the input bundles several asks, say so and offer to split.
- **Never block.** At most one disambiguation question (Step 0) or one round of refine questions
  (Step 2). Otherwise make the best call and note it inline.
