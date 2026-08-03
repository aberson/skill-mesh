# Provider Expansion Plan — Gemini + Local Lanes (Phase 8, Steps 51-61)

**Status:** PLANNED. **Prerequisite:** Phase 7 (host-native discovery & consumer cutover,
`documentation/host-native-discovery-cutover-plan.md`) must be DONE through its final cutover
step before `/build-phase` runs this plan. Step numbering continues from Phase 7's highest step
— **currently 50** after the 2026-08-03 re-scope for the proven GPT discovery retarget. Phase 7
has grown twice (42-48, then 42-50); **before `/repo-sync` mints issues for this plan, re-verify
Phase 7's final highest step number and renumber this plan upward if Phase 7 grew past 50**
(step-number collisions across sibling plans corrupt issue bodies).

This plan is self-contained: every design decision it depends on is restated in §6. It was
ratified from an operator-side MCP/provider investigation (private workspace, 2026-08-02/03);
no external document is required to execute it.

---

## 1. What This Feature Does

Extends the provider-neutral v1.3.0 router from 2.5 working model families (Claude host-native,
GPT via Copilot/OpenAI, local as a disconnected stub) to 4: **Gemini** via a native
`generateContent` REST transport (explicit-invoke-only, proxy-first skill carrier), and a **real
local lane** pointed at the operator's OpenAI-chat-compatible local server (judge/grader
single-call slices only). The rollout is gated by a new mapping-drift test and a de-stubbed
calibration harness, and the deferred team-deployment posture is named in config as a
designed-not-built profile key. No MCP anywhere: the ratified posture is subprocess/REST only.

## 2. Existing Context

- `runtime/skill-router.ps1` (v1.3.0) is the single dispatch point. Transports:
  `Invoke-GPTModel` (:758, Copilot) with `Invoke-OpenAIModel` (:789) behind
  `Invoke-GptWithTransportPrecedence` (:822); `Invoke-ClaudeModel` (:858, host-native stub);
  `Invoke-LocalModel` (:694). Entry points resolve via `Resolve-SkillEntryPoint` (:670);
  GPT tier peers via `Resolve-GptPeer` (:324, sole caller :899). Fail-open contract: router
  errors fall back to Claude (exit 2); exit 3 only when no provider is reachable.
- Config: `config/model-mapping.json` (providers block + per-skill capability rows; sole parser
  `Get-ModelMapping` :521), `config/model-tier-map.json` (Claude-tier to GPT-peer map),
  `config/skill-manifest.json` (authoritative inventory).
- `skills/<name>/core.md` + `providers/{claude,gpt}.md` is the carrier pattern; 47 portable
  skills, 3 Claude-native.
- Phase 7 state at plan time: Step 42 DONE; Step 43 proved the real Copilot discovery roots
  (`.github/skills/`, `.agents/skills/`, `.claude/skills/`; YAML frontmatter required) and
  forced a re-scope; Steps 44-50 pending. Phase 7 owns discovery/install/migration/cutover;
  this plan owns transports/providers/calibration — the file surfaces are disjoint except for
  additive test suites and sequential doc edits.
- Tests are the only automated gate (no lint/typecheck by design, `architecture.md` §8.4).
  Baseline: 285 pass / 3 skip at plan time — re-baseline at Phase 8 start, since Phase 7 will
  have grown the suite. `tests/calibration/calibrate.py` exists but its `invoke_model()` is
  stubbed — no real cross-model call has ever been scored; `phase-3-4-ports.json` covers 35 of
  the 50 skills structurally.
- Known defects this plan fixes: the `providers.local` block points at an Ollama-shaped
  endpoint/model that does not exist on the operator's machine, and `Invoke-LocalModel` ignores
  its `SkillEntryPoint` parameter (no skill text reaches a local model). Telemetry token counts
  for non-Copilot transports are not populated from real usage metadata.
- This repository is public: no absolute user paths in committed files
  (`tests/package-integrity` gates it).

## 3. Scope

**In:** mapping-drift test; provider-aware tier-peer resolution; Gemini transport + dispatch +
proxy-first carrier; local-lane repoint with judge-slice semantics; `deployment.profile` config
key; live-smoke harness + operator smokes; calibration un-stub + anchor gate + ledger backfill;
bounded behavioral baseline; docs.

**Out:** any MCP code (client or server); Gemini as an automatic fallback target; full-fidelity
`providers/gemini.md` authoring for all skills (fork-on-failure only); Phase 7 cutover work
itself; team-profile implementation (key is designed-not-built); paid Gemini key adoption
(free-tier first); local execution of anything beyond judge/grader single-call slices.

