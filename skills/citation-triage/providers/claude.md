---
name: citation-triage
description: Claude provider entry point for citation-triage; loads the canonical shared core.
user-invocable: true
---

# citation-triage - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Never infer an operator decision from rank, from model output, or from a citation alone. This skill is the recorder; the decision is the operator's.
- Invoke exactly ONE of `--keep` / `--cut` / `--rewrite` per decision through the Bash tool, adding `--by <operator>` when the operator identity is supplied.
- On cancel, write nothing -- no partial resolution and no placeholder row. Never edit or apply a target artifact.

## Output normalization

Return only the core's operator-facing output: the presented queue rows and the recorded decisions. Preserve exact locked strings, proposal IDs, and the keep/cut/rewrite enum.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never substitute an inferred decision for an operator one.
