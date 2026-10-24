# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve shipped shared scorers from the current host profile's `_shared` directory. The
  optional golden-corpus preview helper lives only in a source checkout at
  `<repository-root>/skill-eval-setup/scripts/generate_bad_examples.py`; installed profiles do
  not ship it, and no step depends on it (Step 5).
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Skill Eval Setup

Takes a skill name or path, reads its behavior contract, and produces:
1. An `evals/` folder inside the skill directory
2. `evals/evals.json` — true/false assertions auto-derived from the contract
3. `evals/test_scenarios.json` — 2–3 synthetic scenarios to test the skill against
4. `evals/golden/` — a verified good output, one planted-defect bad per discrimination assertion, and `manifest.json` (Step 5), or a named HELD reason
5. A copy-paste prompt the user runs in a fresh window to start the self-improvement loop

Downstream consumers: `/skill-iterate` and `/skill-evolve` require `evals/evals.json` and
`evals/test_scenarios.json`; the optional goldens verification in `_shared/score-skill.md` reads
`evals/golden/good.md` and every top-level `evals/golden/bad_*.md`; and a recorded
judge-calibration gate (`calibrate_judge.py`, used by review-deep) fails closed unless every
fixture in a golden directory that holds `verdicts.jsonl` or `recorded_scores.json` appears in its
recorded maps, so Step 5 never writes into such a directory. These paths and schemas are kept; the
golden manifest gains one additive per-bad field, `sha256` (Step 5).

This skill's grading path invokes only the shipped `grader_prompt.py` and
`score_skill_absolute.py`. It does not invoke `score_skill_composite.py`: that downstream
consumer has additional skill-iterate runtime dependencies and must be qualified by its owning
workflow before use. Emitting the composite file is not evidence that its whole runtime closure
works.

---

## Input

The user provides one of:
- A skill name (e.g., `session-wrap`) — resolved through the current host's discovery root
- A relative or absolute path to a skill folder or SKILL.md

Optional flag:
- `--keep-scenarios` — when the target skill already has `evals/test_scenarios.json`, do NOT overwrite it. Regenerate only `evals.json`. Use this when regenerating the assertion set against a rebuilt eval bar while preserving hand-crafted, project-specific scenarios.

**Behavior contract.** The contract is the target SKILL.md. When that SKILL.md defers its full
specification to a sibling `core.md` (every generated Skill Mesh profile does; its files carry the
marker `SKILL-MESH-GENERATED-FILE`), the contract is SKILL.md plus that `core.md`. In the steps
below, "the target SKILL.md" means this contract, and each assertion's `source` names the file
that holds the rule (`SKILL.md, line N` or `core.md, line N`).

**Generated targets are read-only.** A file whose leading provenance header identifies it as a
`SKILL-MESH-GENERATED-FILE` is overwritten by the next install. Do not use an unanchored substring
test: a contract may quote that marker. This skill never edits a generated contract. It may author
eval files beside an installed generated target, but the emitted loop stops before editing that
target and reports the canonical source named by the provenance header; continued iteration must
use that canonical source through its repository lifecycle. Assertions authored beside an
installed generated target cite the installed contract's line positions, which can differ from
the canonical source because of provenance headers; disclose that limitation in Part 1.

**Resolve the exact target before writing.** Canonicalize the selected skill directory and every
planned output path. Resolve `TARGET_REPO` with
`git -C <skill-dir> rev-parse --show-toplevel`; stop with `target-repo-unresolved` if that command
fails. Every write and every
Git check uses absolute paths under that exact skill directory and `git -C TARGET_REPO`. Refuse a
path that escapes through `..`, a symlink, junction, or reparse point. Never redirect a write to
the invoking window's repository or to a similarly named installed copy.

**Catalog-owned targets use the catalog lifecycle.** Before Steps 1-5 or emitting the Part 3 loop,
if `TARGET_REPO` contains `config/skill-manifest.json` and that manifest owns the selected skill,
stop unconditionally with `PACKAGE_RESOURCE_PLAN_REQUIRED`, whether or not `evals/` already exists.
Report that the requested package-local eval
resources need the repository's supported catalog lifecycle and, because they change resource
topology, a scoped packaging or source-only resource plan. Follow the current manual lifecycle
contract or installed `/skill-crud UPDATE` when available. A host-provided skill creator and a
single-host installed copy are not substitutes.

If the skill, its SKILL.md, or a `core.md` it defers to cannot be found, report the error and stop.

---

## Step 1: Read and analyze the SKILL.md

Read the full contract (SKILL.md and any deferred `core.md`). Extract every testable requirement:

### What to look for

| Signal | Example | Assertion type |
|---|---|---|
| **Required sections** | "Output two parts: X and Y" | Structure — output contains X and Y |
| **Format rules** | "wrapped in a code fence labeled `text`" | Structure — format matches |
| **Quantity constraints** | "4–8 lines", "2–5 files", "300–600 words" | Structure — count in range |
| **Content requirements** | "must be self-contained", "include the magic word" | Content — specific content present |
| **Specificity rules** | "concrete, not generic", "specific, actionable" | Content — no vague placeholders |
| **Process steps** | "Read MEMORY.md", "Check plan.md" | Process — step was performed |
| **Anti-patterns** | "do NOT duplicate", "skip one-off flukes" | Anti-pattern — bad thing absent |
| **Conditional behavior** | "if X exists, do Y; otherwise do Z" | Conditional — correct branch taken |

Assertions extracted from skill specs must be verifiable from output only. Internal tool
invocation order and intermediate file state are NOT valid assertion targets. If a spec
references internal activity, convert to an output-observable equivalent or mark as
non-testable.

### Categorization

Group assertions into categories that match the skill's logical structure. Use the skill's
own section headings as category names when possible. Always include an "Anti-patterns"
category for negative assertions (things the skill must NOT do).

