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
- Publication mechanism, used only when the plan records no `Proposal:` locator or the operator asks for a move: when this session exposes a Claude Artifact tool that keeps the proposal private to the operator (the tool's default), load the `artifact-design` skill first when this host provides it, author the page in the session scratchpad, and publish it as a private Artifact; never make it public or share it unless the operator asks. Use its URL as the stable Proposal locator. Otherwise use the core's standalone-HTML fallback: write the file beside the plan (default `documentation/<plan-slug>-proposal.html`, the Codex and GPT default) and store that repository-relative path as the locator.
- Republish follows the core's locator gates: pass the recorded Artifact URL from the plan's `Proposal:` line to the Artifact tool so the same Artifact updates, including in a new session; keep a recorded repository HTML path as the target; if a recorded Artifact cannot be updated, use the core's HTML fallback, never a second Artifact.
- When the caller passes `--local-only`, skip the Artifact branch entirely: never create or update an Artifact, use the core's standalone-HTML fallback, and treat a recorded Artifact URL as an Artifact this session cannot update, which the core's locator gates report as stale.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
