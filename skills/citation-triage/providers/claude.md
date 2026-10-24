---
name: citation-triage
description: Claude provider entry point for citation-triage; loads the canonical shared core.
user-invocable: true
---

# citation-triage - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting and preserve its gates, no-retry rule, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Never infer an operator decision from rank, from model output, or from a citation alone. This skill is the recorder; the decision is the operator's.
- Recheck the displayed row identity immediately before invoking exactly one of `--keep` / `--cut` / `--rewrite` through the Bash tool. Add `--by <operator>` only when supplied.
- On cancel, make no further resolve calls; preserve and report earlier durable resolutions. Never edit or apply a target artifact.

## Output normalization

The closing output is the core's Report or HELD form; the presentation and row-bound operator questions remain required interactive output. Preserve exact row identities, receipts, and recorded/open/deferred/unknown states.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never substitute an inferred decision for an operator one.
