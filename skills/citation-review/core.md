# NOTE: This is the canonical provider-independent contract. Every provider wrapper must load it in full.

## Provider-neutral host abstractions

- This skill ships no supporting assets. The CLI, prompts, calibration fixtures, and contracts live in the `citation-needed/` project; resolve every path below from the coding-root workspace.
- A **judge call** is one isolated fresh-context task/action invocation selected explicitly for the resolved judge model. A named-skill call is not a judge call.
- Model tier names describe capability roles. Resolve them through the current host policy and `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than substituting a stale or weaker model.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Citation review - evidence-check one LLM-facing artifact

Review ONE scanned LLM-facing artifact (a rule, skill, memory, CLAUDE.md or AGENTS.md, or plan) through Citation Needed's calibrated pipeline. Invoke as `/citation-review <workspace-relative-path> [--calibrate]`, or `/citation-review --calibrate` to calibrate without reviewing. With neither a path nor `--calibrate`, run nothing and return HELD with those usage forms.

Run from the coding-root workspace. The Citation Needed CLI is the only database writer. Never open its database directly, reimplement scoring or verification, or modify the reviewed artifact. The allowed writes are CLI-owned database rows, the calibration cache, and rendered breakdowns.

## Judge identity and capability

Before any calibration or review open, resolve one exact `<judge-model-id>`. The provider wrapper supplies the current default; an explicit operator choice overrides it. A sweep parent may supply the exact id as an explicit caller binding, which this contract MUST use unchanged. Pass it to every model-bearing CLI flag and select it explicitly for every judge call:

- `cite calibrate check --model <judge-model-id>`
- `cite calibrate open --reviewer-model <judge-model-id>`
- `cite calibrate commit --model <judge-model-id>`
- `cite review open <path> --reviewer-model <judge-model-id>`

Never use the CLI default `unspecified` or a bare calibration check. Record the model and effort from each native judge receipt when available. If no receipt is available, report the observed model as UNKNOWN; configuration is not proof. Any observed model different from `<judge-model-id>` invalidates those votes and stops that run before commit. Changing the judge id requires a new calibration.

Before the first open, prove that the parent running this contract can dispatch fresh isolated judge siblings. Judges are always depth 1: the parent prepares their inputs, dispatches them directly, and owns every CLI call. Judges never open runs, prepare evidence, commit, spawn children, see another vote, or receive authority to mutate the target. If this capability is absent or inconclusive, return `required_tool_missing` before opening anything. There is no in-context voting fallback.

## Shared parent-owned phase contract

Direct review and `/citation-sweep` use the same four phases. Direct review runs them in order for one path. A sweep parent may call each phase separately for several paths, but it remains the one parent and supplies the already-resolved judge id.

### OPEN

1. Ensure the exact stored path was discovered by `cite scan` (`memory:<project-dir-slug>/<file>.md` is valid). Do not guess a locator.
2. Run `cite calibrate check --model <judge-model-id>`. Stop on every fingerprint or model mismatch. Calibration older than 30 days stops unless the operator explicitly authorized `--accept-aged`; that flag covers age only and must be passed to both check and open.
3. Prove judge dispatch before opening. Then run `cite review open <path> --reviewer-model <judge-model-id>` with `--accept-aged` only when authorized. Capture this command's returned `run_id`; never recover it from “latest run” state or another invocation.
4. Read the complete open JSON, `citation-needed/prompts/extraction.v1.md`, `citation-needed/prompts/classification.v1.md`, and both schemas under `citation-needed/docs/contracts/`. Reuse a prior `choice_key`, including a removed key, for the same underlying decision.

OPEN returns the exact path, run id, frozen artifact identity, prior choices, judge id, and aged-calibration status to its parent. It performs no extraction, search, judging, or commit. An open failure is final for that attempt: do not retry, recalibrate, reopen, clean up, or substitute another run.

### PREPARE

The parent extracts every distinct decision using `extraction.v1.md`, searches the corpus first, and gathers external or internal evidence honestly. Set `literature_searched` only after a real external search and preserve the actual queries. A searched-but-not-found result is valid; an invented citation is not.

Prepare the complete commit payload except for votes. Each judge input contains `classification.v1.md`, exactly one choice, and exactly the citations, support directions, relevance notes, and search queries that would be committed. It contains no expected label, prior label, other vote, orchestrator rationale, or calibration scoring key. Keep preparation data in the parent invocation unless a specifically scoped private artifact is necessary.

Freeze the prepared choice and evidence bytes before judging. If any committed evidence field changes later, discard the affected vote set and judge that choice again with fresh calls; never mix votes across evidence identities.

### JUDGE

The parent dispatches each vote as a fresh depth-1 judge call with `<judge-model-id>` selected explicitly. The preparing parent never casts a vote.

- Start every choice at k=3.
- Preserve every response. An unparseable response becomes the literal `parse-failed`, counted as `contradicted`; never retry, replace, or drop it.
- A tie exists when two or more labels share the top count after that conversion. Add two fresh votes to the same array for k=5, then k=7, preserving all earlier votes.
- A tie at k=7 leaves that run open and uncommitted with HELD. Never commit a tie.
- A missing, failed, capacity-refused, identity-mismatched, or wrong-model judge call leaves the run open and uncommitted. Do not replace it implicitly or borrow a vote from another choice or run.

### COMMIT

The parent validates the complete payload against the current schema and sends it as one UTF-8 JSON object on standard input to `cite review commit --run <run_id>`. Large JSON never goes on argv. Do not supply fetched page text or an API echo; commit performs those verifications itself.

Run `cite report <path>` only after a successful commit and require it to identify the same run id. A failed commit means no review result. Report the path, run id, composite and band, choice and classification counts, breakdown, citations and documented absences, judge id and observed judge receipts, orchestrating model when reported, and aged-calibration use. A held or failed run reports its exact state (`open #<run_id> (uncommitted)` when applicable), blocker, and next action.

