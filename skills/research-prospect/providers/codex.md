# research-prospect - Codex entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. The pending-decision evidence bar, depth-specific command forms, render-time drops, and mandatory QUICK COPY block remain exactly as the core defines them.
- Fresh-context dispatch is a runtime host capability, not a provider-wide Codex constant. Before Step 2, apply the installed build-step agent-isolation capability contract. A host that proves the capability may map each project to a fresh sibling child and dispatch all siblings in parallel; each child is read-only and single-shot, while validation and consolidation stay in the parent.
- If that isolation contract is unavailable or fails, return `required_tool_missing` naming Step 2's parallel per-project fan-out. Step 1 may still resolve and report the project list. Never replace the arms with parent-context scans, sequential children, or a claimed native Codex fan-out.
- Resolve the Sonnet role to the closest capability the configured Codex model actually provides; `config/model-tier-map.json` declares no Codex peer. An unavailable required capability is visible rather than downgraded.
- Render high-depth `/deep-research-pinned` lines as commands for a fresh Claude workflow window. Codex does not supply that workflow through this adapter, so do not launch it or claim native execution. Medium-depth lines remain narrow prompts.
- `--session-wrap` is supported only when the runtime exposes a stable ID proven to belong to this executing Codex session and the task-state derive helper is available. The current adapter binds neither merely by being on Codex. Without both, print the core's topics-not-parked message after the menu and stop. Never use `CODEX_THREAD_ID` inherited from a parent process, a freshest-session guess, another host's ID, or a direct `current.md` write.
- After a successful own-session park, load session-wrap's installed skill and core and execute its bare same-session path. Preserve its identity preflight and triage; a missing dependency is reported, never simulated.

## Output normalization

Emit only the core's operator-facing menu and guard results. Never reveal hidden chain-of-thought or present a menu that the required fan-out did not produce.

## Unsupported capabilities

Claude Agent/Workflow tools, scratchpad/session paths, Artifact actions, and native `deep-research-pinned` execution are unavailable. Missing fan-out, own-session identity, derive-helper, or named-skill capability remains visible at the step that requires it.
