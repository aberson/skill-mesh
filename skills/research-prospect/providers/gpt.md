# research-prospect - GPT entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Map Step 2 to one fresh-context GPT/Copilot action per resolved project and dispatch all independent actions in one parallel call. Each child is single-shot and read-only; orchestration, JSON validation, filtering, prefix assignment, and rendering stay in the parent.
- Resolve the Sonnet capability role through `config/model-tier-map.json`; an explicit router override may select an equal-or-stronger peer. If the host cannot provide isolated parallel actions, return `required_tool_missing` for Step 2. Sequential or in-session scanning is not a fallback.
- Resolve workspace and project memory through the host's own project-memory convention. Never translate an absent project store into a made-up Claude path.
- The rendered `/deep-research-pinned` line is a command for a fresh Claude workflow window because that harness is not provided by this adapter. Render it faithfully and do not claim GPT launched or natively executed it. Medium-depth lines remain host-neutral narrow research prompts.
- `--session-wrap` requires a stable ID proven to belong to this executing host session plus access to the task-state derive helper. When either is unavailable, print the core's topics-not-parked message and stop after the menu. Never borrow a parent/foreign ID, write `current.md`, or claim a rollup regeneration from a direct shared-file write.
- After a successful own-session park and helper call, invoke session-wrap through the host's named-skill mechanism. A missing invocation adapter is `required_tool_missing`; it does not erase the already parked entries.

## Output normalization

Return only the core-defined menu and guard messages. Preserve JSON rejection, dropped-topic, empty-state, and QUICK COPY contracts exactly.

## Unsupported capabilities

Claude Agent/Workflow tools, Claude scratchpad identity, and native execution of `deep-research-pinned` are unavailable. Use only the explicit mappings above and surface missing runtime capabilities without weakening the core.
