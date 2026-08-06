# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/tier-escalate/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. A fresh-context task invocation or workflow means an isolated host action with the requested capability tier. Provider wrappers map these roles to their native APIs.
- Tier names in this document are resolved to provider model IDs at runtime via `config/model-tier-map.json`. Do not hard-code provider-specific model strings. An unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# tier-escalate

Reads every `SKILL.md` under your `.claude/skills/`, classifies each skill's LLM-bearing roles with a fixed taxonomy, then applies the up-direction escalation rule to decide which (and only which) skills contain a phase worth escalating a *session* to the **fable-tier** (one tier above the opus-tier default). It emits one artifact: a human-readable **tier escalation map** (markdown, grouped by verdict) that tells the operator exactly when the fable-tier buys quality and when it only multiplies cost.

This is the UP-direction sibling of `tier-offload` (which finds the slices safe to route *down* to a cheap local model). It is **discovery + map only** — it identifies the escalation-worthy phases and their triggers; actually switching a session to the fable-tier stays a per-session operator action afterward. It never edits a skill or CLAUDE.md.

## When to use

- You want to know which of *your own* skills have a phase where escalating the session to the fable-tier buys real quality — and which would just double cost for the same output.
- You want to regenerate the escalation map after adding or changing skills (the escalation surface drifts as skills evolve).
- You want the CLAUDE.md model-paragraph escalation list regenerated from the current skill set as a paste-ready block, instead of hand-maintaining it and letting it drift.

## Background — the up verdict rule (the fable-tier signature)

The escalation's one governing rule (the operator's tiering policy, encoded from the 2026-07-09 42-skill scan): **escalate a session to the fable-tier only for a single load-bearing seed-artifact — a phase whose one output is the deliverable's quality ceiling AND where a diversity committee (parallel reviewers/iterations) cannot substitute for a stronger single reasoner.** The three canonical seed-artifact shapes: greenfield architecture authoring (`plan-init`), hard root-cause diagnosis (`user-debug`), deep multi-source cited synthesis (`deep-research`). Everywhere reviewer/iteration DIVERSITY carries quality (the review-*, build-*, skill-* pipelines), opus-tier orchestration + sonnet-tier fan-out stays — a stronger model there adds cost, not quality.

The policy owner is the workspace model-tiering rule (`.claude/references/model-tiering.md`; the `CLAUDE.md` `## Environment` model paragraph is its stub), with long-form provenance in the `user-model-preference` memory. This skill *derives* a map from the current skill set against that policy; it never becomes the policy.

### Taxonomy + classification protocol — shared reference

Classification follows `../../references/skill-role-taxonomy.md`: its **§1 taxonomy** (the seven tags — ORCH / AUTHOR / PLAN / JUDGES / GATE / MECH / SOLO — plus the tag boundaries), its **§2 fan-out classification protocol**, and its **§3 output shape**. That reference is direction-neutral; this skill layers the up-direction (escalation) rules on top: the four up-corrections below and the FABLE-SEED / STAY / CONDITIONAL verdict columns added in Phase 2.

### The four up-corrections (apply them — a naive "hard skill → stronger model" read is wrong)

