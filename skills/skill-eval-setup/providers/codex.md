# skill-eval-setup - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The deliverable is authored files and a copy-paste loop prompt -- Codex's file tools cover the whole Part 1/2/3 output shape.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The generated Part 3 loop text carries the producer/grader split (invariant 1, non-relaxable) VERBATIM. This host authors that text; it never executes the loop, and it must not soften the fresh-context-grader wording because Codex itself could not honor it.
- The golden-corpus generator (root-only `skill-eval-setup/scripts/generate_bad_examples.py`) runs through Codex's shell tool; its sub-agent dispatch and parallel `--fleet` batches live inside the script, not in this host. Where the dispatcher's backend is unavailable in this environment, use the core's documented non-dispatch modes -- `--dry-run`, `--verify-only`, and hand-crafted good/bad examples -- and report which mode ran; the script-deterministic verification gate is unchanged in every mode.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never mark a corpus entry verified without the script's own verification result.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
