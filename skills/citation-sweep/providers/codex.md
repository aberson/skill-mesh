# citation-sweep - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full. The Codex parent owns all artifact OPEN, PREPARE, and COMMIT phases. It never dispatches per-artifact workers or asks a child to spawn judges.
- Resolve one exact judge id through citation-review's current Codex rule and pass it unchanged. Do not hardcode an earlier model or inherit the builder pin. After OPEN ALL, directly dispatch each vote as a fresh depth-1 sibling with that exact id and effort; record native headers and report UNKNOWN when absent.
- Apply the build-step agent-isolation contract before opening. A host that passes may map judge votes to fresh siblings. This core documents NO single-context fallback for that dispatch; an absent or inconclusive capability returns required_tool_missing.
- Preserve project-filtered readiness lists, workspace-wide field labels, the ordered open barrier, exact run ids, frozen evidence, every k=3/5/7 vote, and truthful open-uncommitted/deferred states. Never calibrate, retry, or clean up implicitly.
- Normalize verbosity and never fabricate a citation, model receipt, verdict, or completion.

## Known Codex limitations

Claude Agent/Workflow, Artifact, and session surfaces are unavailable. Never simulate them; use only the mapped Codex sibling primitive after its capability probe.

## Output normalization

Return only the core's scope, per-path states, queue results, failures, and next actions.