## 4. Impact Analysis

| File | Change Type | Reason | Verified |
|---|---|---|---|
| `runtime/skill-router.ps1` | modify | add `Invoke-GeminiModel` + explicit-invoke-only dispatch branch; generalize peer resolution; fix `Invoke-LocalModel` skill-text drop; repoint local transport | read in full; `Resolve-GptPeer` 1 caller (:899); `Invoke-LocalModel` 2 callers (:1012, :1049); `Resolve-SkillEntryPoint` 6 callers (:934, :935, :962, :1009, :1046, :1064) + 2 references in `tests/smoke/test_cross_provider_smoke.py` |
| `config/model-tier-map.json` | extend | additive per-provider peer schema (Gemini tiers) | grep'd all consumers: parsed only by router (:129, :324-342); ~20 `providers/gpt.md`/core.md references are prose-only (no parse); listed in `architecture.md` (:46, :307) and `skill-manifest.json` (:96 transform entry) — both updated in Steps 52/61 |
| `config/model-mapping.json` | extend | `providers.gemini` block; per-skill `gemini` column; `local` column redefined to judge-slice semantics; `deployment.profile` key | sole parser `Get-ModelMapping` (:521); Step 51's drift test guards dir/row/manifest sync both directions |
| `runtime/telemetry/telemetry-writer.ps1` | extend | real token fields from Gemini `usageMetadata`; sink-seam documented for the team profile | callers enumerated at Step 53 build time before edit |
| `tests/package-integrity/` | extend | new mapping-drift test; profile-key validation coverage | suite exists (gates public-safety today); Phase 7 also adds tests here — additive, distinct files |
| `tests/router/`, `tests/smoke/` | extend | Gemini/local/profile unit tests (mocked transport); env-gated live-smoke legs | suites exist per `tests/` layout |
| `tests/calibration/calibrate.py`, `phase-3-4-ports.json`, `test_calibrate.py` | modify/extend | un-stub `invoke_model()` through the production router; anchor gate; ledger 35 → 50 | files confirmed present |
| `documentation/architecture.md`, `documentation/providers/`, `README.md`, `documentation/migration.md` | extend | Gemini provider doc, local semantics, profile key, provider matrix | Step 61; Phase 7 edits some of the same docs — strictly sequential (prerequisite gate), no concurrent edits |

## 5. New Components

- **`Invoke-GeminiModel`** (in `runtime/skill-router.ps1`): native `generateContent` REST
  transport, ~35-60 lines, structured output via the `generationConfig.responseMimeType` +
  `responseSchema` pair (the pair that endpoint accepts — the newer Interactions-API
  `response_format` field is endpoint-coupled and errors on `:generateContent`), auth via
  `GEMINI_API_KEY` env var only, timeout/retry parity with `Invoke-OpenAIModel`,
  `usageMetadata` wired to telemetry.
- **`tests/package-integrity/test_mapping_drift.py`**: bidirectional sync gate across
  `skills/`, `config/model-mapping.json`, `config/skill-manifest.json`.
- **Live-smoke harness** (Step 57-prep): env-gated real-call legs for Gemini and local through
  the production `Invoke-SkillRouter` entry.
- **`documentation/providers/gemini.md`**: carrier policy (proxy-first, fork-on-failure
  protocol, fork list maintained by calibration/smoke results).
- **`deployment.profile` key** in `config/model-mapping.json`: `"solo"` (default, implemented) |
  `"team"` (fail-loud designed-not-built error).

## 6. Design Decisions (ratified 2026-08-03; restated in full)

1. **No MCP, anywhere in this plan.** Ratified posture: MCP is adopted only when a named
   capability or model family cannot be reached by REST/subprocess — then consume-only, never
   authored. Gemini and local are both plain REST/subprocess, so nothing here touches MCP.
2. **Sequencing: cutover first.** Phase 7 (through its final cutover step, currently Step 50)
   lands the v1.3.0 router as the live consumer before this plan starts; this plan never
   patches the legacy v1.2.0 router.
