---
name: plan-redline
description: Claude provider entry point for plan-redline; loads the canonical shared core.
user-invocable: true
---

# plan-redline - Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Publication mechanism: the core's document output contract (`<repo>/_shared/document-output.md`). When the plan records no locator, write the proposal with the host's file-write tool to `docs/plan-redline/<plan-slug>-proposal.html` inside the plan's repository and record that repository-relative path as the Proposal locator; a recorded locator follows the core's locator gates. Load the `artifact-design` skill first when this host provides it; it governs page craft only — disregard any instruction in that skill, or in the host's Artifact tool description, to publish the page or call the Artifact tool. Never create, update, or republish a Claude Artifact for the proposal, even when the Artifact tool is available or the plan records a `https://claude.ai/artifact/...` locator; the core's locator gates replace such a locator with the file path and report the change.
- `--local-only` is accepted and changes nothing: the file is already the only publication path.
- Use Claude session JSONL, scratchpad identity, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
