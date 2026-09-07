# citation-sweep - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Preserve the calibration gate verbatim: `cite calibrate check` through Codex's shell tool first, and STOP if it is invalid. An uncalibrated sweep is not evidence.
- Fresh-context dispatch is a runtime HOST capability, not a provider-wide Codex constant: apply the separate build-step agent-isolation contract before the first isolated arm, and a host that passes it may map the core's per-artifact review work onto one isolated fresh-context worker per artifact, under the terse return contract the core fixes -- path, run id, band, number of choices, citation/absence summary, blocker -- with longer detail staying in the Citation Needed breakdown/queue artifacts. This core documents NO single-context fallback for that dispatch, so on a host that does not pass, halt visibly with `required_tool_missing`, naming the per-artifact review-worker dispatch as the core step that could not run. A serial in-session rail is NOT that fallback: writing one is a CORE edit with its own review. Never widen the return contract to compensate, and never silently pass an unavailable review.
- Cluster genuinely near-duplicate decisions BEFORE reviewing, so equivalent claims do not get independent citation searches or duplicate durable keys.
- Preserve the three-way distinction between evidence-backed, internal-only, and documented no-literature-found results; collapsing them into one bucket erases the sweep's whole finding.
- Never fabricate a corpus hit, an external verification, a calibrated verdict, or a completed review; stop rather than substituting a synthetic sweep for live evidence. Never edit a target artifact.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: scope, clusters, completed and blocked reviews, queue rows, and any producer/API failure. Preserve locked strings, the per-artifact return fields, schemas, and command ordering exactly; reject missing required fields instead of inferring success.
