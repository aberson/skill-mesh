# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Supporting assets resolve against the skill's installed directory (Claude profile:
  `.claude/skills/goblin-suggest/`). The Workflow script `goblin_suggest.workflow.js` and
  `evals/` ship there as support assets; the canonical prose lives here.
- A named skill call means the host's skill-dispatch primitive. Every model call in this skill
  runs inside the Workflow script as an isolated `agent()` arm with fresh context: one generator
  arm, relay arms for the CLI seams, and `--n-judges` judge arms per candidate. A judge never
  shares a context with the generator. The goblin CLI itself makes no model calls.
- The `Workflow` tool is required, and this core documents no fallback for it. The Workflow
  primitive means the whole script, including its deterministic aggregation and its CLI relays.
  Mapping the model arms one by one onto a host's isolated task or action calls does not supply
  it. A host whose adapter maps no Workflow primitive halts `required_tool_missing` naming the
  suggest rail before running any goblin command. Never generate and judge candidates in one
  context, never hand-write graded JSON for the CLI, and never substitute a `claude -p` call.
- Model tier names in inherited procedures describe capability roles. Resolve them through
  `config/model-tier-map.json`; an unavailable required capability returns
  `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured
  artifacts, and operator-facing rationale required by this contract.

# goblin-suggest

Run goblin's project-improvement pipeline against one workspace project. The skill grounds in
the project's real state (instruction file, plan, open issues, memory), generates candidate
improvements anchored to real artifacts, scores each candidate with a parallel four-axis
LLM-judge rubric, ranks the survivors, and persists them as suggestion atoms under goblin's
`brain/suggestions/`, where `/goblin-do` picks them up.

The model steps run through the `Workflow` tool (`goblin_suggest.workflow.js`) inside a Claude
Code session, so every `agent()` call stays on the session's subscription auth. The goblin CLI
supplies only deterministic seams: `--export-prompts` (grounding and prompt assembly),
`--build-judge-prompt` (one judge prompt per candidate), and `--from-candidates-json` (rank,
discriminate, persist). There is no CLI fallback: since goblin `12dd818` a bare
`uv run goblin suggest <project>` exits 1 with `goblin suggest: no LLM boundary`.

## Prerequisites

- A Claude Code session with the `Workflow` tool, signed in with subscription OAuth rather than
  an API key (an API key bills per token). The goblin CLI needs no token of its own.
- `uv sync` has been run in the `b2_project_goblin` directory (installs the `goblin` console
  script and its dependencies).
- `gh auth status` shows you are logged in. Grounding reads the target's open issues via `gh`;
  a project with no remote or no auth yields zero issues with a warning, and the run continues
  with less context.
- The target project is a direct child of the dev workspace root, has a discoverable plan doc,
  and has a SUBSTANTIVE project instruction file — CLAUDE.md or AGENTS.md — under the name
  this run grounds on. Existence is not the test: a pointer to the sibling file does not
  satisfy this, and a substantive file under the other name does not rescue it. For the rules,
  see the Instruction-file contract in plan-init/core.md
  ([`../plan-init/core.md`](../plan-init/core.md)); this core applies it by citation and
  deliberately does not restate it. The installed goblin grounds on `<project>/CLAUDE.md` only
  and expands no imports. Before launching, read that file; if it is missing or is only a
  pointer to the sibling file, report the unmet precondition and stop.
- `<project>` is a plain directory name: letters, digits, `.`, `_` and `-` only, not starting
  with `.` and not containing `..`. The Workflow interpolates it into shell commands before
  goblin validates it, so check it before launching; any other name is a usage error: report
  it and stop.

## Invocation

```text
/goblin-suggest [--small | --big | --uat] [--n-candidates N] [--n-judges N] <project>
```

- Flags may come before or after `<project>`.
- Bare `/goblin-suggest` (no project): print the usage line above and stop. No Workflow launch,
  no prompt.
- `--small` / `--big` / `--uat` select the mode (mutually exclusive; default `--small`). Two at
  once is a usage error: report it and stop.
- `--n-candidates N` (default 5): candidates to generate.
- `--n-judges N` (default 3): judge arms per candidate; see **grade** for the valid-verdict rule.
- Each `N` must be a positive integer (digits only). The Workflow interpolates both values into
  shell commands and sizes the judge fan-out from `--n-judges`, so any other value is a usage
  error: report it and stop.
- `--brain-dir` is not available on this path: the Workflow passes no store override, so the
  store is the goblin repo's `brain/suggestions/`. Today an atom can still land outside it (see
  the write-boundary note under **Where atoms are persisted**).

Launch from the dev workspace root (only once **Write path held** no longer applies):

```javascript
Workflow({
  scriptPath: "<installed-goblin-suggest-directory>/goblin_suggest.workflow.js",
  args: { project: "toybox", mode: "small", n_candidates: 5, n_judges: 3 }
})
```

If the launch is rejected because the script contains control characters (the installed `.js`
has CRLF line endings on Windows), pass the file's contents inline as `script`, with LF line
endings and the same `args`. The run is identical.

Run one goblin-suggest Workflow at a time. The script writes fixed-name files in the user temp
directory (`goblin_prompts_<project>.json`, `goblin_gen_prompt_<project>.txt`,
`goblin_graded_candidates.json`), and concurrent runs overwrite each other's files.

## Modes

- **`--small` (default)**: small, purely additive, non-disruptive quick wins that need at most
  one clarifying question to start. The cheap path for a bare run.
- **`--big`**: the full-fidelity, bigger-improvement framing.
- **`--uat`**: a different activity. It triages the project's operator-asks for AI takeover and
  persists `uat-*.md` atoms, not suggestion atoms. **Held**; see **UAT triage (held)**.

`--small` and `--big` share the pipeline and the four-axis rubric; only the generator's
instruction framing differs. **Both are held today**; see **Write path held**.

## Write path held (`--small` / `--big`)

After the usage checks (including the `<project>` name check) and any `required_tool_missing`
halt the host owes, `--small` and `--big` print
`goblin-suggest: --<mode> is held: goblin's atom write path is unsafe; nothing was written.`
(`<mode>` is `small` or `big`) and stop. Nothing else runs: no instruction-file read, no
Workflow launch, no goblin command. Reason: the only persisting path is unsafe in two layers.
The hold keeps this skill off both; it repairs neither.

