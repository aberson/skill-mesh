# skill-eval-setup - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host
  abstractions; it never weakens a gate the core defines. Resolve the exact target repository
  before any write, keep installed generated targets read-only, and preserve the catalog-lifecycle
  stop.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The generated Part 3 loop text carries the producer/grader split (invariant 1, non-relaxable) VERBATIM. This host authors that text; it never executes the loop, and it must not soften the fresh-context-grader wording to fit whatever the authoring host happens to be able to execute.
- The parent Codex session owns every producer, generator, and grader dispatch. Keep producers
  and graders in separate isolated contexts, and invoke the shipped `grader_prompt.py` and
  `score_skill_absolute.py` from the profile's `_shared` directory. The optional repository
  helper is safe only for the core's `--dry-run` previews; its generate, `--fleet` write,
  and `--verify-only` paths are not wired production entry points.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow
  tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them.
  Use Codex-native isolated agents when available; otherwise return `required_tool_missing`
  before golden writes. Never simulate a missing tool.
- On timeout, rate limit, provider 5xx, parse failure, missing isolation, or missing shipped
  scorer, return the router reason code and consume at most the shared cross-cloud retry
  allowance. Never silently omit a core gate, and never mark a corpus entry verified without
  the production helper's three-trial result.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
