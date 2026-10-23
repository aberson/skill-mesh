# Preflight matrix

Each probe below is an independent invocation. None writes a ledger, emits a seed, or produces QUICK COPY.

## Probe A — required contract unavailable

`required_tool_missing: <repo>/_shared/shakedown-engine.md`

The run stops before Step 0 because a required shared contract cannot be read.

## Probe B — empty normalized slug

`user-gateway: topic clarification required; normalized topic slug is empty; ledger not written`

The punctuation-only topic `!!!` does not become `intake-.md`. The operator must supply a topic with a non-empty normalized identity.

## Probe C — ambiguous near matches

`user-gateway: topic clarification required; no exact intake-switchboard.md exists and multiple near-match ledgers were found; ledger not written`

The run does not arbitrarily load either `intake-switchboard-old.md` or `intake-switchboard-ui.md`.

## Evaluation-corpus availability boundary

These probes cover runtime contracts. The repository-only `skills/user-gateway/evals/`
corpus is not an installed runtime dependency. An installed evaluation route without an
explicit `evals_dir` stops with its missing-input result before grading; it does not turn
ordinary `/user-gateway` use into `required_tool_missing`.