- **goblin's write path.** The generator chooses each atom's `project`, and goblin builds the
  atom's file path from it, so a crafted value can create directories and overwrite existing
  workspace files outside `brain/suggestions/`, including always-loaded instruction and rule
  files (see **Known deviations** and **Write boundary**). goblin's write path stays unsafe for
  every caller until goblin itself binds each atom's `project` to the run's argument and
  validates it before building any path.
- **The Workflow relays.** Two relay arms receive generator text derived from untrusted DATA
  in tool-using contexts: a PowerShell command line, and the persist relay's file-write and
  shell instructions. Candidate text can therefore steer command execution or file writes
  outside goblin's write path (see **Known deviations** and **Write boundary**). goblin's
  engine repair changes neither relay.

Lift the hold only by editing this core, and only when ALL of these hold: (1) goblin's engine
repair above has landed; (2) the judge-prompt relay passes candidate JSON to goblin through a
non-interpreting data transport (for example a file or stdin that is never parsed as code),
never inside a command line; (3) the persist relay moves the graded JSON to its file through a
non-interpreting channel, or runs tool-restricted and handles candidate text only as enveloped
data; and (4) each of those three repairs has been independently verified: an independent
security review covering goblin's write path and both relays has passed before the edit, and
a runtime qualification of the repaired path passes before the edited core is installed. The
engine repair is necessary, not sufficient: until all four hold, this hold stays in force
whatever else lands. The pipeline and output sections below are the contract to restore then.

## What it does (`--small` / `--big`)

None of these steps runs while the write path is held (see **Write path held**).