### Assertion format

Each assertion must be:
- A single declarative statement that can be judged TRUE or FALSE
- Testable by reading the skill's output alone (no access to internal state)
- Traceable to a specific line or section in the contract via the `source` field

---

## Step 1.5: Design discrimination assertions

For each rule extracted in Step 1, name the **defect type** that would violate
the rule. The defect type drives a discrimination assertion: "if the output
exhibits defect D, this assertion grades FALSE."

This is the difference between an eval that catches things and an eval that
just describes things. A shape-checking assertion ("output contains two parts")
passes any well-formed output but cannot tell you whether the assertion is
*useful*. A discrimination assertion ("if either 'Part 1' or 'Part 2' heading
is absent, this assertion grades FALSE") is testable against a deliberately-
broken output corpus.

### Rule → defect type → discrimination assertion

| Rule pattern | Defect type | Discrimination assertion shape |
|---|---|---|
| "Output two parts X and Y" | structural — missing required part | "Output contains both X heading AND Y heading" |
| "wrapped in `text` code fence" | format — wrong fence label | "Output's outer fence label is exactly `text`" |
| "4-8 lines per entry" | quantity-constraint violation | "Every entry has line count in [4, 8]" |
| "must be self-contained" | content — external dependency | "Output references no file path outside the listed Key files set" |
| "do NOT duplicate" | anti-pattern — content-filter | "Output does not contain a memory entry already present in the target memory file" |
| "skip one-off flukes" | anti-pattern — content-filter | "Friction items do not include language matching /typo\|retry\|transient\|attempt/i" |
| "NEVER use triple-backtick fences inside X" | anti-pattern — explicit-rule | "X section contains no occurrences of '```' beyond the outer fence" |
| Fixed-form required bullet ("FIRST bullet must be: <literal>") | required-content — wrong form | "First bullet of `<section>` starts with the literal string `<fixed-form prefix>`" |
| Required fixed string in named section ("the magic word for this project is X") | required-content — fixed-string missing | "`<named section>` contains the literal string `<fixed value>`" |
| Cross-part claim ("Part 1's `<field>` bullet says YES → Part 2 must not reference prior conversation") | internal-inconsistency — cross-part contradiction | "If Part 1's `<field>` bullet contains `<positive value>`, Part 2 contains no occurrences of `/<contradicting pattern>/`" |
| Conditional behavior ("IF multi-project session, THEN use `/` per-repo separator in Git line") | conditional-behavior — rule not applied | "When `<observable signal of condition>` is present in the output, `<observable signal of required behavior>` is also present" |

### Pattern derivation guide — patterns most likely to be missed

The example rows above cover structural and anti-pattern rules well. The four
patterns below get systematically missed by template-following and need
explicit derivation.

**1. Fixed-form content.** When the target SKILL.md says "the first X must be
in this exact form" or "must start with the literal string Y", derive an
assertion that checks for the **literal string**, not just that X exists.
Generic "X is present" assertions pass any well-formed X.

**2. Required fixed strings in named sections.** When the SKILL.md names a
specific section ("Required context") AND specifies that a particular literal
string must appear there ("the magic word X"), derive an assertion that
checks for the literal string **inside the named section**.

**3. Cross-part consistency.** When the SKILL.md output has multiple parts
and one part makes a claim about another (e.g., Part 1's `Self-contained:`
bullet asserts whether Part 2 has external dependencies), derive a cross-part
assertion: read the claim in Part 1, then check Part 2 for content that would
contradict it. The assertion's `source:` field must reference BOTH the
part-making-the-claim AND the part-being-claimed-about. Cross-part assertions
are the hardest pattern for template-following to produce — be explicit about
deriving at least one.

**4. Conditional behavior (IF/THEN rules).** Scan the target SKILL.md for
every "If X, …" / "Multi-X sessions: …" / "When X happens, do Y" pattern.
For each, derive an assertion of the form "if `<observable signal of X>` in
the output, then `<observable signal of Y>` in the output."

### Pair each assertion with a target-skill-section reference

Each assertion's `source:` field must point to the specific lines in the
target SKILL.md that define the violated rule.

**Sourcing precision rule.** For every NEVER / NOT / IF / MUST / "fixed in
form" rule in the target SKILL.md, at least one produced assertion's
`source:` field must name the **specific line** that defines the rule —
either as a standalone number, or as one endpoint of a tight range (≤15
lines wide). A wide line range that brackets but doesn't single out the
rule's line does NOT satisfy this — a reader must be able to locate the
rule from the source string alone.

**Section-heading coverage rule.** Separately from the per-rule precision
above, the produced `source:` fields collectively must reference at least
one line within 10 lines of each major numbered section heading in the
target SKILL.md (Step 1, Step 2, Step 3, etc.). Pure rule-line precision
tends to cluster source citations around sub-rules, leaving section
headings uncovered — derive at least one assertion per major section
whose source field cites the heading line or a line within 10 of it.

### Discrimination quota

Of the assertions in the produced evals.json, **at least 40% must be
discrimination-style** (assertions whose statement names what would make them
grade FALSE, not just what would make them grade TRUE). Shape-only assertions
are still allowed but they are sanity checks, not the primary signal.

Additionally, **at least one of each of the four "patterns most likely to be
missed"** above should appear in the produced evals.json when the target
SKILL.md contains the corresponding rule type. If a pattern type doesn't
apply to a particular target (e.g., target has no multi-part output → no
cross-part consistency assertion possible), note its absence in Part 1
Summary with a one-line "(no X-pattern rules in target — N/A for this skill)".

---

## Step 2: Generate test scenarios

Create 2–3 synthetic test scenarios that exercise different paths through the skill.

### Scenario design principles

- **Cover the main path:** At least one scenario that exercises the skill's primary flow
- **Cover edge cases:** At least one scenario that triggers conditional behavior (e.g., "if
  plan.md is absent", "if the session was clean with no friction")
- **Be self-contained:** Each scenario must include all the context the skill needs to
  produce output — simulated conversation history, file states, user actions
- **Be concrete:** Use realistic project names, file paths, and actions — not "project X"

### Scenario format

```json
{
  "id": "scenario_1",
  "name": "Descriptive name",
  "description": "What this scenario tests",
  "context": "The simulated conversation/environment state the skill sees",
  "expected_assertions": [1, 2, 3, ...]
}
```

The `expected_assertions` field lists which assertion IDs should pass for this scenario.
Typically all assertions apply to all scenarios, but some conditional assertions may only
apply to specific scenarios. List every assertion whose trigger fires in the scenario: the
shared grader grades an ID missing from a non-empty list as vacuously TRUE, so an omitted ID
can never fail.

---

## Step 3: Write the eval files

### evals.json

```json
{
  "skill": "<skill-name>",
  "version": "1.0",
  "description": "True/false evaluation for the <skill-name> skill.",
  "passing_threshold": "<N-2>/<N>",
  "categories": [
    {
      "name": "Category Name",
      "evals": [
        {
          "id": 1,
          "statement": "The output does X.",
          "source": "SKILL.md, lines NN-MM",
          "defect_type": "<one of: structural, format, quantity, content, anti-pattern, required-content, internal-inconsistency, conditional-behavior, n/a-sanity, n/a-coverage>",
          "result": null
        }
      ]
    }
  ]
}
```

Rules:
- Set `passing_threshold` to `(total - 2) / total` — allows 2 failures before the skill
  is considered broken
- Number assertions sequentially starting at 1
- The `result` field is always `null` in the template — the loop fills it in
- The `source` field must reference actual line numbers in the contract file that holds the
  rule (per the Sourcing precision and Section-heading coverage rules in Step 1.5)
- The `defect_type` field categorizes the assertion. Use `n/a-sanity` for pure
  structural sanity checks (valid JSON, sequential ids, etc.) and `n/a-coverage`
  for assertions that aggregate over the target SKILL.md rather than testing a
  specific defect.

### test_scenarios.json

```json
{
  "skill": "<skill-name>",
  "version": "1.0",
  "scenarios": [
    {
      "id": "scenario_1",
      "name": "...",
      "description": "...",
      "context": "...",
      "expected_assertions": [1, 2, 3]
    }
  ]
}
```

Before writing, verify that `evals/evals.json` and `evals/test_scenarios.json` resolve under
the exact target directory. Define the write set as only the paths this run will write; with
`--keep-scenarios`, omit the preserved scenario file. For every existing write-set path, run
`git -C TARGET_REPO check-ignore -q -- <path>` and stop with `dirty-output` if it is ignored.
Then run `git -C TARGET_REPO status --porcelain --untracked-files=all -- <write-set>`; nonempty
stdout or a nonzero exit means `dirty-output`. Advisory stderr such as a line-ending warning is
recorded but is not dirty by itself when the command succeeds. Write only after these checks pass,
and still report kept-scenario ID drift.

### `--keep-scenarios` behavior

When `--keep-scenarios` is passed AND `<skill-folder>/evals/test_scenarios.json` already exists:
1. Do NOT overwrite `test_scenarios.json`.
2. Number the new assertions independently. Compare the kept scenarios' `expected_assertions` with the new IDs and list in Part 1 every kept reference to an ID the new `evals.json` lacks, and every new ID that no kept scenario lists (it can only grade vacuously TRUE). Do not edit the kept file to fix them.
3. In Part 2 of the output, list `test_scenarios.json` with a `(preserved — N scenarios)` suffix instead of as a written file.

When `--keep-scenarios` is passed BUT no existing `test_scenarios.json` is found, fall through to normal behavior (generate fresh scenarios) and note this in Part 1 Summary.

---

## Step 4: Generate the self-improvement loop prompt

Output the following prompt, customized for the target skill. Present it in a code fence
labeled `text` so the user can copy-paste it into a fresh window.

The prompt must include:
1. The skill name and **absolute** paths: the skill directory, every contract file, the one
   editable file (the file that holds the contract's rules: the deferred `core.md` when there
   is one, otherwise SKILL.md), the directory that contains the editable file, and the shared
   scoring-helper directory, which is the `_shared` directory itself (the one that contains
   `score-skill.md`, `grader_prompt.py` and `score_skill_absolute.py` in this install), not its
   parent. Every placeholder in the template must be replaced with concrete absolute values
2. Instructions to read the contract, evals.json and test_scenarios.json
3. A preflight that stops before any edit when the editable file is generated, is outside a git
   work tree, is catalog-owned, is untracked or ignored, is on a detached or changed branch, or
   has uncommitted changes; when a scenario lists an assertion ID that evals.json lacks; when no
   current verified golden pair exists; or when the grader cannot score the stripped good body
   above the stripped bad body. Every git command in the loop runs against the editable file's own
   repository (`git -C` with the root resolved from the editable file's directory), never
   against the window's working directory
4. A baseline scored and logged before any edit
5. The produce-then-grade loop: for each scenario, use a producer invocation to simulate the
   skill's behavior following the contract and produce the output, then use a
   separate fresh-context grader invocation to grade every assertion TRUE/FALSE. The generated
   loop MUST spawn a fresh-context grader invocation separate from the producer invocation. The
   same context window must not produce output and then evaluate it. This is invariant 1 and is
   non-relaxable. Grader prompts come from the shared `build_grader_prompt` helper and scores
   from the shared `score_skill_absolute.py` aggregator, never from hand-written grading rules
6. Score calculation: the aggregator's `simple_score` (TRUE verdicts over scenario-assertion
   pairs), with the baseline and every keep/revert decision taken over 3 trials
7. If any assertions fail: propose ONE targeted change to the editable file, apply it, re-run
   all scenarios, and compare with the baseline
8. Keep/revert logic: keep if the score is strictly higher than the baseline; otherwise confirm
   that the file's diff is only this iteration's change and restore it with
   `git checkout -- <file>`; a diff holding anything else stops the loop without a restore
9. Iteration logging: number, score, keep/discard, what was tried
10. Termination: perfect score or user interrupt
11. Git commit of the editable file alone (a pathspec-limited commit) on each kept change, with
   a message like: `<skill-name> eval: iteration N — <what changed>`

### Prompt template

```text
Run a self-improvement loop on the skill at `<skill-dir>`.

## Setup
- Read the contract in full: `<contract-files>`
- The only skill file this loop may change: `<edit-file>` (in directory `<edit-dir>`)
- Read `<skill-dir>/evals/evals.json` (the assertions)
- Read `<skill-dir>/evals/test_scenarios.json` (the test scenarios)
- Goldens: `<skill-dir>/evals/golden/` (good.md, verified bad_*.md, manifest.json)
- Shared scoring helpers: `<shared-dir>/grader_prompt.py` and `<shared-dir>/score_skill_absolute.py`

## Preflight (stop before any edit and report the reason)
Run every git command in this loop as `git -C REPO ...`, where REPO is resolved below; never run
git from this window's working directory.
- generated-target: the leading provenance header of `<edit-file>` identifies it as a
  SKILL-MESH-GENERATED-FILE. Report the canonical source it names; change that source through its
  own repository's process, not in this loop. A quoted marker elsewhere in the file does not count.
- untracked-target: `git -C <edit-dir> rev-parse --show-toplevel` fails (the file is outside a
  git work tree; otherwise its output is REPO), or this fails because the file is untracked or
  ignored: `git -C REPO ls-files --error-unmatch -- <edit-file>`.
- catalog-target: REPO has `config/skill-manifest.json` and that manifest owns this skill. Stop
  with `PACKAGE_RESOURCE_PLAN_REQUIRED`; do not edit or commit the catalog source from this loop.
- branch-changed: record the nonempty result of `git -C REPO branch --show-current` as BRANCH;
  detached HEAD is a stop. Re-run it before every edit and commit and stop if it differs.
- dirty-target: `git -C REPO status --porcelain --untracked-files=all -- <edit-file>` prints
  anything on stdout or exits nonzero. Record advisory stderr but do not treat a successful
  command's line-ending warning as a dirty file.
- scenario-drift: a scenario's expected_assertions lists an id that evals.json does not define.
- uncalibrated-grader: good.md is missing, or manifest.json lists no bad for an assertion ID in
  the current evals.json with verified_fails: true.
- grader-cannot-discriminate: graded for 3 trials each as in Grade below (scenario_id "golden",
  expected_assertions None), a current verified bad scores greater than or equal to good.md.
  Before grading either artifact, remove only consecutive leading generated answer-key comments
  matching `<!-- BAD OUTPUT ... -->` and `<!-- Violates ... -->`; keep the stored file unchanged.
  Any invalid or incomplete golden grade is indeterminate and fails this preflight.

## Baseline (before any edit)
Run Produce + Grade for 3 trials and log the result as Iteration 0 with Result: BASELINE.
That score is the baseline.

## Loop (repeat until perfect score or interrupted)

### Produce [producer step]
For each scenario in test_scenarios.json:
1. [producer step] Spawn a fresh producer invocation for the scenario
2. [producer step] Give it only the contract and that scenario's `context`; never give a producer
   evals.json, goldens, grader results, or the iteration log
3. [producer step] Treat the scenario context as the whole simulated environment
4. [producer step] Render output text only. Run no commands, use no tools, write or delete no files,
   and make no network, Git, issue-tracker, or other external mutation. Dispatch without tools
   wherever the host supports that restriction
5. [producer step] Return the full text the skill would have produced

### Grade [grader step]
Spawn a fresh-context grader invocation separate from the producer invocation. The same context
window must not produce output and then evaluate it. This producer/grader split is invariant 1
and is non-relaxable.

- [grader step] Build each scenario's grader prompt with
  build_grader_prompt(scenario_id=scenario_id, rendered_output=output, evals_json=evals_text,
  expected_assertions=scenario_expected) from grader_prompt.py (keyword arguments only), using
  that scenario's own id and expected_assertions. Use the template verbatim; do not write your
  own grading rules.
- [grader step] Each grader returns {"verdicts": {...}}. Before aggregation, validate against the
  complete set of assertion IDs in evals.json. On a JSON parse failure, re-dispatch that grader
  once. After that single retry, replace a failed block with every required ID set to JSON boolean
  false. For a parsed block, drop unknown IDs, backfill omitted IDs as false, and coerce every
  non-boolean verdict to false; preserve a short repair reason. Thus every block has every and only
  the required IDs with literal JSON booleans.
- [grader step] Collect the normalized blocks as one payload
  {"trials": [{"scenario_id": ..., "verdicts": {...}}, ...]} with one entry per scenario per
  trial. Write it to a temporary JSON file outside the source tree and run
  `python <shared-dir>/score_skill_absolute.py --evals <skill-dir>/evals/evals.json --input <payload-file>`.
  Accept the result only when `total` equals scenario count times assertion count. The score is
  its simple_score; any other total is a harness error and stops before an edit.
- [grader step] One trial is Produce + Grade over every scenario. Put all 3 trials in one
  payload; the aggregator takes the per-scenario, per-assertion majority.

### Improve
If score < 100%:
1. Identify the root cause of the lowest-confidence FALSE assertions
2. Propose ONE targeted change to `<edit-file>` that would fix them without breaking passing assertions
3. Re-run the branch-changed and dirty-target checks and stop if either fails; then apply the change
4. Re-run Produce [producer step] + Grade [grader step] for 3 trials using separate invocations
5. If the score is strictly higher than the baseline: recheck BRANCH, run
   `git -C REPO add -- <edit-file>`, then
   `git -C REPO commit -m "<skill-name> eval: iteration N - <description>" -- <edit-file>`.
   The new score becomes the baseline.
6. Otherwise: confirm that `git -C REPO diff -- <edit-file>` shows only this iteration's change,
   then run `git -C REPO checkout -- <edit-file>`. If the diff holds anything else, stop without
   restoring and report concurrent-edit.

### Log
Append to `<skill-dir>/evals/iteration_log.md` using this format:

    ## Iteration N
    - Score: X/Y (Z%)
    - Result: BASELINE / KEPT / DISCARDED
    - Change: <one-line description of what was tried>
    - Failures: <list of assertion IDs that failed>

## Rules
- Do NOT stop to ask questions. Run autonomously.
- Do NOT make more than ONE change per iteration.
- Do NOT modify evals.json, test_scenarios.json, or anything in evals/golden/.
- Do NOT change any file except `<edit-file>` and the iteration log, and never commit or restore
  any other path.
- Run producer invocations on the known model the skill uses in production. If that model cannot
  be established or dispatched, stop with `production-model-unknown` or `required_tool_missing`;
  never substitute another model.
- If you hit 3 consecutive DISCARDED iterations with no progress, try a fundamentally
  different approach rather than tweaking the same area.
```

Replace all `<skill-dir>`, `<contract-files>`, `<edit-file>`, `<edit-dir>`, `<shared-dir>` and `<skill-name>` placeholders with actual values. REPO is not a placeholder: the loop resolves it in its own preflight.

---

## Step 5: Build and verify the golden corpus

Run after Step 4. The corpus is a calibration anchor: one known-good output plus one
planted-defect bad per discrimination assertion. `verify_goldens` in
`_shared/score_skill_composite.py` (the goldens verification described in
`_shared/score-skill.md`) loads `evals/golden/good.md` and every top-level
`evals/golden/bad_*.md`, ignores `manifest.json`, and reports harness-error, which parks the
skill when that verification is invoked and any bad scores greater than or equal to the good.
Composite mode does not invoke it automatically. Goldens are optional for that check (absent
means skipped); the Step 4 loop requires a verified pair before its first edit.

### Who dispatches

The agent running this skill dispatches every producer, generator and grader invocation
itself. Every grader is a fresh-context invocation separate from the invocation that wrote the
content it grades. Producers and generators return text only: give them no filesystem, shell,
network, Git, issue-tracker, or other mutation tools where the host can enforce that, and instruct
them to make no external side effects. The parent agent alone performs the validated writes in
this contract. Producers receive only the target contract and scenario context, never evals.json,
goldens, grader results, the manifest, or an iteration log. The helper script's production dispatch and scoring are not wired: outside
`--dry-run` its generate mode stops at the first dispatch (exit 4) after writing `good.md`,
which is a placeholder when none existed, and its `--verify-only` mode records every bad as not
verified and rewrites `manifest.json`. Use the script only for `--dry-run` previews and its pure
helpers (`derive_slug`, `build_generator_prompt`, `build_retry_prompt`). Never run its generate,
`--fleet` (without `--dry-run`) or `--verify-only` modes, and never treat their output as a
verification result.

### Preconditions and HELD outcomes

Check these before any Step 5 dispatch:

- `required_tool_missing`: a required producer, generator or grader invocation is unavailable.
  Steps 1-4 remain a useful standalone authoring path, but Step 5 is HELD and makes no golden
  write; never simulate an unavailable isolated grader in the current context.
- `production-model-unknown`: the target skill's production model cannot be established. Do not
  substitute a cheaper, nearby, or default model for a producer.
- `PACKAGE_RESOURCE_PLAN_REQUIRED`: the unconditional catalog-owned-target guard from Input
  applies even when `evals/` or a prior golden corpus already exists.
- `calibrated-corpus`: `evals/golden/` holds `verdicts.jsonl` or `recorded_scores.json`. A
  recorded judge-calibration gate replays a score for every fixture there and fails closed on a
  fixture it lacks, so any new or replaced bad would break it.
- `manifest-unreadable`: an existing `evals/golden/manifest.json` is not a JSON object, or its
  `bads` is present but not a list, so the merge in Writes cannot preserve it.
- `unanchored-corpus`: `good.md` is absent while top-level `bad_*.md` files or an
  `additional_goods` manifest field already exist. Do not introduce a new primary good whose
  relationship to that curated corpus has not been calibrated.

Step 5 is also HELD with `good-not-verified` when 5a accepts no good. Every HELD outcome writes
nothing under `evals/golden/` (no good, no bad, no manifest), reports the reason in Part 1, and
keeps the Step 1–4 outputs.

Before the first dispatch, state the planned maximum number of invocations: one good producer
(only when 5a has no good to reuse), three independent good-grader trials, and, for each slug
that Step 5b will generate, up to three attempts of one generator plus three independent
grader trials. With a produced good, under the 25-assertion cap this is
`1 + 3 + 25 * 3 * (1 + 3) = 304`; with a reused good it is at most 303. Also announce the
Step 4 loop preflight cost of `3 * (1 + B)` grader invocations for one good and `B` current
verified bads. This is a notice, not a question; then proceed.

### Grading a golden

Derive the grading body without changing the stored artifact: from both good and bad content,
remove only consecutive leading generated answer-key comment lines matching
`<!-- BAD OUTPUT ... -->` and `<!-- Violates ... -->`, then preserve the remainder byte for byte.
This also applies to hand-curated bads and the Step 4 discrimination preflight. Do not remove
arbitrary leading HTML comments.

Grade that body with three independent fresh grader invocations whose prompt is
`build_grader_prompt(scenario_id="golden", rendered_output=<grading-body>, evals_json=<evals.json text>, expected_assertions=None)`
from the shared `grader_prompt.py`. With no list, the template's secondary rule grades an
assertion whose trigger is absent from the content as vacuously TRUE. Aggregate the verdicts
with the shared `score_skill_absolute.py`, passing three blocks with the same scenario id:
`{"trials": [{"scenario_id": "golden", "verdicts": <trial-1>}, ...]}`.
Before aggregation, validate each block against every assertion ID in evals.json. Re-dispatch
once on a JSON parse failure. A block is `indeterminate` if the retry still fails, an ID is
missing or extra, a verdict is absent or is not a literal JSON boolean, or its shape otherwise
differs from the contract. Unlike loop scoring, never backfill or coerce a golden verdict. Write
the complete valid payload to a temporary file outside the source tree and invoke
`score_skill_absolute.py --evals <evals-path> --input <payload-file>`. Require `total` to equal
the assertion count and require `failed_assertions` to be present; otherwise the grade is
`indeterminate`. The content's score is its `simple_score`. An indeterminate grade never satisfies
a gate. Step 5 graders run
at the Sonnet tier resolved through `config/model-tier-map.json`. The absolute aggregator
collapses the three trials by per-assertion majority. Use this same production-helper procedure
for the good and every bad; do not hand-calculate or substitute the composite scorer.

### 5a. Known-good anchor

1. If `evals/golden/good.md` exists and is not the helper's placeholder stub, reuse it. The stub
   is exactly these two lines, compared byte for byte after removing a UTF-8 BOM, converting
   CRLF to LF and removing trailing newlines; any other content, including text added under the
   stub's lines, is a real good:

       <!-- GOOD OUTPUT — auto-generated placeholder (Step 8 of SIHC plan) -->
       <!-- Step 9 will replace this by running the target skill on a canonical scenario. -->

   Keep the earlier manifest's `good_source` when there is one. If it is absent, record
   `hand-crafted` and add `good-provenance-inferred` to Part 1. Never overwrite a reused good.
2. Otherwise dispatch a producer invocation that follows the contract on the main-path
   scenario and returns the full output (`good_source: "auto-generated"`). Run it on the model
   the target skill uses in production.
3. Grade the good, reused or produced. Accept it only when the grade is determinate, `total`
   equals the assertion count, `failed_assertions` is empty, and every assertion grades TRUE; then
   write an accepted produced good to `evals/golden/good.md`, replacing the stub if one is
   there.
4. If the good is not accepted, Step 5 is HELD with `good-not-verified`: list the failing
   assertion IDs in Part 1 and write nothing under `evals/golden/`. Never write a placeholder
   good.

### 5b. One bad per discrimination assertion

#### Per-skill golden directory layout

```
.claude/skills/<skill-name>/evals/golden/
    good.md                       <- accepted known-good output (5a)
    bad_<defect-slug-1>.md        <- one per verified discrimination assertion
    bad_<defect-slug-2>.md
    ...
    inert/bad_<defect-slug-N>.md  <- generated bads the grader could not distinguish
    manifest.json                 <- per-bad metadata index
```

The corpus is **self-contained per skill**: every skill ships with its own goldens and there is
no central corpus directory.

#### Slug derivation rule

Map each assertion's `defect_type` field to a filesystem-safe slug:

1. Lowercase the `defect_type`.
2. Replace every run of non-alphanumeric characters with a single `_`.
3. Strip leading and trailing `_`.
4. Truncate at 60 characters.
5. If the result is empty, use `unnamed`.

| `defect_type` | Derived slug | Filename |
|---|---|---|
| `structural — missing required output part` | `structural_missing_required_output_part` | `bad_structural_missing_required_output_part.md` |
| `anti-pattern — explicit-rule violation` | `anti_pattern_explicit_rule_violation` | `bad_anti_pattern_explicit_rule_violation.md` |
| `quantity-constraint violation` | `quantity_constraint_violation` | `bad_quantity_constraint_violation.md` |
| `required-content — fixed-string missing` | `required_content_fixed_string_missing` | `bad_required_content_fixed_string_missing.md` |

When two assertions share the same `defect_type` (and therefore the same
raw slug), append a numeric suffix: `bad_duplicate_constants.md`,
`bad_duplicate_constants_2.md`, `bad_duplicate_constants_3.md`. The suffix
preserves the 60-char total length cap by trimming the base portion first.
Hand-crafted bads can carry derived names too (several existing corpora were built by hand with
this rule), so a matching name never shows that this skill wrote a file. Writes (below) decides
which existing files Step 5 may replace or remove.

#### Per-assertion mapping

One bad file per **discrimination assertion**, where "discrimination" means
`defect_type` is NOT in `{n/a-sanity, n/a-coverage}`. Sanity-shape and coverage
assertions are excluded because they do not name a planted defect to target.

The mapping is 1:1:1 — one assertion → one defect_type → one slug → one
`bad_<slug>.md` file. If `evals.json` contains 8 discrimination assertions
across all categories, Step 5 generates up to 8 bad files (top level or `inert/`); a slug that
collides with a file it did not write is skipped and reported (Writes).

#### Generator invocation contract

Dispatch one generator invocation per assertion at the Sonnet tier resolved through
`config/model-tier-map.json`, with these inputs:

| Input | Source |
|---|---|
| Assertion text + `defect_type` | from `evals.json` |
| `good.md` content | the accepted good from 5a |
| Target contract content | the SKILL.md and any deferred `core.md` |
| Subtlety instruction | `"subtle"` (this skill has no input that selects the helper's `"obvious"` setting) |

The generator is instructed to:
1. Modify the GOOD output minimally so it violates **exactly** the named
   `defect_type` (prefer a single-line diff against `good.md`).
2. Keep every other contract rule satisfied (only one defect planted).
3. Stay in the **subtle zone** by default — preserve surface plausibility,
   violate only the underlying rule. A sycophantic grader doing a substring
   or paraphrase-tolerant check should still mistakenly pass the output;
   only a strict assertion tied to the named defect_type should catch it.
   (LLMs default to obvious-bad; the explicit subtle instruction is what
   produces real pressure-test material.)
4. Prepend an HTML comment header naming the defect and the contract line
   range it violates. Example:

   ```
   <!-- BAD OUTPUT — DEFECT: <one-line defect summary> -->
   <!-- Violates SKILL.md lines <N-M>: "<quoted rule fragment>" -->
   ```

The generator returns ONLY the bad.md content (header + body). No surrounding
prose, no JSON envelope. When the helper script is available, build the base prompt with its
`build_generator_prompt` and each retry prompt with its `build_retry_prompt`.

#### Verification gate

Grade each generated bad as in Grading a golden, with three grader invocations that are never the
generator. A bad is **accepted** only when its determinate score is **strictly lower** than the
accepted good's score and its target `assertion_id` appears in `failed_assertions`. A different
failure does not verify the claimed mapping. A tie, an unrelated failure, or an `indeterminate`
result does not distinguish the pair and triggers the next attempt; an unverifiable bad is
regenerated, never accepted.

| Attempt | Prompt change | Outcome on `fails` | Outcome on `passes` |
|---|---|---|---|
| 1 | base generator prompt | accept (`verified_fails: true, regen_attempts: 1`) | escalate to attempt 2 |
| 2 | base + "Previous attempt was too obvious; try a SUBTLER defect" | accept (`verified_fails: true, regen_attempts: 2`) | escalate to attempt 3 |
| 3 | base + "FINAL retry; make this attempt MORE SUBTLE than the last" | accept (`verified_fails: true, regen_attempts: 3`) | mark INERT (`verified_fails: false, regen_attempts: 3`) |

The default budget is 3 total attempts per bad. `fails` means the grader scored the bad lower
than the good; `passes` covers ties and `indeterminate` results.

#### INERT marker

After the last attempt without an accepted result, write the most recent content to
`evals/golden/inert/bad_<slug>.md`, never to the top level: a top-level bad that the grader
cannot distinguish makes the goldens verification report harness-error and park the skill.
Record it in the manifest with `verified_fails: false`. The operator can then:

1. Hand-craft a discriminating bad (the generator's planted defects were
   all in the grader's blind spot for this assertion).
2. Tighten the corresponding assertion in `evals.json` (the assertion as
   written cannot distinguish the failure modes the generator considers
   subtle).
3. Accept the gap and revisit it during the next adversarial calibration pass.

#### Writes

Step 5 writes only `good.md` (under 5a's rules), generated `bad_<slug>.md` files at the top
level or under `inert/`, and `manifest.json`, written last. It never replaces or removes a file
that it cannot show it wrote:

- **Own file.** An existing bad is this skill's own unmodified output only when the previous
  manifest lists it at that path with a `sha256` equal to the tool-computed lowercase SHA-256 of
  normalized content: decode UTF-8, remove one leading BOM, convert CRLF and lone CR to LF, then
  encode UTF-8 without a BOM. Never hand-transcribe the digest. This normalization prevents
  `core.autocrlf` from destroying ownership while preserving all textual content. In addition,
  when `evals/golden/` is inside a git work tree, this command must print nothing on stdout and
  exit 0: `git -C <golden-dir> status --porcelain --untracked-files=all -- <file>`
  (`<golden-dir>` is the absolute `evals/golden/` path). Record advisory stderr but do not treat
  a successful line-ending warning as dirt. An entry without `sha256` never proves ownership.
- **Collision.** Before any dispatch for a slug, check both of its paths, `bad_<slug>.md` and
  `inert/bad_<slug>.md`. If either exists and is not an own file, the slug is a collision:
  dispatch nothing for it, write or remove nothing for it, and list it in Part 1 with the path.
- **Replacement.** For a slug without a collision, write the new bad at its new location
  (replacing an own file there) and remove an own file at the other location.
- **Everything else stays.** Leave every other file untouched. List in Part 1 every `bad_*.md`,
  at the top level or under `inert/`, that the new manifest does not list.

When this run wrote no good and wrote or removed no bad, leave `manifest.json` untouched.
Otherwise, record the manifest's normalized SHA-256 at preflight (or record that it is absent),
stage every prospective golden and manifest outside `evals/golden/`, and recheck the manifest
immediately before applying the write set. If it changed, stop with `concurrent-manifest` and
write nothing under `evals/golden/`. Write it by merging with the previous manifest when one exists:

- Keep unchanged every previous `bads` entry for a file this run neither wrote nor removed,
  whatever its fields.
- For each slug this run wrote, one new entry replaces the previous entries for both of its
  paths; carry forward any per-entry field this schema does not define from a replaced entry.
- Keep every top-level field this schema does not define (for example `additional_goods` or
  `update_note`). Set `manifest_version`, `skill`, `generated_at` and `good_source` as this
  schema says, and recompute `verification_summary` over the merged `bads`.
- Read JSON with optional UTF-8 BOM tolerance. Write the manifest as UTF-8 without BOM to a
  temporary file in `evals/golden/`, recheck the recorded manifest hash, then atomically rename
  it over `manifest.json`. A failed recheck or rename leaves the prior manifest intact.

### `manifest.json` schema (v2)

```json
{
  "manifest_version": 2,
  "skill": "<skill-name>",
  "generated_at": "<ISO-8601 timestamp, UTC, second precision>",
  "good_source": "auto-generated" | "hand-crafted",
  "verification_summary": {
    "accepted": <int>,
    "inert": <int>,
    "total": <int>
  },
  "bads": [
    {
      "file": "bad_<slug>.md" | "inert/bad_<slug>.md",
      "defect_type": "<from assertion>",
      "assertion_id": "<from evals.json if present, else null>",
      "verified_fails": true | false,
      "regen_attempts": 1 | 2 | 3,
      "sha256": "<lowercase hex SHA-256 of normalized UTF-8 content>"
    }
  ]
}
```

Schema notes:

- `manifest_version` is `2`. Manifests without it predate verification
  (`verified_fails: null`, `regen_attempts: 0`); the merge carries their entries forward
  unchanged, and they never prove ownership.
- `generated_at` is read from the clock when the manifest is written.
- `file` is the path relative to `evals/golden/`.
- `verification_summary` is a fleet-scannable tally over the merged `bads`:
  `accepted` counts entries with `verified_fails: true`, `inert` counts entries
  with `verified_fails: false`, and `total` is their sum. A jq query for
  `inert > 0` finds skills with gaps. Part 1 reports any carried-forward entry
  whose `verified_fails` is neither `true` nor `false`.
- Every entry this run writes has `verified_fails` `true` (accepted, at the top
  level) or `false` (INERT, under `inert/`), never `null`. Carried-forward
  entries keep their recorded values.
- Per-bad `regen_attempts` is the total number of generator dispatches
  consumed (`1` accepted on first try, `2` on first retry, `3` on second
  retry or INERT-after-final).
- Per-bad `sha256` is an additive field: the lowercase SHA-256 of the normalized UTF-8 content
  defined in Writes. It is the only proof that a later run may replace
  or remove the file (Writes). Goldens verification ignores the manifest.

### Helper script (optional)

The helper lives only in a source checkout at
`<repository-root>/skill-eval-setup/scripts/generate_bad_examples.py`. Safe entry points:

| Command | Effect |
|---|---|
| `python generate_bad_examples.py --skill <name> --dry-run` | Preview one skill's planned bad files without dispatching or writing. |
| `python generate_bad_examples.py --fleet --dry-run` | Preview every discovered skill that has `evals/evals.json` (directories beginning with `_` are skipped). |

Its other modes are not wired to a dispatcher or scorer (see Who dispatches). Re-verifying a
corpus after a grader or contract change therefore means re-running Step 5 under its Writes
rules, not `--verify-only`.
The preview helper discovers skills relative to its own source-checkout directory; it does not
preview an arbitrary absolute target. If that discovery root is not the intended target, skip the
helper and apply this contract directly.

---

## Re-runs and interruptions

- **Steps 1–3.** A re-run replaces `evals/evals.json`, and `evals/test_scenarios.json` unless
  `--keep-scenarios` keeps it. The repository-bound `dirty-output` check above includes
  untracked output files and fails closed on Git errors, so no uncommitted eval file is
  overwritten. Part 2 marks each clean replaced file. Carried-forward manifest entries keep
  their `assertion_id`, which refers to the `evals.json` they were made with.
- **Step 5.** A re-run reuses an accepted good (5a), regenerates only slugs whose paths are
  empty or hold own files, reports every collision, and merges the manifest. A previous run's
  golden files that are still uncommitted count as collisions until the operator commits or
  removes them.
- **Interrupted Step 5.** The manifest is written last, so an interrupted run leaves its bads
  unlisted and without a recorded `sha256`. The next run reports them as collisions or unlisted
  files and never removes them; the operator keeps or deletes them. A `good.md` it wrote is
  reused and graded like any existing good; without an earlier manifest its provenance is
  reported as inferred.
- **The loop.** Each run starts with the preflight and a new baseline, and kept changes are
  already committed. An iteration interrupted after Apply leaves the edit file modified, so the
  next run stops at dirty-target until the operator commits or restores it.

---

## Output format

Output three clearly separated parts:

### Part 1 — Summary

A short paragraph (3–5 lines) confirming:
- How many assertions were generated and in how many categories, AND of those, how many
  are discrimination-style (named `defect_type` other than `n/a-*`)
- How many test scenarios were created and what they cover
- The passing threshold
- The golden corpus result: `accepted/inert/total` and `good_source`, or `HELD <reason>`

Add one line for each N/A pattern note (Step 1.5), kept-scenario drift item (Step 3), replaced
clean eval file (Re-runs), inferred good provenance, Step 5 collision, unlisted bad, or
carried-forward manifest entry whose `verified_fails` is neither `true` nor `false` (Step 5).

### Part 2 — Files created

List every file written, one per line, using its full **absolute** path (e.g., `/abs/path/to/.claude/skills/<skill-name>/evals/evals.json`). Do not use relative paths. Add a `(replaced)` suffix to a file that existed before this run, and list each file Step 5 removed with a `(removed)` suffix.

### Part 3 — Self-improvement prompt

The copy-paste prompt in a `text` code fence.

---

## What NOT to do

- Do not generate assertions that require access to internal state (tool calls made, files
  read) — only test observable output
- Do not generate more than 25 assertions — focus on the most important requirements
- Do not create scenarios that are trivially identical — each must exercise a different path
- Do not hardcode model names in the self-improvement prompt — keep it model-agnostic
- Do not modify the target's contract files — this skill only reads them
- Do not write vague-judgment assertions ("the output is well-structured", "the prompt feels
  clear"). Every assertion must name a specific observable property whose presence or
  absence can be checked mechanically by reading the output alone.
- Do not write assertions whose `statement` only describes positive presence when the
  SKILL.md prose explicitly forbids something. For "NEVER do X" rules, the assertion must
  name X and check for its absence directly — not a surrounding positive property that
  happens to imply X's absence.
- Do not write a placeholder or unverified `good.md`, and do not record a bad as verified
  without a separate grader's result.
- Do not replace or remove a golden file that Step 5 cannot show it wrote, and do not drop an
  earlier manifest entry or field except where Writes replaces the entry of a file this run
  wrote or removed.