3. **Gemini transport: native `generateContent` REST** (not the OpenAI-compat endpoint, not a
   CLI subprocess — the Gemini CLI's free OAuth tier stopped serving 2026-06-18). Rationale:
   native structured output and real `usageMetadata` token telemetry. Free AI Studio key
   (250 req/day, Flash-class only) until a real workload justifies a paid key; therefore Gemini
   tier peers default to flash-class models for all tiers, with pro-class entries added when a
   paid key lands. Current model ids are resolved from the live models endpoint at build time,
   not hardcoded from planning-time knowledge.
4. **Explicit-invoke-only Gemini (v1 escalation contract).** Gemini dispatches only on explicit
   `-Provider`/`-Model gemini`; it is never an automatic fallback target. Gemini-side errors
   fail open to Claude (exit 2) per the existing contract. The two-cloud fallback chain
   (Copilot → OpenAI → Claude) is untouched. Per-skill secondary-fallback choice is a future
   additive upgrade, deliberately deferred.
5. **Proxy-first carrier.** Gemini entry-point resolution reuses the GPT wrapper
   (`providers/gpt.md`) exactly as the local lane's resolution does; a real
   `providers/gemini.md` is authored per-skill only when smoke/calibration shows the proxy
   failing (fork-on-failure). Upfront authoring cost ~0 lines instead of ~1,900.
6. **Local lane: judge-slice-only, repointed at the real server.** Transport becomes
   OpenAI-chat against the operator's local serving stack (llama-swap fronting llama.cpp
   `llama-server`, default `http://localhost:8080/v1`, model id `coder-30b`, env-overridable).
   Evidence basis: 3-30B-class models are reliable on single well-specified calls but collapse
   on multi-tool orchestration, so local executes only bounded judge/grader single-call slices.
   The mapping's `local` column is **redefined**: `true` means "this skill has a bounded
   judge/grader single-call slice" (criteria: single completion; fixed JSON verdict schema; no
   tool use or vision; prompt fits a 30B-class context window), and the ~15 legacy aspirational
   flags are re-derived against those criteria in Step 55.
7. **Local response handling:** parse the `content` field (never `reasoning_content`, where
   local reasoning models bury answers) and request `max_tokens >= 600`.
8. **Team posture is designed, not built.** `deployment.profile` names it in config and fails
   loud if selected. The profile may only ever gate transport + auth + telemetry sink — never
   skill content or routing logic. Two seam obligations are asserted now: the router core keeps
   its `(skill, model, input)` contract with no local-shell assumption, and telemetry writes
   stay behind `telemetry-writer.ps1` so a shared sink can swap in later.
9. **Calibration before trust.** No provider-parity claim is made until `calibrate.py` makes
   real calls, passes an anchor gate (a known-good output must outscore a known-garbage output),
   and the structural ledger covers all 50 skills. First behavioral baseline is bounded:
   5 representative skills x 3 cloud providers, plus the judge-slice on local.
10. **Autonomous-behavior classification:** the router is a one-shot CLI invocation; nothing in
    this plan adds scheduled, background, or always-on behavior, so no long-running observation
    phase is required. The live smokes + bounded baseline are the end-to-end gates.

## 7. Build Steps

### Step 51: Mapping-manifest drift gate
- **Problem:** Nothing keeps `skills/`, `config/model-mapping.json`, and
  `config/skill-manifest.json` in sync; a ported skill missing its mapping row silently fails
  open to Claude (this drift class has already occurred at 2-provider scale). Add a
  package-integrity pytest asserting bidirectional 1:1 sync (every `skills/<name>/` dir has a
  mapping row and manifest entry, and vice versa) plus row sanity (capability values boolean;
  every referenced provider exists in the `providers` block).
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** `tests/package-integrity/test_mapping_drift.py`
- **Done when:** the test goes red when a synthetic skill dir (tmp fixture) is added without a
  mapping row, and when a mapping row has no dir; full suite green at or above the re-baselined
  floor.
- **Depends on:** none

### Step 52: Provider-aware tier-peer resolution
- **Problem:** `config/model-tier-map.json` maps Claude tiers to GPT peers only, and
  `Resolve-GptPeer` (:324, sole caller :899) hardcodes that shape. Extend the schema
  **additively** with a per-provider peer table (Gemini tiers, flash-class defaults per §6.3);
  generalize to a provider-aware resolver with the existing GPT behavior preserved exactly;
  update the `architecture.md` tier-map row.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** extended `config/model-tier-map.json`; resolver changes in
  `runtime/skill-router.ps1`; router tests
- **Done when:** regression tests prove GPT peer resolution is byte-identical to before; Gemini
  peer resolution tested incl. missing-file fail-open warning; full suite green.
- **Depends on:** 51

### Step 53: Gemini transport, explicit-invoke-only
- **Problem:** No Gemini transport exists. Add `providers.gemini` to `model-mapping.json`;
  implement `Invoke-GeminiModel` per §5/§6 (REST, legacy structured-output pair, GEMINI_API_KEY
  env only, timeout/retry parity, `usageMetadata` -> telemetry-writer real token fields —
  enumerate telemetry-writer callers before editing); dispatch branch fires only on explicit
  gemini selection, never as fallback; gemini errors fail open to Claude exit 2; resolve current
  model ids from the live models endpoint during the build.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** router + telemetry changes; `providers.gemini` config block; mocked-HTTP tests
