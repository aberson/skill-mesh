# user-debug - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The forced primary-source investigation, the Diagnosis Block shape, and the bug-vs-feature re-route contract stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Step 1's investigation and Diagnosis Block run natively and remain durable output. Step 2's independent reproduction and Option 4's tie-breaker are capability-conditioned isolated arms; apply the contract below before either dispatch. The core documents no single-context substitute: never compare the parent's diagnosis against itself and call it independent.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Independent-diagnosis capability contract

| Contract field | Required Codex mapping |
|---|---|
| `fresh-context-dispatch` | Treat no-history child dispatch as a runtime host capability, not a provider-wide claim. Inspect the active callable schema and require explicit no-history dispatch such as `collaboration.spawn_agent(fork_turns="none")`, or a semantically equivalent primitive. Before use, a non-mutating probe must show that the child cannot read parent session state; never infer this boundary from a provider name, function name, model label, or non-inheritance claim alone. |
| `step-2-arm` | The parent directly spawns Step 2 as a fresh sibling with explicit no-history dispatch, never as a reuse, follow-up, or child successor. Its prompt contains only the symptom, repro instructions, and bounded read-only primary-source scope. It excludes the parent's diagnosis, root-cause hypothesis, task state, handoff, session material, and Fix Design. The child returns repro evidence and its diagnosis only. |
| `option-4-arm` | Only after the core's Option 1 re-investigation, the parent directly spawns Option 4 as another separate fresh sibling with explicit no-history dispatch. It is not a reuse, follow-up, or child successor of Step 2, and receives no prior diagnosis or Diagnosis Comparison. It receives only the same symptom, repro instructions, and bounded read-only primary-source scope, then returns repro evidence and diagnosis only. |
| `parent-authority` | The parent alone resolves and writes the Diagnosis Comparison, chooses the core's divergence option, authors Fix Design, and confirms it with the user. Children do not compare diagnoses, resolve a tie, design a fix, confirm a fix, or mutate the project. |
| `shared-filesystem-tools` | Shared filesystem and tools are permitted for bounded read-only primary-source investigation; they are not OS isolation. The required boundary is fresh context and parent authority. Snapshot/audit the allowed scope after every child; unexpected child mutation invalidates that arm and fails closed rather than becoming evidence. |
| `missing-capability` | If the active host is ordinary Codex CLI, lacks an explicit no-history primitive, or the non-mutating probe is absent, failed, or inconclusive, stop visibly with `required_tool_missing` at Step 2 before any Fix Design or code change. If capability later becomes unavailable for Option 4, stop visibly with `required_tool_missing` at that tie-breaker; never reuse, follow up, or substitute a prior child. |

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never ship a fix whose diagnosis the independence check did not actually corroborate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
