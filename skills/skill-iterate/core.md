# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- `<skills-root>` is the host skill-discovery root that holds this skill's installed folder (for example `<workspace>/.claude/skills` on Claude). Runtime helpers resolve against it: the deterministic scripts live in `<skills-root>/skill-iterate/scripts/` and the shared scorer in `<skills-root>/_shared/`. Relative links in this file are reader links into the canonical tree; commands use the `<skills-root>` forms.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# /skill-iterate

This skill ports the serial hill-climb pattern from `<workspace>/primatives/autoresearch/program.md` to skill iteration. Three load-bearing rules carry over verbatim:

- **NEVER STOP mid-loop**: no mid-run halts inside a per-skill iteration loop — the loop drains to its budget cap or crashes; nothing else.
- **Simplicity bias on ties**: a mutation that deletes code with a ≥0 score delta is a keep.
- **Wall-clock-bounded experiments**: every per-iteration scoring call has a hard timeout; every per-skill loop has a hard wall-clock cap.

Treat any deviation as a defect.

Two measurement rules bind every score this skill acts on (the workspace measurement-validity rule): score the file the host actually loads (§Target resolution), and treat a silent fallback anywhere in the scoring path as a `crash`, never as a low score (§Integrity checks).

---

## When to use

- The operator has 1+ scorable skills (i.e. `evals/evals.json` + `evals/test_scenarios.json` exist) and wants overnight hill-climb iteration.
- Default invocation drains all scorable skills serially, one worktree per skill, budget-capped.
- Use after `/skill-eval-setup` has bootstrapped evals for the target.

## When NOT to use

- No evals present for the target skill — run `/skill-eval-setup <skill>` first.
- Skill is in the embedded skip-list below (output is side-effect-driven, not text-gradable).
- Skill is at a hill-climb plateau and needs radical exploration — use `/skill-evolve` (parallel A/B with operator-curated variants) instead.
- Single-skill interactive iteration where the operator wants to review each diff — use `/build-step` against a hand-edited SKILL.md instead.
- Changing a Skill Mesh catalog skill in place. Install output is never merged: a generated host profile is edited only on a disposable `skill-iterate/*` branch and yields a reviewable proposal, and an unmarked file in a Skill Mesh install tree is skipped (§Target resolution). The change lands through the Skill Mesh catalog lifecycle.

---

## Defaults

| Flag | Default | Notes |
|---|---|---|
| `--project` | (workspace root) | Project repo whose `.claude/skills/` tree to iterate. Default preserves legacy behavior (the dev/ workspace root). See §Path resolution (`--project` root). |
| `--skill` | (all scorable skills) | Auto-discover `<project>/.claude/skills/*/evals/evals.json`, filter via skip-list. Use `--skill <name>` to scope to one. |
| `--queue` | (none) | Optional file path with one skill name per line; overrides auto-discovery. |
| `--per-skill-budget` | `1h` | Wall-clock cap per skill. |
| `--per-skill-iterations` | `12` | Iteration cap per skill. Whichever cap hits first ends that skill's loop. |
| `--skip-list` | `<embedded>` | Comma-separated skill names to exclude beyond the embedded list. |
| `--force-skip-collision` | off | Treat a skip-list collision in an explicit `--skill` or `--queue` as a warning and continue. Without this flag, the collision halts with an explanatory message. |
| `--calibrate` | off | Run the adversarial-mutation calibration for each queued skill (see Phase 1 § Adversarial-mutation calibration). Skills whose structural-floor catch rate is `<70%` are defect-parked before entering the iteration loop. Off by default; the always-on garbage-anchor check (Phase 2 § Baseline and anchor capture) covers LLM-grader discrimination. |
| `--dry-run` | off | Print resolved queue + budget plan + per-skill worktree paths + target modes, then exit. No work, no lock, no launch-gate checks. |

Max overnight wall-clock: 12 skills x 1h = 12 hours. Queues longer than 12 items spill to a follow-up night.

---

## Path resolution (`--project` root)

Every path this document expresses relative to "the workspace root" (including every bare `.claude/skills/...` reference) is resolved relative to **`--project <path>`**. The default is the workspace root the skill is invoked from (`<workspace>`), so the default behavior is byte-for-byte the legacy behavior. Binding `--project` rebases ALL of the following onto that project's git repo, so the same hill-climb loop can iterate skills living in any repo (the dev/ workspace, `Alpha4Gate`, `void_furnace`, ...). This section is the single source of truth for the rebasing; the per-phase prose below is written workspace-root-relative and is governed by this table.

| Reference | Resolves to |
|---|---|
| Skill discovery glob | `<project>/.claude/skills/*/evals/evals.json` |
| `--skill <name>` / `--queue` skill folder | `<project>/.claude/skills/<name>/` |
| `evals/results.tsv` (cross-night filter + per-iteration append) | `<project>/.claude/skills/<name>/evals/results.tsv` |
| Lock file | `<project>/.skill-iterate.lock` |
| Kill-switch file | `<project>/.skill-iterate-killswitch` |
| `<PROJECT>` (Phase 3 git ops: `git -C <PROJECT>`, worktree create, squash-merge target) | `<project>` |
| Morning-summary dir | `<project>/docs/skill-iterate-runs/` |
| Proposal files (Phase 3 `review-required`) | `<project>/docs/skill-iterate-runs/proposals/` |
| `.gitignore` `worktree_*/` rule | `<project>/.gitignore` |

**Script-home exception (the one thing `--project` does NOT rebase).** The deterministic helper scripts are always invoked from `<skills-root>` (§Provider-neutral host abstractions), regardless of `--project`, because they ship with this skill's host profile, not with each target project. Each takes the target skill / project paths as ARGUMENTS, so cross-tree use needs no copying:

- Queue discovery (Phase 1): `<skills-root>/skill-iterate/scripts/resolve_queue.py --project <project>`
- Structural metrics (Phase 2 Step D, imported by the composite scorer): `<skills-root>/skill-iterate/scripts/structural_metrics.py <file>`
- Absolute aggregator (Phase 2 Step D): `_shared/score_skill_absolute.py` under `<skills-root>`
- Grader-prompt builder (Phase 2 Step D): `_shared/grader_prompt.py::build_grader_prompt`
- Results append (Phase 2 Step G): `<skills-root>/skill-iterate/scripts/append_result.py <skill_path> ...`
- Morning summary (Phase 4): `<skills-root>/skill-iterate/scripts/morning_summary.py`

The worktree parent dir (`<workspace-parent>/worktree_skill-iterate-*`) is unchanged by `--project`; only the git repo the worktree is added to changes (it is the `--project` repo, via `git -C <PROJECT> worktree add`).

---

## Embedded skip-list

- **Exclude** side-effect-driven skills whose output is not text-gradable in a fresh-context Claude session.
- **Extend** (not shrink) the embedded list via `--skip-list`; embedded entries always remain excluded.

- `verify` — runs the app and observes behavior (side-effect skill, no text artifact).
- `run` — launches the app.
- `loop` — recurring task runner (orchestration).
- `schedule` — remote agent scheduler (orchestration).
- `update-config` — `settings.json` edits (config side-effects, not text generation).
- `fewer-permission-prompts` — settings audit (transcript-driven, not scenario-driven).
- `claude-oauth-auth` — credential setup.

The side-effect skills become eligible only after per-skill side-effect harnesses exist (future work).

---

## Autonomy contract

Per the workspace plan-and-issue-flow rule § "Autonomous-by-default skills" and the workspace code-quality rule § "Build-phase halt contract":

This skill MUST default to autonomous execution. No mid-run `(y/n)` prompts. The only legitimate halts are:

1. **Pre-flight failure** — any of:
   - skill folder missing for an explicit `--skill <name>`
   - `evals/evals.json` missing for a discovered or explicit skill
   - kill-switch file (`.skill-iterate-killswitch`) already present at workspace root at launch
   - target skill in skip-list when `--skill <name>` is explicit and `--force-skip-collision` is absent
   - **concurrent /skill-iterate run detected** — see "Concurrent-run detection" below
   - **a required helper or the host workflow primitive is unavailable, or `<project>` is not its own git top level** — the Phase 1 launch gate halts with `required_tool_missing` (or `project-not-toplevel`), naming what is missing
2. **Worktree creation failure** — git error.
3. **3 consecutive iteration crashes on the same skill** — defect surface; park to a GitHub issue and move to next skill in queue (does not halt the whole run).
4. **Kill-switch file appears at workspace root mid-run** — graceful stop between skills, not mid-loop.

Carries autoresearch's `program.md` § "NEVER STOP" rule verbatim: once a per-skill loop enters its iteration phase, the loop runs to its budget cap or until clause 3 (3 consecutive crashes) trips. No `(y/n)` confirmations, no "should I continue?" gates, no asking the operator to review a diff mid-loop. The operator opted into autonomous execution by invoking the skill.

### Concurrent-run detection

Two-check pre-flight at launch (read-only; the lock itself is taken at the Phase 1 launch gate):

1. **Lock file:** check for `.skill-iterate.lock` at workspace root. Schema: JSON `{"pid": <int>, "started_at": <iso8601>, "host": <hostname>}`. Behavior:
   - Lock missing → proceed; the lock is taken at the launch gate.
   - Lock exists + PID alive (cross-platform: `Get-Process -Id <pid>` on Windows, `kill -0 <pid>` on POSIX) → **halt** with message naming the running PID and start time.
   - Lock exists + PID dead → stale; emit `warning: stale lock from PID <N> at <date>; taking over`, proceed; the launch gate overwrites it with the current PID.
2. **Worktree scan:** `git worktree list` matching the prefix `worktree_skill-iterate-*`. Behavior:
   - No matches → proceed.
   - Matches found + no live lock → emit `warning: orphaned worktrees from prior crash: <list>; consider cleanup per the workspace worktree-hygiene rule #4`. Proceed (do not auto-clean; operator decides).
   - Matches found + live lock → halt (caught by check 1 already).

On clean exit (including kill-switch stop), remove `.skill-iterate.lock`. On unclean exit, the lock is stale and check (1) handles takeover on next run.

### Iteration outcome taxonomy

Three distinct outcomes per iteration, distinguished for the autonomy contract's clause-3 crash count:

| Outcome | Definition | Counts as crash? | results.tsv status |
|---|---|---|---|
| **keep** | Score improved (delta > 0), or the Step F simplicity-bias tie (delta >= 0 with a shorter contract file) | No | `keep` |
| **revert** | A well-formed result reports no score improvement (delta <= 0) and is not a simplicity-bias keep. The mutation produced bad output, which is the loop working as intended; `git reset --hard <iter-parent>` (Step F). | No | `revert` |
| **crash** | Scoring harness threw an unhandled exception, OR score-extraction returned no number, OR an integrity check failed (§Integrity checks), OR the Step A return was malformed, changed nothing, or its `old_string` did not occur exactly once, OR the Step A agent modified the contract file, OR per-iteration timeout (10 min hard cap, per Step D) fired, OR git commit/branch op failed. After the row is appended the worktree is reset to `<iter-parent>`, exactly as on revert; this is a no-op when nothing changed and also discards an uncommitted Step B edit. | Yes | `crash` |

Three consecutive `crash` outcomes (no intervening keep/revert) on the same skill triggers autonomy-contract clause 3 — park the skill via a GitHub issue with crash logs, move on to the next in queue.

**Authoritative status classification:** An `unparseable` result (JSON parse failure or missing required fields) is classified as `crash`, NOT `revert`. Revert applies only to a well-formed result indicating regression. The `status != "ok"` blanket rule applies to all non-ok statuses, including `unparseable`; they all route to the crash branch.

