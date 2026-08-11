# _shared/

Resources referenced by several skills. Each `.md` file here is either a
procedure doc the orchestrator-LLM reads at runtime or a shared contract
multiple skills cite; each `.py` file is a thin wrapper that exposes the same
procedure programmatically for tests and Python callers.

Files in this directory are referenced from sibling skill SKILL.md files via
relative paths (e.g. `../_shared/score-skill.md`). The directory is NOT a
skill itself — it has no `SKILL.md`.

| File | Purpose | Consumer |
|---|---|---|
| `judge-core.md` | The shared judging doctrine (archetypes, dimensions, rubric method, honesty invariants) every verdict-rendering skill cites | `review-deep`, `review-gauntlet`, `user-uat`, `build-step`, `build-phase` |
| `skill-pipeline.md` | The routing web: the 8 rails an operator fragment can land on, the re-route edges, and the re-route contract | `user-gateway`, `user-debug`, README workflow maps |
| `intake-engine.md` | The intake-ledger contract: path formula, row grammar, zero-open check, canonical `/goal` string | `user-gateway` + rail skills writing back re-routes |
| `calibrate_judge.py` | Deterministic per-commit judge-calibration gate (freshness / discrimination / agreement over a recorded snapshot) | `review-deep` § Calibration; `judge-core.md` §7 |
| `test_calibrate_judge.py` | Tests for the calibration gate | `pytest` |
| `build_step_verdict.py` | Canonical `verdict.json` schema + the default-deny `classify_verdict` consume rule | `build-step` Step 7 (emit); `build-phase` Step 2c (consume) |
| `test_build_step_verdict.py` | Tests for the verdict contract | `pytest` |
| `score-skill.md` | Composite skill-scoring procedure (structural + differential) | `/skill-iterate` Phase 2 Step D |
| `score_skill_composite.py` | Thin Python wrapper around the composite procedure for tests + non-LLM callers | `test_score_skill.py` + smoke runs |
| `test_score_skill.py` | Integration test for the composite scoring procedure | `pytest` |
| `skill-role-taxonomy.md` | Direction-neutral role taxonomy (the seven tags) + fan-out classification protocol | `tier-escalate`, `tier-offload` |
| `step-authoring.md` | Build-step sizing (one vertical slice), optional example grammar, deferred `Done when:` sentinels | `plan-init`, `plan-feature`, `plan-review`, `build-phase`, `repo-update` |
| `task-state-schema.md` | Task-state field definitions, write discipline, path resolution contract, lifecycle | `user-wrap` |
| `worktree-hygiene.md` | The worktree landmines: removal order, staleness, orphan cleanup | `user-afterparty` |
| `subagent-economy.md` | Terse-verdict returns + delegate-the-read discipline for orchestrators | `user-afterparty` |

**Vendored documents (Step 66).** The last five rows above, plus `skill-pipeline.md` and
`intake-engine.md`, are copies of workspace reference documents brought into this payload
so the cores citing them resolve inside a host discovery root. Each carries a vendoring
note stating its two adaptations (external citations rendered as plain names; operator
identifiers, private issue/cron references and harness-configuration paths removed).
Cores cite them as `<repo>/_shared/<leaf>`, which `tools/build-distributions.ps1` repoints
to `../_shared/<leaf>` at emit time; the reasoning is in this repository's Step 66
decision record under `documentation/`.