- **Done when:** mocked-transport tests cover: happy path; structured output parse; missing-key
  fail-loud; 5xx -> Claude fallback (exit 2); telemetry row carries non-zero token counts from
  mocked `usageMetadata`; full suite green.
- **Depends on:** 52

### Step 54: Proxy-first Gemini carrier
- **Problem:** No per-skill Gemini entry points exist and, per §6.5, none should be authored
  upfront. Extend `Resolve-SkillEntryPoint` (:670, 6 callers) with a `gemini` variant:
  `providers/gemini.md` if present, else proxy to `providers/gpt.md`; add the per-skill
  `gemini` column to `model-mapping.json` mirroring `gpt` for the 47 portable skills (false for
  the 3 Claude-native); create `documentation/providers/gemini.md` documenting the
  fork-on-failure protocol.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** resolver change; mapping column; carrier policy doc; tests
- **Done when:** entry-point tests prove proxy fallback and explicit-override precedence; the
  Step 51 drift test is extended to validate the new column; full suite green.
- **Depends on:** 51, 53

### Step 55: Local lane repoint, judge-slice semantics
- **Problem:** `providers.local` targets a nonexistent Ollama-shaped endpoint and
  `Invoke-LocalModel` (:694; callers :1012, :1049) ignores `SkillEntryPoint`, so no skill text
  reaches a local model. Repoint transport to OpenAI-chat at `http://localhost:8080/v1`
  (model id `coder-30b`; env-overridable — reuse the router's existing local-URL override
  convention, verifying the exact name at `Invoke-LocalModel`); prepend the resolved
  entry-point skill text to the request; parse `content` with `max_tokens >= 600` (§6.7);
  redefine and re-derive the `local` column per §6.6 criteria; local dispatch is limited to
  judge/grader single-call slices.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** router + config changes; re-derived local flags with per-row notes; tests
- **Done when:** mocked-endpoint tests prove skill text is present in the POST body,
  content-field parsing, and server-down defer/fail-open behavior; drift test green; full suite
  green.
- **Depends on:** 51

### Step 56: deployment.profile key + seam hygiene
- **Problem:** The ratified team posture is designed-not-built, but nothing in config names it
  and nothing guards the seams that keep it cheap. Add `deployment.profile` ("solo" | "team")
  to `config/model-mapping.json`; router startup validates (absent -> solo; "team" -> fail-loud
  designed-not-built error naming this plan; unknown -> config error). Document in
  `architecture.md`: the profile gates transport + auth + telemetry sink only; router core keeps
  the `(skill, model, input)` contract; telemetry stays behind the writer seam.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** config key; startup validation; tests; architecture note
- **Done when:** profile tests (absent/solo/team/junk) pass; full suite green.
- **Depends on:** 51

### Step 57-prep: Live-smoke harness
- **Problem:** Steps 53-55 are mock-verified only; real-API shape drift is invisible to mocks.
  Author env-gated smoke legs that exercise the production `Invoke-SkillRouter` entry (never a
  parallel helper): a Gemini leg (one real `generateContent` call through a representative
  skill; assert exit 0, structured output parses, telemetry tokens > 0) and a local leg (one
  real judge-slice call; assert verdict JSON, and clean defer when the server is down). Skipped
  by default when `GEMINI_API_KEY` is absent / the local endpoint is unreachable, so CI stays
  green without secrets.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** smoke legs under `tests/smoke/`
- **Done when:** harness green in skip mode; code review confirms both legs enter via
  `Invoke-SkillRouter`; full suite green.
- **Depends on:** 53, 54, 55

### Step 57: Gemini live smoke
- **Problem:** Verify real Gemini access end-to-end. Create a free Google AI Studio API key,
  set `GEMINI_API_KEY` as a user environment variable (never committed, never echoed to any
  log), and run the Gemini smoke leg — one real call is the programmatic-access verification.
- **Type:** operator
- **Issue:** #
- **Done when:** Gemini leg passes with the real key; telemetry row shows non-zero token counts.
- **Depends on:** 57-prep

### Step 58: Local live smoke
- **Problem:** Verify the repointed local lane against the real server. Start the local serving
  stack (operator-owned; WSL2 `llama-server` behind llama-swap with the localhost keep-alive),
  run the local smoke leg, then stop the server and confirm the clean-defer path.