**`grader-broken-for-skill` is a per-skill park, not an iteration outcome.** It is reached before any iteration, either by the always-on garbage-anchor check (Phase 2 § Baseline and anchor capture: the grader passes known garbage at least as often as the real skill) or by the opt-in `--calibrate` pass (Phase 1 § Adversarial-mutation calibration: injected defects are caught below the 70% threshold). Either way the iteration loop would produce no useful gradient, so the skill is parked and not retried within the run. The park never touches the consecutive-crash counter. See [`scripts/adversarial_calibration.py`](scripts/adversarial_calibration.py) and `../../../docs/investigations/skill-iterate-hill-climbing/06-adversarial-mutation-grader-discrimination-tests.md` for the calibration procedure and rationale.

---

## Scoring

Per-iteration scoring follows the shared procedure in [`../../_shared/score-skill.md`](../../_shared/score-skill.md). Default mode is `composite`: a weighted mean of deterministic structural metrics (40%) and LLM-driven absolute_weighted grading (60%), per SIHC.2 Option A (the prior pair-comparison mode replaced by absolute grading; goldens-verify unwired from the loop body). The procedure also supports `structural`-only and `absolute_weighted`-only modes — see the fragment for inputs, mode semantics, and the brace-safe-substitution requirement for the grader prompt template. Legacy spec-compliance scoring (pre-SIHC) is no longer in scope; all per-iteration scoring now goes through `_shared/score-skill.md` composite/structural/absolute_weighted modes.

A thin Python wrapper at [`../../_shared/score_skill_composite.py`](../../_shared/score_skill_composite.py) exposes the same procedure programmatically (for tests, smoke checks, and non-LLM callers). In composite mode it returns:

```
{"score": <float>, "passed": <int>, "total": <int>, "status": "ok" | "unparseable" | "harness-error"}
```

In composite mode `passed`/`total` count scoring AXES: `2/2` means both the structural and the absolute axis scored. The wrapper still reports `status: "ok"` with `1/2` when one axis failed and the other survived; this skill treats that as a fallback (below). The loop reads `score` to decide keep vs revert. `status != "ok"` is a crash per the taxonomy above.

#### Integrity checks

Every score this skill acts on — baseline, garbage anchor and each iteration — comes from the deterministic production scorers, re-run by the orchestrator on the workflow's saved payload, not from the aggregate agent's transcription of them. After each scoring-workflow invocation (Phase 2 Step D), for each scored version `<id>`, using the file names the shared workflow writes under `work_dir`:

