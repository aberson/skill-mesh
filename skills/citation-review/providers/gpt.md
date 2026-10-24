# citation-review - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full. The parent owns OPEN, PREPARE, and COMMIT; map each JUDGE vote to one fresh isolated action/task child with no prior conversation and no child-spawn authority.
- Resolve the strong-judging role through the current opus entry in config/model-tier-map.json; do not copy a model id into this adapter. An explicit operator choice or sweep caller binding overrides it. Select the resolved exact id on every judge action and record transport receipts; report UNKNOWN when absent.
- Prove fresh isolated action dispatch before opening. Missing or inconclusive capability returns required_tool_missing; independent judges have no single-context fallback.
- Use structured shell actions for CLI calls. Send UTF-8 payloads on standard input and preserve model-bound calibration, schema, evidence identity, k=3/5/7, and exact run-id gates.
- A timeout, rate limit, provider error, parse failure, or missing receipt is truthful vote/run state. Do not consume a generic retry allowance for judge votes: the core forbids implicit replacement.

## Known GPT limitations

Claude-only session and Artifact surfaces are unavailable. Use only core-authorized file or durable-state forms.

## Output normalization

Return the core report or its HELD/partial-state form with exact path and run id.
