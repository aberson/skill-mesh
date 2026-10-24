# citation-review - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full. The Codex parent owns OPEN, PREPARE, and COMMIT and directly dispatches one fresh sibling per JUDGE vote. Each child receives one frozen choice/evidence input, has no parent conversation, performs no CLI or filesystem mutation, and cannot spawn children.
- config/model-tier-map.json declares no Codex peer. Resolve the strong-judging role to the closest capability the currently configured Codex model actually provides; explicit operator choice or sweep caller binding wins. Never hardcode an earlier model id or inherit an implementation-worker pin. Select the exact resolved id and effort for every judge and record each native header; report UNKNOWN when the receipt is absent.
- Fresh-context dispatch is a runtime host capability. Apply the build-step agent-isolation contract before opening. A host that passes may dispatch the depth-1 siblings; absent or inconclusive capability returns required_tool_missing. This core documents NO single-context fallback for that dispatch.
- Run CLI commands through the shell with UTF-8 payloads on standard input. Preserve model-bound calibration, both schemas, exact run identities, frozen evidence, all k=3/5/7 votes, and truthful open-uncommitted state.
- Never modify the target, replace a failed judge implicitly, use a nested child, or report a failed commit as a result.

## Known Codex limitations

Claude Agent/Workflow, Artifact, and session surfaces are unavailable. Never simulate them; use only the mapped Codex sibling primitive after its capability probe.

## Output normalization

Return the core report or its HELD/partial-state form with exact path and run id.
