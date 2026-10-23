# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- This skill ships no runtime scripts or assets. The repository-only corpus at `skills/review-uat/evals/` is an offline maintenance input: distribution builds do not emit it, installed runtime does not load it, and an evaluation route without an explicit available corpus reports missing input rather than inventing results.
- A named skill call means the host's skill-dispatch primitive (Claude: the Skill tool). An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Every step runs in the invoking session: this skill names no model tier and spawns no isolated agent. Delegated skills (`/user-uat`, and the vision judges behind its `--ui`) apply their own bindings. An unavailable required capability — including the `/user-uat` dispatch that `--exec` needs — returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Review UAT

Take a draft UAT script (manual smoke list, M-step in a plan, "things to test before ship" doc) and produce a tightened version where:

1. Every step is **unambiguous** — one valid reading, not three.
2. Every step has **explicit prerequisites** (what state the system must be in first).
3. Every step has **explicit pass criteria** (what the operator looks for, in observable terms).
4. Only the steps that **genuinely need a human** remain on the human's plate. Setup, teardown, and anything verifiable from logs / DB / HTTP gets split out so an agent can do it.

Iteration goal: a future operator (or a fresh Claude session) can execute the UAT cold, without asking clarifying questions or guessing.

---

## Invocation

```
/review-uat                          # ask user for the draft
/review-uat path/to/plan.md#step-21  # refine the M-step at this anchor
/review-uat --apply                  # after refinement, write the result back to the source doc
/review-uat --exec                   # after refinement, delegate execution of the refined script to /user-uat
/review-uat --exec --dry-run         # delegate with --dry-run: /user-uat prints what WOULD run; nothing executes
```

`--apply` and `--exec` are opt-in. Default behavior is read-only describe-only: produce the refined version in chat, do NOT modify the source and do NOT run anything.

**Allowed writes.** None by default. With `--apply`, exactly one: the refined UAT replaces the draft's steps — the replaceable span that Step 5.1 defines — inside its anchored source section, and every other byte of that file is kept. This skill writes no other file, never commits or pushes, and never runs a UAT step itself; with `--exec`, whatever runs is `/user-uat`'s, under `/user-uat`'s own gates.

---

## When to use

- A plan has a "Manual M*" step or "bundled UI smoke" handoff that reads as a terse bullet list.
- The user pastes a UAT script and asks "can you test this?" — the right first move is often to refine the script before running it.
- After a UAT pass that surfaced "wait, what did you mean by X?" — feed the ambiguity back into the doc.
- Before a release-gate handoff to a non-author operator.

Do **not** use to write a UAT from scratch — this skill refines existing drafts. For a brand-new UAT, start with the relevant `--ui` test pass conventions in the project's plan doc.

---

## Inputs

1. **The UAT draft** — paste, file path, or pointer to a section of a plan doc. Resolve it in this order:
   - A `path#anchor` argument: read exactly the section the anchor names — one heading, by its slug or text, or a plan entry such as `### Step 21:` or `### M4:`. The section runs to the line before the next heading of the same or higher level; a `#` line inside a fenced code block is not a heading. A bare path means the whole file is the draft.
   - A draft already in the conversation (e.g., the user pasted it as the trigger).
   - Otherwise end the turn with a one-line request for the draft (paste, path, or `path#anchor`); nothing else runs. This is the only intake ask.
   - If the path is unreadable, or the anchor matches no heading or more than one, stop: name the path/anchor and what was found, write nothing, run nothing.
2. **The feature under test** — one sentence so the skill can ground each step in real code (e.g., "Phase D Step 21 parent PIN gate"). Take it from the draft, its plan step, or the user's message; ask for it only alongside the draft ask. Steps it leaves ungroundable surface as **Blocker: cannot ground** (Step 1).
3. **Operator profile** — use an explicitly supplied profile; otherwise default to "fresh" and assume nothing. Never ask for it separately.

If the draft is supplied (in the conversation or through a path), skip the ask.

---

## Process

### Step 1 — Ground each step in primary source

For every line in the draft, before critiquing it, find the code / config / doc it implicitly references. Cite `file:line`. This is non-negotiable: a critique built on guesses is worse than the original draft.

