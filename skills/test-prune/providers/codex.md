# test-prune - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The evidence bar, the triage table, the confirmation gate, and the tests-only scope fence stay exactly as the core states them.
- Tier names in inherited procedures name capability roles. For Phase 1, use only the Codex host's actual model-selection controls and record the configured model each arm ran. A GPT/Copilot router override is not a native Codex control. If the host cannot select a suitable capability, return `required_tool_missing` rather than claiming an override or weakening the gate.
- Fresh-context, read-only dispatch is a runtime host capability, not a provider-wide Codex constant. A capable host may map the Phase 1 arms to fresh sibling agents with only their assigned files and no write-capable tools. This core has no single-context fallback: if native isolation or read-only enforcement is absent, halt with `required_tool_missing`, name the Phase 1 dispatch, and do not substitute an in-session scan.
- The Phase 2 verify gate, Phase 3 quality gates, and Phase 4 report are grep, citation, and shell work that run unchanged when the flagging phase can run; the triage table remains the gate and deletions are never auto-executed.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider failure, malformed child output, or missing required adapter, report the actual native failure and stop the affected arm or run as the core requires. Do not invent a router reason, cross-provider retry, or implicit fallback. Return `required_tool_missing` when a required native capability is absent. Never silently omit a core gate or delete a test without the cited evidence the core requires.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve its statuses, paths, command ordering, and evidence fields exactly; reject missing required fields instead of inferring success. Report only retries the native host actually performed.