1. **ground + export**: the generator arm runs, from `b2_project_goblin`,
   `uv run goblin suggest <project> --export-prompts --<mode> --n-candidates N --n-judges N`.
   Grounding validates the project argument and reads its real CLAUDE.md or AGENTS.md (the one
   this run grounds on; today goblin reads CLAUDE.md only) + plan + open issues + memory atoms
   (the project's Claude-managed memory directory). All fetched content is
   enveloped as untrusted DATA (prompt-injection defense) before any model sees it. No model
   call happens here.
2. **generate**: the same arm reads the exported generation prompt and returns N candidates
   (`title`, `description`, `anchor`, `project`, `rationale`). The prompt also asks for
   `goal_condition` and `goal_able`; see **Known deviations**. Each candidate must be anchored
   to a real artifact in the DATA; ungrounded advice is forbidden. On this path nothing drops a
   malformed candidate or checks its `project` at parse time (see **Known deviations**).
   **Anchor contract** (owned by `/goblin-do`'s liveness check): the whole anchor is either an
   issue reference (`#N` or `<word>#N`, which must be OPEN when acted on) or one repo-relative
   path tracked by git, optionally with `:<line>`. Anything else (a section reference, a quoted
   line, a path with a parenthetical, two artifacts joined by `+`) is a prose anchor, and
   `/goblin-do` refuses it as stale. Put prose context in the description or rationale.
3. **grade**: for EACH candidate a relay arm passes the candidate's JSON to
   `--build-judge-prompt` as data that is never parsed as code (the installed Workflow does
   not; see **Known deviations**);
   then fan out `--n-judges` judge agent calls IN PARALLEL, each in a fresh context separate
   from the generator, scoring four axes (feasibility, fit, leverage, reversibility) 1–5. **Grading contract:** per-axis median over the valid verdicts;
   composite = mean of the four axis-medians; a candidate with fewer than `--n-judges` valid
   verdicts is DROPPED, never scored on a partial set. Grading does not branch on mode.

   **Optional local-judge offload (switchboard, INERT BY DEFAULT).** This judge fan-out is the
   one role this skill may route to a local model (tier-offload task_class
   `goblin-suggest-judge`; Switchboard Decision 9, a cheap parallel rubric-scoring array). It is
   **off unless switchboard offload is enabled for this slice**. For each judge call, first
   consult the switchboard judge entrypoint with the rubric prompt:
   `python -m switchboard judge --site goblin-suggest-judge --prompt-file <judge-prompt-file>`
   (prints one JSON object, always exits 0). On a **verdict**, use it as that judge's advisory
   vote. On a **defer** (`{"defer": true, ...}`), which is ALWAYS the case when offload is off,
   the slice is disabled, or the model is down, slow or wrong-shaped, fall back to the normal
   Claude judge agent for that vote. The local model only advises an axis vote; the
   median/rank/persist logic is unchanged and never gated by the local model.
   **Status: not wired.** The installed Workflow's judge arms never consult switchboard, so
   every vote comes from a Claude judge arm whatever the switchboard configuration says.
4. **rank + discriminate + persist**: the graded candidates reach a temp JSON file as data,
   never as instructions to a tool-using arm (the installed Workflow does not; see **Known
   deviations**), and a relay arm runs `--from-candidates-json <file> --<mode>`. goblin
   orders the survivors by composite, descending (deterministic tie-break by title). It flags
   the ranking as non-discriminating when the composite spread is below 0.5 or fewer than two
   candidates survived. It persists each survivor (see **Where atoms are persisted**).
5. **report**: relay the persist arm's CLI output verbatim, then print three advisory lines:
   - `Scoring: Workflow means; graded <graded_count>, dropped <dropped> (zero-verdict only).`
   - `Anchors: <k> of <n> ranked anchors are prose; /goblin-do will refuse them: <anchors>`,
     or `Anchors: all <n> ranked anchors are issue refs or paths.` Judge by shape only, from
     the printed `(anchor: ...)` values.
   - `Write boundary: <k> of <n> persisted paths are out of bounds: <paths>`, or
     `Write boundary: all <n> persisted paths are in bounds.` Judge by the printed
     `Persisted` path text only. A path is in bounds when the text after its first
     `brain/suggestions/` (or `brain\suggestions\`) segment holds no further separator, no
     `..` and no `:`, and its file name starts with `sugg-<project>-` for this run's
     `<project>`. After a traceback, print
     `Write boundary: unknown (the persist loop stopped; written paths were not listed).`

   All three lines are advisory. Never edit, move, delete, or re-run atoms or any flagged file
   because of them. A flagged path means goblin may already have replaced an existing file
   there; report it and leave it for the operator.

**Failure.** If the Workflow tool is unavailable, or the Workflow throws (for example,
generation returned no candidates), relay the error and stop. Nothing was persisted unless the
throw came from the persist arm after its CLI command ran. The persist arm's output is relayed
verbatim whatever it says, so a `--from-candidates-json` error reaches the operator in step 5.
Two seam failures do not stop the run cleanly (see **Known deviations**): a failed
judge-prompt relay is still scored, and a persist-time validation error can leave earlier
atoms written but unlisted. Do not edit, move or delete atoms to recover. A re-run
never duplicates an atom, but it rewrites same-identity atoms under the update rules below,
including an operator-set `status`.

## Known deviations in the installed Workflow

The installed `goblin_suggest.workflow.js` does not yet meet the contract above. Until it is
corrected, these hold. Step 5 reports the first two on every run and flags the out-of-bounds
paths the last one can produce; the rest are documented here only:

- **Scores** are per-axis means, not medians, and a candidate is dropped only when it has zero
  valid verdicts. `--from-candidates-json` accepts the supplied scores as they are and always
  prints `Dropped by partial-verdict guard: 0`. The Workflow's return value carries the real
  `graded_count` and `dropped`.
- **Anchors**: the generator is still told it may anchor to "a specific plan line", which
  usually yields a prose anchor.
- **Goal fields are dropped.** The Workflow's candidate schema and JSON seam omit
  `goal_condition` and `goal_able`, so every atom it writes persists `goal_condition: ""` and
  `goal_able: false`. `/goblin-do` then renders a seed, never a `/goal` block, for that atom.
- **Grounding failures are hidden.** The export step discards stderr, so a bad project or a
  missing plan usually surfaces as a generation failure rather than as goblin's own message.
  The generator arm may instead return candidates that are not grounded in goblin's export.
- **Judge-prompt failures are scored.** The Workflow does not check the `--build-judge-prompt`
  relay. An empty reply or an error message becomes the judge prompt; the schema-bound judges
  can still return scores, and the candidate is then ranked and persisted.
- **Two relays hand untrusted-derived text to tool-using arms.** Every candidate field is
  generator output written from untrusted DATA (issue text included), and nothing neutralizes
  it before the relays. (a) The judge-prompt relay is told to run a PowerShell command line
  that carries each candidate's JSON inside a single-quoted string escaped for the ASCII
  apostrophe (U+0027) only (`goblin_suggest.workflow.js:122-129`). PowerShell also treats the
  typographic single quotes (U+2018 to U+201B) as string delimiters, so candidate text can
  close the string, and what follows can run as PowerShell commands; this needs no model
  misbehavior, only the relay's instructed verbatim run. (b) The persist relay is given the
  whole graded JSON verbatim inside its own file-write and shell instructions (`:187-201`),
  with no untrusted-data envelope, so candidate text can steer that arm to run commands or
  write files anywhere its tools reach, with no `-<slug>.md` name limit. goblin's own judge
  prompts fence candidate text as untrusted data; these two relays do not. Either channel can
  run commands or write files outside goblin's write path, the step-5 `Write boundary:` line
  cannot see such writes, and goblin's engine repair changes neither channel. This is the
  second reason `--small` and `--big` are held (see **Write path held**).
- **No parse-time checks on the JSON seam.** `--from-candidates-json` builds candidates
  directly, without goblin's parse-time validation. Malformed candidates are not dropped,
  candidate text skips the untrusted-data neutralization pass, and each atom's `project` (and
  so its filename, `sugg-<project>-<slug>.md`) comes from the generator's output rather than
  the run's argument. goblin checks that `project` only for being non-empty, and only after it
  has built the atom path and created the path's directory. A `project` containing a path
  separator, `..` or `:` can therefore place the atom, and create directories, outside
  `brain/suggestions/`: a repo-slug value such as `owner/repo` writes into a subdirectory that
  goblin's non-recursive atom listings (`/goblin-do` resolution, `goblin prune`) never see, and
  a `..` path can leave the goblin repo entirely. **It can also overwrite.** When a file
  already exists at the resolved path and does not read as a suggestion atom, goblin treats it
  as a corrupt atom and replaces it; only a readable suggestion atom with a different identity
  is skipped. So a crafted `project` can replace an existing file named `<anything>-<slug>.md`
  (`<slug>` from the candidate title) wherever the path reaches, including an always-loaded
  workspace instruction or rule file, with atom text
  the generator wrote from untrusted DATA. goblin keeps no copy of the replaced file. The
  generator reads untrusted DATA, so this value is model-steerable. A multi-line description
  or an empty anchor raises a validation error inside the persist loop: the CLI ends with a
  traceback, atoms written before it stay, and none are listed.

## UAT triage (held)

`--uat` prints `goblin-suggest: --uat is held: no production UAT pipeline; nothing was written.`
and stops before launching the Workflow. goblin implements the UAT pipeline only behind
injected model callables. The Workflow has no UAT path: `--export-prompts --uat` returns the
suggestion prompt, and `--from-candidates-json --uat` would persist `sugg-` atoms tagged
`mode: uat` with four-axis scores, a shape the schema reserves for `uat-` atoms. Existing
`uat-*.md` atoms remain valid input to `/goblin-do`.

The contract to restore once a UAT bridge exists (unchanged):

1. **ground (uat)**: scan the neutralized sources for operator-asks (`## Manual UAT` /
   `### M<n>:` plan blocks, `**Type:** operator|wait` steps, and operator-handoff cue phrases
   such as "please run", "operator confirms/runs", "run X next"); one ask per unit of work.
2. **generate (uat)**: one task per distinct ask (`--n-candidates` does not apply), anchored to
   the source ask; ungrounded tasks are rejected at parse time.
3. **assess (uat)**: `--n-judges` parallel judge calls per task vote `ai_doable` and a
   clarifying-question ordinal (`none` < `one` < `many`). Consensus = boolean MAJORITY (a tie
   resolves to **needs-human**) + ordinal MEDIAN. Fewer than `--n-judges` valid verdicts:
   DROPPED.
4. **rank (uat)**: AI-doable with the fewest questions first; human-residual tasks last.
5. **persist (uat)**: `brain/suggestions/uat-<project>-<slug>.md` (slug from the description;
   `mode: uat`; NO `scores`; the triage fields `ai_doable`, `clarifying_question` and
   `human_residual_steps` are the score).

Its output view: per task, a verdict line (`ai_doable=yes|no`, the consensus count, the anchor,
the description). An AI-doable task with exactly one consensus question adds that question; a
task that is not AI-doable adds its `human_residual_steps` (or "(none listed)"); other tasks add
nothing. Then the dropped count and the persisted `uat-*.md` paths.

## How to read the output (`--small` / `--big`)

The relayed CLI output, in order:

- `goblin suggest -- project '<project>'`
- `Ranked shortlist (<n>):`, then per survivor `<rank>. [<composite>] <title>  (anchor: <anchor>)`
  and a line with the four per-axis scores; or `(no candidates survived grading)`.
- `Discrimination: OK (spread <s>) -- <reason>`: the composite scores have real spread.
  `Discrimination: WARN -- NOT discriminating (spread <s>); treat the ranking as low-confidence.`
  followed by `  reason: <reason>`: the rubric scored everything about the same, or fewer than
  two candidates survived. Re-run or inspect the candidates before acting on the order.
- `Judge agreement: WARN -- ...` appears when the judges disagree markedly on a candidate.
- `Dropped by partial-verdict guard: <n>`: always 0 on this path (see **Known deviations**).
- `Persisted <n> atom(s):` and one path per atom written, or `Persisted 0 atoms.`

A traceback in place of this view means the persist loop stopped part-way (see **Known
deviations**). Then the three advisory lines from step 5. The untrusted-data envelope is applied
inside grounding and is not echoed in the output.

## Where atoms are persisted

Atoms are written to `b2_project_goblin/brain/suggestions/`, one markdown + YAML file each,
subject to the write-boundary note below. The id carries no date: `sugg-<project>-<slug>.md`
(slug from the candidate title), or `uat-<project>-<slug>.md`. The distinct prefixes keep the readers isolated. The frontmatter
spec is `brain/SCHEMA.md`, which mirrors `src/goblin/models.py` (models.py wins). A suggestion
atom carries `type: suggestion`, `mode: small|big`, `status: proposed`, `anchor`, `scores`,
`goal_condition`, `goal_able` and `provenance`.

- **Update in place.** A re-run that yields the same project, slug and anchor rewrites that
  file. It keeps `created` and replaces every other field, so an operator-set `status` returns
  to `proposed` and the goal fields take the new run's values. The same slug with a different
  anchor is a conflict: when the existing file reads as a suggestion atom, that candidate is
  skipped with a warning and the file is not overwritten. That skip protects only readable
  suggestion atoms: any other file at the target path is overwritten (see **Write boundary**).
  A candidate with a different title gets a new file.
- **Not git-tracked.** The goblin repo ignores `sugg-*.md` and `uat-*.md` as generated output,
  so a rewritten atom has no git backup.
- **Write boundary.** The intended boundary is that goblin writes only `brain/suggestions/` and
  the Workflow writes only its temp files; nothing runs git or GitHub writes. Today goblin does
  not enforce it: a generator-supplied `project` containing a path separator, `..` or `:` can
  place an atom, and create directories, wherever that path resolves, including a
  `suggestions/` subdirectory, the target project or a path outside the goblin repo. If a file
  that does not read as a suggestion atom already exists there, goblin overwrites it, so
  existing files, including always-loaded workspace instruction and rule files, can be replaced
  with generator-written text (see **Known deviations**). The Workflow does not enforce its
  half either: two relay arms receive candidate text derived from untrusted DATA in tool-using
  contexts, so that text can steer command execution or file writes, git or GitHub writes
  included, outside both `brain/suggestions/` and the temp files (see **Known deviations**).
  That is why `--small` and `--big` are held (see **Write path held**). Stating it here does
  not make it safe: goblin's write path stays unsafe until goblin binds and validates `project`
  before building any path, the relays stay unsafe until both are repaired, and the hold lifts
  only on the full condition in **Write path held**.

## Next step

```text
/goblin-do <id>
```

`/goblin-do` is the single front door for a persisted atom. It rechecks the anchor (an issue
must be OPEN; a path must be tracked), then prints a `/goal` block when the atom is goal-able
(`goal_able: true` and a non-empty `goal_condition`), or otherwise the kind's seed (a
`/plan-feature` seed for a suggestion). It executes nothing. The id is the atom filename stem,
e.g. `sugg-toybox-add-a-smoke-test`. (`goblin handoff` survives only as a deprecated CLI alias;
see [Relationship to other skills](../goblin-do/core.md#relationship-to-other-skills).)

## Relationship to other skills

- **Consumer:** `/goblin-do` reads the atoms; the anchor contract above is its liveness rule.
- **Seeded by:** `/user-gateway`'s do rail emits `/goblin-suggest --small <project>`, then
  `/goblin-do <atom>`. While the write path is held, that seed prints the held line and
  writes nothing; existing atoms stay valid for `/goblin-do`.
- **Sibling:** `/goblin-sweep` persists `obl-` atoms for work a project already owes; this
  skill invents new ideas. `goblin prune` (report-first) lists prose-anchor atoms as delete
  candidates; this skill never runs it.
- `/tier-offload` may enable the switchboard site `goblin-suggest-judge`; see the offload status
  under **grade**.