1. **Fan-out arms are NEVER fable-tier.** Arms use the sonnet-tier; diversity beats per-arm strength. A JUDGES array, a reviewer committee, or parallel dev retries get their quality from *independent perspectives* — escalating the arms multiplies cost with no ceiling gain. Escalation applies to a solo seed phase, never to an array. (A **solo named-trigger diagnosis arm** — one read-only sub-agent, one sanctioned trigger, at most one spawn per run, e.g. build-step's Step 9 phone-a-friend arm — is a sanctioned seed-artifact shape under the workspace model-tiering rule, not a fan-out arm; arrays remain never-fable.)
2. **Do NOT fan out single-mind synthesis to get it "for free".** A synthesis phase that must hold one coherent voice/judgment (e.g. `memory-distill`'s final latent-principle consolidation step) is a SOLO/GATE-shaped *candidate for escalation*, not for parallelization. Splitting it across arms destroys the coherence that made it valuable; the correct question is "does this one pass warrant a stronger reasoner?", never "can we committee it?".
3. **Conditional escalations must NAME THEIR TRIGGER.** An escalation that applies only sometimes (e.g. a large cross-cutting `plan-feature`, a deep-conflict 3+ `plan-merge`, a high-stakes substrate/schema `review-deep`) is only actionable if the map states the concrete trigger condition. "Escalate when it feels big" is not a verdict — a CONDITIONAL row without a stated trigger is incomplete and must be resolved to FABLE-SEED, STAY, or a named trigger.
4. **Session escalation cascades into unpinned arms — check the dispatch layer.** Invoking the host's model-switch primitive or restarting with the fable-tier configured changes the model for EVERY fresh-context task/workflow arm a skill dispatches unless the skill pins its arms explicitly to a tier. A FABLE-SEED verdict for a skill that fans out is only actionable if its arms are pinned to the sonnet-tier; otherwise the map row must carry an **`arms-unpinned`** flag and its how-to-apply becomes "pin the arms first, then escalate." (Evidence 2026-07-12: `/deep-research` on a fable-tier session ran 104/104 workflow tasks on the fable-tier — ~101 were fan-out arms; ~5x cost plus a session-limit blowout mid-run. Fixed by the owned override `deep-research-pinned` (canonical `dev/.claude/workflows/deep-research-pinned.js`, deployed per-project into `<project>/.claude/workflows/`), which pins search/fetch/verify arms to the sonnet-tier and lets only scope+synthesize inherit. Note the distinct name: built-ins silently shadow same-named local workflows, so a local `deep-research.js` would never resolve.)

## Phase 1 — Bootstrap: discover the skill set

Parse args. Resolve `--skills-dir`:
- If given, resolve to an absolute path.
- Default: walk up from cwd to the innermost ancestor containing a `.claude/skills/` directory; use that.

Enumerate the skill set per the shared reference's §2 steps 1–2 (Glob discovery, skip non-skill entries, `ls` the matched filenames before quoting any into a sub-agent prompt).

Resolve `--out-dir` (default `./tier-escalate-out`). Create it if absent (PowerShell: `New-Item -ItemType Directory -Force <path>`) — skip creation under `--dry-run`.

Print the discovery line before analysis: the resolved skills dir, the count of skills found, and the out dir.

## Phase 2 — Parallel classification (read-only fresh-context fan-out)

Run the shared reference's **§2 fan-out classification protocol** exactly (read-only fresh-context task invocations using the sonnet tier (resolve via model-tier-map.json) per the reference §2, 6–8 skills per batch, all of a batch's tasks dispatched in one message, the §1 taxonomy verbatim in every task's prompt, read-only/classify-only discipline), with these up-direction additions:

- Each agent's prompt must include — besides the reference's §1 taxonomy verbatim, per the reference's own protocol — the **four up-corrections** verbatim (above). Every agent must apply the SAME rules, or the map drifts per-batch.
- Each agent extends the reference's §3 output shape with the up-direction verdict columns, returning per skill: `Skill | Roles (tags) | Verdict (FABLE-SEED / STAY / CONDITIONAL) | Seed-artifact phase (if FABLE-SEED) | Trigger (if CONDITIONAL) | Arms pinned? (yes / no / n-a) | Note`, where **Verdict** is:
  - **FABLE-SEED** — the skill contains a single load-bearing seed-artifact phase (SOLO / AUTHOR / PLAN / GATE-shaped, never a JUDGES array) whose one output is the deliverable's quality ceiling AND where a diversity committee cannot substitute for a stronger single reasoner. Name the specific phase (e.g. "greenfield plan.md authoring pass", "Step 1 root-cause diagnosis").
  - **STAY** — quality is carried by diversity/iteration (JUDGES arrays, multi-lens reviewers, dev retries) or the work is templated/mechanical; opus-tier orchestration + sonnet-tier fan-out. A stronger model adds cost, not quality.
  - **CONDITIONAL** — the seed-artifact shape appears only under a nameable condition. State the concrete trigger (up-correction 3); a trigger-less CONDITIONAL is invalid.
- For each FABLE-SEED verdict, require the specific seed-artifact phase; for each CONDITIONAL, require the concrete trigger.
- For each FABLE-SEED or CONDITIONAL verdict, additionally require the **arms-pinned check** (up-correction 4): does the skill dispatch subagents/workflow arms at all, and if so are those arms explicitly `model:`-pinned in the skill/workflow source? `yes` = pinned, `no` = dispatches unpinned arms (flag `arms-unpinned`), `n-a` = the skill dispatches no arms. STAY rows may leave this column `n-a`.

Collect every agent's table before Phase 3.

## Phase 3 — Synthesize the tier escalation map

Merge all agent tables into one map, grouped by verdict:

1. **The fable-tier-worthy table** — FABLE-SEED skills only: `Skill | Seed-artifact phase | Why a committee can't substitute | Arms pinned? | How to apply`. The how-to-apply column is the same session pattern: **invoke the host's model-switch primitive or restart with the fable-tier configured, run the seed phase, then return to the default tier** — EXCEPT for `arms-unpinned` rows, where it becomes **pin the skill's fan-out arms to the sonnet-tier first, then escalate**; a session escalation on an unpinned fan-out multiplies cost across every arm (up-correction 4). This is the load-bearing output.
2. **Conditional escalations** — `Skill | Trigger | Phase | How to apply`. Each row's trigger must be concrete enough to check at session start (up-correction 3). Note where the escalation is a flag rather than a session switch (e.g. `review-deep --model-override bugs=fable`) — and verify the target skill's flag actually accepts that tier before emitting it as the how-to-apply; if it doesn't yet (review-deep's tier enum is `haiku|sonnet|opus` today, #289), annotate the row and give "invoke the host's model-switch primitive or restart with the fable-tier configured" as the working fallback.
3. **Everything else stays opus-tier + sonnet-tier** — bulleted list of STAY skills, each with its one-line reason (which diversity mechanism or mechanical shape carries its quality).

Optionally append a **paste-ready CLAUDE.md section**: a regenerated version of the model paragraph's escalation list (the FABLE-SEED trio + the conditional triggers), clearly marked as PASTE-READY — this skill only *regenerates* the block; it is never auto-applied to CLAUDE.md. The operator diffs it against the live paragraph and pastes if it has drifted.

Write the map to `<out-dir>/escalation-map.md`. Lead it with a one-paragraph summary: N skills scanned, F fable-tier seed phases found, C conditional escalations, and the date. Skip the write under `--dry-run` (print the map body to the report instead).

## Phase 4 — Report

Print a summary (do not truncate):

```text
tier-escalate — <skills-dir>

Scanned:       N skills
FABLE-SEED:    F skills (each with its named seed-artifact phase)
CONDITIONAL:   C skills (each with its named trigger)
STAY:          S skills (opus-tier orchestration + sonnet-tier fan-out)

Artifact:
  escalation-map.md — <out-dir>/escalation-map.md

Next (per-session, NOT done by this skill):
  For a FABLE-SEED skill: invoke the host's model-switch primitive or restart with the
  fable-tier configured, run the seed phase, then return to the pinned default tier.
  For a CONDITIONAL skill: escalate only when its named trigger holds. Practical
  constraints (retention and model-pin resets):
  see the workspace model-tiering rule (.claude/references/model-tiering.md; the CLAUDE.md
  ## Environment model paragraph is its stub) — the policy owner this map is derived from.
```

End with the exact standalone line:

`tier-escalate wrote the escalation map — switching a session to the fable-tier stays a per-session operator action via the host's model-switch primitive or a restart with the target tier configured (it was NOT auto-applied).`

## Differences from tier-offload (deliberate asymmetries)

- **No config file is emitted.** tier-offload writes a machine-loadable switchboard config because a client consumes it; the escalation map has no machine consumer — it is for the operator, so the markdown map is the whole artifact.
- **No safety gate / gate-precondition concept.** Routing *down* has a correctness failure mode (a weak model on a gate), so tier-offload carries a hard invariant. Escalating *up* to the fable-tier is never unsafe, only wasteful — the failure mode is cost, not correctness — so there is no gate analogue; the up-corrections guard against waste, not danger.
- **The practical constraint worth noting:** The provider model resolved for the fable-tier may have retention requirements, and auto-updates can silently reset a model-tier pin. The workspace model-tiering rule (`.claude/references/model-tiering.md`) is the policy owner for these (the `CLAUDE.md` model paragraph is its stub) — cite it in the map rather than restating it wholesale.

## Constraints

- **Discovery + map only. Never auto-apply.** This skill never edits a `SKILL.md`, never edits CLAUDE.md, and never changes any model setting. It writes the map; the operator escalates per session. The paste-ready CLAUDE.md section is regenerated output, never applied.
- **Use read-only fresh-context task invocations for classification.** They cannot edit or write — the safe substrate for reading someone's skills. Use the sonnet tier (resolve via model-tier-map.json).
- **Apply the four up-corrections.** Fan-out arms are never fable-tier; single-mind synthesis is a candidate for escalation, not parallelization; conditional escalations must name their trigger; session escalation cascades into unpinned arms — flag `arms-unpinned` and require pinning before escalation.
- **Autonomous — no mid-run (y/n) prompts.** Run bare = scan + report + write the map. `--dry-run` prints the report and writes nothing.
- Do not commit. Leave the map in the out dir for the operator.