If a step references behavior whose source you cannot locate, flag it as **Blocker: cannot ground**. The fix is usually a missing link or a stale reference, not a wording change.

### Step 2 — Classify each step on four axes

For each step, score:

| Axis | Question | Output |
|------|----------|--------|
| **Ambiguity** | How many valid readings does this have? | Count + list the readings |
| **Prereq completeness** | What state must hold before this step that isn't stated? | List missing prereqs |
| **Action — human or agent?** | Does the *doing* need a human? (button press, voice, hardware, out-of-band) | "human" / "agent" |
| **Verify — human, vision-judge, or agent?** | Does the *checking* need a human, or can a browser-driven vision-judge do it, or is it a machine probe? | "human" / "vision-judge" / "agent" / "split" |

**Action and Verify are separate decisions.** They almost always split differently. A step can have human action + agent verify (the most common shape). Pure-human verify is rare and should be defended: "why can't this be an HTTP probe / sqlite query / log grep — or, for a *rendered screen*, a `/judge-ui` vision check?" Reserve pure-human verify for motion, audio, and subjective feel.

**Action needs a human when it requires:**

- Real hardware input (mic, speaker, camera, physical button)
- Out-of-band action (second device, parent's phone, recovery procedure)
- A UI interaction the agent can't drive headlessly (or where Playwright would be more setup than the value justifies)

**Verify can be a VISION-JUDGE** (a browser-driven screenshot + vision model via `/judge-ui`, run by `/user-uat --ui`) **when it is:**

- A **rendered screen state** captured in a single frame — layout, a component present, heading/copy text, a list/table's contents, "the right screen showed, no error banner". Emit these as `Verify (visual — vision-judge)` (below) instead of punting to the human — always paired with the API/DB read-back that corroborates the pixels.

**Verify still needs a HUMAN when it requires:**

- **Motion / animation** ("did it flash?", "did the countdown tick?") — a screenshot is one frame, it can't see motion
- Auditory judgment (sfx fired, voice quality)
- Subjective UX (does this feel responsive? is this label clear?)
- Anything credentialed / physical / real-device a browser can't drive

**Verify does NOT need a human when it asks:**

- "Did the API return 200?" (curl + grep)
- "Does the DB row exist? With the right shape?" (sqlite query)
- "Is the file on disk? At the expected path? With the expected size/MIME?" (Read tool)
- "Did the log line appear?" (grep)
- "Does the WebSocket envelope arrive with the right fields?" (a small script)
- "Does the count of X equal Y after the action?" (sqlite COUNT)

When the action is a UI button-press but the *consequence* is recorded in the DB or surfaced via API, the verify is agent. The human's job is the click; the agent's job is the audit.

### Step 3 — Rewrite each step in the canonical format

```
### Step <N>: <one-line title>

**Setup (agent):**
- <command or action the agent runs to put the system in the required state>
- <command or action ...>
- **If the human's action will trigger a backend API call: include a direct probe of that endpoint here (before the human acts).** A 500/404/503 caught in Setup saves the operator from doing browser work that will just fail. Move the primary endpoint smoke-test from Verify into Setup for any step where the human drives a UI that calls the backend.

**Action (human):**
- <single, concrete thing the human does — only the irreducible part>

**Verify (agent):**
- <command + expected result, e.g., "curl /api/auth/parent/status → {pin_set: true, locked: false}">
- <sqlite query + expected row count, e.g., "SELECT count(*) FROM toys WHERE archived=0 → 1">
- <file check, e.g., "ls data/images/toys/ → exactly one .png file matching uuid pattern">
- <log grep, e.g., "grep 'pin_set' logs/backend.log → 1 INFO line, 0 WARNING">

**Verify (visual — vision-judge via `/judge-ui`):**
- <a rendered-state check a browser + vision model can judge in one frame, in observable terms — e.g., "PinSetup heading reads 'Set parent PIN' and two PIN input fields are visible" — PAIRED with the read-back that corroborates it (e.g., "and /api/auth/parent/status → pin_set:false")>
- Omit this block when there's no rendered-state check, or when the only visual checks are motion/audio/feel (those go to Verify (human)). A temporal claim such as "no login screen flashed first" belongs in Verify (human) under the existing motion classification; a single-frame `/judge-ui` check cannot prove it. Run static rendered-state checks via `/user-uat --ui`; on vision-judge uncertainty it falls back to a human ask.

**Verify (human):**
- <observation that genuinely requires eyes ON MOTION/AUDIO/FEEL — e.g., "countdown ticks once per second", "the chime sound fires", "the transition feels smooth">
- <auditory / motion / subjective check that a single screenshot can't settle ...>

**Fail signals (what to flag):**
- <what counts as a regression — e.g., "any flash of the login screen before setup", "countdown stops ticking">

**Source of truth:** <file:line> — link the code that defines the expected behavior. If the supplied project facts give you only a file and a function/section (no line number), write `<file>:<function-name>` or `<file>:<section-name>`; if even that is unavailable, write `<file> (line unknown)`. **Never** emit a bare filename, `TBD`, `the spec`, or a plan-level descriptor like `project-facts:bullet-N` — those are ungrounded and must instead be flagged as **Blocker: cannot ground** per Step 1.
```

If the agent setup or verify is non-trivial, the rewritten step may include short shell blocks. Keep them copy-pasteable AND executable by `/user-uat` (the `--exec` hand-off target — Step 5.5).

**Before writing any shell block, determine the target shell from the project's CLAUDE.md or AGENTS.md, or from the workspace instructions.** Shell syntax must match the runtime environment:
- **Windows / PowerShell (default in many workspaces):** `curl.exe` not `curl` (`curl` aliases to `Invoke-WebRequest` and rejects standard curl flags); backtick (`` ` ``) for line continuation; `$env:VAR` not `$VAR`; `NUL` not `/dev/null`; `ConvertFrom-Json` instead of `python -m json.tool` when piping JSON. **`&&` and `||` chain operators are parser errors in PowerShell 5.1** — split into separate commands or use `; if ($?) { ... }` for conditional chaining; never put multiple install/setup commands in one block with `&&`. For Python projects managed with `uv`: use `uv pip install` not bare `pip` — `pip` is typically not on PATH in uv environments. See `.claude/rules/windows-shell.md` for the full landmine list.
- **bash / POSIX:** standard syntax, but on Windows hosts `gh.exe` and other native tools may not resolve POSIX paths — write temp files under `$TEMP` or an absolute Windows path.

If the target shell is ambiguous, default to PowerShell-safe syntax (no bash-isms) and note the assumption explicitly. A shell block that fails on the first operator run is worse than a verbose one.

If a step has no human-verify (everything is machine-checkable), omit the **Verify (human)** block and shrink **Action (human)** to "do the thing, then say 'done'". If a step has no human-action either, the whole step is a candidate for moving out of the UAT into an integration test.

### Step 4 — Surface cross-step issues

Some problems are not per-step:

- **Ordering dependencies** that aren't stated (step 3 assumes step 2's state).
- **Implicit teardown** that wasn't done (rate limiter still locked from step 4 leaks into step 5).
- **Missing reset path** between repeats (operator can't easily re-run from clean).
- **Coverage gaps** — features in the spec that no step exercises (e.g., "refresh during lockout" wasn't covered but the spec explicitly says it should work).

List these under a separate "Cross-cutting findings" section, grouped by severity.

### Step 5 — Output

Produce these, in this order:

1. **Findings, grouped by severity** (always print all three tiers — empty tiers print "None"):
   - **Blocker** — operator would do the wrong thing, get stuck, or report a false pass/fail. Cannot ship the UAT as-is.
   - **Gap** — operator could probably guess right, but shouldn't have to. Tighten before next handoff.
   - **Minor** — cosmetic, low-stakes, or coverage nice-to-have.

   Step 4's **Cross-cutting findings**, when any exist, print inside Findings after the three tiers.
2. **Refined UAT** — the rewritten steps in the canonical format, in a fenced markdown block so the user can copy it back into the plan doc.
3. **Diff summary** — one line per original step: "Was: ... → Now: ..." with the most important change. A step that needed no change still gets its line, ending "→ Now: unchanged".

Re-running on an already-refined script changes only what is still ambiguous; when nothing changes, every diff line reads "unchanged" and `--apply` writes nothing.

### Step 5.1 — Write-back (if `--apply` was passed)

This is the only write the skill performs. Write only when every condition below holds; otherwise write nothing, keep the refined UAT in chat, and say which condition failed in one line:

- The draft came from a `path#anchor` source. A pasted draft or a bare path has no write target; the operator re-runs with an anchor.
- The anchored section neither is, lies inside, nor contains an M entry (an `M<N>:` or `Step M<N>:` heading) or a `## Manual UAT` block. That block is append-only and owned by `/build-phase`, and M entries' fields are read by build-phase re-runs and by plan scrapers; refine M entries in chat only.
- No clarifying question (Step 6) is open. If one is, the write waits for the answers.
- The draft's steps form one replaceable span (below).
- Re-read just before writing, with anchor resolution re-run under the same 0/>1-match stop as Inputs, the anchored section still matches the text that was refined. If it changed, report the conflict.

**Replaceable span.** The one contiguous run of section lines that the draft's steps were read from: each step's line with its sub-bullets, fenced blocks and tables, plus — on a re-run — each `UAT step <N>:` heading that an earlier write produced, whose block up to the next kept line holds only Step 3's labeled blocks. Everything else in the section stays byte-identical and must not fall inside the span: the section heading; every other nested heading; each metadata field line — a leading bold label that belongs to no draft step, such as `Problem`, `Type`, `Issue`, `Flags`, `Condition`, `Produces`, `Done when`, `Depends on`, `Status`, `Source step`, `Commands` (or `Commands to run`) or `What to look for` (or `What you're looking for`) — with its indented continuation lines; italic preambles; horizontal rules and footers; and any prose that is not a draft step. Hold when the draft sits inside a metadata field (for example an operator step's `**Problem:**`), spans more than one plan or UAT entry, is interleaved with kept lines, or cannot be separated with certainty. After the candidate span, scan to the anchored section boundary. Blank lines and a horizontal rule may trail the span; a heading at the same or shallower level than the written step headings ends the last written step safely. Any other kept field, deeper heading, prose or footer would be absorbed into the last written step, so hold before the first write.

**The write.** Replace exactly that span in place, located by its re-read text, with the refined UAT (the contents of Step 5's fenced block), and preserve every byte outside it, including line endings and any BOM. Two edits apply to headings in the written text, outside fenced code blocks only: every heading shifts by one offset so that the step headings sit at H5, or one level below the section heading when that is deeper; and each step heading `Step <N>: <title>` is written as `UAT step <N>: <title>`. The same `path#anchor` then still selects the whole refined UAT; the H5 level keeps the refined steps below scrapers that read only H2–H4 headings, and the `UAT step` label keeps them from reading as `Step <N>:` plan units at any heading level. Hold if any heading would pass H6. Report the file and changed line range. If the span already equals the text that would be written, write nothing and report "no change".

### Step 5.5 — Delegated execution (if `--exec` was passed)

Execution is [`/user-uat`](../user-uat/core.md)'s whole job — this skill owns refinement only, and keeps zero execution procedure of its own. After producing the Step 5 output (and any Step 5.1 write), hand the refined script off:

1. **What gets handed off:** the refined UAT from Step 5's fenced block. Invoke `/user-uat` with a named skill call on it — bare (user-uat's default source is the UAT block just produced in this conversation), or as `path#anchor` when Step 5.1 wrote it back to the source doc in this run (after a hold, bare). The hand-off line states how many Blockers and clarifying questions remain open. If `/user-uat` is unavailable on this host, stop with `required_tool_missing` naming it — never execute the steps here in its place.
2. **Flag pass-through** (map only flags both skills actually declare; invent none):
   - `--exec --dry-run` → `/user-uat --dry-run` (user-uat classifies + prints what WOULD run; nothing executes).
   - Refined script contains `Verify (visual — vision-judge)` blocks → add `--ui`, so those steps are vision-judged via `/judge-ui` instead of escalated.
   - `--deep` and `--yes-side-effects` are user-uat flags with no review-uat equivalent — never pass them implicitly; user-uat's own defaults stay in force (see [`/user-uat`](../user-uat/core.md)). An operator who wants them invokes `/user-uat` directly.
3. **What comes back:** user-uat's terse per-step report (`step → AUTO-PASS / AUTO-FAIL / ESCALATED → one-line evidence`) plus its "Needs you" section. Relay it verbatim — do not re-judge, re-run, or summarize away the evidence.

The execution procedure itself — tier partition, side-effect gating, mechanical auto-judging, stop-on-FAIL, escalation format — is owned by `/user-uat`; look there, not here.

### Step 6 — Clarifying-questions loop

After the output, check whether any findings need user input to resolve. Common cases:

- Genuine product decisions (does "wipe" mean PIN-row delete or full factory reset? — only the user can decide which one M2.5 should test).
- Ambiguous pass criteria with multiple defensible answers (does "expect setup screen" mean "renders eventually" or "renders within 200ms with no flash"?).
- Missing context that only the user can provide (which environments / browsers / accounts).

If there are clarifying questions:

1. End with a numbered list under a **Clarifying questions** heading.
2. End the run there. The output above is complete; only an `--apply` write-back waits on the answers.
3. After receiving answers, update the refined UAT to absorb them. If `--apply` was set, also write the result back under Step 5.1's conditions and report which file:line ranges changed.

If there are NO clarifying questions:

- End with: "No clarifying questions — refined UAT above is final. Run with `--apply` to write back to <source path>."
- `<source path>` is the actual source path from the invocation, or "the source draft" when the draft was pasted with no path.
- If Step 5.1 wrote the file, end instead with: "No clarifying questions — refined UAT above is final. Written back to <source path>:<first line>-<last line>."

---

## Heuristics: common ambiguities to look for

These are the patterns that recur. Treat them as a checklist when scanning a draft.

| Pattern | Example | Tighten by |
|---------|---------|-----------|
| **Verb without object** | "wipe", "reset", "clear" | Specify the exact command / scope |
| **State noun without check** | "fresh boot", "clean state" | Specify what artifacts must / must not exist |
| **"Expect X"** | "expect setup screen" | Specify the observable: heading text, test id, URL, accessible role |
| **Loose number** | "5 wrong PINs" | Specify pacing (how fast?), order (matters or not?), and whether the 5th attempt itself is the lockout trigger |
| **Time-based assertion** | "15-min lock with countdown" | Specify what ticks, at what cadence, and how the operator confirms it (clock-watch? screenshot? log timestamp?) |
| **Implicit restart** | "first boot after wipe" | State the restart explicitly; call out which in-process state resets with it |
| **Implicit network / fixture state** | "type a PIN" | Note that the backend must be reachable, the frontend dev server must be up, the proxy must be wired |
| **Verification on faith** | "PIN survives refresh" | Specify the second observation (status probe returns `pin_set: true`) AND the first (token gone from store) |
| **Off-the-happy-path silence** | spec mentions "lock takes precedence" but UAT doesn't test it | Add the negative-path step explicitly |
| **Shell-platform mismatch** | `curl -s -o /dev/null -w "%{http_code}"` in a PowerShell context | Identify target shell first; on Windows/PS use `curl.exe` not `curl`; verify flags are valid for that shell's native tools |
| **`&&` in PowerShell 5.1** | `pip install A && pip install B` | `&&` is a parser error in PS 5.1; put each command in its own fenced block; never chain installs with `&&` |
| **Wrong package manager** | `pip install X` in a `uv`-managed project | `pip` is typically not on PATH; use `uv pip install X` instead |

---

## Principles

- **Refine, don't expand.** A tighter 4-step UAT is better than a fuzzy 12-step one. If the original under-specifies, fix the wording — don't bolt on extra checks the original didn't intend.
- **Cite the spec.** Every pass criterion should trace to a line in the plan, the code, or the spec. If it doesn't, the criterion may be invented.
- **Agent-run setup is free.** Use it generously. The human's time is the scarce resource; offload everything mechanical.
- **The agent does the verification too.** Setup is the obvious agent-doable part; verification is the less obvious one. If the spec says "X exists in the DB", the agent reads the DB. The human's verify list should shrink to things that genuinely require eyes on a screen.
- **Pass criteria are observations, not interpretations.** "Setup screen renders" is an interpretation. "Heading reads 'Set parent PIN' and two PIN input fields are visible" is an observation.
- **Negative-path coverage matters.** A UAT that only tests the happy path will miss invariants like "lock takes precedence over correct PIN."
- **Fresh-eyes test.** When done, ask yourself: could a Claude session with no prior context execute this? If not, keep tightening.

---

## What NOT to do

- **Do not run the UAT yourself — ever.** Default is refinement only. With `--exec`, execution happens by delegating the refined script to `/user-uat` (Step 5.5); this skill never executes Setup/Verify blocks inline and never runs human-action steps for the operator.
- **Do not write a UAT from scratch.** Refuse and point at the relevant `--ui` test conventions or existing M-steps for patterns. Exception: when the "draft" is a set of scattered references inside other steps' status notes, gathering those into one block is consolidation, not invention — but label the output as "drafted + refined from scattered status notes" rather than pretending it was pure refinement.
- **Do not modify the source plan doc** unless the user passed `--apply`, and then only under Step 5.1's conditions. Default is propose-in-chat only.
- **Do not invent pass criteria.** If the spec doesn't define what "good" looks like, that's a clarifying question for the user — not a guess.
- **Do not delete coverage.** If the original draft tests something the refinement can't ground, flag it as a Blocker, don't drop it.
- **Do not mass-rewrite tone or voice.** Tighten ambiguity; preserve the author's framing.
- **Do not punt verification to the human when an agent can do it.** "Check the row exists", "confirm the file is on disk", "verify the API returned 200" are HTTP probes / sqlite queries / Read-tool calls — not human tasks. Reserve human-verify for visual / auditory / subjective judgment. Default verify is agent; human-verify needs justification.

---

## Interaction with other skills

- **`/user-uat` + `/judge-ui`** — the executors for what this skill writes: review-uat REFINES, user-uat EXECUTES, and `--exec` is refine-then-delegate (Step 5.5 invokes `/user-uat` on the refined script with a named skill call). `review-uat` *emits* the `Verify (visual — vision-judge)` blocks; `/user-uat --ui` *runs* them via the `/judge-ui` engine (drives the screen, vision-judges it, cross-checks a read-back), reserving `Verify (human)` for motion / audio / feel. Transition-shaped motion stays `Verify (human)` here; when `--ui` is passed, `/user-uat`'s own classification may still route such a step to `/judge-motion` (Claude only). Refine here → execute there.
- **`/plan-wrap`** — same family (self-sufficiency check), but for plans, not UATs. Use both: plan-wrap on the plan, review-uat on its M-steps.
- **`/user-draft`** — overlapping ambiguity-hunting discipline; the heuristics table here borrows from user-draft's "weak verbs" finding.
- **`/plan-review`** — the build-step counterpart. plan-review covers what gets built; review-uat covers what humans verify after build.
- **`/repo-update`** — if the refined UAT gets applied (`--apply`), repo-update is the natural follow-up to commit + push the doc change; this skill never commits.
- **`/user-walkthrough`, `/user-shakedown`** — the sibling operator-acceptance modes. `/review-uat` REFINES a fuzzy script; `/user-walkthrough` lets the operator DRIVE exploration of a fresh build (agent answers from source, fixes small, logs big); `/user-shakedown` AUTONOMOUSLY CLOSES the resulting ledger to zero open items. Refine a script with review-uat; poke a build with the walkthrough/shakedown pair.

## Maintenance

The source-only corpus contains four unmeasured assertions, two scenarios, and four golden
fixtures registered by one manifest. It covers only the selected `--apply` ownership, span,
stale-byte and idempotency boundaries and the `--exec` named-dispatch, flag and missing-capability
boundaries. Every result begins `null`; source review is not a grader result. This compact corpus
does not inherit or replace the historical 31-file evaluator and does not qualify unrelated
refinement behavior. Because distributions omit it, an installed evaluation needs an explicit
available `evals_dir`; missing input halts that evaluation without affecting ordinary refinement.