## `--calibrate`

Calibration is mandatory, explicit, and never an implicit response to a failed review open.

1. Run `cite calibrate check --model <judge-model-id>`. If VALID, stop calibration work.
2. Otherwise prove depth-1 judge dispatch, then run `cite calibrate open --reviewer-model <judge-model-id>`.
3. Before preparing either anchor, read the complete calibration-open JSON, both current schemas under `citation-needed/docs/contracts/`, `extraction.v1.md`, and `classification.v1.md`. Prepare and judge both anchors through the same PREPARE and JUDGE rules without invoking real review OPEN. The open context's `expected_labels` are the scoring key and never enter a judge input.
4. Validate both complete anchor payloads against the current review-commit schema before submission. If either is invalid, stop without committing. Send exactly `{"good": <payload>, "garbage": <payload>}` as UTF-8 JSON on standard input to `cite calibrate commit --model <judge-model-id>`.
5. Re-run the exact model-bound check and report the CLI verdict.

The real database remains untouched by calibration. A gate failure or parse-fail abort is not a pass. Never rerun calibration in the same invocation to obtain a different result. With a path, continue only after VALID; without a path, stop after calibration.

## Direct-review order

A direct `/citation-review` performs OPEN, PREPARE, JUDGE, COMMIT for its one path. It never opens a second run as an implicit retry. Re-running the skill is a new invocation and a new run. A commit invalidates calibration for a later open only when it adds citation rows; report the next calibration action when that happens rather than claiming every commit always invalidates it.

## Constraints

- Never edit the reviewed artifact or present a proposal as applied.
- Never invent a citation id, corpus hit, external verification, score, band, model receipt, or completed review.
- Never show a judge another vote or the scoring key, drop a parse failure, commit a tie, or let a child spawn a judge.
- Never recalibrate, reopen, retry, abort, or clean up implicitly after a phase failure.
- An uncommitted run is durable partial state, not evidence.

## Next step

Hand a committed review to `/citation-distill <path>`. Use `/citation-sweep <project-slug>` for a bounded project pass; its parent consumes this phase contract directly and returns each run's truthful committed, open-uncommitted, or deferred state.