- **Type:** operator
- **Issue:** #
- **Done when:** live pass and server-down defer both observed.
- **Depends on:** 57-prep

### Step 59: Calibration un-stub, anchor gate, ledger backfill
- **Problem:** "35/35 calibration tests pass" is file-existence checking: `invoke_model()` in
  `tests/calibration/calibrate.py` is stubbed and `phase-3-4-ports.json` covers 35 of 50 skills
  (omitting the 13 heaviest pipeline skills). Implement `invoke_model()` through the production
  router; add the anchor gate (known-good output must outscore known-garbage before any
  baseline number is reported — the gate hard-fails otherwise); backfill the structural ledger
  to all 50 skills.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** working `calibrate.py`; 50-entry ledger; extended `test_calibrate.py`
- **Done when:** anchor gate demonstrably goes red on garbage (self-test); ledger count equals
  the `skills/` dir count (cross-checked by the drift test); real-call path env-gated
  skip-by-default; full suite green.
- **Depends on:** 53, 55

### Step 60: Bounded behavioral baseline
- **Problem:** Produce the first real cross-provider quality measurement. Run `calibrate.py`
  over 5 representative skills (one each from the plan-, build-, review-, user-, and goblin-
  families) x claude/gpt/gemini, plus the judge-slice on local; review the anchored scores;
  record which skills (if any) need a forked `providers/gemini.md` per the Step 54 protocol.
- **Type:** operator
- **Issue:** #
- **Produces:** recorded baseline results + operator disposition notes (data, not code)
- **Done when:** baseline recorded with the anchor gate green; the fork-on-failure list
  (possibly empty) is written into `documentation/providers/gemini.md`.
- **Depends on:** 57, 58, 59

### Step 61: Documentation + provider matrix
- **Problem:** Bring the docs to 4-family truth: `architecture.md` (Gemini provider section,
  local judge-slice semantics, `deployment.profile`), finalized
  `documentation/providers/gemini.md`, README provider matrix, `migration.md` note.
- **Issue:** #
- **Flags:** --reviewers code
- **Produces:** updated docs
- **Done when:** docs match shipped behavior; package-integrity (public-safety) and full suite
  green.
- **Depends on:** 51-60

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Gemini free tier (250/day, flash-class only) | Baseline or smokes exhaust quota; flash-class may under-perform on heavier skills | Bounded 5-skill baseline; spread runs; paid-key decision explicitly deferred and cheap to flip (config + key swap) |
| Legacy structured-output pair on `:generateContent` | Google further deprecates the legacy pair in favor of the Interactions API | Transport isolated inside `Invoke-GeminiModel`; switching endpoint+field is a one-function change |
| Gemini model-id churn | Planning-time model names go stale | Ids resolved from the live models endpoint at build time; tier map additive |
| Local server availability | Smokes/baseline blocked if the operator-owned server is down | Defer path tested; server start is always operator-owned (never auto-spawned); Step 58 verifies both directions |
| Proxy-first carrier misfit | GPT wrappers may prompt Gemini poorly for some skills | Fork-on-failure protocol + Step 60 baseline catch it; forking is per-skill and additive |
| Phase 7 slippage or growth | This plan is inert until Phase 7's final cutover step lands; Phase 7 has already grown twice (42-48 → 42-50) | Prerequisite stated at top; no step targets the legacy router; **re-verify Phase 7's highest step and renumber before `/repo-sync`** |
| Parallel-session state | Phase 7's live cutover step requires a parked-work handshake (no fresh expedite state, no competing worktrees) in the consumer repo | Do not run `/plan-expedite` for this plan while the Phase 7 window is mid-run; coordinate at a Phase 7 boundary |

## 9. Testing Strategy

pytest is the only automated gate (no lint/typecheck, by design). Per step: mocked-transport
unit tests (router suites) so no secret or live endpoint is needed for CI; the Step 51 drift
test guards every subsequent mapping edit; live verification is concentrated in the env-gated
smoke legs (Steps 57/58) and the anchored calibration baseline (Steps 59/60), all entering
through the production `Invoke-SkillRouter` — never a parallel prompt builder. Regression
floor: 285 pass / 3 skip at plan time, re-baselined at Phase 8 start (Phase 7 grows the suite);
each code step's Done-when requires the full suite green at or above the floor plus its own new
tests. Existing behavior that must not change and is regression-pinned: GPT peer resolution
(Step 52), the Copilot→OpenAI→Claude fallback chain (Step 53), and entry-point resolution for
claude/gpt variants (Step 54).
