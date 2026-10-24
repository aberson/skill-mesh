# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/skill-evolve/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Hidden chain-of-thought (internal model reasoning) must not be exposed in final output. An explicit chain-of-thought scratchpad requested by a variant is a structured intermediate artifact, not hidden reasoning — it is produced intentionally and its content is the variant's deliverable. The prohibition applies to unintentional leakage of internal reasoning, not to explicitly requested reasoning artifacts.

# Skill Evolve

`/skill-evolve` runs N parallel A/B variants of a skill's behavior contract (its SKILL.md, or the core file that SKILL.md defers to) against the skill's existing eval suite and reports which variant won. Built on top of the produce-grade loop documented in [`skill-eval-setup`](../skill-eval-setup/core.md). The skill's whole reason to exist is to compress what would be N sequential `/skill-eval-setup` self-improvement runs into one parallel fanout.

---

## Execution model — autonomous, parallel-fanout, no auto-PR (HEAVY)

This skill exists so the operator can test 3-5 candidate prompt mutations in one shot instead of running them sequentially over days. The whole point is parallel evaluation with honest reporting. Therefore:

1. **Parallel by default, via the scoring workflow.** Variants are evaluated by the shared workflow at [`../../_shared/score_skill.workflow.js`](../../_shared/score_skill.workflow.js), which fans out all variants — and within each variant, all scenarios — concurrently. Sequential variant runs defeat the whole purpose. If the host workflow primitive is unavailable in this environment, halt with a clear error rather than silently falling back to a single self-grading agent (the defect this skill was rebuilt to avoid — see #6).

2. **No automatic push or PR.** Print the `gh pr create` command for the operator to run. Do not push or create a PR without operator confirmation. Workspace convention: never push without explicit ask.

3. **Single trial is honest about being single trial.** Default `--trials 1`. The comparison table includes a "single-trial; treat deltas <5pp as noise" caveat in the header. If the operator wants tight CIs, they pass `--trials 3` or higher; each trial multiplies grading cost linearly. Trials re-grade the same single render of each scenario, so they measure grader agreement, not render variance; the report says so. Do NOT silently inflate confidence claims when only one trial ran.

4. **No mid-run confirmations.** No `(y/n)` gates. No "ready to dispatch variants?". The operator opted into the parallel run by invoking `/skill-evolve`. Halts are reserved for: pre-flight failures, agent crashes that prevent producing a score, or genuine ambiguity in the variant strategy that needs operator judgment (which should be rare — variant strategies are operator-authored, not LLM-generated).

5. **Loser-analysis is the next-generation seed.** Every variant — winners AND losers — produces a captured analysis with: full contract-file diff, score breakdown per assertion, and a short analysis of why the strategy did or did not move the score. The loser analyses are filed under `docs/investigations/skill-evolve/<skill>/<timestamp>/` so the next round can read them and propose better strategies.

6. **Produce and grade are different agents — always.** No agent grades output it produced. The workflow spawns a RENDER agent and a SEPARATE GRADER agent per scenario; the mutator agent only mutates. This is non-negotiable: a grader biased by having authored the artifact is exactly the failure the 2026-05-27 consolidated render+grade incident surfaced (see [`../../_shared/score-skill.md`](../../_shared/score-skill.md) § Absolute grading). Agent nesting is depth-1, so this split MUST live in the workflow (or an orchestrator that is itself the main loop) — never inside a spawned variant agent, which cannot fan out further and would be forced to self-grade.

This is by strong operator preference; treat any deviation as a defect.

Two further rules come from workspace authority (measurement validity and the Skill Mesh catalog lifecycle), not operator preference:

7. **Score the production artifact; a fallback is a failure.** BASELINE is an exact byte copy of the contract file the host loads, scored through the same workflow path as every variant — never an agent's reproduction of it. A result that silently fell back (missing render or verdict file, backfilled verdict, missing payload, unapplied strategy, baseline bytes that changed) is `FAILED`, never a low score (§ Step 3, Integrity checks).

8. **Generated surfaces are read-only.** A file carrying the `SKILL-MESH-GENERATED-FILE` marker is a Skill Mesh install output. This skill never edits, branches or commits it; a winner for such a target becomes a proposal for its canonical source (§ Step 4).

---

## When to use

- 3+ candidate mutations are on the table for one skill and the operator wants to know which (if any) actually move the score.
- A skill's current score has a clear ceiling (e.g., stuck at 76% over multiple iterations) and the operator wants to try fundamentally different approaches in parallel rather than tweak one variable at a time.
- Pre-existing `evals/evals.json` + `evals/test_scenarios.json` exist for the target skill (per [`skill-eval-setup`](../skill-eval-setup/core.md)).

## When NOT to use

- The skill has no `evals/` folder yet — run `/skill-eval-setup <skill>` first.
- The mutation is mechanical (rename a section, fix a typo, add a missing field) — just edit the contract file directly (for a generated profile, its canonical source).
- The operator wants to evolve eval assertions or scenarios themselves, not the contract file — that's a different workflow (the `evals.json` is the ground truth A/B variants are scored against; mutating it invalidates the comparison).
- The skill is already at 100% on its current eval suite — there's nothing to evolve toward without first sharpening the assertions.

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--skill` | yes | -- | Skill name (resolved to `.claude/skills/<name>/SKILL.md`) or absolute path to a SKILL.md. Step 0 resolves the contract file from it. |
| `--variants` | no | brainstorm | Either an absolute path to a variants file (one strategy per line, format below) OR an inline semicolon-separated string of strategies. If omitted, the skill enters **brainstorm mode** (see § Variant sourcing — brainstorm mode): LLM proposes a candidate list, writes it to a file, and exits before any worktrees are created. |
| `--trials` | no | 1 | Number of independent grading trials per scenario (more = tighter CI on grader agreement, linear grading cost increase) |
| `--baseline-from-results` | no | -- | Skip the BASELINE scoring run; read the latest usable `baseline` row from `evals/results.tsv` instead. Faster but may compare against an older committed baseline. Allowed only when the resolved contract file is the SKILL.md itself. A usable row has the exact repository-relative contract identity and a `sha256=` that matches that contract's blob at the row's commit (Step 2). Deferred cores and identity-free `keep` rows are inadmissible. |
| `--dry-run` | no | -- | Print the resolved contract file, variant list, work-dir plan, winner mode and cost estimate, then exit. No worktrees created, no agents dispatched. |

---

## Variants file format

Plain text. One variant per non-blank, non-comment line. Each line must start with a bracketed short ID, then the strategy prose. The ID is used for the variant's mutated-copy filename, the winner's branch name, and the comparison-table row.

```text
# Each line: [<short-id>] <strategy prose>
# Short IDs must match [a-z0-9-]{1,30}. They become git refs.

[aggressive-parallel] Wherever the SKILL.md tells the executor to call tools sequentially, identify opportunities to batch independent calls in a single message. Add explicit "dispatch in parallel" guidance to any step with 2+ independent reads.
[scratchpad] Add an explicit chain-of-thought scratchpad section the executor uses to plan before producing the final output. Prose-only, no JSON.
[compress-30] Compress the SKILL.md by ~30% by removing redundant prose, collapsing examples to single lines, and tightening lists. Preserve every assertion-load-bearing instruction; remove only verbiage.
[example-rich] Add 1-2 concrete worked examples per major step. Examples should be small enough to read in 3-5 lines but specific enough that an executor can pattern-match.
```

Parse rules:

- Lines starting with `#` are comments; ignored.
- Blank lines ignored.
- Each line MUST start with `[<id>]` then whitespace then strategy prose. Lines not matching this shape are pre-flight errors.
- IDs must be unique within the file. Duplicates are pre-flight errors. `BASELINE` is reserved.
- Inline form (`--variants "[id1] strategy 1;[id2] strategy 2"`) splits on `;` and applies the same per-line rules.

Practical N: 2-5 variants per run is the sweet spot. 6+ burns parallel-agent budget and bloats the comparison table; 1 variant defeats the A/B purpose (just run `skill-eval-setup`'s loop directly).

---

## Variant sourcing — brainstorm mode

If `--variants` is omitted, the orchestrator enters **brainstorm mode**: it proposes 10–15 candidate strategies, writes them to a file, prints them inline, and exits before any worktrees are created. The operator then curates the file and re-invokes with `--variants <path>`.

This is a deliberate pre-dispatch exit, NOT a mid-run halt or a `(y/n)` gate. The operator opted into the brainstorm flow by omitting `--variants`; the autonomous-no-confirmations contract (§ Execution model #4) still holds for variant-supplied runs. Auto-running LLM-generated variants without operator curation would drift toward "Claude-pleasing" patterns rather than testing real hypotheses (see Limitations).

### Brainstorm procedure

1. **Resolve and verify target skill** (same as Step 0 pre-flight #1). If missing, halt with the standard pre-flight error — brainstorm mode does not paper over a missing skill.

2. **Read the target's contract file** (Step 0 #1). Full read.

3. **Read prior loser analyses** under `docs/investigations/skill-evolve/<skill>/*/` (if the directory exists). Goal: do not re-propose strategies that already lost. If the directory exists, list the variant IDs and one-line strategy from each prior run's `00-comparison.md`; treat them as exclusions.

3a. **Read operator-seeded proposals** at `docs/investigations/skill-evolve/<skill>/_proposed.md` (if the file exists). Each non-comment line in variants-file format (`[<id>] <strategy>`) is a SEED — include it verbatim in the candidate list with priority placement (top of the list). Seeds are operator-curated hypotheses captured between runs; do not discard them in favor of LLM-generated alternatives. Skip any seed whose `<id>` collides with a prior-run loser ID (the exclusion list from step 3 wins on conflict — re-proposing a known loser requires the operator to either rename or explicitly remove the loser analysis first). The `_proposed.md` file is NOT a timestamped run dir (the leading underscore distinguishes it); leave it in place after the brainstorm — the operator manages its lifecycle (delete entries once tried).

4. **Read recent `evals/results.tsv`** (last 5 rows, if present) to see which assertions have been stuck at FALSE across iterations. Strategies that plausibly move those specific assertions get priority placement in the list.

5. **Generate 10–15 axis-spanning candidate strategies.** Each candidate is `[<short-id>] <one-sentence strategy>` followed (on the next line, after a `# ` comment marker so it's ignored on re-invocation) by a one-sentence rationale. Span axes, not minor wording tweaks:
   - Structural changes (compress / expand / reorder / split into sub-skills)
   - Process changes (parallel-dispatch / serial / scratchpad / two-stage produce-then-grade)
   - Output-format changes (single-artifact / multi-file / inline-only / file-only)
   - Content-source changes (verbatim-quote / paraphrase / cite-line / cite-section)
   - Scenario emphasis (adversarial / happy-path / grounded-in-real-fixtures)
   - Extraction order (anti-pattern-first / positive-rule-first)
   - Termination / scoring (strict TRUE/FALSE / confidence-weighted / tiered must-vs-should)

   IDs must match `[a-z0-9-]{1,30}` and be unique. Do not include strategies from the loser-analysis exclusion list.

6. **Write `docs/investigations/skill-evolve/<skill>/<timestamp>/proposed-variants.txt`** containing all candidates, uncommented (ready to consume as-is). Use absolute path. Path format: `<dev-root>/docs/investigations/skill-evolve/<skill>/<YYYYMMDD-HHMMSS>/proposed-variants.txt`.

7. **Print the list inline** so the operator can see it without opening the file.

8. **Exit with this exact follow-up block** (no other output after it):

   ```text
   Brainstorm mode — no worktrees created, no agents dispatched.

   Proposed variants written to:
     <abs-path-to-proposed-variants.txt>

   To run ALL proposed variants as-is:
     /skill-evolve --skill <skill> --variants <abs-path>

   To run a SUBSET: open the file, delete or `#`-comment lines to drop, then re-invoke with the same path.

   Practical N reminder: 2–5 variants is the sweet spot. Trim before re-invoking.
   ```

Brainstorm mode never creates worktrees, never dispatches agents, never pushes branches. The only side effect is one file under `docs/investigations/skill-evolve/`.

---

## Steps

### Step 0: Pre-flight

Before creating any worktrees or dispatching any agents, all of:

1. **Resolve and verify target skill.** `<skill>` → `<dev-root>/.claude/skills/<skill>/SKILL.md` (or the absolute path given). Then resolve two separate facts:
   - **Contract file** — the file whose text is mutated and scored. The complete recognized defer forms are a `Core: core.md` line and a `See [core.md](core.md) for the full specification.` link. Exactly one form selects the named file, resolved relative to SKILL.md (in an installed profile, its sibling `core.md`). Neither form selects SKILL.md itself, including a provider-native SKILL.md that carries the generated-file marker but defers to no core. Both forms together are ambiguous and halt below rather than silently selecting a proxy.
   - **Generated target** — the contract file carries the `SKILL-MESH-GENERATED-FILE` marker. Record the `Canonical source:` path that marker names (for a deferred core, the skill's `core.md`; for a provider-native SKILL.md, its `providers/<host>.md`).
   - **Files.** Confirm SKILL.md, the contract file, `evals/evals.json`, and `evals/test_scenarios.json` (beside the SKILL.md) all exist. Missing any → halt with the missing-path list. Record the contract file's SHA-256.
   - **Variant-supplied runs only** (not brainstorm), also halt when: SKILL.md contains both recognized defer forms; SKILL.md carries the marker, has a sibling `core.md`, and contains neither recognized defer form (the target is ambiguous); SKILL.md carries the marker but the core it defers to does not (mixed install output; no canonical destination can be named); or `--baseline-from-results` was passed and the contract file is not the SKILL.md itself — only a usable `baseline` row for the resolved SKILL.md is admissible, so a deferred core halts (say so, name the contract file, and tell the operator to re-run without the flag); or `--baseline-from-results` was passed and `evals/results.tsv` has no usable row (Step 2).

2. **Resolve variants source.**
   - If `--variants` was provided: parse per the rules in § Variants file format. Collect ALL malformed lines / duplicate IDs and report at once; do not halt after the first.
   - If `--variants` was omitted: switch to **brainstorm mode** (see § Variant sourcing — brainstorm mode). Generate candidates, write the file, print the list, and exit. Skip the remaining pre-flight steps (working-tree-clean check is not required for a no-side-effect brainstorm exit) and skip Steps 1–6 entirely.

3. **Resolve the repository and check it is clean.** REPO is `git -C <contract-file-directory> rev-parse --show-toplevel`; not inside a git work tree → halt. Define `<contract-rel>` as the contract file's `/`-separated path relative to REPO, with no `.` or `..` segment; this exact form is the results-row identity in Step 2. Every git command in this run that reads or writes a repository names it with `git -C` (REPO or the winner worktree), never the session's working directory; the only exception is `git diff --no-index`, which compares two file paths and reads no repository. Run `git -C REPO status --porcelain`. If non-empty, halt: "Working tree dirty — stash or commit before running /skill-evolve." and name REPO. This is a real constraint: variants are mutations OF the live contract file and the winner's branch is cut from HEAD, so uncommitted edits would confound the baseline and could land unintended changes on the winner branch.

4. **Resolve `shared_dir`.** `shared_dir` is the `_shared` directory beside this skill's installed directory (`<skills-root>/_shared/`, home of the scoring workflow linked in § Execution model and the Python scorers). This item only resolves the path; the scorer check runs at the start of Step 1, after the workflow-primitive check, so `--dry-run` and halt #2 never depend on the Python scorers.

5. **Disk space check (advisory, not gating).** The single winner worktree (Step 4, non-generated targets only) pulls roughly `du -sh .` of REPO; losers use temp files under `work_dir`, not worktrees. Print the estimate; do not halt — the operator owns the disk decision.

6. **Cost estimate (advisory).** For N variants, M scenarios and K trials, the variants invocation runs `N × (M × (1 + K) + 2) + 1` agents (mutate, renders, grades and aggregate per variant, plus one load) and the BASELINE invocation runs `M × (1 + K) + 2`. Print the total before proceeding. Per the autonomous-by-default contract, do not ask for confirmation; the operator opted in.

7. **Dry-run exit.** If `--dry-run`, print the contract file (and whether it is a generated target), the resolved variant list, the work-dir plan, the winner mode (branch or proposal) and the cost estimate, state that the workflow-primitive and scorer checks (Step 1) were not run, then exit. No side effects.

### Step 1: Prepare the scoring run

If the host has no workflow primitive, halt now under § Halts #2, before creating the work dir. Otherwise run the **scorer check** once: `python -B <shared_dir>/score_skill_composite.py --help`. A nonzero exit (for example a missing import dependency) is a pre-flight failure under § Halts #1, still before the work dir, because otherwise every scoring agent would run before the aggregator failed.

All mutate + produce + grade work is delegated to the shared scoring workflow at
[`../../_shared/score_skill.workflow.js`](../../_shared/score_skill.workflow.js). That workflow is the orchestration
level: per variant it spawns a MUTATOR agent (applies the strategy to a fresh copy of the contract file), then a RENDER
agent and a SEPARATE GRADER agent per scenario. The grader only reads a file the render agent wrote — it never
grades output it produced.

This is the fix for the original defect: a single variant sub-agent used to both simulate the skill output AND
grade itself. A sub-agent cannot spawn its own producer/grader sub-agents (agent nesting is depth-1), so it was
forced to self-grade. Moving the fan-out into a workflow flattens it — every agent is a sibling of the script.
See § Execution model.

**Local-grader offload (switchboard call site `skill-evolve-grader`): not wired.** Switchboard declares this call site (tier-offload task_class `skill-evolve-grader`; Switchboard Decision 9 — a cheap parallel scoring array), but the scoring workflow's grader agents make no switchboard call and this orchestrator never holds a per-scenario grading prompt. Do not grade outside the workflow to create a call point, and never let a local verdict replace or alter an independent grader's verdict. A future wired grader would call `python -m switchboard judge --site skill-evolve-grader --prompt-file <grading-prompt-file>` (prints one JSON object, always exits 0, defers whenever offload is off or the model is unavailable) and use a verdict only as an advisory score; wiring it is a change to the workflow, not a run-time choice.

Create a temp work dir for this run, then assemble the workflow `args`:

- `shared_dir` — the absolute path resolved in Step 0 #4.
- `work_dir` — a fresh temp dir, e.g. `C:/Users/<user>/AppData/Local/Temp/skill-evolve-<skill>-<epoch>`. Create it first; agents write mutated copies, renders, verdicts, and payloads here. (Use `AppData/Local/Temp`, not `/tmp` — see `.claude/rules/windows-shell.md`.)
- `evals_dir` — the `evals` folder beside the SKILL.md (the UNMUTATED eval suite; every variant is scored against the same assertions, held constant per § Limitations).
- `trials` — the `--trials` value (default 1). On `--trials N`, each scenario is graded N times and the aggregator collapses by per-(scenario, assertion) majority vote (ties → False).
- `variants` (variants invocation) — one object per parsed `[<id>] <strategy>` line: `{ id, label: id, strategy, base_skill_md_path: <abs path to the contract file> }`.
- `versions` (BASELINE invocation) — unless `--baseline-from-results` was passed, copy the contract file byte-for-byte (a file copy, not an agent) to `<work_dir>/variant_BASELINE.SKILL.md`, confirm its SHA-256 equals the Step 0 hash, and pass `[{ id: "BASELINE", label: "BASELINE", skill_md_path: <that copy> }]`. Scoring the exact baseline bytes from the same directory as the variants, through the identical render/grade/aggregate path, is what makes it a valid reference point.

### Step 2: Run the workflow

Invoke the scoring workflow through the host workflow primitive twice — once with the `variants` args, once with the BASELINE `versions` args — concurrently when the host allows, otherwise BASELINE first. Each invocation fans out all of its versions and scenarios concurrently. Pass:

```
scriptPath: "<shared_dir>/score_skill.workflow.js"
args: <the args assembled in Step 1 for that invocation>
```

Each returns one result object per variant or version:
`{ id, label, skill_md_path, score, passed, total, status, failed_assertions, passing_pairs }`.
`score` is the composite in `[0.0, 1.0]`; `skill_md_path` points at the copy under `work_dir` (Step 4 reads
the winner's copy from there). No per-variant worktrees are created — the only git side effect is Step 4's single
winner branch, and only for a non-generated target.

If `--baseline-from-results`, skip the BASELINE invocation and read `evals/results.tsv` (columns `commit`, `score`, `status`, `description`, `wall_seconds`). A row is **usable** only when all of these hold: `status` is `baseline` (case-insensitive); `description` contains exactly one `contract=<path>` token and one 64-lowercase-hex `sha256=<digest>` token; `<path>` exactly equals `<contract-rel>`; `commit` resolves unambiguously to a commit in REPO; and the SHA-256 of that commit's `<contract-rel>` blob equals `<digest>`. Obtain the blob bytes with a Python `subprocess.run(["git", "-C", REPO, "show", "<resolved-commit>:<contract-rel>"], stdout=subprocess.PIPE, check=True)` launcher and hash `stdout` directly — no shell pipe or text decoding, so checkout CRLF conversion cannot change the identity. Select the last usable row, use its score (validated in `[0,1]`) as the baseline, and name its original commit plus resolved full SHA in the report header. State whether that full SHA equals current HEAD; a historical row is scoring evidence for its bound blob, not proof that its commit landed. Identity-free `keep` rows are deliberately ignored. No usable row is Halt #1.

### Step 3: Collect results and produce comparison

The workflow's return arrays ARE the result set — no per-agent JSON to parse. A variant whose scoring errored comes
back with `status: "harness-error"` and `score: null` (mark it `FAILED`); the others are still valid data.

**Integrity checks (before any delta).** Mark BASELINE or a variant `FAILED`, with the reason in its Verdict cell, when any of these holds:

- `status != "ok"`.
- `passed != total` (a partial-axis fallback can still report `status: "ok"`).
- Its copy at `skill_md_path` is missing or empty, or (variants only) identical to the contract file after line-ending normalization — the strategy was not applied.
- For some scenario, `<work_dir>/render_<id>_<scenario-id>.md` is missing or empty, or one of its `<work_dir>/verdicts_<id>_<scenario-id>_t<k>.json` files (k = 0 to K-1) is missing — the workflow would otherwise grade or aggregate around the gap.
- `<work_dir>/payload_<id>.json` is missing, holds any verdict whose reason is `grader omitted` (the aggregator backfills a missing grade as FALSE), or both `passing_pairs` and `failed_assertions` are empty (no absolute-grader axis).

Then re-hash the contract file (and the BASELINE copy, when one was scored). A hash that differs from Step 0, or a `FAILED` BASELINE, leaves no valid reference: halt under § Halts #3 with a partial report.

Compute each variant's delta against the baseline in percentage points: `(score - baseline_score) * 100`. Pairs passed is `len(passing_pairs)` out of `len(passing_pairs) + len(failed_assertions)`.

**Echo each result object (BASELINE first) verbatim to stdout, under a `## Variant results` heading, BEFORE the
comparison table**, so the per-variant contract is auditable. The key set on every object is exactly:
`id`, `label`, `skill_md_path`, `score`, `passed`, `total`, `status`, `failed_assertions`, `passing_pairs`.

Produce a comparison table. Markdown. Example:

```markdown
# /skill-evolve report — <skill> — <timestamp>

Contract file: <path> (<generated target: proposal only | branch>)
Baseline: <baseline_score> (<source: workflow BASELINE | results.tsv blob-bound at <full-commit>, current HEAD|historical>)
Trials per variant: <K> (re-grades of one render per scenario)
Caveat: <if K==1: "Single-trial run; treat deltas <5pp as noise.">

| Variant | Score | Δ vs baseline | Pairs passed | Status | Verdict |
|---|---|---|---|---|---|
| BASELINE | 0.760 | — | 20/30 | ok | reference |
| [aggressive-parallel] | 0.790 | +3.0pp | 21/30 | ok | NOISE (single-trial, Δ<5pp) |
| [scratchpad] | 0.850 | +9.0pp | 24/30 | ok | WINNER |
| [compress-30] | 0.710 | -5.0pp | 18/30 | ok | REGRESSION |
| [example-rich] | — | — | — | harness-error | FAILED |

## Winner: [scratchpad]
- Mutated copy: <work_dir>/variant_scratchpad.SKILL.md
- Δ: +9.0pp; pairs passed 24/30 vs BASELINE 20/30
- Top remaining failures: <first 1-2 `failed_assertions` statements, if any>
```

Verdict rules (thresholds unchanged from prior versions; `score` is in `[0,1]`, deltas in pp):
- `WINNER`: highest `score` AND Δ ≥ 5pp vs baseline (a tighter threshold is allowed at K ≥ 3).
- `NOISE`: 0 < Δ < 5pp at K=1.
- `REGRESSION`: Δ < 0.
- `NO WINNER`: no variant cleared the 5pp threshold. The report still ships; the operator decides whether to iterate.
- `FAILED`: `status != "ok"` or an integrity check failed.

Ties on `score`: prefer the variant whose mutated copy is the smaller diff vs baseline (Occam's). Document the tiebreak inline.

**No pair gain.** If the WINNER's pairs-passed count does not exceed BASELINE's, say so on the Winner lines: the pair count did not improve, so the gain may come from the structural axis of the composite (easily Goodharted) or from category weighting in the absolute axis (passes moved between categories of different weight or size change that axis at an equal pair count). The operator reviews the diff hunk by hunk before merging or proposing it.

### Step 4: Winner handling

If there is a `WINNER` and the target is **not generated**:

1. **Materialize the winner on a branch.** `<winner-branch>` is `skill-evolve/<skill>-<winner-id>` and `<winner-worktree>` is `<dev-root>/../worktree_skill-evolve_<skill>_<winner-id>/`. If that branch already exists in REPO (`git -C REPO rev-parse --verify --quiet refs/heads/<winner-branch>` exits 0; exit 1 means absent and is expected) or that path already exists, an earlier run left them: append `-<timestamp>` (this run's analysis-directory timestamp) to both names, and never reuse, reset, delete or overwrite the earlier branch or worktree. Create ONE worktree, for the winner only:
   `git -C REPO worktree add <winner-worktree> -b <winner-branch>` (off current HEAD; record HEAD's branch as `<base-branch>`). Copy the winner's mutated copy from `<work_dir>/variant_<winner-id>.SKILL.md` over the worktree's contract file (`<contract-rel>`, its path relative to REPO), then run two separate commands:
   `git -C <worktree> add -- <contract-rel>` and `git -C <worktree> commit --file <message-file> -- <contract-rel>`. Write `<message-file>` as BOM-less UTF-8 containing `skill-evolve <skill> [<winner-id>]: <one-line strategy summary>` plus a final newline; never interpolate the LLM-written summary into an inline `-m` argument. See `.claude/rules/worktree-hygiene.md`.

2. **Do not push the winner's branch automatically.** Print the local branch name and the push command the operator would need before using the PR command below. Do not run either command without operator confirmation.

3. **Print the gh pr create command** for the operator to paste:
   ```bash
   gh -R <repo-from-gh-remote> pr create \
     --base <base-branch> \
     --head <winner-branch> \
     --title "skill-evolve(<skill>): [<winner-id>] +<delta>pp" \
     --body-file <abs-path-to-loser-analysis-dir>/00-comparison.md
   ```
   Use `--body-file` (workspace rule — never inline body for non-trivial PRs).

4. **Leave the winner's worktree in place** for inspection. The path is in the report.

If there is a `WINNER` and the target **is generated**: create no worktree, branch or commit, and never write the installed profile or the canonical source. In the run's analysis directory write `winner-<winner-id>.proposal.md` (the winner's copy with the generated-file header comment removed) and `winner-<winner-id>.diff` (`git diff --no-index -- <contract-file> <work_dir>/variant_<winner-id>.SKILL.md`; exit 1 means the files differ and is expected). Print the canonical destination recorded in Step 0 and state that applying it is a Skill Mesh catalog `UPDATE` under the lifecycle contract (`documentation/skill-catalog-lifecycle.md` in the Skill Mesh source tree) followed by a rebuild — never an edit of an installed copy. The `Canonical source:` value is relative to a Skill Mesh source tree. Look for it only under `<dev-root>/skill-mesh`, and only when that directory satisfies the lifecycle's source-tree predicate (a Git working tree containing `config/skill-manifest.json`). If the canonical source is readable there, report whether it matches the installed contract file apart from the generated header and the `_shared` link spelling; a mismatch means the installed profile is stale and the operator must rebase the proposal. Otherwise report that this comparison was not performed. No push or PR command is printed.

If `NO WINNER`: skip the worktree, the proposal and the PR command. Print "No variant cleared the threshold; iterate with new strategies."

### Step 5: Variant analyses

For every variant — the WINNER and every non-winner (REGRESSION, NOISE, NO-WINNER, FAILED):

1. **Capture analysis.** Write `docs/investigations/skill-evolve/<skill>/<timestamp>/<variant-id>.md` with:
   - Strategy verbatim.
   - `score`, Δ vs baseline, pairs passed, `status`.
   - The contract-file diff: `git diff --no-index -- <contract-file> <work_dir>/variant_<variant-id>.SKILL.md` (the mutated copy vs the live baseline). `--no-index` exits 1 when the files differ — that is expected, not an error.
   - The variant's top `failed_assertions` (statement + grader_reason) — the next round's targeting signal.
   - Orchestrator's classification (WINNER / NOISE / REGRESSION / NO-WINNER / FAILED, with any integrity reason) and a short note of which assertions moved versus BASELINE.

2. **Write the comparison summary.** `docs/investigations/skill-evolve/<skill>/<timestamp>/00-comparison.md` is the same markdown table as the stdout report. This is the file `--body-file` references for the PR.

No per-variant worktrees exist to clean up — losers leave only their mutated copy under `work_dir` (a temp dir) plus their analysis file. Optionally delete `work_dir` once every analysis is written; it holds no git state, so there is no unmerged-work risk (contrast the old per-variant-worktree cleanup, which `.claude/rules/worktree-hygiene.md` §2-§4 flag as a recurring Windows file-lock hazard).

### Step 6: Final stdout output

Emit, in order:
- The comparison table (Step 3).
- For a WINNER: the gh pr create command (non-generated target) or the proposal and diff paths with the canonical destination (generated target); for NO WINNER, the "iterate" message.
- The path to the investigations directory: `Analyses written to docs/investigations/skill-evolve/<skill>/<timestamp>/`
- The winner's worktree path (if any), and the `work_dir` temp path (safe to delete once analyses are written).

---

## Halts

The 4 conditions under which this skill halts mid-run. Anything else is a defect.

1. **Pre-flight failure.** Skill / contract file / evals missing, both recognized defer forms present, a marked SKILL.md with a sibling core but no recognized defer line, a marked SKILL.md deferring to an unmarked core, `--baseline-from-results` with a contract file other than SKILL.md or with no usable blob-bound `baseline` row, variants file malformed, contract file outside a git work tree, working tree dirty, or the scorer check failed (run at the start of Step 1, after the workflow-primitive check). Halt before creating any worktree or work dir.
2. **Workflow unavailable.** The host workflow primitive cannot run in this environment. Halt rather than fall back to a single self-grading agent (defeats the skill's purpose and reintroduces the original defect).
3. **No valid comparison.** Every variant came back `FAILED`, BASELINE failed its integrity checks, or the contract file changed during the run. Halt with the workflow output and a partial report — there's nothing valid to compare.
4. **Operator killswitch.** If `.skill-evolve-killswitch` exists in the REPO root, halt at the next safe point (after a workflow invocation returns) and write a partial report. (Less critical than `/build-queue`'s killswitch because runs are typically 10-30 min, not 8 hours, but still useful.)

Note specifically: a single variant crashing is NOT a halt. The other variants are still data.

---

## Relationship to other skills

| Skill | Role |
|---|---|
| `/skill-eval-setup` | Sets up the `evals/` folder this skill A/B-tests against. Must be run on the target skill before `/skill-evolve` can operate. |
| `/skill-iterate` | Serial hill-climb on the same eval suite and scoring workflow; recommends `/skill-evolve` when a skill plateaus. Only its blob-bound `baseline` rows are eligible for `--baseline-from-results`: `contract=` must equal the resolved SKILL.md's repository-relative path and `sha256=` must match that path at the row's commit. A deferred core halts; identity-free keep rows are ignored. |
| `/build-queue` | Different shape — drains a queue of distinct plans. `/skill-evolve` runs N parallel variants of ONE skill. |
| `/user-draft` | Single-skill iterative refinement, no A/B. Use when you have ONE candidate change to a skill and want to refine it; use `/skill-evolve` when you have N candidates and want to know which wins. |
| `/loop` | Different shape — sequential repeats of one prompt on an interval. |

## Limitations

- **LLM grading is noisy.** Single-trial deltas under 5pp are statistical noise, not signal. The verdict logic enforces this; reports surface it visibly. If you need tight CIs, pass `--trials 5+` and accept the cost. Trials re-grade one render per scenario, so render variance is never sampled.
- **Strategies are operator-authored OR operator-curated, never LLM-auto-executed.** When `--variants` is supplied, the operator authored them. When `--variants` is omitted (brainstorm mode), the LLM proposes a list but exits before dispatching — the operator curates the file and re-invokes. Auto-running LLM-generated variants would drift toward "Claude-pleasing" patterns rather than testing real hypotheses; the operator-decision step (authorship or curation) preserves the contract. If a run produces NO WINNER, the next move is operator-side: read the loser analyses, propose or brainstorm new strategies.
- **The `evals.json` is held constant.** Mutating both the contract file and the eval suite in the same run would invalidate the A/B. If the eval suite itself is suspect (e.g., assertions are stuck at borderline-judgment), fix the evals first via `/skill-eval-setup` or manual edit, then re-run `/skill-evolve`.
- **No cross-skill parallelism.** This skill A/B-tests variants of ONE target skill. Running multiple `/skill-evolve` invocations on different skills concurrently has undefined behavior (worktree-name collisions if two runs target the same skill, disk pressure across the board). If you want concurrent skill evolution, run them in separate Claude sessions, separate target skills, separate timestamps.
- **No branch-push side effect.** Step 4 prints the local branch name, push command, and `gh pr create` command. It does not push or create a PR without operator confirmation.
- **Generated targets yield a proposal, not a branch.** The Skill Mesh catalog lifecycle owns every change to a catalog skill. Render agents read only the contract file, so a deferring launcher's host-specific lines are not part of the scored artifact.
- **No resume; re-runs are independent.** A run that halts, hits the killswitch or crashes is re-run from the start and reuses nothing from the earlier `work_dir`. Halts #3 and #4 leave a partial report; a crash may leave a partial analysis directory. Only a run that actually writes proposals, variant lists, analyses or a comparison creates a new `<timestamp>` directory; `--dry-run` and halts #1/#2 write nothing. Every scoring run creates a new `work_dir`, so earlier written artifacts are never overwritten. A non-generated winner's branch and worktree persist until the operator removes them; a later run whose winner reuses that id gets timestamp-suffixed names (Step 4).
- **Worktree pollution is largely eliminated by the workflow rewire.** Variants are scored from temp-file copies, not per-variant worktrees, so the only worktree created is the winner's (Step 4) — left in place deliberately for inspection. The recurring Windows file-lock cleanup hazard (worktree-hygiene §2-§4) no longer applies to losers; `work_dir` is a plain temp dir.
- **The mutation step is an LLM judgment call.** "Compress by 30%" is interpreted by the agent; another agent might produce a different mutation from the same strategy. Single-shot mutation comparison; if reproducibility matters, log the mutated contract file in the analysis (which Step 5 already does via the diff).