1. **Recompute.** Run `python -B <skills-root>/_shared/score_skill_composite.py --skill-md <file> --baseline <file> --modified <file> --mode composite --absolute-verdicts <work_dir>/payload_<id>.json --evals <evals_dir>/evals.json` and `python -B <skills-root>/_shared/score_skill_absolute.py --evals <evals_dir>/evals.json --input <work_dir>/payload_<id>.json`. Capture each process's stdout byte-for-byte as UTF-8 into `<work_dir>/composite_<id>.json` and `<work_dir>/absolute_<id>.json` using a short Python `subprocess.run(..., stdout=file, check=True)` launcher or a non-PowerShell shell. Never use Windows PowerShell 5.1 `>` redirection, which can add a BOM or change encoding. An unparseable read-back is a crash. `<file>` is the version's `skill_md_path`. Read back only the decision fields: composite `score`, `status`, `passed`, `total`; absolute `n_trials_per_scenario` and the lengths of `passing_pairs` and `failed_assertions`.
2. **Crash conditions.** The version's result is a `crash` — never a low score — when any of these holds:
   - the workflow result's `status != "ok"`, or the recomputed composite's `status != "ok"`, or its `score` is missing, null or non-numeric;
   - the recomputed composite scored fewer than `2/2` axes (one axis silently fell back);
   - for some scenario in `test_scenarios.json`, `<work_dir>/render_<id>_<scenario-id>.md` is missing, or is empty for any version other than the garbage anchor (the stub may legitimately render nothing), or `n_trials_per_scenario` for that scenario is not the requested `trials`;
   - `<work_dir>/payload_<id>.json` is missing, or holds a verdict whose reason is `grader omitted` (the aggregate step's backfill for a missing grade).
3. **Signal.** Otherwise the recomputed composite `score` is the version's score; `<work_dir>/absolute_<id>.json` holds its `failed_assertions` (ranked by category weight) and `passing_pairs`; `pairs_passed` is the number of `passing_pairs`. The workflow result's own `score` is an agent's transcription: when it differs from the recomputed score by more than `5e-4`, print `warning: workflow score <w> differs from recompute <r> for <id>`; the recomputed score still gates and the mismatch alone is not a crash. Keep the orchestrator's own context to these decision fields, the Step A prompt fields (top failure, compact remaining failures) and file paths (the workspace subagent-economy rule).

#### Switchboard local grader (`skill-iterate-grader`): not wired

Switchboard Decision 9 names the `absolute_weighted` grading slice as the one role this skill may route to a local model (tier-offload task_class `skill-iterate-grader`), and switchboard config can enable that site. No step of this skill calls it: grading happens inside the shared workflow's grade agents, and the orchestrator never holds a grading prompt to send. Do not call switchboard from this skill. The planned call shape, kept for a future wiring, is `python -m switchboard judge --site skill-iterate-grader --prompt-file <grading-prompt-file>` (one JSON object on stdout, always exit 0; a `defer` result means use the normal grader). A local model may only ever *advise* a score; it is never the keep/revert gate.

---

## Flow

### Phase 0 — Pre-flight

Four read-only checks run before the queue is built: concurrent-run detection, kill-switch absence, skip-list resolution, and explicit `--skill` / `--queue` validation. Any failure here halts under §Autonomy contract clause 1. Phase 0 writes nothing; the lock file is taken only at the end of Phase 1 (§Launch gate), after the `--dry-run` and empty-queue exits.

#### Concurrent-run detection

Run the lock-file + worktree-scan procedure documented in §Autonomy contract → Concurrent-run detection. The full two-check logic lives there; this phase invokes it as a pre-flight gate. Action on detection:

- **Live lock detected** (lock file exists, PID alive) — halt with the message naming the running PID and start time. Do not write any state; do not touch the lock file.
- **Stale lock detected** (lock file exists, PID dead) — emit the `warning: stale lock from PID <N> at <date>; taking over` warning, then continue pre-flight. The lock file is overwritten at the Phase 1 launch gate (§Take the lock file).
- **Orphan worktrees only** (no lock, but `worktree_skill-iterate-*` dirs match `git worktree list`) — emit `warning: orphaned worktrees from prior crash: <list>; consider cleanup per the workspace worktree-hygiene rule #4` and proceed. Do not auto-clean; the operator decides whether to remove them.

#### Kill-switch absence check

Confirm `.skill-iterate-killswitch` is ABSENT at workspace root at launch. If present, halt with:

```
kill-switch is set at <abs-path>; remove the file to proceed
```

Mid-run kill-switch polling is handled in Phase 3 (between skills); this check is the launch-time gate.

#### Skip-list resolution

The effective skip-list at this phase is the union of:

- The embedded skip-list (per §Embedded skip-list).
- Any `--skip-list <comma-separated>` extension passed by the operator. Operators can EXTEND (not shrink) the embedded list.

The merged set is what auto-discovery filters against in Phase 1 and what `--skill <name>` validates against below.

#### Explicit --skill / --queue handling

When `--skill <name>` is passed:

- Verify `.claude/skills/<name>/` exists. If not, halt — pre-flight failure per §Autonomy contract clause 1.
- Verify both `.claude/skills/<name>/evals/evals.json` AND `.claude/skills/<name>/evals/test_scenarios.json` exist. If either is missing, halt with the message `evals not bootstrapped for <name>; run /skill-eval-setup <name> first`.
- If `<name>` appears in the merged skip-list and `--force-skip-collision` is absent, halt with `skip-list collision: <name> is excluded; pass --force-skip-collision to treat this as a warning and continue`. With `--force-skip-collision`, emit that warning and continue.

When `--queue <path>` is passed:

- Read the file: one skill name per line. Parsing rules — stated explicitly so operator hand-edits do not 4AM-halt on benign whitespace or inline comments:
  - Strip leading AND trailing whitespace from every line before processing.
  - Blank lines (empty after stripping) are ignored.
  - Lines starting with `#` (after leading-whitespace strip) are whole-line comments and ignored.
  - Inline comments are supported: a `#` anywhere on a non-comment line introduces a trailing comment — split on the FIRST `#` and take the left side, then re-strip trailing whitespace. Example: `session-wrap   # known winner overnight` parses as `session-wrap`.
  - Skill names containing `#` are not permitted (no skill name in `.claude/skills/*/` contains `#`, so this is a non-collision in practice).
- For each parsed skill name, run the same three checks as `--skill` (folder + evals/evals.json + evals/test_scenarios.json + skip-list collision). Halt on the FIRST failure rather than silently skipping, except that `--force-skip-collision` converts only a skip-list collision to a warning and continues — `--queue` is an explicit operator-curated list, and silent skips would mask typos.

#### Pre-flight failure modes

Restated for the developer agent — these are the six conditions under which the run halts before any skill is processed (the five Phase 0 checks plus the Phase 1 launch gate). Calibration and garbage-anchor parks and target-resolution skips are per-skill, not whole-run, so they are not in this list:

1. Skill folder missing (for an explicit `--skill <name>` or any name in `--queue <path>`).
2. `evals/evals.json` or `evals/test_scenarios.json` missing for an explicit skill.
3. Kill-switch file (`.skill-iterate-killswitch`) present at workspace root at launch.
4. Skill in the merged skip-list when passed explicitly via `--skill <name>` or `--queue <path>`.
5. Concurrent run detected (live lock file with a running PID).
6. At the launch gate: a required helper or the host workflow primitive is unavailable (`required_tool_missing`), or `<project>` is not its own git top level (`project-not-toplevel`).

All six map to §Autonomy contract clause 1; none of them count toward the consecutive-crash defect-park counter.

### Phase 1 — Discover queue

Six sub-steps resolve the queue. Target resolution then classifies each queued skill, and the launch gate checks helpers and takes the lock. The output of this phase is an ordered list of skill names to iterate with their contract files and modes, plus (under `--dry-run`) a printed plan with the worktree paths, budget and target mode per skill.

#### Auto-discovery procedure

Glob `<project>/.claude/skills/*/evals/evals.json` (per §Path resolution; `<project>` defaults to the workspace root). The candidate skill list is the set of parent-parent directory names (i.e. for `<project>/.claude/skills/session-wrap/evals/evals.json`, the candidate is `session-wrap`).

The deterministic implementation of this entire Phase 1 resolution (discovery + skip-list filter + 24h freshness filter + alphabetical order, plus the `--dry-run` plan text) is `<skills-root>/skill-iterate/scripts/resolve_queue.py --project <project>`, per §Path resolution. The orchestrator SHOULD call it and parse its JSON output (or `--dry-run` text) rather than re-deriving the glob by hand — this keeps the cross-tree `--project` rebasing in one tested place.

For each candidate, verify BOTH `evals/evals.json` AND `evals/test_scenarios.json` exist. Candidates missing `test_scenarios.json` are dropped SILENTLY — half-bootstrapped skills (eval suite started but not finished by `/skill-eval-setup`) are not ready for iteration, and surfacing them as warnings would noise the overnight run with operator-known incomplete work.

Skip auto-discovery entirely when `--skill <name>` or `--queue <path>` was passed. In those cases, the queue is the operator's explicit list (already validated in Phase 0), filtered only by the cross-night-resume filter below.

#### Skip-list filtering

Remove candidates whose name is in the merged skip-list from Phase 0. The `--skip-list` extension applies to BOTH auto-discovery AND `--queue`-driven runs (operators who extend the skip-list want that extension respected even when they hand-curated a queue file; in practice an operator wanting to override the skip-list per-run would edit the `--queue` file directly rather than passing `--skip-list`).

Explicit `--skill <name>` was already validated against the skip-list in Phase 0 and would have halted there — so by Phase 1, an explicit `--skill` is either in-list (halted) or not-in-list (proceeds unfiltered).

#### Cross-night-resume filter (24h freshness)

For each remaining candidate: if `.claude/skills/<name>/evals/results.tsv` exists AND its mtime is within the last 24 hours (UTC), SKIP it silently. This deduplicates back-to-back overnight runs against the same fleet.

Comparison uses `time.time() - st_mtime < 86400` (epoch-seconds, platform-portable; `st_mtime` is UTC epoch on all platforms — no timezone conversion required).

Three caveats apply:

- **Hard 24h cliff.** A skill that ran 23h ago is filtered; a skill that ran 26h ago is eligible. Manual `touch .claude/skills/<name>/evals/results.tsv` resets the window if the operator wants to force re-iteration.
- **No round-robin preservation.** The filter is strictly mtime-based — there is no rotation that prefers skills not run recently.
- **Acceptable for default.** Operators wanting different semantics (run all every night, run only N skills in rotation) use `--queue <file>` to override; the default's role is to drain stale skills serially.

#### Queue ordering

Alphabetical by skill name. This is deterministic and reproducible — the morning summary in Phase 4 can be cross-referenced run-over-run with predictable ordering, and a partial-run kill-switch stop leaves a predictable "what was processed" boundary.

#### Target resolution

For each queued skill, resolve the file this run scores and edits — its **contract file** — and whether that file is generated. Read `<project>/.claude/skills/<name>/SKILL.md`:

- **Contract file.** The complete recognized defer set is a `Core: core.md` line or a `See [core.md](core.md) …` link. Exactly one defer form must be present to select the sibling core. Neither form selects SKILL.md itself. Both forms together are ambiguous and are skipped below rather than scored as a launcher proxy. Render agents read only the file they are given, so scoring a deferring launcher measures a proxy, not the behavior the host loads (the workspace measurement-validity rule: score the production artifact). `<contract-path>` below is the contract file's path relative to `<project>`; every later step uses it where older prose says "SKILL.md".
- **Generated.** The contract file is generated when it contains the marker `SKILL-MESH-GENERATED-FILE`. Its **canonical destination** is the `Canonical source:` path in that marker comment, inside the Skill Mesh source tree (a `core.md`, or `providers/<host>.md` for a provider-native skill).
- **Install tree.** `<project>/.claude/skills/` is a **Skill Mesh install** when the `SKILL.md` or `core.md` of any skill folder in it carries the marker. An install tree is a consumer discovery root owned by the installer (`skill-catalog-lifecycle.md`, class table). An unmarked file there does not prove a hand-authored skill, so the resolver fails closed: only a project whose skill tree carries no marker at all has `merge` targets.
- **Mode.** `merge` for an unmarked contract file in a tree that is not a Skill Mesh install. `proposal` for a generated one: the full loop still runs in the disposable per-skill worktree, but Phase 3 never merges it and routes any earned change to a proposal (`review-required`). Editing or merging install output is forbidden (`skill-mesh/docs/skill-catalog-lifecycle.md`, "Forbidden, without exception"; workspace rule: edit the canonical source and rebuild).

Drop the skill from the queue and print `target skipped: <name> (<reason>)` when:

- `mixed-install` — SKILL.md carries the marker but the core it defers to does not: no canonical destination can be named, and treating the core as non-generated would merge into install output.
- `unrecognized-deferral` — SKILL.md carries the marker, has a sibling `core.md`, and contains neither recognized defer form: the production contract is ambiguous, so do not score the launcher proxy.
- `ambiguous-deferral` — SKILL.md contains both recognized defer forms: two independent directives name the core, so fail closed instead of guessing which directive owns production behavior.
- `unmarked-install` — the contract file carries no marker but the tree is a Skill Mesh install (for example a legacy compatibility launcher): no canonical destination can be named, and `merge` would edit install output. A target is never `merge` in an install tree.
- `untracked-target` — the contract file, its `evals/evals.json`, or its `evals/test_scenarios.json` is not committed at `HEAD` in `<project>` (the corresponding `git -C <project> cat-file -e HEAD:./<path>` fails; the `./` resolves each path from `<project>`, not from the repository root), so a fresh `git worktree add` would not contain the complete scored input.

These are per-skill skips, never run halts.

#### --dry-run handling

When `--dry-run` is set, after the queue is resolved and targets are resolved, print to stdout:

1. The resolved queue (one skill name per line, in queue order).
2. For each skill in queue: the worktree path that WOULD be created — `<workspace-parent>/worktree_skill-iterate-<skill>-<epoch>` (with a placeholder `<epoch>` so the operator sees the path shape).
3. Per-skill budget plan: `<budget>` wall-clock cap (default `1h`), `<iterations>` iteration cap (default `12`).
4. Skills excluded by skip-list (one per line, with reason `skip-list: <embedded|--skip-list extension>`).
5. Skills excluded by the cross-night-resume filter (one per line, with the `results.tsv` mtime).
6. After that text, a `Target modes:` block: one line `  <name> -> <contract-path> (<merge|proposal>)` per queued skill, then any `target skipped` lines.

Items 1–5 use `resolve_queue.py`'s `--dry-run` output; that helper owns their exact formatting and may add its documented half-bootstrapped block. The example below is illustrative rather than a string-equality target. The helper abbreviates `<workspace-parent>` as `~` in its printed worktree paths. ASCII hyphens throughout (no em-dashes per the workspace Windows-shell rule § Shell args):

```
Resolved queue (1 skill):
  session-wrap

Per-skill worktrees:
  session-wrap -> ~/worktree_skill-iterate-session-wrap-<epoch>

Per-skill budget:
  budget=1h iterations=12

Excluded by skip-list:
  skill-evolve  (skip-list: --skip-list extension)

Excluded by cross-night-resume filter:
  user-debug  (results.tsv mtime: 2026-05-23T22:15:04Z)
```

Then EXIT 0 without running the launch gate, entering Phase 2 or taking the lock file. `--dry-run` does NOT touch the lock; it is a pure inspect-and-exit mode per the workspace plan-and-issue-flow rule § "Autonomous-by-default skills" (preview behavior uses an opt-in flag, never an after-the-fact prompt).

#### Empty queue handling

If the resolved queue is empty after all filtering (everything skip-listed or cross-night-skipped), print:

```
Queue empty -- nothing to iterate. All scorable skills were either skip-listed or have results.tsv mtime within the last 24h.
```

Then exit 0. This is a clean exit, not a defect — it means the prior overnight run drained the fleet and this run has nothing to do. If target resolution dropped every remaining skill, print its `target skipped` lines first; the exit is the same.

#### Launch gate

Runs only when the queue is non-empty and `--dry-run` is off. Nothing has been written yet. A failed check halts under §Autonomy contract clause 1 with `required_tool_missing`, naming what is missing:

1. **Host workflow primitive.** Phase 2 Step D runs the shared scoring workflow through it. A host without one halts here — before the lock, any worktree or any agent — and never self-grades or serializes render and grade into one context instead (see the provider adapters).
2. **Helpers.** `<skills-root>/_shared/score_skill.workflow.js`, `<skills-root>/skill-iterate/scripts/append_result.py` and `<skills-root>/skill-iterate/scripts/morning_summary.py` exist, and `python -B <skills-root>/_shared/score_skill_composite.py --help` exits 0 (the composite scorer imports the structural and differential helpers from `<skills-root>/skill-iterate/scripts/` at load time).
3. **Repository identity.** `git -C <project> rev-parse --show-toplevel` names `<project>` itself (compare normalized absolute paths); otherwise halt with `project-not-toplevel`. `git -C` on a directory that is not its own top level resolves to an enclosing repository, so every worktree, commit and merge would land there. With this check, the commit repository is always the target `<project>`.
4. **Lock.** Take the lock file (below).

#### Take the lock file

After the launch-gate checks above pass, write `.skill-iterate.lock` at workspace root with JSON:

```json
{"pid": <int>, "started_at": <iso8601>, "host": <hostname>}
```

**The write MUST use atomic exclusive-create**, not a check-then-write sequence. The implementation:

- Python: `open(path, 'x')` mode, OR `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`.
- On `FileExistsError`: another process owns the lock — fall through to the stale-PID branch documented in §Autonomy contract → Concurrent-run detection. Read the existing lock's PID, check `Get-Process -Id <pid>` on Windows or `kill -0 <pid>` on POSIX:
  - PID alive → halt per §Autonomy contract clause 1 (live lock).
  - PID dead → unlink the stale lock, retry the exclusive-create ONCE. If the retry also raises `FileExistsError` (a third process raced in between unlink and retry), halt defensively rather than overwriting blindly.

The atomic exclusive-create is what makes the concurrent-run halt actually exclusive; check-then-write would race. The §Autonomy contract → Concurrent-run detection section above describes the contract (the WHAT — "lock file exists + PID alive → halt"); this subsection specifies the implementation contract (the HOW — atomic exclusive-create, not check-then-write). Do not split the check and the write into two filesystem ops.

Schema and takeover semantics per §Autonomy contract → Concurrent-run detection. The lock is held until clean exit (Phase 3 final cleanup) or kill-switch stop (Phase 3 mid-queue check). Unclean exit (Python exception, signal) leaves the lock stale; the next run takes over per the §Autonomy contract takeover rule.

#### Adversarial-mutation calibration (opt-in via `--calibrate`)

OFF by default. When `--calibrate` is set, after the launch gate but BEFORE the per-skill iterate loop (Phase 2) begins, run [`scripts/adversarial_calibration.py`](scripts/adversarial_calibration.py) for each queued skill against its contract file. `calibrate_skill` reads `<skill_dir>/SKILL.md`, so pass a temporary directory holding a byte copy of the contract file named `SKILL.md` (discarded afterwards), and the structural score function the helper's own CLI uses:

```python
from adversarial_calibration import calibrate_skill, GRADER_BROKEN_CRASH_CLASS, _default_structural_score_fn
result = calibrate_skill(tmp_dir, _default_structural_score_fn, num_mutations=10, threshold=0.70)
if result["verdict"] == GRADER_BROKEN_CRASH_CLASS:
    # defect-park this skill BEFORE entering Phase 2
    ...
```

The procedure injects 10 known defects into copies of the contract file (mutation kinds: delete required bullet, paraphrase heading, remove code fence, swap MUST with should, delete section, duplicate paragraph, remove leading imperative, remove constraint line, add trailing garbage, shuffle steps), scores each, and computes the catch rate (fraction whose score dropped strictly below baseline). A Python callable cannot drive the host scoring workflow, so this pass measures the deterministic **structural floor** only — whether the structural axis drops for injected defects. It does not calibrate the LLM grader; the garbage-anchor check in Phase 2 does. Verdicts:

- `verdict == "ok"` — catch rate `>= 70%` (configurable via the CLI `--threshold` flag). Skill proceeds into Phase 2 normally.
- `verdict == "grader-broken-for-skill"` — catch rate `< 70%`. The scorer cannot reliably tell defective from baseline content on this skill; the iteration loop would produce no useful gradient. Defect-park before the skill enters Phase 2:
  - File a GitHub issue using the same `gh issue create` flow Phase 3 uses for clause-3 defect-park, with title `skill-iterate: <skill> grader-broken-for-skill (calibration catch rate <N>%)`. The issue body MUST include the full `calibrate_skill` result dict (mutation kinds, per-mutation scores, baseline score, threshold) so the operator can see exactly which defect classes the grader is missing.
  - On `gh issue create` failure, write the same body to `docs/skill-iterate-runs/calibration-broken-<skill>-<epoch>.md` (mirroring the Phase 3 local-fallback path documented in [§Per-skill ship gate → Ship decision § defect-park](#per-skill-ship-gate)).
  - Skip this skill; advance to the next in the queue.
  - This does NOT count toward the consecutive-crash defect-park counter — calibration runs once per skill at pre-flight, before any iteration has happened.

Calibration is off by default because (a) its verdict covers only the structural floor, while the always-on garbage anchor covers the grader, and (b) it has the cross-night-resume problem the iteration loop solves with its 24h freshness filter — re-running calibration nightly produces near-identical verdicts. Recommended cadence: weekly (passed explicitly on Monday-morning runs) OR after any grader-prompt / grader-model change OR after a material SKILL.md rewrite. See `../../../docs/investigations/skill-iterate-hill-climbing/06-adversarial-mutation-grader-discrimination-tests.md` § When to apply.

### Phase 2 — Per-skill iterate loop

For each skill in the resolved queue, run the steps below in order. The loop is the heart of this skill; every other phase exists to set it up or wrap it up. The loop NEVER halts mid-iteration for operator input — see §Autonomy contract.

#### Per-skill pre-flight

Before entering the loop, confirm the following for the current skill (the orchestrator-level pre-flight in Phase 0 already ran; this is the per-skill repeat for late-discovered defects):

- Skill folder exists at `.claude/skills/<name>/`.
- Both `evals/evals.json` and `evals/test_scenarios.json` exist.
- Skill name is not in the merged skip-list, unless `--force-skip-collision` was passed; then emit the collision warning again and continue. Per-skill pre-flight warnings are advisory only.
- Cross-night-resume filter: either `evals/results.tsv` is absent, or its mtime is older than 24h. Skills with a fresher results.tsv are skipped silently (deduplicated overnight runs).
- The contract file and its mode still match target resolution.
- The orchestrator-level concurrent-run detection from §Autonomy contract already ran in Phase 0; do NOT re-check the lock file or worktree scan here.

Any pre-flight failure here removes this skill from the queue and advances to the next; it does NOT halt the whole run.

#### Worktree setup

- Worktree path: `<workspace-parent>/worktree_skill-iterate-<skill>-<epoch>` (note: workspace-root parent dir, NOT inside `dev/`). Same parent-dir convention as `/skill-evolve`'s worktrees, with a distinct `skill-iterate` namespace.
- Branch name: `skill-iterate/<skill>-<epoch>`.
- The `skill-iterate/*` branch namespace is deliberately distinct from autoresearch's `autoresearch/*` namespace to avoid sibling collision in this workspace.
- Record `<base-sha>` = the full 40-hex output of `git -C <PROJECT> rev-parse HEAD` and `<base-ref>` = `git -C <PROJECT> symbolic-ref -q --short HEAD` (empty when HEAD is detached), then create the worktree from `<base-sha>`: `git -C <PROJECT> worktree add -b skill-iterate/<skill>-<epoch> <worktree-path> <base-sha>`. Set `<kept-sha>` = `<base-sha>`; it is always a full 40-hex SHA naming the most recently kept, scored commit. Every equality check involving `<base-sha>`, `<kept-sha>` or `<iter-parent>` compares the full value. Only the `results.tsv` commit column and operator messages use a 7-character short SHA. `<work_dir>` below is this worktree path (Step D's `work_dir`); scoring artifacts stay untracked there.
- Define the **worktree identity guard** immediately after creation. Refuse an empty `<worktree-path>`. Resolve it to an absolute normalized path, require `git -C <worktree-path> rev-parse --show-toplevel` to resolve to that exact path and not `<PROJECT>`, require `git -C <worktree-path> symbolic-ref --short HEAD` to equal `skill-iterate/<skill>-<epoch>`, and require that exact path/branch pair in `git -C <PROJECT> worktree list --porcelain`. A failure is `branch-state`; run no commit, reset, removal or deletion. Re-run the guard at every iteration start and immediately before every commit, `reset --hard` or `worktree remove --force`. After a successful removal, a branch deletion instead requires that the path/branch pair is absent from `worktree list --porcelain` and that `refs/heads/skill-iterate/<skill>-<epoch>` still resolves to the expected branch tip; otherwise keep the branch.
- After creating the worktree, follow the workspace worktree-hygiene rule #1: fresh worktrees do NOT inherit dependencies. For a prose-skill workspace there is typically nothing to install, but if a future scoring fragment depends on tooling, this is where it runs.

#### Baseline and anchor capture

The baseline is captured before any edit and does not count as an iteration. Lock it first: an edit made before the baseline is scored inflates the baseline and hides the edit's gain. Procedure:

1. Require worktree HEAD to equal `<base-sha>` and `git -C <worktree-path> diff --quiet <base-sha> -- <contract-path>` to exit 0. Define `<baseline-sha256>` as the SHA-256 of the **committed blob bytes**, obtained by a short Python launcher using `subprocess.run(["git", "-C", <worktree-path>, "show", "<base-sha>:<contract-path>"], stdout=subprocess.PIPE, check=True)` and hashing `stdout`; do not use a shell pipe or text decoding. The checkout may be a clean CRLF materialization of an LF blob, so its raw-file hash may legitimately differ and is not the baseline identity.
2. Write the **garbage anchor** — a known-garbage stand-in for the skill — to `<work_dir>/garbage.md` with exactly this content: a `# <name>` line, a blank line, and the line `This skill has no instructions.`
3. Score both in ONE invocation of the scoring workflow (Step D's call shape) with two versions: `{ id: "baseline", label: "<name>", skill_md_path: "<worktree>/<contract-path>" }` and `{ id: "garbage", label: "<name>-garbage", skill_md_path: "<work_dir>/garbage.md" }`, under a 20-minute hard timeout (Step D's 10-minute cap, once per version). Apply §Integrity checks to both. Make at most three attempts:
   - The baseline version fails a check, or the call times out or errors: the attempt is a baseline `crash`. Append a `crash` row and retry.
   - Only the garbage version fails a check: append no row, print `warning: garbage anchor unscorable for <skill> (<check>)` and retry. This attempt is not a baseline crash.
   - If all three attempts were baseline crashes, defect-park the skill (§Autonomy contract clause 3) without entering Step A. If three attempts end without one that passed both versions, and they were not all baseline crashes, take the park defined in item 4 with reason `anchor-unscorable`, skipping that item's `g`/`b` comparison, so no `baseline` row is appended: a grader that cannot be calibrated is not trusted, and neither is its baseline score.
4. **Anchor gate** (calibrate the grader before trusting it). Evaluate this gate before writing any `baseline` row. Count only **firing pairs**. A passing pair `(assertion_id, scenario_id)` is firing when `assertion_id` is in that scenario's `expected_assertions` in `test_scenarios.json`; in a scenario whose `expected_assertions` is empty or missing, every pair is firing. Non-firing pairs grade TRUE without the grader inspecting the output (`_shared/grader_prompt.py`, PRIMARY RULE), so they cannot tell a skill from garbage. Let `b` be the number of the baseline's firing passing pairs and `g` the garbage anchor's. The grader must not pass garbage at least as often as the real skill: if `g > 0` and `g >= b`, the skill is `grader-broken-for-skill` (reason `anchor`). When `g == 0` the gate passes, so a deeply-failing baseline still enters the loop. Park, for either reason:
   - Write `docs/skill-iterate-runs/calibration-broken-<skill>-<epoch>.md` with the reason, both versions' scores, firing and total `pairs_passed`, and passing pairs (for `anchor-unscorable`, those the final attempt produced, plus each attempt's failed check). Copy the `composite_*`, `absolute_*`, `payload_*`, `render_*` and `verdicts_*` files the final attempt left in `<work_dir>` (each attempt overwrites them; for reason `anchor` the final attempt is the gated one) into the folder `docs/skill-iterate-runs/calibration-broken-<skill>-<epoch>/`, so the evidence outlives the worktree.
   - Print `warning: grader-broken-for-skill (<reason>) for <skill>; parked locally at <path>`.
   - After any per-attempt baseline-crash rows, append exactly one freshness row with `commit=<short base-sha>`, `score=NULL`, `status=crash`, `description=anchor-park: <reason>; contract=<contract-path>; sha256=<baseline-sha256>`, and the elapsed wall time. Append no `baseline` row for either `anchor` or `anchor-unscorable`.
   - Remove the worktree and delete the branch only after the unmerged-commit check (its tip is `<base-sha>`, so the check normally passes and nothing is lost; Phase 3 § Worktree cleanup), run the between-skill kill-switch poll, and advance to the next skill.
   - This park files no GitHub issue and does not touch the consecutive-crash counter.
5. Only after the anchor gate passes, append a row to `<project>/.claude/skills/<name>/evals/results.tsv` with `commit=<short base-sha>`, `score=<baseline score>`, `status=baseline`, `description=initial baseline; contract=<contract-path>; sha256=<baseline-sha256>`, `wall_seconds=<elapsed>`. Columns: `commit\tscore\tstatus\tdescription\twall_seconds`. The schema has no scored-artifact column, so the description carries the identity.
6. Record the passing baseline score, its `pairs_passed`, its line count and its `absolute_baseline.json` path for Step A, Step F and Phase 3.

#### Per-iteration loop body

Repeat steps A through H until the budget cap fires (see Step H). Steps A through G are one logical "iteration"; the iteration counter increments on each cycle (baseline does NOT count). At the start of each iteration, first run the worktree identity guard, confirm `git -C <worktree-path> rev-parse HEAD` equals `<kept-sha>`, and require `git -C <worktree-path> status --porcelain --untracked-files=no` to exit 0 with empty output. Then record `<iter-parent>` = the full 40-hex `<kept-sha>` and the contract file's SHA-256; all later equality and reset checks use that full SHA. If the check fails (for example a revert or crash reset did not complete), start no iteration: exit the loop, and Phase 3 Routing step 1 defect-parks the skill with reason `branch-state`.

**Step A — brainstorm one hypothesis.** Dispatch ONE read-only sub-agent (no edit or write tools) on the sonnet tier, passing that model explicitly whatever agent type is used: a host's built-in read-only type, such as an Explore agent, can default to a different model, so where the host cannot set the model on that type, use a general agent with the edit and write tools withheld. Give it (a) the path of the current contract file in the worktree, and (b) the absolute-grader aggregate ([`../../_shared/score-skill.md`](../../_shared/score-skill.md) §Absolute grading) of the version currently in the worktree: after a keep, that iteration's `absolute_<id>.json`; after a revert or crash, the most recently kept version's (the baseline's until the first keep). The "do not break" list must describe the file being edited. The aggregate's `failed_assertions` list (already sorted by `-category_weight, assertion_id` per the aggregator in `score_skill_absolute.aggregate()`) selects which branch of the prompt fires. Design source: `../../../docs/investigations/skill-iterate-hill-climbing/07-failed-assertion-targeted-brainstorm-prompts.md`.

**A.1 — Targeted mode** (when `failed_assertions` is non-empty). The sub-agent prompt contains:

- The path of the current contract file (the working copy in the per-skill worktree); the sub-agent reads it in full. The orchestrator does not paste the body into the prompt.
- The top-ranked failure (`failed_assertions[0]`) — passed in full, with every field visible: `assertion_id`, `category_name`, `category_weight`, `statement` (the assertion text the grader applied), `source` (the `file:line` reference into the eval source doc), `defect_type` (e.g. "structural — missing required output part", "format — wrong fence label"), `grader_reason` (the grader sub-agent's reason for marking this assertion false).
- The remaining failures (`failed_assertions[1:]`) in compact form — `assertion_id`, `statement`, `category_weight` only — so the sub-agent knows what else needs fixing without burning context on full records. If only one failure exists, `remaining_failures_compact` is empty; the orchestrator omits the "Other failures" block from the substituted prompt.
- The path of the aggregate file whose `passing_pairs` list holds every `(assertion_id, scenario_id)` tuple currently grading TRUE, in the JSON-array shape returned by `score_skill_absolute.aggregate()` (list of `{assertion_id: int, scenario_id: str}` objects, lex-sorted by `(assertion_id, scenario_id)`). This is the "do not break" anchor; the sub-agent reads it from the file. If `passing_pairs` is empty (typical only on iteration 1 of a deeply-failing skill), the sub-agent emits the literal substitute string per the template; the "do not break" contract is vacuously satisfied.

The sub-agent is instructed to:

- Propose ONE minimal, named edit to SKILL.md that targets the top-ranked failure.
- Cite at least one passing pair in its rationale — proves it considered side-effects.
- Return the edit as `{description, old_string, new_string}` for Step B to apply.
- NOT propose unrelated mutations or whole-section rewrites.

The literal prompt template the orchestrator hands to the Step A sub-agent (via a fresh-context task invocation using the sonnet tier (resolve via model-tier-map.json; pass it explicitly, per Step A) — hill-climb iteration + revert-on-regression carry the quality; the arm must not inherit an escalated session) — `{{placeholder}}` syntax marks fields substituted at dispatch time. In both templates "SKILL.md" means the contract file (§Target resolution), which may be a `core.md`:

```text
You are a strict editor. Propose ONE minimal, named edit to a SKILL.md to make the
top-ranked failing assertion grade TRUE on the next scoring pass — without breaking
any currently-passing (assertion, scenario) pair.

Current SKILL.md (read this file in full before proposing; it is the only file
your edit may touch):
{{current_contract_file_path}}

Top-ranked failure (anchor your edit on this one):
  assertion_id:     {{top_failure.assertion_id}}
  category:         {{top_failure.category_name}} (weight={{top_failure.category_weight}})
  statement:        {{top_failure.statement}}
  source:           {{top_failure.source}}
  defect_type:      {{top_failure.defect_type}}
  grader_reason:    {{top_failure.grader_reason}}

Other failures (compact — for context only, do NOT target):
{{remaining_failures_compact}}
  (each line: "  id={{id}}  weight={{weight}}  statement: {{statement}}")
  (omit this entire block if remaining_failures is empty)

Passing pairs (the "do not break" anchor — your edit MUST NOT regress any of these):
the "passing_pairs" array in {{aggregate_json_path}}
  (a JSON array of {assertion_id, scenario_id} objects, lex-sorted by
  (assertion_id, scenario_id) per score_skill_absolute aggregator output)
  (if empty: the orchestrator replaces the line above with the literal text "(no passing pairs — first iteration on a deeply-failing skill)")

Return a JSON object with exactly three keys:
  {
    "description": "one-line summary of the edit, in present tense",
    "old_string":  "exact text to be replaced in SKILL.md (must be unique in the file)",
    "new_string":  "replacement text"
  }

In `description`, cite at least one passing pair you considered (by assertion_id) and
explain why your edit does not regress it. If passing_pairs is empty, cite "(none —
deeply-failing baseline)" verbatim instead. Failure to cite is a violation of the
"do not break" contract.

Do NOT propose unrelated mutations, whole-section rewrites (unless radical mode is on),
or edits that touch other files.
```

Anchoring on `failed_assertions[0]` follows operator D2 (2026-05-26): "highest category weight first." The remaining failures are context, not targets.

**A.2 — Simplification mode** (when the current version's three-trial aggregate has an empty `failed_assertions`, i.e. all-pass — see "Mode selection" below). The sub-agent prompt contains:

- The path of the current contract file; the sub-agent reads it in full.
- The path of the aggregate file whose `passing_pairs` list holds every assertion currently protected, in the same JSON-array shape as A.1 (`score_skill_absolute.aggregate()` output: list of `{assertion_id: int, scenario_id: str}` objects, lex-sorted by `(assertion_id, scenario_id)`).

The sub-agent is instructed to:

- Propose ONE minimal SIMPLIFICATION — delete a redundant section, fold two near-duplicate rules, remove an example that adds no discrimination, tighten verbose prose.
- NOT propose behavioral mutations — no rule changes, no new sections, no example additions.
- Explicitly note in rationale: "this is a simplification-mode edit; no failing assertion to target."
- Return the edit as `{description, old_string, new_string}`.

The literal prompt template the orchestrator hands to the Step A sub-agent in simplification mode (via a fresh-context task invocation using the sonnet tier (resolve via model-tier-map.json; pass it explicitly, per Step A) — same arm pin as targeted mode):

```text
You are a strict editor. The SKILL.md below currently passes all grader assertions
(verified by the N=3 median of /skill-iterate Phase 2 Step D). Your job is to
SIMPLIFY — delete a redundant section, fold two near-duplicate rules, remove an
example that adds no discrimination, or tighten verbose prose.

DO NOT propose a behavioral mutation: no rule changes, no new sections, no example
additions. There is no failing-assertion signal to optimize against; behavioral
changes would be unguided and likely score-neutral or score-negative.

Current SKILL.md (read this file in full before proposing; it is the only file
your edit may touch):
{{current_contract_file_path}}

Passing pairs (every assertion currently grades TRUE — do not regress any of these):
the "passing_pairs" array in {{aggregate_json_path}}
  (a JSON array of {assertion_id, scenario_id} objects)

Return a JSON object with exactly three keys:
  {
    "description": "one-line summary of the simplification, must include the phrase
                    'this is a simplification-mode edit; no failing assertion to target.'",
    "old_string":  "exact text to be deleted/replaced (must be unique in the file)",
    "new_string":  "replacement text (often shorter; '' for pure deletion)"
  }
```

**Mode selection.** Every scoring call grades each scenario three times (Step D), so `failed_assertions` is always the per-(scenario, assertion) majority over three grades (ties → `False`). Step A fires targeted mode when the current version's `failed_assertions` is non-empty and simplification mode when it is empty. Brainstorm is therefore always gated on a median signal: a noisy single-grade all-pass cannot trigger simplification.

**Radical-mode integration.** The 3-consecutive-`revert` trigger from prior Step A is preserved across both branches. After 3 consecutive reverts on the targeted branch, the prompt explicitly invites larger restructures — delete a whole section, rewrite a section, swap orderings — while still anchored on the top-ranked failure. After 3 consecutive reverts on the simplification branch, the prompt invites more aggressive simplification — merge two sections, not just delete a paragraph. The consecutive-revert counter is **shared** between branches; a switch from targeted to simplification (or vice versa) does NOT reset it. A keep on either branch resets the counter to 0 and the next iteration's Step A reverts to the default minimal-edit prompt. The threshold of 3 mirrors autoresearch's anti-stagnation pattern.

**Step B — apply edit.** First validate: the contract file's SHA-256 still equals the value recorded at the start of the iteration (the Step A agent changed nothing), and the Step A return is a JSON object with exactly the keys `description`, `old_string` and `new_string`, where `old_string` differs from `new_string`. Save that return as BOM-less UTF-8 JSON at `<work_dir>/stepA_<N>.json`; never pass the strings as command-line arguments. A short Python script reads the contract as bytes, preserves any UTF-8 BOM, rejects invalid UTF-8 or mixed line endings, detects its single line-ending convention (LF or CRLF), normalizes only the two JSON strings to that convention, encodes them as UTF-8, and requires the resulting `old_string` bytes to occur exactly once. Replace that one byte span and write `prefix + bytes_before + replacement_bytes + bytes_after`; verify every byte outside the selected span is unchanged and only `<contract-path>` changed. Do not decode and re-emit the whole file, use a shell byte pipe, or impose a `numstat` line-count bound: a legitimate exact replacement can add or remove arbitrary lines, while the byte-span proof precisely detects unrelated changes. The edit MUST be in-place: no unrelated section is refactored, no whitespace is reflowed, and no other file is touched. A failed validation is a `crash` with no commit; its `description` (if any) is still recorded.

**Step C — git commit.** Re-run the worktree identity guard. In the per-skill worktree, run two separate commands (never chained with `&&`, which is a PowerShell 5.1 parser error): `git -C <worktree-path> add -- <contract-path>`, then `git -C <worktree-path> commit --file <message-file> -- <contract-path>`, where `<message-file>` is a BOM-less UTF-8 temp file holding the one-line edit description (an inline `-m "<description>"` splits on embedded double quotes in PowerShell). A commit was created only when both commands exit 0 and `git -C <worktree-path> rev-parse HEAD` now differs from `<iter-parent>`; otherwise the iteration is a `crash` (git op failed). Capture the full 40-hex `git -C <worktree-path> rev-parse HEAD` value; only its first 7 characters go in `results.tsv` and operator messages. Per the workspace worktree-hygiene rule #5, prefer `git -C` over `cd`-then-git to avoid silent no-ops in the wrong worktree.

**Step D — run scoring with 10-min hard timeout.** Score the modified contract file via the composite procedure documented at [`../../_shared/score-skill.md`](../../_shared/score-skill.md) (default mode: `composite`): structural metrics + `absolute_weighted`, weights `0.4 / 0.6`. **Hard wall-clock timeout: 10 minutes per iteration**, per `primatives/autoresearch/program.md:108-110`. On timeout, kill the scoring subprocess (or interrupt the scoring sub-agent dispatch), and classify the outcome as `crash` per the §Autonomy contract iteration outcome taxonomy. The timeout enforcement is the caller's responsibility — the shared scoring fragment does NOT enforce it internally.

The scoring is delegated to the shared scoring workflow at [`../../_shared/score_skill.workflow.js`](../../_shared/score_skill.workflow.js), which performs the render/grade split for you: a RENDER task produces each scenario's output, a SEPARATE GRADER task grades it (no task grades its own output; the grader prompt is built from `_shared/grader_prompt.py::build_grader_prompt` inside the workflow), then it aggregates via `score_skill_composite.py` + `score_skill_absolute.py`. Invoke structured multi-step orchestration via the host's workflow primitive with the script path (the shared workflow _shared/score_skill.workflow.js under `<skills-root>`) and arguments below:

```
scriptPath: "<skills-root>/_shared/score_skill.workflow.js"
args: {
    shared_dir: "<skills-root>/_shared",
    work_dir:   "<per-skill worktree path>",
    evals_dir:  "<worktree>/.claude/skills/<name>/evals",
    trials:     3,
    versions:   [{ id: "iter<N>", label: "<name>", skill_md_path: "<worktree>/<contract-path>" }]
}
```

It returns one result object per version, `{ id, label, skill_md_path, score, passed, total, status, failed_assertions, passing_pairs }`. The orchestrator then applies §Integrity checks: the recomputed composite is the score for Step F's keep/revert decision, and the recomputed aggregate file supplies `failed_assertions` (already ranked by category weight; Step A's brainstorm anchor) and `passing_pairs` (the "do not break" list). Keeping render and grade as separate agents is non-negotiable — the 2026-05-27 M2 launch showed consolidated render+grade graders misgrade vacuous-true assertions (see [`../../_shared/score-skill.md`](../../_shared/score-skill.md) §Absolute grading). The numbered per-scenario dispatch contract the workflow implements internally is documented in that fragment's § Orchestrator-LLM as dispatcher.

A failed dispatch — a grader task crashes mid-run, a fresh-context task invocation returns no output, or the render step raises — or any failed integrity check classifies the iteration as `crash` per the §Autonomy contract iteration outcome taxonomy. No score is computed from incomplete trials.

**Three trials on every call.** Every scoring call — baseline and garbage anchor, and every iteration — passes `trials: 3` (k≥3 judge samples, the workspace measurement-validity reference § Calibrate with anchors). The workflow renders each scenario ONCE and grades it 3× on that fixed render, so the median measures grader stability on the same input, not render-side variance. The aggregator collapses per-(scenario, assertion) verdicts by majority vote (ties → `False`) THEN computes one canonical float from the collapsed verdicts; the score is NOT `mean(trial1, trial2, trial3)`. See `_shared/score-skill.md` §Absolute grading § N=3 median trigger for the aggregation contract (that section still describes N=3 as saturation-only; this skill applies it to every call). The 10-min hard timeout covers the whole call (20 minutes for the two-version baseline call). Cost per scored version for an S-scenario skill: 1 load + S render + 3S grade + 1 aggregate agents (14 for S = 3); a baseline call scores two versions.

NOTE: Goldens-verification handling (per SIHC.1 Step 12) is unwired from this loop body as of SIHC.2 (Option A); see `_shared/score-skill.md` § Goldens verification for the standalone-callable function. Direct invocation by future callers remains supported.

**Step E — extract score.** Take the recomputed composite `score` from §Integrity checks as the iteration's single canonical score, a float in `[0.0, 1.0]`. Classify in this order:

1. If `score` is missing, null, or non-numeric, or any integrity check failed, classify as `crash` per the taxonomy (reserved for harness-side failures only).
2. Else, proceed to Step F's delta comparison with the numeric `score`.

**Step F — decide keep / revert / crash, append results.tsv row, then apply git op.** Apply the iteration outcome taxonomy from §Autonomy contract. For each outcome, append the results.tsv row FIRST (Step G), THEN run any git side-effect — this preserves the commit SHA in the audit trail before a revert orphans it:

- **keep** — score improved (delta > 0): advance the branch (the commit from Step C already exists) and set `<kept-sha>` to it. Reset the consecutive-revert counter to 0. Reset the consecutive-crash counter to 0. Append results.tsv row. No further git op needed.
- **simplicity-bias on ties** — if the candidate edit shrank the contract file (net negative line count delta) AND the score delta is `>= 0`, classify as `keep` per `primatives/autoresearch/program.md:37` ("removing something and getting equal or better results is a great outcome — that's a simplification win"). This explicit override prevents the loop from rejecting deletion-only simplifications.
- **revert** — a well-formed result has score delta `<= 0` (and is not a simplicity-bias keep): Append results.tsv row with the Step C commit SHA FIRST, re-run the worktree identity guard, THEN `git -C <worktree-path> reset --hard <iter-parent>`. The TSV-before-reset ordering ensures the audit trail row exists before the SHA is removed from branch history. Increment the consecutive-revert counter (feeds the Step A radical-mode threshold). Reset the consecutive-crash counter to 0.
- **crash** — any `status != "ok"` result (including `unparseable`), failed integrity check, failed Step B validation, scoring exception, missing required field, unhandled error, 10-min timeout, or git op failure: Append results.tsv row with the new commit SHA when Step C created one, otherwise `commit=none`. Re-run the worktree identity guard, THEN `git -C <worktree-path> reset --hard <iter-parent>` in every case, so neither an unscored commit nor an uncommitted edit stays where a later keep or Phase 3 would carry it; the reset changes nothing when nothing changed. If the guard fails, perform no reset and route to the `branch-state` park. Increment the per-skill consecutive-crash counter. Do NOT touch the consecutive-revert counter. Three consecutive crashes triggers §Autonomy contract clause 3 — park the skill via a GitHub issue and advance to the next skill in queue (handled by Phase 3, not this loop body).

The keep/revert decision compares against the **most recent kept score** (baseline on iteration 1, then the running high-water mark), not the immediate-prior iteration's score — revert and crash iterations don't change the comparison anchor. The iteration's score is always the three-trial composite from Step D. Track the most recently kept version's `<kept-sha>`, `pairs_passed`, line count and aggregate file alongside its score; Step A and Phase 3 use them.

**Step G — append results.tsv row.** Save the six validated fields (`skill_path`, `commit`, `score`, `status`, `description`, `wall_seconds`) as UTF-8 JSON at `<work_dir>/append_result_<iteration>.json`. Run a short Python launcher that reads that file, imports `append_result()` from `<skills-root>/skill-iterate/scripts/append_result.py`, and calls it with typed values. Do not interpolate the LLM-written description into a PowerShell command line. The helper writes the TSV header on first call and appends one row per subsequent call; it formats `score` to 6 decimals (or literal `NULL` if the iteration was unscorable), sanitizes tabs/newlines in `description` to single spaces, and formats `wall_seconds` to 3 decimals. This append happens BEFORE the revert- and crash-path `git reset --hard <iter-parent>` in Step F, so the row's commit SHA references a SHA that existed in branch history at the time of writing (even if the reset subsequently orphans it from the branch tip). The file is append-only and is expected to be gitignored per autoresearch convention (in this workspace by the root `.gitignore` rule `.claude/skills/*/evals/results.tsv`; some skills also carry an `evals/.gitignore`).

**Step H — check budget caps.** Exit the per-skill loop when ANY of:

- Wall-clock elapsed >= `--per-skill-budget` (default 1h).
- Iteration count >= `--per-skill-iterations` (default 12).
- Consecutive-crash counter >= 3 (triggers §Autonomy contract clause 3; Phase 3 handles the parking).

Otherwise, return to Step A for the next iteration. No other exit condition is permitted, apart from a failed iteration-start state check (§Per-iteration loop body) — no mid-loop operator prompts, no "should I continue?" gates, no kill-switch polling within the loop (kill-switch is polled BETWEEN skills in Phase 3, per §Autonomy contract clause 4 — "graceful stop between skills, not mid-loop").

**Per-skill wall-clock total.** Per-iteration `wall_seconds` rows in `evals/results.tsv` are not aggregated by this loop; the per-skill total = `sum(wall_seconds)` across that skill's results.tsv rows, which Phase 4 surfaces per skill.

### Phase 3 — Per-skill ship gate

After each per-skill Phase 2 exits (budget cap hit, iteration cap hit, 3-consecutive-crash defect-park triggered, OR a failed iteration-start state check; a garbage-anchor park skips Phase 3's ship decision), Phase 3 runs the ship decision, the worktree cleanup, the between-skill kill-switch poll, and (at queue end) the lock release.

#### Ship decision

In this phase, "master" means `<base-ref>`, the branch that was checked out in `<PROJECT>` when `<base-sha>` was recorded.

**Branch-state check.** Before routing, run the worktree identity guard and confirm the worktree holds exactly the scored state: `git -C <worktree-path> rev-parse HEAD` equals `<kept-sha>`, and `git -C <worktree-path> status --porcelain --untracked-files=no` exits 0 with empty output (untracked scoring artifacts are expected). Then run `git -C <worktree-path> diff --quiet <base-sha> <kept-sha> -- <contract-path>`: exit 1 means the kept version changed the contract file; exit 0 means it equals the baseline's (`empty-delta`: nothing was kept, or the keeps cancel out, so a merge would stage nothing and a proposal would be empty), which Routing step 2 treats as no-improvement; any other exit fails the check. A failure, here or at an iteration start, means the branch no longer matches what was scored; Routing step 1 sends it to defect-park, never to a merge or a proposal.

**Pre-ship clean-master check.** BEFORE any merge/branch op on the merge route (Routing step 5 below), run `git -C <PROJECT> status --porcelain --untracked-files=no`. If the output is non-empty, or the command exits non-zero, master is dirty — sibling sessions in this workspace may be actively committing (workspace `CLAUDE.md` § "Parallel session safety" warns about this exact case). Do NOT merge: a `git merge --squash` against a dirty master would sweep sibling work into the skill-iterate squash commit. Instead, take the **dirty-master-skip** path documented below. The pre-ship check runs once per skill, at Routing step 5, shortly before the merge call. The `--untracked-files=no` flag prevents the m2-launcher's own log directory (untracked, written mid-run) from triggering false dirty-master-skips.

**Line-count measurement protocol.** A short Python launcher obtains each committed blob with `subprocess.run(["git", "-C", <worktree-path>, "show", "<sha>:<contract-path>"], stdout=subprocess.PIPE, check=True)` and counts its byte lines without a shell pipe or text-mode rewrite. `total_lines_baseline` is the count at `<base-sha>`; `total_lines_final` is the count at `<kept-sha>`, the last scored version, read after the final keep/revert/crash resolves and before the Phase 3 ship gate runs. `lines_delta = total_lines_final - total_lines_baseline` (negative = simplification). The line count covers the contract file only (not adjacent eval files or scripts/). The composite scoring procedure that produces `final_score` (the score of the most recently kept version, Step F's high-water mark) and `baseline_score` is defined in [`../../_shared/score-skill.md`](../../_shared/score-skill.md); the ship gate combines those scores with `total_lines_baseline` / `total_lines_final` via the SHIP-when rule below.

**Ship-gate rule (composite).** Per the hill-climbing plan's §6 D4 (`docs/skill-iterate-hill-climbing-plan.md`), the ship gate is a **composite of score and line-count** so it stays aligned with the per-iteration simplicity-bias keep classification at §Phase 2 — Per-skill iterate loop > Per-iteration loop body, Step F's `simplicity-bias on ties` bullet (mirroring `primatives/autoresearch/program.md`). Without this alignment, a per-iteration `keep` produced by a line-reducing edit that tied on score would still be discarded at merge — silently nullifying the simplicity-bias philosophy.

> **SHIP when** `(final_score > baseline_score) OR (final_score >= baseline_score AND total_lines_final < total_lines_baseline)`
>
> **no-improvement when** `(final_score < baseline_score) OR (final_score == baseline_score AND total_lines_final >= total_lines_baseline)`

The two clauses of the SHIP condition correspond to (1) any strict score improvement, regardless of line count, and (2) a simplification win — equal score AND fewer lines — which mirrors the Step F simplicity-bias keep at §Phase 2 — Per-skill iterate loop > Per-iteration loop body. Any drop in score blocks shipping (clause 1 disqualifies it; clause 2 cannot rescue it because clause 2 requires `final >= baseline`), so a line-reducing edit that also regresses the score is correctly classified as no-improvement and never reaches master. An `empty-delta` routes to no-improvement even when `final_score > baseline_score`, because there is no contract delta to ship.

Expected outcomes by `(final_score, baseline_score, lines_delta)`:

| Score relation | lines_delta | Ship status | Why |
|---|---|---|---|
| `final > baseline` | any | **SHIP** | Strict improvement always satisfies SHIP (clause 1); Routing below decides merge or review. |
| `final == baseline` | `< 0` (fewer lines) | **SHIP** | Simplicity-bias preserved — tie with deletion is a simplification win (clause 2); with no pair gain, Routing sends it to review. |
| `final == baseline` | `>= 0` (no change or more lines) | **DISCARD (no-improvement)** | No score gain and no line reduction — nothing earned. (Includes the `lines_delta == 0` boundary: a strict-less-than win is required for simplification-bias.) |
| `final < baseline` | any | **DISCARD (no-improvement)** | Regression; line deletion cannot rescue a score drop. |

**Routing.** The SHIP condition says a change was earned; it does not by itself authorize a merge. Route each skill to exactly one outcome, checking in this order (`final_pairs_passed` is the `pairs_passed` of that same most recently kept version (Step F's high-water mark), and `baseline_pairs_passed` is the baseline value):

1. **defect-park** — Phase 2's Step H exited on the 3-consecutive-crash counter, or three baseline attempts crashed (autonomy contract clause 3), or the branch-state check failed, at an iteration start or before routing (reason `branch-state`).
2. **no-improvement** — the SHIP condition is NOT satisfied, or the branch-state check found an `empty-delta`.
3. **review-required** (reason `generated-target`) — the target mode is `proposal`.
4. **review-required** (reason `no-pair-gain`) — `final_pairs_passed <= baseline_pairs_passed`: the composite gain did not come from more passing pairs. It came from the structural axis, a simplicity-bias tie, or a weighting swap among an equal number of pairs. Structural-only gains are Goodhartable (imperative-prefix sweeps, hard-wrapped prose, deleted scope rows), and none of these shows the skill passing more of its evals, so they are harvested hunk by hunk by the operator, never merged per branch.
5. **dirty-master-skip** — the pre-ship clean-master check output is non-empty or the check exits non-zero.
6. **review-required** — reason `target-moved` when `git -C <PROJECT> diff --quiet <base-sha> HEAD -- <contract-path>` exits non-zero: master changed the same file during the run, so a squash merge could leave conflicts in the operator's checkout. Reason `branch-moved` when `<base-ref>` is empty (HEAD was detached), `git -C <PROJECT> symbolic-ref -q --short HEAD` no longer prints `<base-ref>`, or `git -C <PROJECT> merge-base --is-ancestor <base-sha> HEAD` exits non-zero: the squash would land on another branch, or would merge from an older merge-base and sweep unrelated history into the commit.
7. **keep (merge to master)** — otherwise. Exception: once a merge has failed in this run (merge-failed, below), every later skill that reaches this step takes **dirty-master-skip** with reason `merges-suspended`.

Five outcomes:

- **keep (merge to master)** when routing reaches step 7: the SHIP condition holds with a pair gain on a non-generated target, master is clean, `<PROJECT>` is still on `<base-ref>` and descends from `<base-sha>`, and the contract file is unchanged on master since `<base-sha>`. Procedure: do NOT cd into the per-skill worktree (it is about to be removed and the orchestrator never holds cwd there — see worktree cleanup below). From the project root, run these as separate commands and stop at the first failure:
  1. Record `<pre-merge-head>` = `git -C <PROJECT> rev-parse HEAD`.
  2. `git -C <PROJECT> merge --squash skill-iterate/<skill>-<epoch>` (squash to keep master history clean — each successful per-skill loop becomes ONE squashed commit, not N keep-commits per iteration).
  3. `git -C <PROJECT> diff --cached --name-only` prints exactly `<contract-path>`.
  4. `git -C <PROJECT> commit --file <message-file> -- <contract-path>`, where `<message-file>` is a BOM-less UTF-8 temp file holding `skill-iterate: <skill>: baseline N.NN -> final N.NN over K iterations (lines_delta=<+/-N>)`. When it exits 0, record `<squash-sha>` = `git -C <PROJECT> rev-parse HEAD`.
  5. Verify the squash landed: `git -C <PROJECT> rev-parse HEAD~1` equals `<pre-merge-head>`; `git -C <PROJECT> diff --quiet HEAD skill-iterate/<skill>-<epoch> -- <contract-path>` exits 0; and `git -C <PROJECT> diff --name-only <base-sha> skill-iterate/<skill>-<epoch>` prints only `<contract-path>`. Together these confirm that the branch's whole delta is on master. This is the squash-merge confirmation the workspace worktree-hygiene rule requires before a `--force` removal or `branch -D`.

  The squash-commit message format is canonical so the morning summary in Phase 4 can cross-reference master history, and `lines_delta` is included so simplification-win merges are distinguishable from strict-score-improvement merges at a glance.

  **merge-failed.** Any non-zero exit or failed check in steps 2-5 is a merge failure:
  - For this skill, run no further git command that changes `<PROJECT>`'s checkout, index or `<base-ref>`: no reset, no restore, no second commit. Do NOT delete the branch. Do NOT remove the worktree. Later skills still create and clean up their own worktrees and branches; only merges stay suspended.
  - Print `merge-failed: <skill> at step <n>; branch and worktree preserved`, then the first 20 lines of `git -C <PROJECT> status --porcelain --untracked-files=no`. When step 2 succeeded but no commit landed, also print `warning: <PROJECT> index may hold the uncommitted squash of skill-iterate/<skill>-<epoch>; inspect before the next commit`. When step 4 exited 0 and a step-5 check failed, the squash commit has already landed: also print `merge-failed: squash commit <squash-sha> landed on <base-ref>; verify it before any manual merge`.
  - Record `ship_status=dirty-master-skip` with the worktree path in the link cell. The current writer accepts this preserving status.
  - Merges stay suspended for the rest of the run (Routing step 7).
- **no-improvement (no merge)** when the composite SHIP condition is NOT satisfied — i.e. `(final < baseline) OR (final == baseline AND total_lines_final >= total_lines_baseline)` — or the branch-state check found an `empty-delta`. Nothing lands on master. Every keep raises the kept score or shortens the contract file at an equal score, so a run that fails the SHIP condition kept nothing and its branch tip is still `<base-sha>`; only an `empty-delta` run can carry kept commits. Worktree cleanup below deletes the branch only when the unmerged-commit check passes, and otherwise keeps it.
- **defect-park** when Phase 2's Step H exited on the 3-consecutive-crash counter, or three baseline attempts crashed (autonomy contract clause 3), or the branch-state check failed (at an iteration start or before routing). For the branch-state case, print `defect-park: <skill> (branch-state)`. Procedure:
  - File a GitHub issue in `<PROJECT>`'s repository — run `gh issue create --title "<title>" --body-file <body-file>` from `<PROJECT>` so `gh` resolves that repository (the workspace working-directory rule) — with title `skill-iterate: <skill> parked after N consecutive crashes`. The issue body uses this template:

    ```markdown
    ## skill-iterate: <skill> parked (3 consecutive crashes)

    **Skill:** <name>
    **Crash count:** <N>
    **Last-3 iteration descriptions:**
    1. <desc>
    2. <desc>
    3. <desc>

    **Worktree:** <path>

    **results.tsv contents:**
    ```
    <tsv content here>
    ```
    ```

  - **gh failure fallback.** Wrap the `gh issue create` invocation in try/except (Python `subprocess.CalledProcessError` or non-zero exit). On failure (gh unreachable, auth expired, network out): write the same issue body to `docs/skill-iterate-runs/parked-<skill>-<epoch>.md` (local fallback path; mkdir parents if absent). Print a warning naming the failure mode and the local fallback path, e.g. `warning: gh issue create failed (<exit-code>); parked locally at <path>`. Continue to the next skill — clause 3's "park-and-continue" semantics are still satisfied. The morning summary in Phase 4 reads from both GH and the local fallback directory.
  - **Reason `branch-state`.** Skip `gh` and write the park file directly to the local fallback path, with the expected `<kept-sha>`, the actual worktree HEAD and the worktree status output. This harness-state park adds no outbound trigger.
  - Do NOT delete the worktree. Do NOT delete the branch. The operator inspects, decides whether the harness is broken or the skill has hit a hard plateau, and cleans up manually.
  - Advance to the next skill in the queue. The defect-park does NOT halt the whole run; this is the autonomy contract's explicit carve-out for clause 3 (per §Autonomy contract).
- **dirty-master-skip** when routing reaches step 5: the change earned a merge with a pair gain on a non-generated target, BUT `git status --porcelain --untracked-files=no` is non-empty (or fails) at pre-ship time. Only the ship environment blocks it. The same outcome records a merge-failed or `merges-suspended` keep. Procedure:
  - Do NOT merge. Do NOT delete the branch. Do NOT delete the per-skill worktree (preserved so the operator can manually merge after resolving the dirty state).
  - Print the list of dirty files (the `git status --porcelain --untracked-files=no` output, capped to first 20 entries) to stdout, and record `ship_status=dirty-master-skip` with the preserved worktree path in the morning summary's link cell (the writer has no dirty-file field).
  - This is NOT a defect-park (clause 3 is reserved for 3-consecutive-crash). Dirty-master-skip is a legitimate non-halt outcome of Phase 3 — it counts toward neither the consecutive-crash defect-park counter nor any halt clause. The per-skill loop completed successfully; only the ship gate skipped.
  - Advance to the next skill in the queue.
- **review-required** when routing reaches step 3, 4 or 6. The change earned the SHIP condition but must not be merged per branch. Procedure:
  - Do NOT merge. Do NOT delete the branch.
  - Write the proposal under `<proposals-dir>` = `<project>/docs/skill-iterate-runs/proposals/` (absolute; mkdir parents if absent): `git -C <PROJECT> diff --output=<proposals-dir>/<skill>-<epoch>.diff <base-sha> <kept-sha> -- <contract-path>` (git writes the file itself; a PowerShell 5.1 redirect can add a BOM), and `<skill>-<epoch>.md` beside it with: skill, reason, `<contract-path>`, the canonical destination (generated targets; otherwise the contract path itself), `<base-sha>`, `<kept-sha>`, branch, baseline and final score, baseline and final `pairs_passed` out of the total pairs, `lines_delta`, and the descriptions of this run's `keep` rows. The `.md` states that hunks are harvested one at a time, and — for a generated target — that the diff is against the generated copy (marker header, repointed links), so each accepted hunk is applied to the canonical destination through the Skill Mesh catalog lifecycle, never to the installed copy.
  - Then remove the worktree (Worktree cleanup). The branch, the `.diff` and `<base-sha>` hold everything the harvest needs, and the next run's orphan-worktree warning stays reserved for parks and skips.
  - Record `ship_status=review-required` with the proposal `.md` path in the morning summary's link cell, and print `review-required: <skill> (<reason>) -> <proposal path>`.
  - Not a defect-park and not a halt; it counts toward no crash counter. Advance to the next skill in the queue.

#### Worktree cleanup

Cleanup runs immediately after the ship decision lands. Per the workspace worktree-hygiene rule #2, the orchestrator must NOT cd into the worktree before removing it (Windows file-lock risk — Python processes holding `.pyc` handles or a shell cwd inside the worktree both block removal). Before any `worktree remove --force`, re-run the worktree identity guard, then run `git -C <worktree-path> status --porcelain --untracked-files=no`. If either fails or status prints anything, skip the removal and print `warning: worktree at <path> failed identity/clean checks; leaving it for inspection`. The untracked files in the worktree are scoring artifacts and are disposable.

- **On keep (merge):** only after step 5 of the keep procedure confirmed the squash landed, remove the worktree. Only when removal succeeds, the path/branch pair is absent from `worktree list --porcelain`, and the branch ref still resolves to the expected `<kept-sha>`, run `git -C <PROJECT> branch -D skill-iterate/<skill>-<epoch>`. If removal or either identity check fails, skip deletion and keep the branch. The orchestrator never `cd`'d into the per-skill worktree (Phase 2 used `git -C <worktree>` for all in-worktree ops, per worktree-hygiene #5), so one cause of the file-lock failure mode is sidestepped — but not all causes (see retry below). A merge-failed keep is cleaned up as dirty-master-skip.
- **On no-improvement:** same worktree-remove invocation (after the tracked-clean check above). Only after removal succeeds, apply the unmerged-commit check of the workspace worktree-hygiene rule before any branch delete: run `git -C <PROJECT> branch -D skill-iterate/<skill>-<epoch>` only when `<base-ref>` is non-empty and `git -C <PROJECT> merge-base --is-ancestor skill-iterate/<skill>-<epoch> <base-ref>` exits 0, which proves the branch holds no unmerged commit (the usual case: its tip is `<base-sha>`). If removal failed, skip deletion because the branch is still checked out. Otherwise keep the branch, print `no-improvement: <skill> (empty-delta); branch skill-iterate/<skill>-<epoch> kept`, and put the branch name in the link cell. When deletion succeeds, print `no-improvement: <skill> (empty-delta); branch skill-iterate/<skill>-<epoch> deleted`. An unmerged or still-checked-out branch is never deleted here; the operator decides.
- **On defect-park:** skip both. Leave the worktree and branch for operator inspection — the GitHub issue (or local park file) references the worktree path.
- **On dirty-master-skip** (including merge-failed and `merges-suspended`): skip both. Leave the worktree and branch for operator's manual merge after resolving the dirty state; after a step-5 merge-failed the squash commit already landed, so the operator verifies the printed `<squash-sha>` instead of merging again. The morning summary's `dirty-master-skip` row links the preserved worktree path.
- **On review-required:** remove the worktree as above; keep the branch for per-hunk harvest. The proposal `.md` names the branch.
- **On a garbage-anchor park (Phase 2):** remove the worktree and apply the no-improvement branch rule. Its tip is `<base-sha>`, so nothing was committed and the unmerged-commit check normally passes; when it does not, the branch is kept. Print exactly `anchor-park: <skill> (<reason>); branch <name> kept` or, after a successful deletion, `anchor-park: <skill> (<reason>); branch <name> deleted` (an anchor park has no link cell).

**Windows file-lock recovery.** Even with `--force`, `git worktree remove` can fail on Windows when AV scans hold file handles or Python `.pyc` handles linger — the no-cd discipline addresses only one cause (per worktree-hygiene #2). Recovery procedure:

1. First attempt: `git -C <PROJECT> worktree remove --force <path>`.
2. On failure: sleep 2 seconds (gives AV / GC time to release handles), then retry once.
3. On second failure: print `warning: worktree at <path> could not be removed; leaving for manual cleanup` and continue to the next skill. Do NOT halt the orchestrator — orphaned worktree directories are recoverable (Phase 0's worktree-scan in the next run will re-warn), but a halted overnight queue costs the operator the morning's results.

After removal, do NOT verify with `git worktree list` mid-queue (the verification only matters for the morning summary). Per worktree-hygiene #4, an `.gitignore` rule for `worktree_*/` at workspace root prevents accidental `git status` noise if a removal silently failed.

#### Kill-switch poll BETWEEN skills

After each skill's ship decision (whether merge, delete, or park) AND its worktree cleanup, check for `.skill-iterate-killswitch` at workspace root. If present:

1. Hand off to Phase 4's morning-summary writer with the partial queue (skills processed so far + their ship outcomes); the writer handles the partial case.
2. Release the `.skill-iterate.lock` file at workspace root (unlink it).
3. Print `Kill-switch detected; graceful stop after <N> of <total> skills.` to stdout.
4. Exit 0.

Do NOT check the kill-switch within Phase 2's iteration loop. Autonomy contract clause 4 mandates BETWEEN-skill polling only; within-loop polling is mid-loop halting, which violates the NEVER-STOP discipline carried over from autoresearch's `program.md`.

#### Lock release on clean queue completion

After the last skill in the queue completes ship + cleanup (no kill-switch hit), remove the `.skill-iterate.lock` file at workspace root. Then proceed to Phase 4 for the morning summary.

**Defensive lock release on exception paths.** The implementation wraps the entire orchestrator loop (the launch gate's lock-taken point through Phase 4's summary) in `try/finally`. The `finally` block unlinks `.skill-iterate.lock` unconditionally — regardless of whether the loop exited cleanly, raised an uncaught exception, or hit a signal. A secondary `atexit.register(<unlink-lock>)` handler is registered immediately after the lock is taken; this covers `SIGINT` (Ctrl+C) and clean interpreter shutdown paths that `try/finally` alone does not cover when the exception path bypasses normal scope unwinding (e.g. `os._exit` or fatal signals; `atexit` catches the clean-shutdown subset). The combination minimizes the stale-lock window to OS-crash-only.

On unclean exit that bypasses both `try/finally` and `atexit` (OS crash, SIGKILL, power loss), the lock file is left stale. The next `/skill-iterate` invocation's Phase 0 concurrent-run detection handles the takeover per §Autonomy contract — the stale-lock branch overwrites with a warning rather than halting, so a single crashed run does not block the next night's queue.

### Phase 4 — Morning summary

**Trigger.** Phase 4 runs once at the tail of every orchestrator invocation, on three paths: (1) clean queue completion after the last skill ships, (2) kill-switch graceful stop between skills (per Phase 3's contract), and (3) the exception path via the `try/finally` block that wraps the orchestrator loop. Path (3) ensures a partial summary always lands even if Phase 2 raises — the `finally` clause invokes the writer with whatever `SkillResult` records the orchestrator has accumulated up to the failure point.

**Output path.** The writer emits a single markdown file at `docs/skill-iterate-runs/YYYY-MM-DD.md` where `YYYY-MM-DD` is the date in UTC at orchestrator start. The writer auto-disambiguates filenames per the workspace memory `feedback_auto_disambiguate_filenames`: if the target filename already exists (an earlier run today, or a manual stash), the writer appends `b`, then `c`, then `d`, ... up through `z` to find a non-existing path and writes there instead. The actual written path is returned to the orchestrator and printed on stdout for the operator's morning glance.

**Writer invocation.** The orchestrator-LLM collects one `SkillResult` per processed skill across the Phase 2/Phase 3 loop and invokes the writer once at the very end via `python <skills-root>/skill-iterate/scripts/morning_summary.py <runs_dir> --input <payload.json> [--date YYYY-MM-DD] [--partial] [--started-at <iso8601>] [--ended-at <iso8601>]`. The JSON payload has a `skill_results` list (one entry per skill with the `SkillResult` fields) plus optional `skipped_by_skip_list` and `skipped_by_cross_night` arrays. The writer is deterministic and stdlib-only — no flakiness contributes to the morning summary itself.

**Ship statuses and the link cell.** `ship_status` is one of `keep`, `no-improvement`, `defect-park`, `dirty-master-skip`, `review-required`; the writer rejects any other value, so `review-required` requires the writer's accepted-status set to include it. `parked_issue_url` fills the summary's link cell: the issue URL or local fallback path for a defect-park, the proposal `.md` path for review-required, the preserved worktree path for dirty-master-skip (which also records a merge-failed or `merges-suspended` keep; stdout names which), and the kept branch name for a no-improvement whose branch failed the unmerged-commit check. Garbage-anchor and calibration parks and target-resolution skips are not `SkillResult` rows; they are reported on stdout and in their local files.

**Partial-summary handling.** When the orchestrator hits the kill-switch between skills (Phase 3 path) OR exits via the exception `finally`, it invokes the writer with `--partial`. The output gets a header line directly under the H1 reading `(partial -- stopped at <iso8601>)` so the operator can distinguish a complete drain from a stopped one at a glance. The `SkillResult` list passed in is whatever subset completed before the stop signal — the writer does not re-shape it.

**Per-skill total wall time.** `wall_seconds_total` in each `SkillResult` is the sum of the `wall_seconds` column across that skill's `evals/results.tsv` rows (baseline row included). The orchestrator computes this per skill before passing to the writer; it is NOT recomputed inside the writer.

**Skills with delta < 1%.** Per-skill delta below 1% (`final_score - baseline_score < 0.01`) indicates the hill-climb plateaued — Phase 2's serial exploitation has run out of low-hanging mutations. Such skills are candidates for `/skill-evolve` next session, which dispatches parallel A/B exploration with operator-curated variants instead of serial hill-climb. The morning summary table makes these visible in the `delta` column; the operator can scan for `+0.00`, `0.00`, or single-digit-thousandths deltas and queue those skills for the next overnight via `/skill-evolve --skill <name>`. A `review-required` row with reason `no-pair-gain` is the same signal: the absolute axis has no headroom and only the structural axis moved.

---

## Limitations

- **Emitted fleet calibration is unsupported.** The v2 core invokes per-skill calibration only. The packaged `adversarial_calibration.py --fleet` path depends on `skill-eval-setup/scripts/generate_bad_examples.py`, which is not emitted; the retained legacy fleet tests prove only the legacy repository layout. The in-repository [`../../_shared/score_skill_composite.py`](../../_shared/score_skill_composite.py) likewise continues to import the unchanged legacy helper copies, while emitted composites resolve the canonical packaged copies.
- **Precondition:** `/skill-eval-setup` must have run for the target skill — no `evals/evals.json` means no scoring, means the skill is silently skipped from auto-discovery (and halted on if passed explicitly via `--skill`).
- **Skip-list skills require per-skill side-effect harnesses** (future work). The side-effect skills listed under "Embedded skip-list" produce side-effects rather than text artifacts; the current scoring procedure cannot grade them.
- **Wall-clock OR iteration cap, whichever first.** A skill that produces fast iterations may hit the 12-iteration cap well under 1h; a skill with slow scoring may hit the 1h wall-clock cap on iteration 3. Both are accepted exit conditions.
- **Cross-night-resume is a hard 24h cliff** on `evals/results.tsv` mtime. Manual `touch` resets the window; no round-robin preservation. Acceptable for default.
- **No mid-loop halts.** This is by design — see "Autonomy contract" above. If a per-skill loop needs an operator decision, the right tool is `/skill-evolve` (parallel A/B with curated variants), not `/skill-iterate`.
- **One concurrent run per workspace.** The lock file + worktree scan enforces this; a second concurrent invocation halts at pre-flight rather than racing for worktrees and commits.
- **Install output yields proposals or skips, not merges.** A Skill Mesh catalog skill improves only when an operator applies accepted hunks to its canonical source through the catalog lifecycle. Its `results.tsv` is still written in the installed profile's `evals/` folder — a gitignored run artifact, not a catalog change. In an install tree, even a hand-authored skill without a marker is skipped as `unmarked-install`, because the resolver cannot tell it from install output.
- **Render variance is not smoothed.** Three trials re-grade one render per scenario; one unlucky render can still revert a good edit or keep a lucky one. Phase 3's pair-gain routing keeps such keeps from auto-merging when the absolute axis did not improve.
- **Host lines are not scored.** For a deferring launcher, the contract file is the core; the launcher's own lines and the provider adapter text are not rendered.
- **Not coverable by scenario evals:** the integrity-check crash branch, the 10-min-timeout crash branch, and the 3-consecutive-crash defect-park branch need fixture-based integration tests (a deliberately incomplete workflow result, a stub that sleeps past the cap, deliberately broken `evals/`).
- **Scoring composes structural + absolute_weighted axes.** The per-iteration scoring shape is documented above; the procedure itself lives at [`../../_shared/score-skill.md`](../../_shared/score-skill.md) with a Python wrapper at [`../../_shared/score_skill_composite.py`](../../_shared/score_skill_composite.py). Composite mode (the default) weights structural metrics at 0.4 and absolute_weighted at 0.6 per SIHC.2 Option A (goldens-verify unwired; the prior pair-comparison mode replaced by absolute grading); weights are configurable via two top-of-procedure constants. Structural-only and absolute_weighted-only modes are available via the `mode` argument for skills that need them. Legacy spec-compliance scoring (pre-SIHC) is no longer in scope; all per-iteration scoring now goes through `_shared/score-skill.md` composite/structural/absolute_weighted modes.
