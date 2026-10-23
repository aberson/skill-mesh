# NOTE: This is the canonical provider-independent contract. Every provider wrapper must load it in full.

## Provider-neutral host abstractions

- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`, except where **Model roles** names an explicit model. An unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- judge-ui ships no package scripts. Flow specs, adapter commands, capture commands and read-back calls resolve from the target project and its adapter.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# UI Judge

> **Judging doctrine:** invariants, archetypes, and the judge↔advisor spectrum live in [`_shared/judge-core.md`](../../_shared/judge-core.md) — this skill instantiates them (it is the §10 reference implementation for separate-vision-judge + read-back + escalate). Its calibration gate applies judge-core §7 and the workspace measurement-validity rule.

The generic engine for the **visual tier** of UAT. It drives a real browser through a flow,
captures a screenshot at each stage, and dispatches an **independent vision-judge sub-agent**
that views the pixels, cross-checks them against a structured read-back (API JSON / DB query),
and returns a per-stage verdict with evidence.

The point: "did the screen render correctly?" has always been a human's job. A browser driver
plus a vision model can now *do* most of it — but only safely if the judgment is disciplined.
This skill is that discipline. It is **project-agnostic**: everything project-specific (how to
start the app, how to reach an authed state, which testids to click) comes from a **project
adapter** (e.g. toybox's `/uat-ui`). Without an adapter it runs an inline flow spec you supply.

## When to use / not

- **Use:** a UI flow needs driving + visual judgment — a parent dashboard renders a list, a
  wizard advances through screens, a form's result must look right. Or `/user-uat --ui` routed a
  visual-tier step here. Or a project adapter calls you with a named flow.
- **Don't use** for things a still frame can't judge: **animation/motion, audio/sfx, real-device
  input, or subjective "does it feel right"** (a screenshot is one frame; it cannot see a
  countdown tick or hear a sound). Motion/transition review (route change, modal open/close, … —
  full list: `/judge-motion`'s When-to-use) routes to `/judge-motion`; audio,
  real-device input, and feel stay human. Don't use it to *refine* a fuzzy UAT (that is
  `/review-uat`) or to run shell-only checks (that is `/user-uat`'s mechanical tier).

## Invocation

```text
/judge-ui --adapter toybox --flow room-import   # run a named flow from a project adapter
/judge-ui <path-to-flow-spec>                    # run an inline flow spec (no adapter)
/judge-ui --adapter toybox --flow room-import --dry-run   # print the plan + the stages; drive nothing
```

Bare `/judge-ui`, or `--adapter` without `--flow`, prints usage (plus adapter flow names when
available), drives nothing, writes nothing, and returns no verdict. `--dry-run` prints the
resolved plan, stages, paths, judge readiness and calibration readiness; it also drives nothing,
writes nothing, and creates no run directory.

## The flow-spec contract (what a flow must provide)

A flow is the parametrized input the engine drives. A project adapter supplies the first three;
the caller or the adapter supplies the rest.

1. **Bring-up** — how to get the app running + reachable: start command(s), a readiness probe,
   and the base URL. Skipped if the app is already up. *Usually project-specific → adapter.*
2. **Reach state** — how to get from cold to the flow's starting UI state: auth (login / PIN),
   seed fixtures, feature-flag values. *Usually project-specific → adapter.*
3. **Read-back handle** — how to read the ground truth out of band (an authed API call, a DB
   query) so the judge can cross-check pixels against data. *Adapter provides the auth.*
4. **Stages** — an ordered list. Each stage = an **action** (navigate / click / fill), a
   **screenshot** target path, optional **mechanical DOM asserts** (testid present, heading
   text, row count, URL), and a **required read-back** call.
   API/DB structured read-back is MANDATORY for every stage that produces a PASS verdict.
   A stage cannot be marked PASS without cross-checking screenshot evidence against the
   structured read-back. This is non-relaxable per judge-core §4.
5. **Rubric** — per-stage natural-language pass criteria for the vision judge, in *observable*
   terms ("review table shows 7 rows; first row name is editable; a Create button is present").
   Borrow these verbatim from a `Verify (visual — vision-judge)` block if `/review-uat` produced one.
6. **Calibration anchors** — frozen pre-graded inputs for the vision judge: at least one
   known-good screenshot/read-back/rubric tuple (expected `PASS`) and one known-garbage tuple
   (expected not-PASS). Record each fixture path and SHA-256; never regenerate anchors during a
   run. The caller or adapter supplies them. Their absence does not block driving, but makes the
   instrument uncalibrated and therefore unable to return `VERDICT: PASS`.

## Model roles

- **Driver** — the invoking session performs bring-up, flow actions, mechanical checks,
  read-back calls, deterministic reduction and verdict-doc assembly. It does not judge pixels.
- **Vision judge** — one fresh-context, image-capable dispatch per run. Fresh isolation and the
  child's ability to open the supplied image files are separate required capabilities and must
  be proven by the current host. Claude requests `opus`; GPT and native Codex request
  `gpt-5.6-sol`. Select the model explicitly where the host supports selection. There is no
  single-context, API, router or cross-cloud fallback.
- **Judge identity record** — record requested model; selection (`explicit` or
  `not selectable (inherited)`); runtime-reported model and its source, or `not reported`; and
  match (`matches`, `differs`, or `not reported`). A judge's own prose is not runtime evidence.
  `opus` matches a reported `claude-opus-*`; `gpt-5.6-sol` matches only itself.
- A judge gates only when it is not local, offloaded or weaker-tier; its reported model does not
  differ; and either selection was explicit or the reported model matches. Otherwise its result
  is advisory and cannot resolve the run to PASS. The vision result is still only the visual
  result: `/user-uat --ui` owns its separate fresh strong-final gate before `AUTO-PASS`.

## The run loop

Before step 1, check both vision-judge capabilities. `--dry-run` reports that check without
dispatching. A known missing capability halts before bring-up with `required_tool_missing`,
names the failed isolation or image capability and the blocked step-3 dispatch, writes no run
artifacts and returns no verdict. An unproven required capability is unavailable for this run;
report that actual host evidence state without turning it into a provider-wide claim.

1. **Ensure the app is up.** Run the adapter's bring-up (or verify an already-running instance
   with the readiness probe). For Windows / port-collision / parallel-session hazards, defer to
   the adapter — it owns the safe bring-up + teardown.
2. **Drive the flow.** Prefer the adapter's parametrized Playwright spec so DOM asserts and
   screenshots share one pass. Run mechanical DOM/API asserts first at each stage, then capture
   to the run's stage path and perform the required read-back. A mechanical failure stops the
   flow and is a product FAIL without a vision call. A missing, blank or unreadable screenshot,
   or a read-back error, empty payload or fallback payload, is a **capture/instrument failure**:
   stop and cite it distinctly rather than labeling it a product defect.
3. **Dispatch the vision judge.** Insert the calibration anchors among the real stages at random
   under neutral IDs; only the driver retains the anchor map and expected labels. Pass each
   screenshot file, read-back JSON, rubric and flow intent, but no producer identity, driver
   assessment or expected anchor label. The fresh judge must open every image file itself; DOM
   text, accessibility trees and driver narration are not pixel evidence. For every ID it returns
   exactly one structured record:
   `verdict` (`PASS` / `FAIL` / `UNCERTAIN`), `readback_agrees` (`yes` / `no` / `unknown`), and
   non-empty `evidence` naming what was visible and the read-back value compared. `PASS` means
   every rubric criterion is visibly met and `readback_agrees` is `yes`. A pixel/read-back
   disagreement is never PASS; return `FAIL` or `UNCERTAIN` with the discrepancy. If a capability
   that was ready at preflight fails at dispatch, preserve the actual host error and continue to
   steps 4–5 with missing records normalized to `UNCERTAIN`; never substitute another provider.
4. **Calibrate and reduce** with this fixed driver-side rule; no LLM performs aggregation.
   First validate the raw response by neutral ID. A required record is valid only when that ID
   occurs exactly once, the record parses, both enums are allowed, evidence is non-empty, and a
   `PASS` has `readback_agrees: yes`. Retain this validity bit beside the normalized verdict;
   normalization never repairs an invalid record. Normalize every invalid record and every valid
   `FAIL` with `readback_agrees: unknown` to `UNCERTAIN`. Other valid records retain their verdict.
   - Calibration succeeds only when every required anchor record is valid and evidenced, every
     known-good anchor normalizes to PASS, and every known-garbage anchor normalizes to not-PASS.
     Thus a valid evidenced negative `FAIL` or `UNCERTAIN` can demonstrate abstention, while a
     missing, duplicate, malformed, invalid-enum or evidence-free result cannot. Any supplied
     anchor set that fails these conditions → `calibration failed`; absent input anchors →
     `uncalibrated`.
   - Any mechanical product failure → **FAIL**.
   - Any capture/instrument failure → **FAIL**, explicitly classified as instrument failure.
   - Otherwise, an uncalibrated or failed calibration, a non-gating judge, or a missing judge
     dispatch → **ESCALATE** with the judge observations treated as advisory.
   - For a calibrated gating result, first retain a normalized line for every real stage and a
     one-line human ask for every `readback_agrees: no` or normalized `UNCERTAIN`; a later overall
     precedence decision never discards those stage details or asks.
   - Then reduce all real stages with this complete precedence: any valid evidenced `FAIL` with
     `readback_agrees: yes` → overall **FAIL**; otherwise any `readback_agrees: no` or normalized
     `UNCERTAIN` → overall **ESCALATE**; otherwise every stage is `PASS` with agreement `yes` →
     overall **PASS**. In particular, valid `FAIL`/`unknown` normalizes to `UNCERTAIN` and
     escalates. A mixed corroborated FAIL plus a mismatch or uncertainty is overall FAIL while
     preserving the mismatch/uncertainty and its human ask. This matches `/user-uat`'s
     state-mismatch rule and never fabricates a PASS.
5. **Write the verdict doc** (the durable artifact) and return a structured result to the
   caller. Doc structure — **all six sections always present, even on an early-exit run**:
   scope, environment, per-stage "what the judge saw" (legible observations, not vibes), the
   read-back summary, findings, verdict. Environment records the app/base URL, judge identity
   record and gating state, anchor paths/hashes, and calibration outcomes. On a fail-fast (a
   mechanical or capture failure that never reached the vision step), still emit every section —
   mark the unreached ones explicitly
   ("what the judge saw: not invoked — mechanical gate failed at <stage>"; "read-back: not
   reached — flow stopped") rather than dropping them, and capture a screenshot of the failing
   state to cite as evidence unless capture itself failed. **Last line is exactly
   `VERDICT: PASS` / `VERDICT: FAIL` / `VERDICT: ESCALATE`.**

## Outputs, writes and reruns

- Return the overall verdict, verdict-doc path, calibration state, one normalized line per real
  stage (`<stage> → PASS | FAIL | UNCERTAIN | not reached → <screenshot> + <read-back>`), and a
  one-line ask for every escalation.
- Unless the adapter or caller names a project-specific destination, write only to the target
  project's `.judge-ui/<run-id>/`, where `<run-id>` is
  `YYYYMMDD-HHMMSS-<flow-slug>` in UTC. Store `stages/<stage>.png` and `verdict.md`. Create the
  directory exclusively; on collision try `-2`, `-3`, and so on. Never overwrite a prior run.
  judge-ui does not edit `.gitignore`; the project adapter owns that entry.
- Flow actions remain subject to `/user-uat`'s side-effect gate. Each invocation is single-shot;
  a rerun creates a new run and does not resume or reuse verdict state.

## The honesty invariants (do not skip — these are why it's safe)

A vision-judge is an agent grading an agent-rendered surface — the same trap operator UAT
exists to prevent (agents grading agent work codify regressions: toybox G2 / the audit-wire-
shape rule). These six rules keep it honest:

1. **Read-back cross-check is mandatory.** The judge may not PASS on pixels alone — every PASS
   must be corroborated by the API/DB read-back. A pretty screen over a wrong DB is a
   contradiction and cannot PASS; the reducer escalates it under the state-mismatch rule.
2. **Low confidence → Human, not PASS.** Uncertainty degrades to escalation. The engine's job is
   to *remove the easy visual checks from the human's plate*, not to fabricate confidence.
3. **Mechanical asserts gate the judge.** Deterministic DOM/API checks run first and fail fast;
   the vision call only judges what they couldn't.
4. **The judge is a separate sub-agent.** Independent eyes. The orchestrator that drove the
   browser does not also render the verdict.
5. **Evidence on every verdict.** Each PASS/FAIL cites the screenshot path *and* the read-back
   value. A verdict with no evidence is a defect (inherited from `/user-uat`).
6. **Calibration gates trust.** A visual PASS requires both anchors to discriminate in the same
   dispatch from a gating judge. An uncalibrated, fallback or unverified instrument escalates.

Side-effecting flows (form submits, real writes, sends) inherit `/user-uat`'s safety gate: tag
them side-effectful, confirm before running, prefer an isolated fixture/DB. The adapter should
run against an isolated store, never the operator's real data.

## Reuse — don't reimplement

`/build-step --ui` owns optional app-lifecycle and capture primitives. When its
`scripts/capture_evidence.py` is present in the host, reuse its headless capture,
Windows-aware readiness polling and teardown rather than rebuilding those utilities. It is not
part of every generated profile; absence is not an error, and the adapter's Playwright/capture
path remains authoritative. What build-step **lacks** — and what this skill adds — is the
*judgment*: a structured PASS/FAIL verdict against an acceptance rubric.
Capture there; judge here.

## Relationship to other skills

- **`/user-uat`** — its **Visual tier** (`--ui`) delegates single-frame states here. `user-uat`
  owns the partition, separate strong-final gate and terse report; `judge-ui` owns the drive and
  visual verdict. ESCALATE feeds its `Needs you` section.
- **`/judge-motion`** — the motion/transition sibling: it owns the temporal residual this
  skill's "Don't use" clause disclaims; single-frame static states stay here.
- **`/review-uat`** — emits the `Verify (visual — vision-judge)` blocks this skill consumes;
  its rubric *is* the per-stage pass criteria. Refine → judge.
- **`/build-step --ui`** — the capture/lifecycle primitives to reuse (above).
- **Project adapters** (e.g. toybox `/uat-ui`) — supply bring-up + auth + the flow library;
  this engine is the project-agnostic half they call.
